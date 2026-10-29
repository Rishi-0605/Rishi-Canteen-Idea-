"""Yahoo Finance chart adapter. UNOFFICIAL: prices only, never treated as an
exchange source, and every series it returns is marked official=False.

Symbols: NSE symbol + ".NS", BSE scrip code + ".BO". Index symbols (^NSEI)
are passed through as given.

STATUS: response parser tested on a hand-written fixture of the documented
v8 chart JSON shape; NOT verified live (blocked in the development sandbox).
"""

from __future__ import annotations

import datetime as dt
import urllib.parse
from typing import Optional

from ..models import IST, CorporateAction, PriceBar, PriceSeries, Security, Source, now_ist
from .base import Provider, ProviderError
from .http import FetchError, HttpClient, parse_json

CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=1d&events=split"


def parse_chart(payload: dict, url: str, retrieved_at: str) -> Optional[PriceSeries]:
    chart = (payload or {}).get("chart") or {}
    if chart.get("error"):
        raise ProviderError("Yahoo error: %s" % chart["error"])
    res = (chart.get("result") or [None])[0]
    if not res or not res.get("timestamp"):
        return None
    q = res["indicators"]["quote"][0]
    bars = []
    for i, ts in enumerate(res["timestamp"]):
        c = q["close"][i]
        if c is None:
            continue  # Yahoo emits null rows for halted/holiday sessions
        d = dt.datetime.fromtimestamp(ts, IST).date()
        o, h, lo, v = q["open"][i], q["high"][i], q["low"][i], q["volume"][i]
        bars.append(PriceBar(d, o if o is not None else c, h if h is not None else c,
                             lo if lo is not None else c, c, v or 0))
    if not bars:
        return None
    meta = res.get("meta", {})
    src = Source(url=url, title="Yahoo Finance chart %s (unofficial)" % meta.get("symbol", ""),
                 publisher="Yahoo Finance", official=False, provider="yahoo", retrieved_at=retrieved_at,
                 published=bars[-1].date.isoformat(), period="%s to %s" % (bars[0].date, bars[-1].date),
                 note="unofficial; not an exchange source; close is not dividend-adjusted")
    exch = "BSE" if str(meta.get("symbol", "")).endswith(".BO") else "NSE"
    return PriceSeries(bars=bars, source=src, exchange=exch, adjusted=False)


def parse_splits(payload: dict, url: str, retrieved_at: str) -> list:
    """Split events in the chart response (events.splits). Unofficial: use to cross-check exchange data."""
    res = (((payload or {}).get("chart") or {}).get("result") or [None])[0] or {}
    out = []
    for ev in ((res.get("events") or {}).get("splits") or {}).values():
        num, den = ev.get("numerator"), ev.get("denominator")
        if not num or not den or not ev.get("date"):
            continue
        d = dt.datetime.fromtimestamp(ev["date"], IST).date()
        f = float(num) / float(den)
        src = Source(url=url, title="Yahoo Finance split event (unofficial)", publisher="Yahoo Finance", official=False,
                     provider="yahoo", retrieved_at=retrieved_at, published=d.isoformat(), locator="events.splits")
        # Yahoo reports bonus issues as splits too; kind says what we know
        out.append(CorporateAction(d, "split_or_bonus", f, "%s:%s (Yahoo split event)" % (num, den), src))
    return sorted(out, key=lambda a: a.ex_date)


class YahooProvider(Provider):
    name = "yahoo"
    official = False
    capabilities = frozenset(["prices", "benchmark", "corporate_actions"])

    def __init__(self, http: HttpClient, range_: str = "2y"):
        self.http = http
        self.range = range_
        http.set_min_interval("query2.finance.yahoo.com", 1.0)

    def _payload(self, symbol: str) -> tuple:
        url = CHART_URL % (urllib.parse.quote(symbol), self.range)
        try:
            return parse_json(self.http.get(url, provider=self.name), url), url
        except FetchError as exc:
            raise ProviderError("Yahoo chart unavailable: %s" % exc)

    def _get(self, symbol: str) -> Optional[PriceSeries]:
        payload, url = self._payload(symbol)
        return parse_chart(payload, url, now_ist().isoformat())

    def corporate_actions(self, sec: Security) -> list:
        sym = sec.yahoo_symbol("NSE") or sec.yahoo_symbol("BSE")
        if not sym:
            return []
        payload, url = self._payload(sym)
        return parse_splits(payload, url, now_ist().isoformat())

    def prices(self, sec: Security, start=None, end=None) -> Optional[PriceSeries]:
        sym = sec.yahoo_symbol("NSE") or sec.yahoo_symbol("BSE")
        if not sym:
            return None
        s = self._get(sym)
        if s:
            s.bars = [b for b in s.bars if (not start or b.date >= start) and (not end or b.date <= end)]
        return s

    def benchmark(self, name: str, start=None, end=None) -> Optional[PriceSeries]:
        symbol = {"NIFTY50": "^NSEI", "SENSEX": "^BSESN", "NIFTY500": "^CRSLDX"}.get(name, name)
        return self._get(symbol)
