"""Resolve and verify a company from a name, NSE symbol, BSE scrip code or ISIN.

The resolver never guesses. A query that matches more than one security
returns status "ambiguous" with the candidates, and one that matches nothing
returns "not_found".
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Optional

from .models import Security

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
SUFFIXES = re.compile(r"\b(limited|ltd|ltd\.|the|co|company|corporation|corp|inc|india)\b\.?", re.I)


def isin_check_digit(first11: str) -> int:
    digits = "".join(str(int(c, 36)) for c in first11.upper())
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return (10 - total % 10) % 10


def isin_valid(isin: Optional[str]) -> bool:
    if not isin or not ISIN_RE.match(isin.upper()):
        return False
    return isin_check_digit(isin[:11]) == int(isin[11])


def normalise_name(name: str) -> str:
    s = SUFFIXES.sub(" ", (name or "").lower())
    s = re.sub(r"[^a-z0-9& ]", " ", s)
    return " ".join(s.split())


def clean_symbol(query: str) -> str:
    """Strip exchange decorations: 'NSE:INFY', 'INFY.NS', '500209.BO', 'BSE: 500209'."""
    q = query.strip().upper()
    q = re.sub(r"^(NSE|BSE)\s*:\s*", "", q)
    q = re.sub(r"\.(NS|BO)$", "", q)
    return q


@dataclass
class Resolution:
    status: str  # resolved | ambiguous | not_found
    query: str
    security: Optional[Security] = None
    candidates: list = field(default_factory=list)
    sources: list = field(default_factory=list)  # Source objects of master rows used
    warnings: list = field(default_factory=list)


def merge_master(records: list) -> list:
    """Merge rows for the same ISIN from several masters (NSE gives the symbol, BSE the code)."""
    by_key: dict = {}
    for r in records:
        key = (r.get("isin") or "").upper() or ("NSE:%s" % r.get("nse_symbol") if r.get("nse_symbol")
                                                  else "BSE:%s" % r.get("bse_code"))
        cur = by_key.setdefault(key, {"sources": [], "conflicts": []})
        for f in ("name", "isin", "nse_symbol", "bse_code", "series", "face_value"):
            v = r.get(f)
            if v in (None, ""):
                continue
            existing = cur.get(f)
            if existing in (None, ""):
                cur[f] = v
            elif f != "name" and str(existing).upper() != str(v).upper():
                cur["conflicts"].append("%s: %s vs %s" % (f, existing, v))
        cur["synthetic"] = cur.get("synthetic", False) or bool(r.get("synthetic"))
        if r.get("source") is not None:
            cur["sources"].append(r["source"])
    return list(by_key.values())


def _to_security(rec: dict) -> Security:
    return Security(name=rec.get("name", ""), isin=(rec.get("isin") or None),
                    nse_symbol=rec.get("nse_symbol"), bse_code=(str(rec["bse_code"]) if rec.get("bse_code") else None),
                    series=rec.get("series"), face_value=rec.get("face_value"),
                    synthetic=bool(rec.get("synthetic")))


def resolve(query: str, master: list) -> Resolution:
    recs = merge_master(master)
    q = clean_symbol(query)
    hits = []
    if ISIN_RE.match(q):
        hits = [r for r in recs if (r.get("isin") or "").upper() == q]
    elif re.fullmatch(r"\d{6}", q):
        hits = [r for r in recs if str(r.get("bse_code") or "") == q]
    if not hits:
        hits = [r for r in recs if (r.get("nse_symbol") or "").upper() == q]
    if not hits:
        nq = normalise_name(query)
        hits = [r for r in recs if normalise_name(r.get("name", "")) == nq]
        if not hits and nq:
            scored = []
            for r in recs:
                nn = normalise_name(r.get("name", ""))
                ratio = difflib.SequenceMatcher(None, nq, nn).ratio()
                if ratio >= 0.8 or (len(nq) >= 4 and nq in nn):
                    scored.append((ratio, r))
            scored.sort(key=lambda t: -t[0])
            if len(scored) == 1 or (len(scored) > 1 and scored[0][0] >= 0.95 > scored[1][0]):
                hits = [scored[0][1]]
            else:
                hits = [r for _, r in scored]
    if not hits:
        return Resolution("not_found", query)
    if len(hits) > 1:
        return Resolution("ambiguous", query, candidates=[_to_security(r) for r in hits[:10]])
    rec = hits[0]
    sec = _to_security(rec)
    res = Resolution("resolved", query, security=sec, sources=rec.get("sources", []))
    verify(sec, rec, res)
    return res


def verify(sec: Security, rec: dict, res: Resolution) -> None:
    checks = sec.verification
    if sec.isin:
        if isin_valid(sec.isin):
            checks.append("ISIN %s has a valid check digit" % sec.isin)
        else:
            res.warnings.append("ISIN %s fails the ISO 6166 check digit" % sec.isin)
        if not sec.isin.upper().startswith("IN"):
            res.warnings.append("ISIN %s is not an Indian (IN) ISIN" % sec.isin)
        elif not sec.isin.upper().startswith("INE"):
            res.warnings.append("ISIN %s is not an INE (company equity) ISIN" % sec.isin)
    else:
        res.warnings.append("no ISIN in the securities master: identity rests on the exchange code alone")
    if sec.nse_symbol and sec.bse_code:
        checks.append("NSE %s and BSE %s map to the same ISIN" % (sec.nse_symbol, sec.bse_code))
    if rec.get("conflicts"):
        res.warnings.append("securities masters disagree: " + "; ".join(rec["conflicts"]))
    if sec.series and sec.series not in ("EQ", "BE", "BZ", "SM", "ST"):
        res.warnings.append("NSE series %s is not a regular equity series" % sec.series)
    elif sec.series in ("BE", "BZ"):
        res.warnings.append("NSE series %s: trade-for-trade segment (surveillance / compulsory delivery)" % sec.series)
    official = [s for s in res.sources if s.official and not s.synthetic]
    if official:
        checks.append("listed in official master: " + ", ".join(sorted({s.publisher for s in official})))
    elif sec.synthetic:
        res.warnings.append("SYNTHETIC sample security: not a real listed company")
    else:
        res.warnings.append("not confirmed against an official exchange master (local master only)")


def check_profile(sec: Security, profile: Optional[dict], res: Resolution) -> None:
    """Cross-check the company profile file against the master record."""
    if not profile:
        res.warnings.append("no company profile available (sector, shares outstanding, peers)")
        return
    for f in ("isin", "nse_symbol", "bse_code"):
        pv, sv = profile.get(f), getattr(sec, f)
        if pv and sv and str(pv).upper() != str(sv).upper():
            res.warnings.append("profile %s %s does not match master %s" % (f, pv, sv))
    if profile.get("name") and normalise_name(profile["name"]) != normalise_name(sec.name):
        ratio = difflib.SequenceMatcher(None, normalise_name(profile["name"]), normalise_name(sec.name)).ratio()
        if ratio < 0.8:
            res.warnings.append("profile name %r differs from master name %r" % (profile["name"], sec.name))
    sec.sector = profile.get("sector") or sec.sector
    sec.industry = profile.get("industry") or sec.industry
    sec.face_value = profile.get("face_value") or sec.face_value
