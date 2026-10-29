"""Compare a new analysis with the previous one for the same company.

Reports: metric moves beyond a threshold, findings that appeared or cleared,
the valuation position and fair-value range, risk level, new announcements,
new data periods, and previous thesis-invalidation conditions re-tested
against the new data.
"""

from __future__ import annotations

from ..analysis.risk import evaluate_conditions

# metric -> (threshold, kind) where kind is "pp" (absolute points) or "pct" (relative change)
WATCH = {
    "q.revenue_yoy": (3.0, "pp"), "q.pat_yoy": (5.0, "pp"), "q.ebitda_margin": (1.0, "pp"),
    "ttm.revenue": (2.0, "pct"), "ttm.pat": (3.0, "pct"), "ttm.eps": (3.0, "pct"), "ttm.ebitda_margin": (0.75, "pp"),
    "fy.roe": (1.0, "pp"), "fy.roce": (1.0, "pp"), "fy.debt_to_equity": (0.1, "abs"),
    "val.price": (5.0, "pct"), "val.pe": (5.0, "pct"), "val.ev_ebitda": (5.0, "pct"), "val.market_cap": (5.0, "pct"),
    "tech.rsi_14": (10.0, "abs"), "tech.sma_200": (3.0, "pct"),
    "own.promoter_pct": (0.25, "pp"), "own.promoter_pledged_pct": (1.0, "pp"),
}


def _moved(old, new, thr, kind) -> bool:
    if old is None or new is None:
        return old is not new
    if kind == "pct":
        return old != 0 and abs(new / old - 1) * 100 >= thr
    return abs(new - old) >= thr


def compare(prev: dict, cur: dict) -> dict:
    out = {"previous_id": prev.get("_id"), "previous_as_of": prev["as_of"], "previous_created_at": prev["created_at"],
           "current_as_of": cur["as_of"], "metric_changes": [], "findings_new": [], "findings_cleared": [],
           "severity_changes": [], "conditions": [], "new_periods": [], "new_announcements": [], "summary_changes": []}
    pm, cm = prev.get("metrics", {}), cur.get("metrics", {})
    for k, (thr, kind) in WATCH.items():
        a, b = pm.get(k, {}).get("value"), cm.get(k, {}).get("value")
        if a is None and b is None:
            continue
        if _moved(a, b, thr, kind):
            out["metric_changes"].append({"metric": k, "previous": a, "current": b, "unit": (cm.get(k) or pm.get(k))["unit"],
                                          "previous_period": pm.get(k, {}).get("period"), "current_period": cm.get(k, {}).get("period")})
    key = lambda f: (f["module"], f["code"])  # noqa: E731
    pf = {key(f): f for f in prev.get("findings", [])}
    cf = {key(f): f for f in cur.get("findings", [])}
    out["findings_new"] = [cf[k] for k in cf if k not in pf and cf[k]["severity"] != "info"]
    out["findings_cleared"] = [pf[k] for k in pf if k not in cf and pf[k]["severity"] != "info"]
    for k in cf:
        if k in pf and (pf[k]["severity"] != cf[k]["severity"] or pf[k]["message"] != cf[k]["message"]):
            out["severity_changes"].append({"code": k[1], "previous": pf[k]["severity"], "current": cf[k]["severity"],
                                            "previous_message": pf[k]["message"], "message": cf[k]["message"]})
    out["conditions"] = evaluate_conditions(prev.get("conditions", []), cur.get("state", {}))
    pp, cp = set(prev.get("periods", [])), set(cur.get("periods", []))
    out["new_periods"] = sorted(cp - pp)
    old_fp = {i["fingerprint"] for i in prev.get("news", {}).get("items", [])}
    out["new_announcements"] = [i for i in cur.get("news", {}).get("items", []) if i["fingerprint"] not in old_fp]
    ps, cs = prev.get("summary", {}), cur.get("summary", {})
    for k in ("valuation_position", "risk_level", "fundamentals", "governance", "trend", "confidence"):
        if ps.get(k) != cs.get(k):
            out["summary_changes"].append({"field": k, "previous": ps.get(k), "current": cs.get(k)})
    pfv, cfv = ps.get("fair_value") or {}, cs.get("fair_value") or {}
    if pfv.get("mid") and cfv.get("mid") and abs(cfv["mid"] / pfv["mid"] - 1) >= 0.05:
        out["summary_changes"].append({"field": "fair_value_mid", "previous": round(pfv["mid"], 2), "current": round(cfv["mid"], 2)})
    triggered = [c for c in out["conditions"] if c["status"] == "TRIGGERED"]
    out["headline"] = _headline(out, triggered)
    return out


def _headline(d: dict, triggered: list) -> str:
    parts = []
    if d["new_periods"]:
        parts.append("new data for %s" % ", ".join(d["new_periods"]))
    if triggered:
        parts.append("%d thesis condition(s) triggered" % len(triggered))
    if d["findings_new"]:
        parts.append("%d new flag(s)" % len(d["findings_new"]))
    if d["findings_cleared"]:
        parts.append("%d flag(s) cleared" % len(d["findings_cleared"]))
    if d["metric_changes"]:
        parts.append("%d material metric move(s)" % len(d["metric_changes"]))
    if d["new_announcements"]:
        parts.append("%d new announcement(s)" % len(d["new_announcements"]))
    return "; ".join(parts) if parts else "no material change since the previous analysis"
