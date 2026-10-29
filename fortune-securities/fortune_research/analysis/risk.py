"""Risk analyst: downside scenarios, liquidity, valuation and balance-sheet risk,
and explicit thesis-invalidation conditions that the next analysis re-tests.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Optional

from ..models import Finding

OPS = {"<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge, "==": operator.eq}


@dataclass
class RiskResult:
    findings: list = field(default_factory=list)
    scenarios: dict = field(default_factory=dict)  # name -> {price, change_pct, basis}
    liquidity: dict = field(default_factory=dict)
    conditions: list = field(default_factory=list)  # invalidation conditions
    level: str = "unknown"


def state_snapshot(fa, ta, shareholding: list, governance: Optional[dict], price: Optional[float]) -> dict:
    """The values invalidation conditions are tested against (stored with each analysis)."""
    s = {}

    def put(key, metric):
        if metric is not None and getattr(metric, "value", None) is not None:
            s[key] = round(metric.value, 4)

    put("q.revenue_yoy", fa.q("revenue_yoy"))
    put("q.pat_yoy", fa.q("pat_yoy"))
    put("ttm.ebitda_margin", fa.ttm.get("ebitda_margin"))
    put("fy.debt_to_equity", fa.fy("debt_to_equity"))
    put("fy.interest_coverage", fa.fy("interest_coverage"))
    put("fy.roce", fa.fy("roce"))
    if shareholding:
        last = shareholding[-1]
        if last.promoter_pledged_pct is not None:
            s["promoter_pledged_pct"] = last.promoter_pledged_pct
        if last.promoter_pct is not None:
            s["promoter_pct"] = last.promoter_pct
    if governance and governance.get("fiscal_years"):
        fy = sorted(governance["fiscal_years"])[-1]
        op = (governance["fiscal_years"][fy].get("audit_opinion") or "").lower()
        if op:
            s["audit_opinion_modified"] = 1 if op in ("qualified", "adverse", "disclaimer") else 0
    if price is not None:
        s["price_close"] = price
    if ta and ta.values.get("sma_200") is not None:
        s["sma_200"] = round(ta.values["sma_200"], 2)
    return s


def build_conditions(state: dict, ta) -> list:
    c = []

    def add(cid, key, op, thr, text):
        c.append({"id": cid, "key": key, "op": op, "threshold": round(thr, 4), "text": text})

    if "q.revenue_yoy" in state:
        thr = max(0.0, state["q.revenue_yoy"] - 10)
        add("rev_growth_break", "q.revenue_yoy", "<", thr, "Quarterly revenue growth (YoY) falls below %.1f%%" % thr)
    if "q.pat_yoy" in state:
        add("pat_decline", "q.pat_yoy", "<", 0.0, "Quarterly PAT declines year on year")
    if "ttm.ebitda_margin" in state:
        thr = state["ttm.ebitda_margin"] - 2
        add("margin_break", "ttm.ebitda_margin", "<", thr, "TTM EBITDA margin falls below %.1f%%" % thr)
    if "promoter_pledged_pct" in state:
        thr = max(10.0, state["promoter_pledged_pct"] + 5)
        add("pledge_rise", "promoter_pledged_pct", ">", thr, "Promoter pledge rises above %.1f%% of promoter holding" % thr)
    if "promoter_pct" in state:
        thr = state["promoter_pct"] - 2
        add("promoter_exit", "promoter_pct", "<", thr, "Promoter holding falls below %.2f%%" % thr)
    if "audit_opinion_modified" in state:
        add("audit_modified", "audit_opinion_modified", "==", 1, "Auditor issues a qualified, adverse or disclaimer opinion")
    if "fy.debt_to_equity" in state:
        thr = max(1.0, state["fy.debt_to_equity"] * 1.5)
        add("leverage_up", "fy.debt_to_equity", ">", thr, "Debt/equity rises above %.2fx" % thr)
    if ta and ta.support and "price_close" in state:
        # nearest support at least 3% below the price, so ordinary noise does not trigger it
        deeper = [lv for lv, _ in ta.support if lv <= state["price_close"] * 0.97]
        lvl = deeper[0] if deeper else ta.support[-1][0]
        add("support_break", "price_close", "<", lvl, "Price closes below support %.2f" % lvl)
    return c


def evaluate_conditions(conditions: list, state: dict) -> list:
    out = []
    for c in conditions:
        v = state.get(c["key"])
        if v is None:
            out.append({**c, "status": "unknown", "value": None})
            continue
        hit = OPS[c["op"]](v, c["threshold"])
        out.append({**c, "status": "TRIGGERED" if hit else "holds", "value": v})
    return out


def _r(code, sev, msg, evidence=None, sources=None):
    return Finding("risk", code, sev, msg, evidence or {}, list(sources or []))


def analyse(fa, ta, vr, forensic: list, cfg: dict, position_value_cr: Optional[float] = None) -> RiskResult:
    rr = RiskResult()
    f = rr.findings
    # liquidity
    adv = ta.values.get("avg_traded_value_20d_cr") if ta else None
    part = cfg.get("adv_participation", 0.10)
    rr.liquidity = {"avg_traded_value_20d_cr": adv, "participation": part}
    if adv is None:
        f.append(_r("liquidity_unknown", "info", "Average traded value unknown (no price/volume data)"))
    else:
        if adv < 1:
            f.append(_r("illiquid", "high", "Average daily traded value INR %.2f cr (<1 cr): exits may move the price" % adv,
                        {"adv_cr": adv}, [ta.source_id]))
        elif adv < 5:
            f.append(_r("thin_liquidity", "medium", "Average daily traded value INR %.2f cr (<5 cr)" % adv,
                        {"adv_cr": adv}, [ta.source_id]))
        if position_value_cr:
            days = position_value_cr / (adv * part) if adv > 0 else None
            rr.liquidity["position_value_cr"] = position_value_cr
            rr.liquidity["days_to_exit"] = days
            if days is not None and days > 5:
                f.append(_r("exit_days", "medium" if days < 20 else "high",
                            "Exiting the INR %.2f cr position at %.0f%% of ADV takes ~%.1f trading days" % (position_value_cr, part * 100, days),
                            {"days": round(days, 1)}, [ta.source_id]))
    # balance sheet
    de, ic, cr = fa.fy("debt_to_equity"), fa.fy("interest_coverage"), fa.fy("current_ratio")
    if de and de.value is not None and de.value > 1:
        f.append(_r("leverage", "high" if de.value > 2 else "medium", "Debt/equity %.2fx (%s)" % (de.value, de.period),
                    {"de": round(de.value, 3)}, de.source_ids))
    if ic and ic.value is not None and ic.value < 3:
        f.append(_r("interest_cover", "high" if ic.value < 1.5 else "medium", "Interest coverage %.2fx (%s)" % (ic.value, ic.period),
                    {"ic": round(ic.value, 3)}, ic.source_ids))
    if cr and cr.value is not None and cr.value < 1:
        f.append(_r("current_ratio", "medium", "Current ratio %.2fx (%s): current liabilities exceed current assets" % (cr.value, cr.period),
                    {"cr": round(cr.value, 3)}, cr.source_ids))
    nd, e = fa.fy("net_debt"), fa.fy("ebitda")
    if nd and e and nd.value is not None and e.value and e.value > 0 and nd.value / e.value > 3:
        f.append(_r("net_debt_ebitda", "medium", "Net debt / EBITDA %.2fx (%s)" % (nd.value / e.value, nd.period),
                    {"x": round(nd.value / e.value, 3)}, nd.source_ids + e.source_ids))
    # earnings momentum
    py = fa.q("pat_yoy")
    if py and py.value is not None and py.value < -10:
        f.append(_r("earnings_decline", "medium", "Latest quarter PAT %.1f%% YoY (%s)" % (py.value, py.period),
                    {"pat_yoy": round(py.value, 2)}, py.source_ids))
    # valuation risk
    pe = vr.multiples.get("pe") if vr else None
    pst = vr.peer_stats.get("pe") if vr else None
    if pe and pe.value and pst:
        prem = (pe.value / pst["median"] - 1) * 100
        if pe.value > pst["p75"]:
            f.append(_r("valuation_premium", "medium", "P/E %.1fx is above the peer 75th percentile (%.1fx); %.0f%% premium to the peer median"
                        % (pe.value, pst["p75"], prem), {"pe": round(pe.value, 2), "peer_median": round(pst["median"], 2)}, pe.source_ids))
    if vr and vr.position == "above_range":
        f.append(_r("above_fair_range", "medium", "Price %.2f is above the model fair-value range %.2f-%.2f"
                    % (vr.price, vr.fair_value["low"], vr.fair_value["high"])))
    # price behaviour
    vol = ta.values.get("volatility_ann") if ta else None
    if vol is not None and vol > 0.45:
        f.append(_r("high_volatility", "medium", "Annualised volatility %.0f%%" % (vol * 100), {"vol": round(vol, 4)}, [ta.source_id]))
    # scenarios (per share)
    price = vr.price if vr else None
    eps = fa.ttm.get("eps")
    if price and eps and eps.value and eps.value > 0:
        bear_pe = pst["p25"] if pst else (pe.value * 0.75 if pe and pe.value else None)
        basis = "peer P/E 25th pct" if pst else "own P/E de-rated 25%"
        if bear_pe:
            bear_eps = eps.value * (1 - cfg.get("bear_eps_decline", 0.20))
            bp = bear_eps * bear_pe
            rr.scenarios["bear"] = {"price": bp, "change_pct": (bp / price - 1) * 100,
                                    "basis": "TTM EPS -%d%% x %s (%.1fx)" % (cfg.get("bear_eps_decline", 0.20) * 100, basis, bear_pe)}
    if price and vr and vr.fair_value:
        rr.scenarios["base"] = {"price": vr.fair_value["mid"], "change_pct": (vr.fair_value["mid"] / price - 1) * 100,
                                "basis": "median of valuation methods (%s)" % ", ".join(vr.fair_value["methods"])}
        rr.scenarios["bull"] = {"price": vr.fair_value["high"], "change_pct": (vr.fair_value["high"] / price - 1) * 100,
                                "basis": "top of valuation range"}
    mdd = ta.values.get("max_drawdown_1y") if ta else None
    if price and mdd is not None:
        rr.scenarios["repeat_1y_drawdown"] = {"price": price * (1 + mdd), "change_pct": mdd * 100,
                                              "basis": "repeat of the worst peak-to-trough fall in the last year"}
    # overall level, counting forensic findings too
    sev = [x.severity for x in f + list(forensic)]
    if "critical" in sev or sev.count("high") >= 2:
        rr.level = "high"
    elif "high" in sev or sev.count("medium") >= 3:
        rr.level = "elevated"
    elif "medium" in sev:
        rr.level = "moderate"
    else:
        rr.level = "low"
    return rr
