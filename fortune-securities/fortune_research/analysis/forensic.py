"""Forensic analyst: evidence-backed governance and accounting-quality flags.

Every finding cites the record it rests on (shareholding pattern quarter,
annual-report page, or computed metric). A flag is a question to investigate,
not a conclusion of wrongdoing.
"""

from __future__ import annotations

from ..models import Finding, fy_label
from .calc import source_ids_of

PLEDGE_HIGH = 25.0      # % of promoter holding pledged
PLEDGE_MEDIUM = 10.0
PROMOTER_DROP_PP = 2.0  # percentage-point fall over the window
RPT_REVENUE_PCT = 10.0
CONTINGENT_PCT = 20.0
CFO_PAT_MIN = 0.7
OTHER_INCOME_PCT = 25.0
RECEIVABLE_DAYS_JUMP = 15.0


def _f(module, code, sev, msg, evidence=None, sources=None):
    return Finding(module, code, sev, msg, evidence or {}, [s for s in (sources or []) if s])


def shareholding_flags(records: list) -> list:
    out = []
    if not records:
        out.append(_f("forensic", "no_shareholding", "info", "No shareholding-pattern data: pledge and ownership checks not run"))
        return out
    last = records[-1]
    q = fy_label(last.quarter_end, "Q")
    if last.promoter_pledged_pct is not None:
        p = last.promoter_pledged_pct
        sev = "high" if p >= PLEDGE_HIGH else "medium" if p >= PLEDGE_MEDIUM else "low" if p > 0 else None
        if sev:
            out.append(_f("forensic", "promoter_pledge", sev, "%.1f%% of promoter holding pledged/encumbered at %s" % (p, q),
                          {"quarter": q, "pledged_pct": p}, [last.source.id]))
        hist = [r for r in records if r.promoter_pledged_pct is not None]
        if len(hist) >= 2 and hist[-1].promoter_pledged_pct > hist[0].promoter_pledged_pct:
            out.append(_f("forensic", "pledge_rising", "medium",
                          "Promoter pledge rose from %.1f%% (%s) to %.1f%% (%s)"
                          % (hist[0].promoter_pledged_pct, fy_label(hist[0].quarter_end, "Q"), hist[-1].promoter_pledged_pct, q),
                          {"from": hist[0].promoter_pledged_pct, "to": hist[-1].promoter_pledged_pct},
                          [hist[0].source.id, hist[-1].source.id]))
    else:
        out.append(_f("forensic", "pledge_unknown", "info", "Pledge data not available for %s" % q, sources=[last.source.id]))
    ph = [r for r in records[-5:] if r.promoter_pct is not None]
    if len(ph) >= 2:
        drop = ph[0].promoter_pct - ph[-1].promoter_pct
        if drop >= PROMOTER_DROP_PP:
            out.append(_f("forensic", "promoter_selling", "medium",
                          "Promoter holding fell %.2f pp from %.2f%% (%s) to %.2f%% (%s)"
                          % (drop, ph[0].promoter_pct, fy_label(ph[0].quarter_end, "Q"), ph[-1].promoter_pct, q),
                          {"from": ph[0].promoter_pct, "to": ph[-1].promoter_pct}, [ph[0].source.id, ph[-1].source.id]))
        elif drop > 0:
            out.append(_f("forensic", "promoter_holding_down", "low",
                          "Promoter holding down %.2f pp over %d quarters" % (drop, len(ph) - 1),
                          {"from": ph[0].promoter_pct, "to": ph[-1].promoter_pct}, [ph[0].source.id, ph[-1].source.id]))
    if last.promoter_pct is not None and last.promoter_pct > 75:
        out.append(_f("forensic", "mps_breach", "medium", "Promoter holding %.2f%% exceeds 75%%: minimum public shareholding "
                      "(SCRR 19A) not met" % last.promoter_pct, {"promoter_pct": last.promoter_pct}, [last.source.id]))
    return out


def governance_flags(gov: dict, revenue_by_fy: dict) -> list:
    out = []
    if not gov or not gov.get("fiscal_years"):
        out.append(_f("forensic", "no_governance", "info", "No annual-report governance data entered: auditor, related-party "
                      "and contingent-liability checks not run"))
        return out
    years = sorted(gov["fiscal_years"].keys())
    latest = years[-1]
    for fy in years:
        rec = gov["fiscal_years"][fy]
        sid = rec.get("_source").id if rec.get("_source") else None
        op = (rec.get("audit_opinion") or "").lower()
        if op in ("qualified", "adverse", "disclaimer"):
            out.append(_f("forensic", "audit_" + op, "critical" if op != "qualified" else "high",
                          "%s: auditor issued a %s opinion%s" % (fy, op, (": " + rec["qualification_text"]) if rec.get("qualification_text") else ""),
                          {"fy": fy, "auditor": rec.get("auditor")}, [sid]))
        elif not op:
            out.append(_f("forensic", "audit_opinion_unknown", "info", "%s: audit opinion not recorded" % fy, {"fy": fy}, [sid]))
        if rec.get("emphasis_of_matter"):
            out.append(_f("forensic", "emphasis_of_matter", "medium", "%s: emphasis of matter: %s" % (fy, rec["emphasis_of_matter"]),
                          {"fy": fy}, [sid]))
        if rec.get("auditor_resigned"):
            out.append(_f("forensic", "auditor_resigned", "critical", "%s: statutory auditor resigned mid-term%s"
                          % (fy, (" (%s)" % rec["auditor_resignation_reason"]) if rec.get("auditor_resignation_reason") else ""),
                          {"fy": fy}, [sid]))
        elif rec.get("auditor_changed"):
            out.append(_f("forensic", "auditor_changed", "low", "%s: statutory auditor changed (rotation or replacement)" % fy,
                          {"fy": fy}, [sid]))
        for remark in rec.get("caro_adverse_remarks") or []:
            out.append(_f("forensic", "caro_remark", "medium", "%s: CARO remark: %s" % (fy, remark), {"fy": fy}, [sid]))
        rpt = rec.get("rpt_total_cr")
        rev = revenue_by_fy.get(fy)
        if rpt is not None and rev and rev.value:
            pct = rpt / rev.value * 100
            sev = "high" if pct >= 2 * RPT_REVENUE_PCT else "medium" if pct >= RPT_REVENUE_PCT else "low" if pct >= 5 else None
            if sev:
                out.append(_f("forensic", "related_party", sev, "%s: related-party transactions INR %.0f cr = %.1f%% of revenue%s"
                              % (fy, rpt, pct, ("; " + rec["rpt_note"]) if rec.get("rpt_note") else ""),
                              {"fy": fy, "rpt_cr": rpt, "pct_revenue": round(pct, 2)}, [sid] + source_ids_of(rev)))
        for ev in rec.get("other_events") or []:
            out.append(_f("forensic", "governance_event", ev.get("severity", "medium"), "%s: %s" % (fy, ev.get("text", "")),
                          {"fy": fy}, [sid]))
    if latest and gov["fiscal_years"][latest].get("rpt_total_cr") is None:
        out.append(_f("forensic", "rpt_unknown", "info", "%s: related-party total not recorded" % latest))
    return out


def accounting_flags(fa) -> list:
    """Accrual-quality signals from the computed financials."""
    out = []
    if not fa.fy_periods:
        return out
    labels = [fy_label(p, "FY") for p in fa.fy_periods]
    recent = labels[-3:]
    cfo = [fa.annual[l]["cfo"].value for l in recent]
    pat = [fa.annual[l]["pat"].value for l in recent]
    if None not in cfo and None not in pat and sum(pat) > 0:
        ratio = sum(cfo) / sum(pat)
        if ratio < CFO_PAT_MIN:
            ids = sum((fa.annual[l]["cfo"].source_ids + fa.annual[l]["pat"].source_ids for l in recent), [])
            out.append(_f("forensic", "weak_cash_conversion", "high" if ratio < 0.4 else "medium",
                          "Cumulative CFO/PAT over %s-%s is %.2f (below %.1f): profits not converting to cash"
                          % (recent[0], recent[-1], ratio, CFO_PAT_MIN), {"cfo_to_pat": round(ratio, 3)}, ids))
    last = fa.annual[labels[-1]]
    oi = last["other_income_share_of_pbt"]
    if oi.value is not None and oi.value > OTHER_INCOME_PCT:
        out.append(_f("forensic", "other_income_dependence", "medium", "%s: other income is %.1f%% of PBT" % (labels[-1], oi.value),
                      {"pct": round(oi.value, 2)}, oi.source_ids))
    if len(labels) >= 3:
        r0, r1 = fa.annual[labels[-3]]["receivable_days"], last["receivable_days"]
        if r0.value is not None and r1.value is not None and r1.value - r0.value >= RECEIVABLE_DAYS_JUMP:
            out.append(_f("forensic", "receivables_stretching", "medium",
                          "Receivable days rose from %.0f (%s) to %.0f (%s)" % (r0.value, labels[-3], r1.value, labels[-1]),
                          {"from": round(r0.value, 1), "to": round(r1.value, 1)}, r0.source_ids + r1.source_ids))
        elif r0.value is not None and r1.value is not None and r1.value - r0.value >= RECEIVABLE_DAYS_JUMP / 2:
            out.append(_f("forensic", "receivables_rising", "low",
                          "Receivable days up from %.0f (%s) to %.0f (%s)" % (r0.value, labels[-3], r1.value, labels[-1]),
                          {"from": round(r0.value, 1), "to": round(r1.value, 1)}, r0.source_ids + r1.source_ids))
    cl = last["contingent_liabilities_to_equity"]
    if cl.value is not None and cl.value >= CONTINGENT_PCT:
        out.append(_f("forensic", "contingent_liabilities", "medium", "%s: contingent liabilities are %.1f%% of net worth"
                      % (labels[-1], cl.value), {"pct": round(cl.value, 2)}, cl.source_ids))
    etr = last["effective_tax_rate"]
    if etr.value is not None and etr.value < 15:
        out.append(_f("forensic", "low_tax_rate", "low", "%s: effective tax rate %.1f%% (well below the ~25%% statutory rate; "
                      "check incentives or one-offs)" % (labels[-1], etr.value), {"etr": round(etr.value, 2)}, etr.source_ids))
    return out


def analyse(fa, shareholding: list, governance: dict) -> list:
    rev = {fy_label(p, "FY"): fa.annual[fy_label(p, "FY")]["revenue"] for p in fa.fy_periods}
    return shareholding_flags(shareholding) + governance_flags(governance, rev) + accounting_flags(fa)
