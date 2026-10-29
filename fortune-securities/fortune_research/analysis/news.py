"""News monitor: classify exchange announcements and news into SEBI LODR-style
categories with a materiality tag, de-duplicate, and mark what is new since
the previous analysis.

Exchange filings are primary evidence; publisher headlines are leads to verify.
Keyword rules are transparent and listed here so a misclassification can be
traced and fixed.
"""

from __future__ import annotations

import re

# (category, materiality, patterns) - first match wins, so specific rules come first
RULES = [
    ("auditor_change", "high", [r"resignation of (the )?(statutory )?auditor", r"auditor.{0,20}resign"]),
    ("insolvency", "high", [r"\binsolvency\b", r"\bnclt\b", r"\bibc\b", r"corporate insolvency"]),
    ("regulatory_action", "high", [r"\bsebi\b.{0,40}(order|penalty|show cause|adjudicat)", r"show cause notice", r"\bsfio\b",
                                    r"enforcement directorate", r"\braid\b", r"search and seizure", r"income tax search"]),
    ("default", "high", [r"\bdefault\b", r"delay in (payment|servicing)", r"non-payment of interest"]),
    ("kmp_change", "high", [r"(resignation|cessation) of.{0,30}(\bceo\b|\bcfo\b|chief executive|chief financial|managing director|\bmd\b|"
                            r"whole[- ]time director|company secretary|key managerial|\bkmp\b)",
                            r"(\bceo\b|\bcfo\b|chief executive officer|chief financial officer|managing director).{0,20}resign"]),
    ("pledge", "high", [r"\bpledge\b", r"encumbrance", r"reg(ulation)?\.?\s*31\(1\)", r"invocation"]),
    ("financial_results", "high", [r"financial results", r"audited results", r"unaudited results", r"outcome of board meeting.{0,40}result"]),
    ("credit_rating", "medium", [r"credit rating", r"\brating\b.{0,30}(upgrade|downgrade|reaffirm|revis)"]),
    ("acquisition_or_merger", "medium", [r"acquisition", r"amalgamation", r"\bmerger\b", r"scheme of arrangement", r"demerger"]),
    ("fund_raising", "medium", [r"\bqip\b", r"preferential (issue|allotment)", r"rights issue", r"fund raising", r"\bncd", r"warrants"]),
    ("insider_or_sast", "medium", [r"\bsast\b", r"reg(ulation)?\.?\s*29", r"insider trading", r"\bpit\b", r"regulation 7\(2\)"]),
    ("litigation", "medium", [r"litigation", r"\bcourt\b", r"arbitration", r"\bclaim\b", r"tribunal"]),
    ("order_win", "medium", [r"order (win|received|bagged)", r"\bbags?\b.{0,20}order", r"letter of award", r"contract (award|win)"]),
    ("corporate_action", "medium", [r"dividend", r"\bbonus\b", r"split", r"buy[- ]?back", r"record date"]),
    ("board_meeting", "low", [r"board meeting", r"intimation of board"]),
    ("investor_meet", "low", [r"analyst", r"investor (meet|call|presentation)", r"earnings call", r"con[- ]?call", r"transcript"]),
    ("agm_or_egm", "low", [r"\bagm\b", r"\begm\b", r"annual general meeting", r"postal ballot", r"voting results"]),
    ("compliance_routine", "info", [r"trading window", r"reg(ulation)?\.?\s*74\(5\)", r"certificate under", r"loss of share certificate",
                                    r"newspaper (publication|advertisement)", r"compliance certificate"]),
]
COMPILED = [(c, m, [re.compile(p, re.I) for p in ps]) for c, m, ps in RULES]


def classify(subject: str, hint: str = "", details: str = "") -> tuple:
    text = " ".join([subject or "", hint or "", details or ""])
    for cat, mat, pats in COMPILED:
        if any(p.search(text) for p in pats):
            return cat, mat
    return "other", "low"


# disclosures that are governance evidence in themselves
GOVERNANCE_CATEGORIES = {"auditor_change": "critical", "insolvency": "critical", "default": "high", "regulatory_action": "high",
                         "kmp_change": "medium"}


def governance_findings(items: list, as_of, window_days: int = 180) -> list:
    """Exchange disclosures (not news headlines) in governance categories within the window."""
    import datetime as _dt
    from ..models import Finding
    out = []
    for i in items:
        sev = GOVERNANCE_CATEGORIES.get(i["category"])
        if not sev or i["is_news"] or (as_of - _dt.date.fromisoformat(i["date"])).days > window_days:
            continue
        out.append(Finding("forensic", "disclosure_" + i["category"], sev, "%s disclosure on %s: %s" % (i["exchange"], i["date"], i["subject"]),
                           {"date": i["date"], "category": i["category"]}, [i["source_id"]]))
    return out


def analyse(announcements: list, news: list, seen_fingerprints: set) -> dict:
    """Return {'items': [...], 'new_count', 'material'} with items newest first."""
    items, seen = [], set()
    for a in list(announcements) + list(news):
        fp = a.fingerprint
        if fp in seen:
            continue
        seen.add(fp)
        is_news = a.category == "news"
        cat, mat = ("news", "lead") if is_news else classify(a.subject, a.category, a.details)
        items.append({"date": a.date.isoformat(), "exchange": a.exchange, "subject": a.subject, "category": cat,
                      "materiality": mat, "url": a.url, "official": a.source.official, "source_id": a.source.id,
                      "fingerprint": fp, "new": fp not in seen_fingerprints, "is_news": is_news})
    items.sort(key=lambda x: x["date"], reverse=True)
    material = [i for i in items if i["materiality"] == "high"]
    return {"items": items, "new_count": sum(1 for i in items if i["new"]), "material": material}
