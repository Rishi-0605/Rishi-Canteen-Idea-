"""Provider health check.

For every enabled provider and every capability it serves, it runs one real
retrieval for a test company and reports, separately:

  connection  did the server answer at all (any HTTP status counts; DOWN means no response)
  retrieval   did the parser produce records (a 200 with an HTML block page,
              an empty list or unparseable data is a FAILED retrieval)
  fields      which fields actually came back, and which expected ones did not
  source      URL and retrieval timestamp of what came back
  freshness   newest date in the data and its age
  errors      every error message, verbatim
  suitability for each calculation that would use it: suitable or not, and why

A connection that succeeds is never reported as a successful data retrieval.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from .identity import resolve
from .models import Security, now_ist
from .providers.base import CAPABILITIES, ProviderError
from .providers.http import FetchError

EXPECTED = {
    "master": ["name", "isin", "nse_symbol", "bse_code"],
    "profile": ["name", "sector", "industry", "peers"],
    "financials": ["revenue", "pat", "pbt", "eps_diluted", "finance_costs", "depreciation", "total_equity|equity_share_capital+other_equity",
                   "borrowings_noncurrent", "cash_and_equivalents", "cfo", "shares_outstanding"],
    "prices": ["date", "open", "high", "low", "close", "volume"],
    "announcements": ["date", "subject", "url"],
    "shareholding": ["promoter_pct", "promoter_pledged_pct", "fii_pct", "dii_pct", "public_pct"],
    "governance": ["audit_opinion", "rpt_total_cr", "auditor"],
    "news": ["date", "subject", "publisher", "url"],
    "benchmark": ["date", "close"],
    "corporate_actions": ["ex_date", "kind", "factor"],
    "documents": ["pages", "units", "period", "published"],
}
FRESH_DAYS = {"prices": 5, "benchmark": 5, "financials": 140, "shareholding": 120, "announcements": 45, "news": 14}


@dataclass
class ProbeResult:
    provider: str
    capability: str
    official: bool
    connection: str = "not_attempted"  # ok | failed | local | not_attempted
    http: list = field(default_factory=list)
    retrieval: str = "not_attempted"  # ok | empty | failed
    records: int = 0
    fields_returned: list = field(default_factory=list)
    fields_missing: list = field(default_factory=list)
    source_url: Optional[str] = None
    retrieved_at: Optional[str] = None
    newest_date: Optional[str] = None
    age_days: Optional[int] = None
    fresh: Optional[bool] = None
    errors: list = field(default_factory=list)
    suitability: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    synthetic: bool = False

    @property
    def status(self) -> str:
        if self.retrieval == "ok" and all(v["ok"] for v in self.suitability.values()):
            return "OPERATIONAL"
        if self.retrieval == "ok":
            return "PARTIAL"
        if self.connection in ("ok", "local") and self.retrieval in ("failed", "empty"):
            return "CONNECTED_NO_DATA"
        return "DOWN" if self.connection == "failed" else "NO_DATA"

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["status"] = self.status
        return d


def _ok(flag: bool, reason: str) -> dict:
    return {"ok": bool(flag), "reason": reason}


def _fields(objs: list) -> list:
    names = set()
    for o in objs:
        d = o if isinstance(o, dict) else (dataclasses.asdict(o) if dataclasses.is_dataclass(o) else vars(o))
        names |= {k for k, v in d.items() if v not in (None, "", [], {})}
    return sorted(names)


def _missing(expected: list, present: set) -> list:
    out = []
    for e in expected:
        alts = e.split("|")
        if not any(all(p in present for p in alt.split("+")) for alt in alts):
            out.append(e)
    return out


def _freshness(r: ProbeResult, newest: Optional[dt.date], today: dt.date) -> None:
    if newest is None:
        return
    r.newest_date = newest.isoformat()
    r.age_days = (today - newest).days
    lim = FRESH_DAYS.get(r.capability)
    r.fresh = None if lim is None else r.age_days <= lim


# -- per-capability evaluation ------------------------------------------------------------
def _eval_master(r, data, sec, today):
    r.records = len(data)
    r.fields_returned = _fields([{k: v for k, v in x.items() if k != "source"} for x in data[:2000]])
    if data and data[0].get("source"):
        r.source_url, r.retrieved_at = data[0]["source"].url, data[0]["source"].retrieved_at
    res = resolve(sec.nse_symbol or sec.bse_code or sec.name, data) if data else None
    found = res is not None and res.status == "resolved"
    present = set(_fields([{k: v for k, v in dataclasses.asdict(res.security).items()}])) if found else set()
    r.fields_missing = _missing(["isin", "nse_symbol|bse_code"], present) if found else ["target security"]
    r.suitability["identity resolution"] = _ok(found and res.security.isin, (
        "found %s (%s, ISIN %s)" % (res.security.name, res.security.display_symbol, res.security.isin)) if found and res.security.isin
        else "target not found or has no ISIN in this master" if not found else "target found but no ISIN")


def _eval_prices(r, s, sec, today):
    if not s or not s.bars:
        r.retrieval = "empty"
        return
    r.records = len(s.bars)
    r.fields_returned = [f for f in EXPECTED["prices"] if any(getattr(b, f, None) not in (None, 0) for b in s.bars)]
    r.fields_missing = [f for f in EXPECTED["prices"] if f not in r.fields_returned]
    r.source_url, r.retrieved_at = s.source.url, s.source.retrieved_at
    _freshness(r, s.bars[-1].date, today)
    vol_ok = sum(1 for b in s.bars if b.volume) >= 0.9 * len(s.bars)
    r.suitability["technical indicators (SMA 200)"] = _ok(len(s.bars) >= 200, "%d bars" % len(s.bars))
    r.suitability["valuation (current price)"] = _ok(bool(r.fresh), "latest close %s, %s days old" % (r.newest_date, r.age_days))
    r.suitability["liquidity (traded value)"] = _ok(vol_ok, "volume present on %s of bars" % ("most" if vol_ok else "too few"))
    r.suitability["split/bonus consistency"] = _ok(s.adjusted is not None, "adjusted for corporate actions" if s.adjusted
                                                  else "unadjusted (as traded): agent back-adjusts using corporate actions"
                                                  if s.adjusted is False else "adjustment status unknown")
    if not s.source.official:
        r.suitability["official exchange price"] = _ok(False, "unofficial source (%s): cross-check before relying on it" % s.source.publisher)


def _eval_financials(r, facts, sec, today):
    if not facts:
        r.retrieval = "empty"
        return
    r.records = len(facts)
    names = {f.name for f in facts}
    r.fields_returned = sorted(names)
    r.fields_missing = _missing(EXPECTED["financials"], names)
    newest = max(f.period_end for f in facts)
    latest = [f for f in facts if f.period_end == newest]
    r.source_url, r.retrieved_at = latest[0].source.url, latest[0].source.retrieved_at
    _freshness(r, newest, today)
    fy = sorted({f.period_end for f in facts if f.period_type == "FY"})
    qs = sorted({f.period_end for f in facts if f.period_type == "Q"})
    fy_names = {f.name for f in facts if fy and f.period_end == fy[-1] and f.period_type == "FY"}
    need = ["revenue", "pat", "pbt", "finance_costs"]
    r.suitability["P&L ratios and margins"] = _ok(all(n in fy_names or n in names for n in need),
                                                  "needs %s" % ", ".join(n for n in need if n not in names) if not all(n in names for n in need) else "present")
    bs = _missing(["total_equity|equity_share_capital+other_equity", "borrowings_noncurrent|borrowings_current"], fy_names)
    r.suitability["ROE / ROCE / leverage"] = _ok(not bs, "latest FY balance sheet has equity and borrowings" if not bs
                                                 else "latest FY lacks %s (results filings often carry the balance sheet only half-yearly)" % ", ".join(bs))
    r.suitability["growth (YoY) and TTM"] = _ok(len(fy) >= 2 or len(qs) >= 5, "%d fiscal years, %d quarters" % (len(fy), len(qs)))
    r.suitability["per-share valuation"] = _ok("shares_outstanding" in names or "eps_diluted" in names,
                                               "share count or EPS present" if ("shares_outstanding" in names or "eps_diluted" in names)
                                               else "no share count or EPS")
    unoff = sum(1 for f in facts if not f.source.official)
    r.suitability["official source"] = _ok(unoff == 0, "all figures from official filings" if not unoff else "%d figures from unofficial sources" % unoff)
    pub_unknown = sum(1 for f in facts if not f.source.published)
    if pub_unknown:
        r.suitability["point-in-time (no look-ahead)"] = _ok(False, "%d figures lack a publication date (deadline assumption used)" % pub_unknown)
    else:
        r.suitability["point-in-time (no look-ahead)"] = _ok(True, "every figure has a publication date")


def _eval_list(r, items, sec, today, date_attr, checks):
    if not items:
        r.retrieval = "empty"
        return
    r.records = len(items)
    r.fields_returned = _fields(items)
    present = set(r.fields_returned) | ({"publisher"} if any(getattr(i, "source", None) and i.source.publisher for i in items) else set())
    if r.capability in ("announcements", "news"):
        present |= {"url"} if any(getattr(i, "url", None) for i in items) else set()
    r.fields_missing = _missing(EXPECTED[r.capability], present)
    src = getattr(items[-1], "source", None)
    if src:
        r.source_url, r.retrieved_at = src.url, src.retrieved_at
    dates = [getattr(i, date_attr) for i in items if getattr(i, date_attr, None)]
    _freshness(r, max(dates) if dates else None, today)
    for name, fn in checks:
        r.suitability[name] = fn(items)


def _eval_documents(r, docs, sec, today):
    if not docs:
        r.retrieval = "empty"
        return
    r.records = len(docs)
    r.source_url = docs[0].url
    r.fields_returned = sorted({k for d in docs for k, v in d.summary().items() if v not in (None, "", [], 0)})
    texty = [d for d in docs if d.pages and not d.error]
    units = [d for d in texty if any(d.units_by_page.values())]
    r.fields_missing = [] if units else ["units"]
    r.suitability["citable text (page numbers)"] = _ok(bool(texty), "%d of %d documents have extractable text" % (len(texty), len(docs)))
    r.suitability["units stated"] = _ok(bool(units), "%d documents state their units" % len(units))
    r.suitability["automatic figures for calculations"] = _ok(False, "PDF figures are review-only evidence by design")
    pubs = [dt.date.fromisoformat(d.published[:10]) for d in docs if d.published]
    _freshness(r, max(pubs) if pubs else None, today)


def _eval_generic(r, data, sec, today):
    if not data:
        r.retrieval = "empty"
        return
    r.records = 1
    r.fields_returned = sorted(k for k, v in data.items() if v not in (None, "", [], {})) if isinstance(data, dict) else []
    if r.capability == "governance":
        recs = (data.get("fiscal_years") or {}).values()
        present = {k for rec in recs for k, v in rec.items() if v not in (None, "")}
        r.fields_missing = _missing(EXPECTED["governance"], present)
        r.suitability["forensic checks (auditor, RPT)"] = _ok(not r.fields_missing, "complete" if not r.fields_missing
                                                              else "missing %s" % ", ".join(r.fields_missing))
    else:
        r.fields_missing = _missing(EXPECTED.get(r.capability, []), set(r.fields_returned))
        r.suitability["sector / peer selection"] = _ok("sector" in r.fields_returned and "peers" in r.fields_returned,
                                                       "sector and peers given" if not r.fields_missing else "missing %s" % ", ".join(r.fields_missing))


def _sh_checks():
    return [("ownership trend", lambda xs: _ok(sum(1 for x in xs if x.promoter_pct is not None) >= 2,
                                               "%d quarters with promoter %%" % sum(1 for x in xs if x.promoter_pct is not None))),
            ("pledge check", lambda xs: _ok(any(x.promoter_pledged_pct is not None for x in xs),
                                            "pledge %% present" if any(x.promoter_pledged_pct is not None for x in xs)
                                            else "pledge %% not in this source: pledge checks cannot run"))]


def _ann_checks():
    return [("news monitor (dated, linked filings)", lambda xs: _ok(all(x.date and x.url for x in xs), "%d dated items with links" % len(xs))),
            ("official disclosures", lambda xs: _ok(all(x.source.official for x in xs), "exchange filings" if all(x.source.official for x in xs)
                                                     else "includes unofficial items"))]


def _news_checks():
    return [("media monitor (dated, attributable)", lambda xs: _ok(all(x.date and x.source.publisher for x in xs),
                                                                   "%d items with publisher and date" % len(xs))),
            ("treated as commentary, not filings", lambda xs: _ok(not any(x.source.official for x in xs), "media items are unofficial"))]


def _ca_checks():
    def adj(xs):
        sb = [x for x in xs if x.kind in ("split", "bonus", "consolidation", "split_or_bonus") or x.kind.endswith("_unparsed")]
        bad = [x.description for x in sb if not x.factor]
        return _ok(not bad, ("%d split/bonus actions with factors" % len(sb)) if not bad else "unparsed: %s" % "; ".join(bad[:3]))
    return [("split/bonus adjustment", adj),
            ("official record", lambda xs: _ok(all(x.source.official for x in xs), "exchange record" if all(x.source.official for x in xs)
                                               else "unofficial (Yahoo): confirm against exchange"))]


def run(registry, sec: Security, capabilities: Optional[list] = None, only: Optional[list] = None,
        today: Optional[dt.date] = None, profile: Optional[dict] = None, benchmark: str = "NIFTY50") -> list:
    """Probe every (provider, capability) pair. `registry.http.on_fetch` events are captured per probe."""
    today = today or now_ist().date()
    log: list = []
    prev = registry.http.on_fetch

    def tap(entry):
        log.append(entry)
        if prev:
            prev(entry)

    registry.http.on_fetch = tap
    results = []
    try:
        for name, p in registry.providers.items():
            if only and name not in only:
                continue
            for cap in CAPABILITIES:
                if cap not in p.capabilities or (capabilities and cap not in capabilities):
                    continue
                r = ProbeResult(name, cap, p.official)
                log.clear()
                method = {"master": "securities_master"}.get(cap, cap)
                try:
                    if cap == "master":
                        data = p.securities_master()
                    elif cap == "prices":
                        data = p.prices(sec, today - dt.timedelta(days=400), today)
                    elif cap == "benchmark":
                        data = p.benchmark(benchmark, today - dt.timedelta(days=400), today)
                    elif cap in ("announcements", "news"):
                        data = getattr(p, method)(sec, today - dt.timedelta(days=365))
                    elif cap == "documents":
                        data = p.documents(sec, profile=profile)
                    else:
                        data = getattr(p, method)(sec)
                    r.retrieval = "ok"
                except (ProviderError, FetchError) as exc:
                    data, r.retrieval = None, "failed"
                    r.errors.append(str(exc))
                except NotImplementedError:
                    continue
                except Exception as exc:  # a parser bug must show up here, not crash the whole check
                    data, r.retrieval = None, "failed"
                    r.errors.append("%s: %s" % (exc.__class__.__name__, exc))
                r.http = [{k: e.get(k) for k in ("url", "status", "cache_hit", "bytes", "error")} for e in log]
                if name == "local":
                    r.connection = "local"
                elif not log:
                    r.connection = "not_attempted"
                elif any(e.get("status") for e in log):
                    r.connection = "ok"  # the server answered (any HTTP status); whether data came back is `retrieval`
                else:
                    r.connection = "failed"
                    for e in log:
                        if e.get("error") and e["error"] not in r.errors:
                            r.errors.append(e["error"])
                if r.retrieval == "ok":
                    if cap == "master":
                        _eval_master(r, data or [], sec, today)
                    elif cap in ("prices", "benchmark"):
                        _eval_prices(r, data, sec, today)
                        if cap == "benchmark":
                            r.suitability = {"beta / benchmark comparison": _ok(r.records >= 60 and bool(r.fresh),
                                                                              "%d bars, %s days old" % (r.records, r.age_days))}
                    elif cap == "financials":
                        _eval_financials(r, data or [], sec, today)
                    elif cap == "shareholding":
                        _eval_list(r, data or [], sec, today, "quarter_end", _sh_checks())
                    elif cap == "announcements":
                        _eval_list(r, data or [], sec, today, "date", _ann_checks())
                    elif cap == "news":
                        _eval_list(r, data or [], sec, today, "date", _news_checks())
                    elif cap == "corporate_actions":
                        _eval_list(r, data or [], sec, today, "ex_date", _ca_checks())
                    elif cap == "documents":
                        _eval_documents(r, data or [], sec, today)
                    else:
                        _eval_generic(r, data, sec, today)
                    if r.retrieval == "ok" and r.records == 0:
                        r.retrieval = "empty"
                if r.retrieval == "empty":
                    if name != "local" and not log:
                        r.errors.append("no request made: %s has no identifier this provider needs (e.g. BSE scrip code, "
                                        "company IR pages) - resolve the company through a securities master first" % sec.display_symbol)
                    else:
                        r.errors.append("request completed but no records were returned for %s"
                                        % (sec.display_symbol if cap != "master" else "the master"))
                diag = getattr(p, "diagnostics", {}).get(cap)
                if diag:
                    r.diagnostics = diag
                r.synthetic = bool(name == "local" and sec.synthetic)
                results.append(r)
    finally:
        registry.http.on_fetch = prev
    return results


def render(results: list, sec: Security, today: dt.date) -> str:
    L = ["# Provider health check", "", "Target: %s (%s) | run %s | %d probes" % (sec.name or sec.display_symbol, sec.display_symbol,
                                                                               now_ist().isoformat(), len(results)), "",
         "Status: OPERATIONAL = data retrieved and suitable for every listed use; PARTIAL = data retrieved, some uses unsuitable; "
         "CONNECTED_NO_DATA = the server answered but no usable data came back; DOWN = no connection; NO_DATA = nothing returned.", ""]
    L += ["| Provider | Capability | Status | Connection | Retrieval | Records | Newest | Age (d) | Missing fields |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        L.append("| %s%s | %s | **%s** | %s%s | %s | %d | %s | %s | %s |" % (
            r.provider, "" if r.official else " (unofficial)", r.capability, r.status, r.connection,
            (" (HTTP %s)" % ",".join(sorted({str(h["status"]) if h["status"] else "no response" for h in r.http}))) if r.http else "",
            r.retrieval, r.records,
            r.newest_date or "-", r.age_days if r.age_days is not None else "-", ", ".join(r.fields_missing) or "none"))
    for r in results:
        L += ["", "## %s / %s: %s" % (r.provider, r.capability, r.status)]
        if r.synthetic:
            L.append("- SYNTHETIC sample data: this proves the code path, not a live source.")
        L.append("- Source: %s (retrieved %s)" % (r.source_url or "n/a", r.retrieved_at or "n/a"))
        L.append("- Fields returned: %s" % (", ".join(r.fields_returned[:40]) or "none"))
        for k, v in r.suitability.items():
            L.append("- %s %s: %s" % ("[ok]" if v["ok"] else "[NOT SUITABLE]", k, v["reason"]))
        for e in r.errors:
            L.append("- Error: %s" % e)
        if r.diagnostics:
            L.append("- Diagnostics: %s" % ", ".join("%s=%s" % (k, (len(v) if isinstance(v, list) else v)) for k, v in r.diagnostics.items()))
    return "\n".join(L) + "\n"
