"""NSE (National Stock Exchange of India) adapter. Official source.

STATUS: written against NSE's published file formats and observed JSON field
names, but NOT verified against live endpoints (the development sandbox blocks
NSE). Unit tests cover only the parsers, using hand-written format fixtures.
Enable it in settings.toml (`[providers.nse] enabled = true`) after reviewing
NSE's terms of use, and run `python -m fortune_research providers --check`.

Endpoints:
  securities master  https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv
  EOD bhavcopy       https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_<YYYYMMDD>_F_0000.csv.zip
                     (UDiFF format, July 2024 onward)
  announcements      https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=<SYMBOL>
                     (JSON; needs a browser-like session: cookies from the home page first)
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import urllib.parse
import zipfile
from typing import Optional

from ..models import Announcement, PriceBar, PriceSeries, Security, Source, now_ist, parse_date
from .base import Provider, ProviderError
from .http import FetchError, HttpClient

MASTER_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
BHAV_URL = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_%s_F_0000.csv.zip"
HOME_URL = "https://www.nseindia.com/"
ANN_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=%s"
ANN_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
BROWSER_HEADERS = {"Accept": "application/json,text/html,*/*", "Accept-Language": "en-IN,en;q=0.9",
                   "Referer": "https://www.nseindia.com/"}


def parse_equity_master(text: str, retrieved_at: str) -> list:
    """EQUITY_L.csv: SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE,
    MARKET LOT, ISIN NUMBER, FACE VALUE (headers carry leading spaces in the real file)."""
    src = Source(url=MASTER_URL, title="NSE equity securities list (EQUITY_L.csv)", publisher="NSE",
                 official=True, provider="nse", retrieved_at=retrieved_at)
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        r = {(k or "").strip().upper(): (v or "").strip() for k, v in row.items()}
        if not r.get("SYMBOL"):
            continue
        fv = r.get("FACE VALUE")
        out.append({"name": r.get("NAME OF COMPANY", ""), "isin": r.get("ISIN NUMBER") or None,
                    "nse_symbol": r["SYMBOL"], "bse_code": None, "series": r.get("SERIES") or None,
                    "face_value": float(fv) if fv else None, "synthetic": False, "source": src})
    return out


def parse_bhavcopy(text: str, symbol: str, series: str = "EQ") -> Optional[dict]:
    """One row of a UDiFF bhavcopy for symbol/series, or None."""
    for row in csv.DictReader(io.StringIO(text)):
        r = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        if r.get("TckrSymb") == symbol and (r.get("SctySrs") or "EQ") == series:
            return {"date": parse_date(r["TradDt"]), "open": float(r["OpnPric"]), "high": float(r["HghPric"]),
                    "low": float(r["LwPric"]), "close": float(r["ClsPric"]),
                    "volume": float(r.get("TtlTradgVol") or 0), "isin": r.get("ISIN")}
    return None


def parse_announcements(payload, symbol: str, retrieved_at: str) -> list:
    """NSE corporate-announcements JSON: list of objects with (as observed) keys
    symbol, desc, an_dt ("29-Oct-2026 18:30:12"), attchmntFile, attchmntText."""
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    out = []
    for r in rows or []:
        if (r.get("symbol") or symbol) != symbol:
            continue
        stamp = (r.get("an_dt") or r.get("sort_date") or "").split(" ")[0]
        try:
            d = parse_date(stamp)
        except ValueError:
            continue
        url = r.get("attchmntFile") or ANN_PAGE
        subject = r.get("desc") or ""
        src = Source(url=url, title="NSE announcement: %s" % subject, publisher="NSE", official=True,
                     provider="nse", retrieved_at=retrieved_at, published=d.isoformat())
        out.append(Announcement(date=d, exchange="NSE", subject=subject, category="", url=url, source=src,
                                details=(r.get("attchmntText") or "")[:500]))
    return sorted(out, key=lambda a: a.date, reverse=True)


class NSEProvider(Provider):
    name = "nse"
    official = True
    capabilities = frozenset(["master", "prices", "announcements"])

    def __init__(self, http: HttpClient, max_bhav_days: int = 400):
        self.http = http
        self.max_bhav_days = max_bhav_days
        self._warm = False
        for host in ("www.nseindia.com", "nsearchives.nseindia.com"):
            http.set_min_interval(host, 1.5)

    def _warmup(self):
        if not self._warm:
            try:
                self.http.get(HOME_URL, headers=BROWSER_HEADERS, provider=self.name, use_cache=False)
            except FetchError:
                pass
            self._warm = True

    def securities_master(self) -> list:
        try:
            body = self.http.get(MASTER_URL, provider=self.name)
        except FetchError as exc:
            raise ProviderError("NSE master unavailable: %s" % exc)
        return parse_equity_master(body.decode("utf-8", "replace"), now_ist().isoformat())

    def prices(self, sec: Security, start=None, end=None) -> Optional[PriceSeries]:
        if not sec.nse_symbol:
            return None
        end = end or now_ist().date()
        start = start or (end - dt.timedelta(days=self.max_bhav_days))
        bars, day, misses = [], end, 0
        while day >= start and misses < 15:
            if day.weekday() < 5:
                url = BHAV_URL % day.strftime("%Y%m%d")
                try:
                    raw = self.http.get(url, provider=self.name)
                    with zipfile.ZipFile(io.BytesIO(raw)) as z:
                        text = z.read(z.namelist()[0]).decode("utf-8", "replace")
                    row = parse_bhavcopy(text, sec.nse_symbol, sec.series or "EQ")
                    if row:
                        bars.append(PriceBar(row["date"], row["open"], row["high"], row["low"],
                                             row["close"], row["volume"]))
                    misses = 0
                except (FetchError, zipfile.BadZipFile, KeyError, ValueError):
                    misses += 1  # holiday or not yet published
            day -= dt.timedelta(days=1)
        if not bars:
            return None
        bars.sort(key=lambda b: b.date)
        src = Source(url=BHAV_URL % "<YYYYMMDD>", title="NSE CM bhavcopy (UDiFF)", publisher="NSE",
                     official=True, provider=self.name, retrieved_at=now_ist().isoformat(),
                     published=bars[-1].date.isoformat(), period="%s to %s" % (bars[0].date, bars[-1].date))
        return PriceSeries(bars=bars, source=src, exchange="NSE", adjusted=False)

    def announcements(self, sec: Security, since=None) -> list:
        if not sec.nse_symbol:
            return []
        self._warmup()
        url = ANN_URL % urllib.parse.quote(sec.nse_symbol)
        try:
            payload = json.loads(self.http.get(url, headers=BROWSER_HEADERS, provider=self.name))
        except (FetchError, ValueError) as exc:
            raise ProviderError("NSE announcements unavailable: %s" % exc)
        rows = parse_announcements(payload, sec.nse_symbol, now_ist().isoformat())
        return [a for a in rows if not since or a.date >= since]
