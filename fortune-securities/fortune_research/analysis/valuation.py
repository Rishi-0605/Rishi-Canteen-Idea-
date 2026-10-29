"""Valuation analyst: market multiples, peer comparison, DCF and sector methods.

- Multiples: P/E (TTM), P/B, EV/EBITDA, EV/Sales, dividend yield, FCF yield.
- Peer comps: implied value per share from peer median multiples (with 25th/75th
  percentile range), needing at least `min_peers` peers with that multiple.
- DCF (non-financial companies): FCFF = CFO - capex (Ind AS 7 lets interest paid sit in
  financing, so CFO is treated as pre-interest; stated as an assumption). Runs only
  when risk-free rate and equity risk premium are set in settings.
- Banks / NBFCs / insurers: EV-based and DCF methods are skipped; P/B vs ROE
  (justified P/B = (ROE - g) / (CoE - g)) is used instead.

Outputs are model estimates under stated assumptions, not price targets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models import Metric, fy_label
from .calc import derive, median, percentile

FINANCIAL_SECTORS = ("bank", "banks", "nbfc", "financial services", "insurance", "housing finance", "finance")


def is_financial(sector: Optional[str], industry: Optional[str] = None) -> bool:
    text = " ".join([sector or "", industry or ""]).lower()
    return any(s in text for s in FINANCIAL_SECTORS)


@dataclass
class Assumption:
    name: str
    value: object
    source: str  # where it came from: settings / computed / fallback

    def to_dict(self):
        return {"name": self.name, "value": self.value, "source": self.source}


@dataclass
class ValuationResult:
    multiples: dict = field(default_factory=dict)  # name -> Metric
    peers: list = field(default_factory=list)  # [{symbol, name, pe, pb, ev_ebitda, ...}]
    peer_stats: dict = field(default_factory=dict)  # multiple -> {median, p25, p75, n}
    implied: dict = field(default_factory=dict)  # method -> {low, mid, high, note}
    dcf: Optional[dict] = None
    assumptions: list = field(default_factory=list)
    skipped: list = field(default_factory=list)  # (method, reason)
    fair_value: Optional[dict] = None  # {low, mid, high, methods}
    price: Optional[float] = None
    position: Optional[str] = None  # below_range | within_range | above_range


def market_multiples(price: Optional[Metric], shares: Optional[Metric], fa, label: str = "current") -> dict:
    """Multiples from a price metric, a share-count metric and a FinancialAnalysis."""
    m = {}
    m["price"] = price
    m["market_cap"] = derive("market_cap", label, "INR crore", "price x shares / 1e7", {"p": price, "s": shares},
                             lambda p, s: p * s / 1e7)
    eps, pat = fa.ttm.get("eps"), fa.ttm.get("pat")
    m["pe"] = derive("pe", label, "x", "price / TTM EPS", {"p": price, "eps": eps},
                     lambda p, eps: p / eps if eps > 0 else None,
                     "" if not eps or not eps.value or eps.value > 0 else "negative earnings")
    eq = fa.fy("total_equity")
    m["pb"] = derive("pb", label, "x", "market_cap / total_equity (latest FY)", {"mc": m["market_cap"], "eq": eq},
                     lambda mc, eq: mc / eq if eq > 0 else None)
    nd = fa.fy("net_debt")
    m["ev"] = derive("ev", label, "INR crore", "market_cap + net_debt (latest FY)", {"mc": m["market_cap"], "nd": nd},
                     lambda mc, nd: mc + nd)
    m["ev_ebitda"] = derive("ev_ebitda", label, "x", "ev / TTM EBITDA", {"ev": m["ev"], "e": fa.ttm.get("ebitda")},
                            lambda ev, e: ev / e if e > 0 else None)
    m["ev_sales"] = derive("ev_sales", label, "x", "ev / TTM revenue", {"ev": m["ev"], "r": fa.ttm.get("revenue")},
                           lambda ev, r: ev / r if r > 0 else None)
    m["earnings_yield"] = derive("earnings_yield", label, "%", "TTM PAT / market_cap x 100", {"pat": pat, "mc": m["market_cap"]},
                                 lambda pat, mc: pat / mc * 100)
    m["fcf_yield"] = derive("fcf_yield", label, "%", "FCF (latest FY) / market_cap x 100",
                            {"fcf": fa.fy("fcf"), "mc": m["market_cap"]}, lambda fcf, mc: fcf / mc * 100)
    div = fa.fy("dividend_payout")
    m["dividend_yield"] = derive("dividend_yield", label, "%", "dividend payout x earnings yield (latest FY)",
                                 {"d": div, "pat": fa.fy("pat"), "mc": m["market_cap"]},
                                 lambda d, pat, mc: d / 100 * pat / mc * 100)
    m["roe"] = fa.fy("roe")
    return m


def _implied_from(multiple: str, stats: dict, own: dict, fa, shares: Metric) -> Optional[dict]:
    st = stats.get(multiple)
    if not st:
        return None
    per_share = {}
    for k in ("p25", "median", "p75"):
        x = st[k]
        if multiple == "pe":
            eps = fa.ttm.get("eps")
            per_share[k] = x * eps.value if eps and eps.value and eps.value > 0 else None
        elif multiple == "ev_ebitda":
            e, nd = fa.ttm.get("ebitda"), fa.fy("net_debt")
            if e and e.value and e.value > 0 and nd and nd.value is not None and shares and shares.value:
                per_share[k] = (x * e.value - nd.value) * 1e7 / shares.value
            else:
                per_share[k] = None
        elif multiple == "pb":
            eq = fa.fy("total_equity")
            per_share[k] = x * eq.value * 1e7 / shares.value if eq and eq.value and shares and shares.value else None
    if any(v is None for v in per_share.values()):
        return None
    return {"low": per_share["p25"], "mid": per_share["median"], "high": per_share["p75"],
            "note": "peer %s p25/median/p75 = %.1f / %.1f / %.1f (n=%d)" % (multiple, st["p25"], st["median"], st["p75"], st["n"])}


def dcf(fa, shares: Metric, market_cap: Optional[float], beta: Optional[float], cfg: dict, assumptions: list) -> tuple:
    """Two-stage FCFF DCF. Returns (result dict or None, reason if skipped)."""
    rf, erp = cfg.get("risk_free_rate"), cfg.get("equity_risk_premium")
    if rf is None or erp is None:
        return None, "risk_free_rate and equity_risk_premium are not set in settings [valuation]"
    g = cfg.get("terminal_growth", 0.05)
    years = int(cfg.get("forecast_years", 5))
    labels = [fy_label(p, "FY") for p in fa.fy_periods]
    if len(labels) < 3:
        return None, "needs at least 3 fiscal years of statements"
    last = fa.annual[labels[-1]]
    rev = last["revenue"].value
    margins = [fa.annual[l]["fcf_margin"].value for l in labels[-3:]]
    if rev is None or None in margins:
        return None, "revenue or FCF missing in the last 3 years"
    fcf_margin = sum(margins) / len(margins) / 100
    if fcf_margin <= 0:
        return None, "average FCF margin is not positive; DCF not meaningful"
    rcagr = fa.growth.get("revenue_cagr_3y")
    g0 = (rcagr.value / 100) if rcagr and rcagr.value is not None else None
    if g0 is None:
        return None, "3-year revenue CAGR not available"
    g0 = max(min(g0, 0.25), g)
    b, b_src = (beta, "estimated from 1y daily returns vs benchmark") if beta is not None else (cfg.get("beta_fallback", 1.0), "fallback setting (beta not estimable)")
    coe = rf + b * erp
    debt, fin = last["total_debt"].value, last["finance_costs"].value
    nd = last["net_debt"].value
    etr = (last["effective_tax_rate"].value or 25.17) / 100
    if not market_cap or debt is None or nd is None:
        return None, "market cap, debt or net debt missing"
    prev = fa.annual[labels[-2]]["total_debt"].value
    avg_debt = (debt + prev) / 2 if prev is not None else debt
    kd = (fin / avg_debt) if (fin is not None and avg_debt) else rf
    kd_at = kd * (1 - etr)
    wd = debt / (debt + market_cap)
    wacc = (1 - wd) * coe + wd * kd_at
    if wacc - g < 0.01:
        return None, "WACC %.2f%% is too close to terminal growth %.2f%%" % (wacc * 100, g * 100)

    def run(w, gt):
        r, pv, path = rev, 0.0, []
        for t in range(1, years + 1):
            gr = g0 + (gt - g0) * (t - 1) / max(years - 1, 1)
            r *= 1 + gr
            f = r * fcf_margin
            pv += f / (1 + w) ** t
            path.append({"year": t, "growth": gr, "revenue": r, "fcff": f})
        tv = path[-1]["fcff"] * (1 + gt) / (w - gt)
        pv_tv = tv / (1 + w) ** years
        ev = pv + pv_tv
        eq = ev - nd
        return {"ev": ev, "equity": eq, "per_share": eq * 1e7 / shares.value, "pv_tv_share": pv_tv / ev, "path": path}

    base = run(wacc, g)
    grid = {}
    for dw in (-0.01, 0.0, 0.01):
        for dg in (-0.01, 0.0, 0.01):
            if (wacc + dw) - (g + dg) >= 0.01:
                grid["%.1f%%|%.1f%%" % ((wacc + dw) * 100, (g + dg) * 100)] = run(wacc + dw, g + dg)["per_share"]
    for a in (Assumption("risk_free_rate", rf, "settings [valuation] (as of %s; %s)" % (cfg.get("risk_free_rate_as_of", "date not given"),
                                                                                          cfg.get("risk_free_rate_source", "source not given"))),
              Assumption("equity_risk_premium", erp, "settings [valuation]"),
              Assumption("beta", round(b, 3), b_src),
              Assumption("cost_of_equity", round(coe, 4), "rf + beta x ERP"),
              Assumption("pre_tax_cost_of_debt", round(kd, 4), "finance costs / average borrowings (latest FY)"),
              Assumption("tax_rate", round(etr, 4), "effective tax rate, latest FY"),
              Assumption("debt_weight", round(wd, 4), "book debt / (book debt + market cap)"),
              Assumption("wacc", round(wacc, 4), "computed"),
              Assumption("initial_growth", round(g0, 4), "3y revenue CAGR, capped at 25%, floored at terminal growth"),
              Assumption("terminal_growth", g, "settings [valuation]"),
              Assumption("fcf_margin", round(fcf_margin, 4), "average FCF / revenue over the last 3 FY"),
              Assumption("fcff_definition", "CFO - capex", "interest paid assumed classified in financing activities")):
        assumptions.append(a)
    return {"wacc": wacc, "terminal_growth": g, "per_share": base["per_share"], "ev": base["ev"], "equity": base["equity"],
            "terminal_value_share_of_ev": base["pv_tv_share"], "path": base["path"], "sensitivity": grid}, None


def analyse(price: Optional[Metric], shares: Optional[Metric], fa, peers: list, sector: Optional[str],
            industry: Optional[str], beta: Optional[float], cfg: dict) -> ValuationResult:
    vr = ValuationResult(price=price.value if price else None)
    own = market_multiples(price, shares, fa)
    vr.multiples = own
    fin = is_financial(sector, industry)
    use = ["pe", "pb"] if fin else ["pe", "ev_ebitda"]  # P/B is shown for non-financials but not used
    if fin:
        vr.skipped.append(("ev_ebitda / dcf", "financial-sector company: EV-based and FCFF methods are not meaningful"))
    # peers
    vr.peers = peers
    min_peers = int(cfg.get("min_peers", 2))
    for k in ("pe", "pb", "ev_ebitda", "ev_sales"):
        xs = [p.get(k) for p in peers if p.get(k) is not None and p.get(k) > 0]
        if len(xs) >= min_peers:
            vr.peer_stats[k] = {"median": median(xs), "p25": percentile(xs, 25), "p75": percentile(xs, 75), "n": len(xs)}
    if not peers:
        vr.skipped.append(("peer comps", "no peers defined in the company profile"))
    for k in use:
        if k not in vr.peer_stats:
            if peers:
                vr.skipped.append(("peer %s" % k, "fewer than %d peers with a usable %s" % (min_peers, k)))
            continue
        imp = _implied_from(k, vr.peer_stats, own, fa, shares)
        if imp:
            vr.implied["peer_" + k] = imp
        else:
            vr.skipped.append(("peer %s" % k, "company's own %s inputs missing or negative" % k))
    if fin:
        coe = None
        if cfg.get("risk_free_rate") is not None and cfg.get("equity_risk_premium") is not None:
            b = beta if beta is not None else cfg.get("beta_fallback", 1.0)
            coe = cfg["risk_free_rate"] + b * cfg["equity_risk_premium"]
        roe, g = fa.fy("roe"), cfg.get("terminal_growth", 0.05)
        eq = fa.fy("total_equity")
        if coe and roe and roe.value is not None and coe - g > 0.01 and eq and eq.value and shares and shares.value:
            jpb = (roe.value / 100 - g) / (coe - g)
            bvps = eq.value * 1e7 / shares.value
            vr.implied["justified_pb"] = {"low": jpb * bvps * 0.9, "mid": jpb * bvps, "high": jpb * bvps * 1.1,
                                          "note": "justified P/B %.2f = (ROE %.1f%% - g) / (CoE %.1f%% - g); +/-10%% band"
                                          % (jpb, roe.value, coe * 100)}
            vr.assumptions.append(Assumption("cost_of_equity", round(coe, 4), "rf + beta x ERP"))
        else:
            vr.skipped.append(("justified P/B", "cost of equity assumptions not set or ROE missing"))
    else:
        mc = own["market_cap"].value
        res, why = dcf(fa, shares, mc, beta, cfg, vr.assumptions) if shares and shares.value else (None, "shares outstanding missing")
        if res:
            vr.dcf = res
            grid = list(res["sensitivity"].values())
            vr.implied["dcf"] = {"low": min(grid), "mid": res["per_share"], "high": max(grid),
                                 "note": "WACC %.2f%%, g %.2f%%; range = WACC +/-1pp x g +/-1pp" % (res["wacc"] * 100, res["terminal_growth"] * 100)}
        else:
            vr.skipped.append(("dcf", why))
    if vr.implied:
        # median across methods, so one outlier method cannot stretch the range
        vals = list(vr.implied.values())
        vr.fair_value = {"low": median([v["low"] for v in vals]), "mid": median([v["mid"] for v in vals]),
                         "high": median([v["high"] for v in vals]), "methods": sorted(vr.implied.keys()),
                         "method_spread": (min(v["mid"] for v in vals), max(v["mid"] for v in vals))}
        if vr.price is not None:
            fv = vr.fair_value
            vr.position = "below_range" if vr.price < fv["low"] else "above_range" if vr.price > fv["high"] else "within_range"
    return vr
