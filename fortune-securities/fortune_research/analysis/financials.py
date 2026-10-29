"""Financial analyst: growth, margins, EPS, ROE, ROCE, leverage, cash flow and
working capital from Ind AS statement facts (amounts in INR crore).

Canonical line items (financials.csv `line_item`), see docs/DATA_FORMATS.md:
  P&L       revenue, other_income, operating_expenses, cost_of_goods_sold, depreciation,
            finance_costs, pbt, tax_expense, pat, pat_attributable, eps_diluted
  Balance   equity_share_capital, other_equity, total_equity, borrowings_noncurrent,
            borrowings_current, lease_liabilities, cash_and_equivalents, current_investments,
            trade_receivables, inventories, trade_payables, current_assets, current_liabilities,
            total_assets, total_liabilities, contingent_liabilities
  Cash flow cfo, capex (purchase of PPE; outflow), dividends_paid
  Other     shares_outstanding (shares, at period end)

Conventions (stated in reports):
  EBITDA = revenue - operating_expenses; if operating_expenses is absent,
           PBT + finance costs + depreciation - other income.
  EBIT   = PBT + finance costs (includes other income).
  ROE    = PAT / average total equity (closing equity when no prior year).
  ROCE   = EBIT / average (total equity + total debt).
  Debt   = borrowings (non-current + current) + lease liabilities when given.
  FCF    = CFO - |capex|.
  Days   = closing balance / annual flow x 365 (inventory and payables on COGS
           when given, else on revenue, which is labelled).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from ..models import Fact, Metric, fy_label
from .calc import cagr, derive, given

CR_TO_RUPEES = 1e7


class Statements:
    """Facts indexed by (name, period_type, period_end) for one basis."""

    def __init__(self, facts: list, prefer: str = "consolidated"):
        bases = {f.basis for f in facts if f.period_type == "FY"}
        self.basis = prefer if prefer in bases else (sorted(bases)[0] if bases else prefer)
        self.idx: dict = {}
        for f in facts:
            if f.basis in (self.basis, "n/a"):
                self.idx[(f.name, f.period_type, f.period_end)] = f
        self.all_bases = sorted({f.basis for f in facts})

    def get(self, name: str, ptype: str, pe: dt.date) -> Optional[Fact]:
        return self.idx.get((name, ptype, pe))

    def periods(self, ptype: str) -> list:
        return sorted({k[2] for k in self.idx if k[1] == ptype})

    def facts(self) -> list:
        return list(self.idx.values())


@dataclass
class FinancialAnalysis:
    basis: str
    annual: dict = field(default_factory=dict)  # label -> {name: Metric}
    quarterly: dict = field(default_factory=dict)
    ttm: dict = field(default_factory=dict)
    growth: dict = field(default_factory=dict)
    fy_periods: list = field(default_factory=list)
    q_periods: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def latest_fy(self) -> Optional[str]:
        return fy_label(self.fy_periods[-1], "FY") if self.fy_periods else None

    @property
    def latest_q(self) -> Optional[str]:
        return fy_label(self.q_periods[-1], "Q") if self.q_periods else None

    def fy(self, name: str, offset: int = 0) -> Optional[Metric]:
        """Metric for the latest FY (offset=0), previous (1), ..."""
        if len(self.fy_periods) <= offset:
            return None
        return self.annual[fy_label(self.fy_periods[-1 - offset], "FY")].get(name)

    def q(self, name: str, offset: int = 0) -> Optional[Metric]:
        if len(self.q_periods) <= offset:
            return None
        return self.quarterly[fy_label(self.q_periods[-1 - offset], "Q")].get(name)

    def flat(self) -> dict:
        """name -> Metric for the headline values (latest FY, latest quarter, TTM, growth)."""
        out = {}
        if self.fy_periods:
            for k, m in self.annual[self.latest_fy].items():
                out["fy." + k] = m
        if self.q_periods:
            for k, m in self.quarterly[self.latest_q].items():
                out["q." + k] = m
        for k, m in self.ttm.items():
            out["ttm." + k] = m
        for k, m in self.growth.items():
            out["growth." + k] = m
        return out


def _prev_year(pe: dt.date) -> dt.date:
    try:
        return pe.replace(year=pe.year - 1)
    except ValueError:  # 29 Feb
        return pe.replace(year=pe.year - 1, day=28)


def _sum_metric(name, period, unit, parts: dict) -> Metric:
    return derive(name, period, unit, " + ".join(parts.keys()), parts, lambda **kw: sum(kw.values()))


def _ebitda(st: Statements, pt: str, pe: dt.date, label: str) -> Metric:
    rev, opex = st.get("revenue", pt, pe), st.get("operating_expenses", pt, pe)
    if opex is not None:
        return derive("ebitda", label, "INR crore", "revenue - operating_expenses",
                      {"revenue": rev, "operating_expenses": opex}, lambda revenue, operating_expenses: revenue - operating_expenses)
    return derive("ebitda", label, "INR crore", "pbt + finance_costs + depreciation - other_income",
                  {"pbt": st.get("pbt", pt, pe), "finance_costs": st.get("finance_costs", pt, pe),
                   "depreciation": st.get("depreciation", pt, pe), "other_income": st.get("other_income", pt, pe)},
                  lambda pbt, finance_costs, depreciation, other_income: pbt + finance_costs + depreciation - other_income)


def _pl_metrics(st: Statements, pt: str, pe: dt.date, label: str) -> dict:
    g = lambda n: st.get(n, pt, pe)  # noqa: E731
    out = {}
    for n in ("revenue", "other_income", "pbt", "tax_expense", "pat", "finance_costs", "depreciation"):
        f = g(n)
        out[n] = given(n, label, f.value if f else None, "INR crore", "reported", [f.source.id] if f else [])
    pat_for_eps = g("pat_attributable") or g("pat")
    out["ebitda"] = _ebitda(st, pt, pe, label)
    out["ebitda_margin"] = derive("ebitda_margin", label, "%", "ebitda / revenue x 100",
                                  {"ebitda": out["ebitda"], "revenue": g("revenue")},
                                  lambda ebitda, revenue: ebitda / revenue * 100)
    out["ebit"] = derive("ebit", label, "INR crore", "pbt + finance_costs",
                         {"pbt": g("pbt"), "finance_costs": g("finance_costs")}, lambda pbt, finance_costs: pbt + finance_costs)
    out["pat_margin"] = derive("pat_margin", label, "%", "pat / revenue x 100", {"pat": g("pat"), "revenue": g("revenue")},
                               lambda pat, revenue: pat / revenue * 100)
    out["effective_tax_rate"] = derive("effective_tax_rate", label, "%", "tax_expense / pbt x 100",
                                       {"tax_expense": g("tax_expense"), "pbt": g("pbt")},
                                       lambda tax_expense, pbt: tax_expense / pbt * 100 if pbt > 0 else None)
    out["other_income_share_of_pbt"] = derive("other_income_share_of_pbt", label, "%", "other_income / pbt x 100",
                                              {"other_income": g("other_income"), "pbt": g("pbt")},
                                              lambda other_income, pbt: other_income / pbt * 100 if pbt > 0 else None)
    eps = g("eps_diluted")
    out["eps_reported"] = given("eps_reported", label, eps.value if eps else None, "INR per share",
                                "reported diluted EPS", [eps.source.id] if eps else [])
    out["eps_computed"] = derive("eps_computed", label, "INR per share", "pat (attributable) x 1e7 / shares_outstanding",
                                 {"pat": pat_for_eps, "shares_outstanding": g("shares_outstanding")},
                                 lambda pat, shares_outstanding: pat * CR_TO_RUPEES / shares_outstanding)
    out["eps"] = out["eps_reported"] if out["eps_reported"].available else out["eps_computed"]
    return out


def _balance_metrics(st: Statements, pe: dt.date, prev: Optional[dt.date], label: str, pl: dict) -> dict:
    g = lambda n, d=pe: st.get(n, "FY", d) if d else None  # noqa: E731
    out = {}

    def equity_at(d):
        if d is None:
            return None
        te = g("total_equity", d)
        if te is not None:
            return given("total_equity", label, te.value, "INR crore", "reported", [te.source.id])
        return _sum_metric("total_equity", label, "INR crore",
                           {"equity_share_capital": g("equity_share_capital", d), "other_equity": g("other_equity", d)})

    def debt_at(d):
        if d is None:
            return None
        parts = {"borrowings_noncurrent": g("borrowings_noncurrent", d), "borrowings_current": g("borrowings_current", d)}
        if g("lease_liabilities", d) is not None:
            parts["lease_liabilities"] = g("lease_liabilities", d)
        return _sum_metric("total_debt", label, "INR crore", parts)

    eq, eq0 = equity_at(pe), equity_at(prev)
    debt, debt0 = debt_at(pe), debt_at(prev)
    out["total_equity"], out["total_debt"] = eq, debt
    have_prev = eq0 is not None and eq0.available
    avg_note = "" if have_prev else "closing balance (no prior year)"
    avg_eq = derive("avg_equity", label, "INR crore", "(equity_t + equity_t-1) / 2" if have_prev else "equity_t",
                    {"e1": eq, "e0": eq0} if have_prev else {"e1": eq},
                    (lambda e1, e0: (e1 + e0) / 2) if have_prev else (lambda e1: e1), avg_note)
    out["roe"] = derive("roe", label, "%", "pat / avg_equity x 100", {"pat": g("pat_attributable") or g("pat"), "avg_equity": avg_eq},
                        lambda pat, avg_equity: pat / avg_equity * 100 if avg_equity > 0 else None, avg_note)
    ce = derive("capital_employed", label, "INR crore", "total_equity + total_debt", {"eq": eq, "debt": debt},
                lambda eq, debt: eq + debt)
    have_prev_ce = have_prev and debt0 is not None and debt0.available
    if have_prev_ce:
        ce0 = derive("capital_employed_prev", label, "INR crore", "total_equity + total_debt", {"eq": eq0, "debt": debt0},
                     lambda eq, debt: eq + debt)
        avg_ce = derive("avg_capital_employed", label, "INR crore", "(ce_t + ce_t-1) / 2", {"c1": ce, "c0": ce0},
                        lambda c1, c0: (c1 + c0) / 2)
    else:
        avg_ce = ce
    out["capital_employed"] = ce
    out["roce"] = derive("roce", label, "%", "ebit / avg_capital_employed x 100", {"ebit": pl["ebit"], "ce": avg_ce},
                         lambda ebit, ce: ebit / ce * 100 if ce > 0 else None,
                         "" if have_prev_ce else "closing capital employed (no prior year)")
    out["debt_to_equity"] = derive("debt_to_equity", label, "x", "total_debt / total_equity", {"debt": debt, "eq": eq},
                                   lambda debt, eq: debt / eq if eq > 0 else None)
    cash_parts = {"cash_and_equivalents": g("cash_and_equivalents")}
    if g("current_investments") is not None:
        cash_parts["current_investments"] = g("current_investments")
    cash = _sum_metric("cash_and_liquid_investments", label, "INR crore", cash_parts)
    out["cash"] = cash
    out["net_debt"] = derive("net_debt", label, "INR crore", "total_debt - cash_and_liquid_investments",
                             {"debt": debt, "cash": cash}, lambda debt, cash: debt - cash)
    out["interest_coverage"] = derive("interest_coverage", label, "x", "ebit / finance_costs",
                                      {"ebit": pl["ebit"], "finance_costs": g("finance_costs")},
                                      lambda ebit, finance_costs: ebit / finance_costs)
    out["current_ratio"] = derive("current_ratio", label, "x", "current_assets / current_liabilities",
                                  {"ca": g("current_assets"), "cl": g("current_liabilities")}, lambda ca, cl: ca / cl)
    # cash flow
    cfo, capex = g("cfo"), g("capex")
    out["cfo"] = given("cfo", label, cfo.value if cfo else None, "INR crore", "reported", [cfo.source.id] if cfo else [])
    out["capex"] = given("capex", label, -abs(capex.value) if capex and capex.value is not None else None, "INR crore",
                         "reported (outflow, negative)", [capex.source.id] if capex else [])
    out["fcf"] = derive("fcf", label, "INR crore", "cfo - |capex|", {"cfo": cfo, "capex": capex},
                        lambda cfo, capex: cfo - abs(capex))
    out["cfo_to_pat"] = derive("cfo_to_pat", label, "x", "cfo / pat", {"cfo": cfo, "pat": g("pat")},
                               lambda cfo, pat: cfo / pat if pat > 0 else None)
    out["fcf_margin"] = derive("fcf_margin", label, "%", "fcf / revenue x 100", {"fcf": out["fcf"], "revenue": g("revenue")},
                               lambda fcf, revenue: fcf / revenue * 100)
    div = g("dividends_paid")
    out["dividend_payout"] = derive("dividend_payout", label, "%", "|dividends_paid| / pat x 100",
                                    {"div": div, "pat": g("pat")}, lambda div, pat: abs(div) / pat * 100 if pat > 0 else None)
    # working capital
    cogs = g("cost_of_goods_sold")
    base, base_name = (cogs, "cost_of_goods_sold") if cogs is not None else (g("revenue"), "revenue")
    base_note = "" if cogs is not None else "on revenue (COGS not given)"
    out["receivable_days"] = derive("receivable_days", label, "days", "trade_receivables / revenue x 365",
                                    {"rec": g("trade_receivables"), "rev": g("revenue")}, lambda rec, rev: rec / rev * 365)
    out["inventory_days"] = derive("inventory_days", label, "days", "inventories / %s x 365" % base_name,
                                   {"inv": g("inventories"), "base": base}, lambda inv, base: inv / base * 365, base_note)
    out["payable_days"] = derive("payable_days", label, "days", "trade_payables / %s x 365" % base_name,
                                 {"pay": g("trade_payables"), "base": base}, lambda pay, base: pay / base * 365, base_note)
    out["cash_conversion_cycle"] = derive("cash_conversion_cycle", label, "days",
                                          "receivable_days + inventory_days - payable_days",
                                          {"r": out["receivable_days"], "i": out["inventory_days"], "p": out["payable_days"]},
                                          lambda r, i, p: r + i - p, base_note)
    out["net_working_capital"] = derive("net_working_capital", label, "INR crore",
                                        "trade_receivables + inventories - trade_payables",
                                        {"r": g("trade_receivables"), "i": g("inventories"), "p": g("trade_payables")},
                                        lambda r, i, p: r + i - p)
    cl = g("contingent_liabilities")
    out["contingent_liabilities_to_equity"] = derive("contingent_liabilities_to_equity", label, "%",
                                                     "contingent_liabilities / total_equity x 100",
                                                     {"cl": cl, "eq": eq}, lambda cl, eq: cl / eq * 100 if eq > 0 else None)
    return out


def _growth(cur: Metric, prev: Optional[Metric], name: str, label: str, basis: str) -> Metric:
    return derive(name, label, "%", "(x_t / x_%s - 1) x 100" % basis, {"cur": cur, "prev": prev},
                  lambda cur, prev: (cur / prev - 1) * 100 if prev > 0 else None,
                  "" if prev is not None else "no comparable prior period")


def analyse(facts: list, prefer_basis: str = "consolidated") -> FinancialAnalysis:
    st = Statements(facts, prefer_basis)
    fa = FinancialAnalysis(basis=st.basis)
    if len(st.all_bases) > 1:
        fa.notes.append("statements available on bases %s; using %s" % (", ".join(st.all_bases), st.basis))
    # annual
    fa.fy_periods = [p for p in st.periods("FY") if st.get("revenue", "FY", p) is not None]
    for i, pe in enumerate(fa.fy_periods):
        label = fy_label(pe, "FY")
        prev = _prev_year(pe)
        prev = prev if prev in fa.fy_periods else None
        pl = _pl_metrics(st, "FY", pe, label)
        bs = _balance_metrics(st, pe, prev, label, pl)
        row = {**pl, **bs}
        if prev is not None:
            pl0 = fa.annual[fy_label(prev, "FY")]
            for n in ("revenue", "ebitda", "pat", "eps"):
                row[n + "_growth"] = _growth(row[n], pl0[n], n + "_growth", label, "t-1")
        else:
            for n in ("revenue", "ebitda", "pat", "eps"):
                row[n + "_growth"] = _growth(row[n], None, n + "_growth", label, "t-1")
        fa.annual[label] = row
    # CAGRs over 3 and 5 years where the endpoints exist
    if fa.fy_periods:
        last = fa.fy_periods[-1]
        for yrs in (3, 5):
            start = last.replace(year=last.year - yrs)
            if start in fa.fy_periods:
                a, b = fa.annual[fy_label(start, "FY")], fa.annual[fy_label(last, "FY")]
                for n in ("revenue", "pat", "eps"):
                    fa.growth["%s_cagr_%dy" % (n, yrs)] = derive(
                        "%s_cagr_%dy" % (n, yrs), "%s-%s" % (fy_label(start, "FY"), fy_label(last, "FY")), "%",
                        "((x_end / x_start)^(1/%d) - 1) x 100" % yrs, {"start": a[n], "end": b[n]},
                        lambda start, end, y=yrs: (lambda c: c * 100 if c is not None else None)(cagr(start, end, y)))
    # quarterly
    fa.q_periods = [p for p in st.periods("Q") if st.get("revenue", "Q", p) is not None]
    for pe in fa.q_periods:
        label = fy_label(pe, "Q")
        row = _pl_metrics(st, "Q", pe, label)
        ly = _prev_year(pe)
        prior = fa.quarterly.get(fy_label(ly, "Q")) if ly in fa.q_periods else None
        idx = fa.q_periods.index(pe)
        qprev = fa.quarterly.get(fy_label(fa.q_periods[idx - 1], "Q")) if idx > 0 else None
        for n in ("revenue", "ebitda", "pat", "eps"):
            row[n + "_yoy"] = _growth(row[n], prior[n] if prior else None, n + "_yoy", label, "same quarter last year")
            row[n + "_qoq"] = _growth(row[n], qprev[n] if qprev else None, n + "_qoq", label, "previous quarter")
        fa.quarterly[label] = row
    # TTM: the last four consecutive quarters, else the latest FY
    fa.ttm = _ttm(st, fa)
    return fa


def _consecutive(qs: list) -> bool:
    for a, b in zip(qs, qs[1:]):
        if not (85 <= (b - a).days <= 95):
            return False
    return True


def _ttm(st: Statements, fa: FinancialAnalysis) -> dict:
    out = {}
    qs = fa.q_periods[-4:]
    use_q = len(qs) == 4 and _consecutive(qs) and (not fa.fy_periods or qs[-1] > fa.fy_periods[-1])
    if use_q:
        label = "TTM to %s" % fy_label(qs[-1], "Q")
        for n in ("revenue", "ebitda", "pat", "eps"):
            parts = {fy_label(q, "Q"): fa.quarterly[fy_label(q, "Q")][n] for q in qs}
            out[n] = derive(n, label, "INR per share" if n == "eps" else "INR crore", "sum of last 4 quarters",
                            parts, lambda **kw: sum(kw.values()),
                            "sum of quarterly EPS (approximate)" if n == "eps" else "")
    elif fa.fy_periods:
        fy = fa.annual[fa.latest_fy]
        for n in ("revenue", "ebitda", "pat", "eps"):
            m = fy[n]
            out[n] = Metric(n, m.value, m.unit, "%s (latest FY; quarters unavailable)" % fa.latest_fy, m.formula,
                            m.source_ids, m.missing, "latest full year used as TTM")
    if out.get("revenue") and out.get("ebitda"):
        out["ebitda_margin"] = derive("ebitda_margin", out["revenue"].period, "%", "ebitda / revenue x 100",
                                      {"e": out["ebitda"], "r": out["revenue"]}, lambda e, r: e / r * 100)
    return out
