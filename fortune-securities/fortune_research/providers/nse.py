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
  financial results  https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol=<SYMBOL>&period=Quarterly
                     index of Reg. 33 filings; each row links an XBRL instance (parsed by providers/xbrl.py)
  corporate actions  https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=<SYMBOL>
  shareholding       https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol=<SYMBOL>
                     (promoter / public totals only; pledge detail is NOT in this endpoint)

Field names for the JSON endpoints are taken from observed responses and are read
defensively (several candidate keys). The health check reports the fields that were
actually returned, so a renamed field shows up as a retrieval failure, not bad data.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import urllib.parse
import zipfile
from typing import Optional

from ..analysis.corporate_actions import parse_subject
from ..models import (Announcement, CorporateAction, PriceBar, PriceSeries, Security, ShareholdingRecord, Source,
                      fy_label, now_ist, parse_date)
from . import xbrl
from .base import Provider, ProviderError
from .http import FetchError, HttpClient, parse_json

MASTER_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
BHAV_URL = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_%s_F_0000.csv.zip"
HOME_URL = "https://www.nseindia.com/"
ANN_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=%s"
ANN_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
RESULTS_URL = "https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol=%s&period=%s"
CA_URL = "https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=%s"
SHP_URL = "https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol=%s"
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


def _first(row: dict, *keys):
    for k in keys:
        if row.get(k) not in (None, "", "-"):
            return row[k]
    return None


def _rows(payload):
    if isinstance(payload, dict):
        for k in ("data", "rows", "Table"):
            if isinstance(payload.get(k), list):
                return payload[k]
        return []
    return payload or []


def parse_results_index(payload) -> list:
    """Financial-results index -> [{xbrl_url, period_start, period_end, basis, audited, filed}].
    Rows without an XBRL link are returned with xbrl_url None (PDF-only filings)."""
    out = []
    for r in _rows(payload):
        try:
            start = parse_date(str(_first(r, "fromDate", "from_date", "periodFrom") or "").split(" ")[0] or None)
            end = parse_date(str(_first(r, "toDate", "to_date", "periodTo") or "").split(" ")[0] or None)
            filed = parse_date(str(_first(r, "filingDate", "broadcastDate", "exchdisstime", "submissionDate") or "").split(" ")[0] or None)
        except ValueError:
            continue
        if end is None:
            continue
        cons = str(_first(r, "consolidated", "type", "resultType") or "").lower()
        basis = "consolidated" if cons.startswith("consol") else "standalone" if cons else "unknown"
        out.append({"xbrl_url": _first(r, "xbrl", "xbrlFile", "xbrl_url"), "pdf_url": _first(r, "pdfLink", "attachment", "attchmntFile"),
                    "period_start": start, "period_end": end, "basis": basis, "audited": _first(r, "audited", "auditedUnaudited"),
                    "filed": filed, "raw_keys": sorted(r.keys())})
    return sorted(out, key=lambda x: (x["period_end"], x["filed"] or x["period_end"]), reverse=True)


def parse_corporate_actions(payload, symbol: str, retrieved_at: str) -> list:
    out = []
    for r in _rows(payload):
        if (r.get("symbol") or symbol) != symbol:
            continue
        subj = _first(r, "subject", "purpose", "PURPOSE") or ""
        try:
            ex = parse_date(str(_first(r, "exDate", "ex_date", "Ex_date") or "").split(" ")[0] or None)
        except ValueError:
            ex = None
        if not ex or not subj:
            continue
        kind, factor = parse_subject(subj)
        src = Source(url=CA_URL % urllib.parse.quote(symbol), title="NSE corporate action: %s" % subj, publisher="NSE",
                     official=True, provider="nse", retrieved_at=retrieved_at, published=ex.isoformat(), locator="subject/exDate")
        out.append(CorporateAction(ex, kind, factor, subj, src))
    return sorted(out, key=lambda a: a.ex_date)


def _pct(v):
    try:
        return float(str(v).replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def parse_shareholding(payload, symbol: str, retrieved_at: str) -> list:
    out = []
    for r in _rows(payload):
        try:
            q = parse_date(str(_first(r, "date", "asOnDate", "quarterEnded") or "").split(" ")[0] or None)
        except ValueError:
            continue
        prom = _pct(_first(r, "pr_and_prgrp", "promoterAndPromoterGroup", "promoter"))
        pub = _pct(_first(r, "public_val", "public"))
        if q is None or (prom is None and pub is None):
            continue
        filed = _first(r, "submissionDate", "broadcastDate")
        try:
            filed = parse_date(str(filed).split(" ")[0]).isoformat() if filed else None
        except ValueError:
            filed = None
        src = Source(url=_first(r, "xbrl") or SHP_URL % urllib.parse.quote(symbol), title="NSE shareholding pattern %s" % q,
                     publisher="NSE", official=True, provider="nse", retrieved_at=retrieved_at, published=filed,
                     period=fy_label(q, "Q"), locator="pr_and_prgrp / public_val")
        # pledge, FII and DII are not in this endpoint: left as None (unknown), never 0
        out.append(ShareholdingRecord(q, prom, None, None, None, pub, src))
    return sorted(out, key=lambda x: x.quarter_end)




class NSEProvider(Provider):
    name = "nse"
    official = True
    capabilities = frozenset(["master", "prices", "announcements", "financials", "corporate_actions", "shareholding"])

    def __init__(self, http: HttpClient, max_bhav_days: int = 400, max_filings: int = 8):
        self.http = http
        self.max_bhav_days = max_bhav_days
        self.max_filings = max_filings
        self.diagnostics: dict = {}  # last parse details per capability, read by the health check
        self._warm = False
        for host in ("www.nseindia.com", "nsearchives.nseindia.com"):
            http.set_min_interval(host, 1.5)

    def _warmup(self):
        if not self._warm:
            try:
                self.http.get(HOME_URL, headers=BROWSER_HEADERS, provider=self.name, use_cache=False)
            except FetchError:
                pass  # the API call that follows reports the real failure
            self._warm = True

    def _api(self, url: str, what: str):
        self._warmup()
        try:
            return parse_json(self.http.get(url, headers=BROWSER_HEADERS, provider=self.name), url)
        except FetchError as exc:
            raise ProviderError("NSE %s unavailable: %s" % (what, exc))

    def securities_master(self) -> list:
        try:
            body = self.http.get(MASTER_URL, provider=self.name)
        except FetchError as exc:
            raise ProviderError("NSE master unavailable: %s" % exc)
        text = body.decode("utf-8", "replace")
        if text.lstrip()[:1] == "<":
            raise ProviderError("NSE master: HTML page instead of CSV (blocked or moved)")
        rows = parse_equity_master(text, now_ist().isoformat())
        if not rows:
            raise ProviderError("NSE master: file parsed but contained no securities (format changed?)")
        return rows

    def prices(self, sec: Security, start=None, end=None) -> Optional[PriceSeries]:
        if not sec.nse_symbol:
            return None
        end = end or now_ist().date()
        start = start or (end - dt.timedelta(days=self.max_bhav_days))
        bars, day, misses = [], end, 0
        while day >= start and misses < 10:
            if day.weekday() < 5:
                url = BHAV_URL % day.strftime("%Y%m%d")
                try:
                    raw = self.http.get(url, provider=self.name)
                    with zipfile.ZipFile(io.BytesIO(raw)) as z:
                        text = z.read(z.namelist()[0]).decode("utf-8", "replace")
                    row = parse_bhavcopy(text, sec.nse_symbol, sec.series or "EQ")
                    if row:
                        bars.append(PriceBar(row["date"], row["open"], row["high"], row["low"], row["close"], row["volume"]))
                    misses = 0
                except FetchError as exc:
                    if exc.status != 404:  # 404 = holiday / not yet published; anything else is a real failure
                        if not bars:
                            raise ProviderError("NSE bhavcopy unavailable: %s" % exc)
                        break
                    misses += 1
                except (zipfile.BadZipFile, KeyError, ValueError):
                    misses += 1
            day -= dt.timedelta(days=1)
        if not bars:
            return None
        bars.sort(key=lambda b: b.date)
        src = Source(url=BHAV_URL % "<YYYYMMDD>", title="NSE CM bhavcopy (UDiFF)", publisher="NSE",
                     official=True, provider=self.name, retrieved_at=now_ist().isoformat(),
                     published=bars[-1].date.isoformat(), period="%s to %s" % (bars[0].date, bars[-1].date),
                     locator="TckrSymb=%s SctySrs=%s" % (sec.nse_symbol, sec.series or "EQ"))
        # bhavcopy prices are as traded on the day: NOT adjusted for later splits/bonuses
        return PriceSeries(bars=bars, source=src, exchange="NSE", adjusted=False)

    def announcements(self, sec: Security, since=None) -> list:
        if not sec.nse_symbol:
            return []
        payload = self._api(ANN_URL % urllib.parse.quote(sec.nse_symbol), "announcements")
        rows = parse_announcements(payload, sec.nse_symbol, now_ist().isoformat())
        return [a for a in rows if not since or a.date >= since]

    def corporate_actions(self, sec: Security) -> list:
        if not sec.nse_symbol:
            return []
        return parse_corporate_actions(self._api(CA_URL % urllib.parse.quote(sec.nse_symbol), "corporate actions"),
                                       sec.nse_symbol, now_ist().isoformat())

    def shareholding(self, sec: Security) -> list:
        if not sec.nse_symbol:
            return []
        return parse_shareholding(self._api(SHP_URL % urllib.parse.quote(sec.nse_symbol), "shareholding"),
                                  sec.nse_symbol, now_ist().isoformat())

    def financials(self, sec: Security) -> list:
        """Latest Reg. 33 filings (quarterly and annual) parsed from their XBRL instances."""
        if not sec.nse_symbol:
            return []
        filings = []
        for period in ("Quarterly", "Annual"):
            try:
                filings += parse_results_index(self._api(RESULTS_URL % (urllib.parse.quote(sec.nse_symbol), period), "results index"))
            except ProviderError as exc:
                self.diagnostics.setdefault("financials", {}).setdefault("errors", []).append(str(exc))
        uniq, seen = [], set()
        for f in filings:  # the quarterly and annual indexes can list the same filing
            key = f["xbrl_url"] or (f["period_end"], f["basis"], f["filed"])
            if key not in seen:
                seen.add(key)
                uniq.append(f)
        filings = uniq
        diag = self.diagnostics.setdefault("financials", {})
        diag.update({"filings_listed": len(filings), "parsed": [], "identity_problems": [], "unmapped": [], "no_xbrl": 0})
        if not filings:
            raise ProviderError("NSE results index returned no filings" + (": " + "; ".join(diag.get("errors", [])) if diag.get("errors") else ""))
        facts = []
        for f in [x for x in filings if x["xbrl_url"]][: self.max_filings]:
            try:
                body = self.http.get(f["xbrl_url"], provider=self.name)
                res = xbrl.parse(body, f["xbrl_url"], now_ist().isoformat(), f["filed"].isoformat() if f["filed"] else None, f["basis"])
            except (FetchError, xbrl.XBRLError) as exc:
                diag.setdefault("errors", []).append("%s: %s" % (f["xbrl_url"], exc))
                continue
            problems = xbrl.check_identity(res, sec.isin, sec.nse_symbol, sec.bse_code)
            if any("does not match" in p for p in problems):
                diag["identity_problems"].append({"url": f["xbrl_url"], "problems": problems})
                continue  # never use a document that names another company
            diag["parsed"].append({"url": f["xbrl_url"], "facts": len(res.facts), "period_end": str(f["period_end"]),
                                   "basis": res.metadata.get("basis_normalised"), "identity_notes": problems})
            diag["unmapped"] += res.unmapped[:50]
            facts += res.facts
        diag["no_xbrl"] = sum(1 for x in filings if not x["xbrl_url"])
        return facts
