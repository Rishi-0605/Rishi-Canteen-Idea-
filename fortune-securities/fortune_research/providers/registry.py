"""Provider registry: builds the configured providers and serves each
capability from the first provider (in priority order) that returns data.

Adding a provider (a paid vendor API or an MCP-backed bridge):
  1. subclass providers.base.Provider, set name / official / capabilities;
  2. register a factory with `register_factory("myvendor", fn)` where
     fn(settings, http) -> Provider (read its key with config.secret(env_name));
  3. list "myvendor" under [providers] for the capabilities it serves.
"""

from __future__ import annotations

from typing import Callable

from ..config import Settings
from .base import CAPABILITIES, ProviderError
from .http import FetchError, HttpClient, ResponseCache
from .local_files import LocalFilesProvider

_FACTORIES: dict = {}


def register_factory(name: str, fn: Callable) -> None:
    _FACTORIES[name] = fn


def _nse(settings, http):
    from .nse import NSEProvider
    return NSEProvider(http, max_bhav_days=settings.get("providers.nse.max_bhav_days", 400),
                       max_filings=settings.get("providers.nse.max_filings", 8))


def _bse(settings, http):
    from .bse import BSEProvider
    return BSEProvider(http)


def _yahoo(settings, http):
    from .yahoo import YahooProvider
    return YahooProvider(http)


def _rss(settings, http):
    from .rss import RSSProvider
    return RSSProvider(http, settings.get("providers.rss.feeds", []),
                       settings.get("providers.rss.allowed_domains", []))


def _ir(settings, http):
    from .ir import IRProvider
    return IRProvider(http)


register_factory("ir", _ir)
register_factory("nse", _nse)
register_factory("bse", _bse)
register_factory("yahoo", _yahoo)
register_factory("rss", _rss)


class Registry:
    def __init__(self, settings: Settings, on_fetch=None, http: HttpClient = None):
        self.settings = settings
        self.http = http or HttpClient(
            user_agent=settings.get("http.user_agent"), timeout=settings.get("http.timeout_seconds", 20),
            max_retries=settings.get("http.max_retries", 3), backoff=settings.get("http.backoff_seconds", 2.0),
            cache=ResponseCache(settings.path("general.data_dir") / "http_cache.db"),
            cache_ttl_seconds=settings.get("http.cache_ttl_hours", 12) * 3600, on_fetch=on_fetch)
        self.providers: dict = {"local": LocalFilesProvider(settings.paths("providers.local.roots"))}
        for name, fn in _FACTORIES.items():
            if settings.get("providers.%s.enabled" % name, False):
                self.providers[name] = fn(settings, self.http)
        self.errors: list = []  # (capability, provider, message)

    @property
    def local(self) -> LocalFilesProvider:
        return self.providers["local"]

    def order(self, capability: str) -> list:
        if capability not in CAPABILITIES:
            raise ValueError("unknown capability %s" % capability)
        names = self.settings.get("providers.%s" % capability, ["local"])
        return [self.providers[n] for n in names
                if n in self.providers and capability in self.providers[n].capabilities]

    def fetch(self, capability: str, *args, **kwargs):
        """Return (result, provider_name). Result is None/[] when no provider had data."""
        method = {"master": "securities_master"}.get(capability, capability)
        for p in self.order(capability):
            try:
                result = getattr(p, method)(*args, **kwargs)
            except (ProviderError, FetchError, NotImplementedError) as exc:
                self.errors.append((capability, p.name, str(exc)))
                continue
            if result:
                return result, p.name
        return (None if capability in ("profile", "prices", "governance", "benchmark") else []), None

    def fetch_all(self, capability: str, *args, **kwargs) -> list:
        """Merge results from every provider (used for announcements and the master)."""
        method = {"master": "securities_master"}.get(capability, capability)
        out = []
        for p in self.order(capability):
            try:
                out.extend(getattr(p, method)(*args, **kwargs) or [])
            except (ProviderError, FetchError, NotImplementedError) as exc:
                self.errors.append((capability, p.name, str(exc)))
        return out

    def describe(self) -> list:
        rows = []
        for name, p in self.providers.items():
            rows.append({"provider": name, "official": p.official, "capabilities": sorted(p.capabilities),
                         "serves": [c for c in CAPABILITIES if p in self.order(c)]})
        return rows
