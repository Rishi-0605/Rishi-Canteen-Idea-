"""HTTP client shared by network providers.

- rate limit per host (min interval between requests)
- retries with exponential backoff on network errors, 429 and 5xx
- SQLite response cache with a TTL (so re-running an analysis does not re-hit exchanges)
- every request (cache hit or not) is reported to `on_fetch` for the source log

Uses `requests` when available. No credentials are ever logged: only the URL
without its query string's secret-looking parameters.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from contextlib import contextmanager
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Callable, Optional

from ..models import now_ist

try:  # pragma: no cover - import guard
    import requests
except ImportError:  # pragma: no cover
    requests = None


class FetchError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, url: str = ""):
        super().__init__(message)
        self.status = status
        self.url = url


SECRET_PARAMS = ("key", "token", "apikey", "api_key", "secret", "password", "sig")


def redact(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    if not parts.query:
        return url
    q = [(k, "REDACTED" if any(s in k.lower() for s in SECRET_PARAMS) else v)
         for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))


@contextmanager
def _connect(path: Path):
    """Commit and always close; sqlite3's own context manager leaves the connection open."""
    db = sqlite3.connect(path)
    try:
        with db:
            yield db
    finally:
        db.close()


def parse_json(body: bytes, url: str = ""):
    """Decode a JSON API response. A 200 status with an HTML body (bot-protection or
    login page) is a failed retrieval, not data: raise with a clear reason."""
    import json
    text = body.decode("utf-8", "replace").lstrip("\ufeff").strip()
    if not text:
        raise FetchError("empty response body", url=redact(url))
    if text[:1] == "<":
        hint = "HTML page instead of JSON (bot protection, login or error page)"
        low = text[:2000].lower()
        if "access denied" in low or "akamai" in low or "captcha" in low:
            hint = "HTML 'access denied' / bot-protection page instead of JSON"
        raise FetchError(hint, url=redact(url))
    try:
        return json.loads(text)
    except ValueError as exc:
        raise FetchError("invalid JSON: %s" % exc, url=redact(url))


class ResponseCache:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        with _connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS http_cache (key TEXT PRIMARY KEY, url TEXT, "
                       "fetched_at REAL, status INTEGER, body BLOB)")

    @staticmethod
    def key(url: str, headers: Optional[dict]) -> str:
        return hashlib.sha256((url + "|" + repr(sorted((headers or {}).items()))).encode()).hexdigest()

    def get(self, key: str, ttl_seconds: float) -> Optional[tuple]:
        with self._lock, _connect(self.path) as db:
            row = db.execute("SELECT fetched_at, status, body FROM http_cache WHERE key=?", (key,)).fetchone()
        if row and (time.time() - row[0]) <= ttl_seconds:
            return row
        return None

    def put(self, key: str, url: str, status: int, body: bytes) -> None:
        with self._lock, _connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO http_cache VALUES (?,?,?,?,?)",
                       (key, redact(url), time.time(), status, body))


class HttpClient:
    def __init__(self, user_agent: str, timeout: float = 20, max_retries: int = 3,
                 backoff: float = 2.0, cache: Optional[ResponseCache] = None,
                 cache_ttl_seconds: float = 12 * 3600,
                 on_fetch: Optional[Callable[[dict], None]] = None,
                 sleep: Callable[[float], None] = time.sleep,
                 transport: Optional[Callable] = None, capture_dir: Optional[Path] = None):
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.cache = cache
        self.cache_ttl = cache_ttl_seconds
        self.on_fetch = on_fetch
        self.sleep = sleep
        self.capture_dir = Path(capture_dir) if capture_dir else None  # save raw responses as test fixtures
        self._last = {}
        self._min_interval = {}
        self._session = requests.Session() if (requests and transport is None) else None
        # transport(url, headers, timeout) -> (status, body bytes); injectable for tests
        self.transport = transport or self._requests_transport

    def set_min_interval(self, host: str, seconds: float) -> None:
        self._min_interval[host] = seconds

    def _requests_transport(self, url, headers, timeout):
        if self._session is None:
            raise FetchError("the 'requests' package is not installed", url=url)
        resp = self._session.get(url, headers=headers, timeout=timeout)
        return resp.status_code, resp.content

    def _throttle(self, host: str) -> None:
        gap = self._min_interval.get(host, 0)
        last = self._last.get(host)
        if gap and last is not None:
            wait = gap - (time.monotonic() - last)
            if wait > 0:
                self.sleep(wait)
        self._last[host] = time.monotonic()

    def _capture(self, url: str, provider: str, body: bytes) -> None:
        import json
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256(body).hexdigest()
        name = "%s-%s" % (provider or "http", sha[:16])
        (self.capture_dir / (name + ".body")).write_bytes(body)
        (self.capture_dir / (name + ".meta.json")).write_text(json.dumps(
            {"url": redact(url), "provider": provider, "retrieved_at": now_ist().isoformat(), "sha256": sha, "bytes": len(body),
             "note": "captured live response; real-source fixture"}, indent=1), encoding="utf-8")

    def _log(self, **entry) -> None:
        if self.on_fetch:
            entry.setdefault("retrieved_at", now_ist().isoformat())
            self.on_fetch(entry)

    def get(self, url: str, headers: Optional[dict] = None, provider: str = "",
            use_cache: bool = True) -> bytes:
        hdrs = {"User-Agent": self.user_agent}
        hdrs.update(headers or {})
        ckey = ResponseCache.key(url, headers)
        if use_cache and self.cache:
            hit = self.cache.get(ckey, self.cache_ttl)
            if hit:
                self._log(provider=provider, url=redact(url), status=hit[1], cache_hit=True,
                          bytes=len(hit[2]), sha256=hashlib.sha256(hit[2]).hexdigest())
                return hit[2]
        host = urllib.parse.urlsplit(url).netloc
        attempt, last_err = 0, None
        while attempt <= self.max_retries:
            self._throttle(host)
            try:
                status, body = self.transport(url, hdrs, self.timeout)
            except FetchError:
                raise
            except Exception as exc:  # network error: retry
                detail = re.sub(r"\?[^\s'\"]*", "?<query redacted>", str(exc))[:180]  # never echo query strings (may hold keys)
                last_err = FetchError("network error: %s: %s" % (exc.__class__.__name__, detail), url=redact(url))
                status, body = None, b""
            if status is not None:
                if status == 200:
                    if self.cache and use_cache:
                        self.cache.put(ckey, url, status, body)
                    if self.capture_dir:
                        self._capture(url, provider, body)
                    self._log(provider=provider, url=redact(url), status=status, cache_hit=False,
                              bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
                    return body
                last_err = FetchError("HTTP %s" % status, status=status, url=redact(url))
                if status not in (429, 500, 502, 503, 504):
                    break  # 4xx other than 429: retrying will not help
            attempt += 1
            if attempt <= self.max_retries:
                self.sleep(self.backoff * (2 ** (attempt - 1)))
        self._log(provider=provider, url=redact(url), status=getattr(last_err, "status", None),
                  cache_hit=False, bytes=0, error=str(last_err))
        raise last_err
