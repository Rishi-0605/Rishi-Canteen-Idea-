"""Data validation, reconciliation and staleness checks.

Nothing here changes data. It reports DataIssue rows that the report prints in
its data-quality section, and errors lower the confidence stated in the report.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Optional

from ..models import DataIssue, fy_label

AMOUNT_ITEMS = {"revenue", "other_income", "operating_expenses", "cost_of_goods_sold", "depreciation", "finance_costs",
                "pbt", "tax_expense", "pat", "pat_attributable", "equity_share_capital", "other_equity", "total_equity",
                "borrowings_noncurrent", "borrowings_current", "lease_liabilities", "cash_and_equivalents",
                "current_investments", "trade_receivables", "inventories", "trade_payables", "current_assets",
                "current_liabilities", "total_assets", "total_liabilities", "contingent_liabilities", "cfo", "capex",
                "dividends_paid", "ebitda"}
NON_NEGATIVE = {"revenue", "trade_receivables", "inventories", "trade_payables", "cash_and_equivalents", "total_assets",
                "shares_outstanding", "borrowings_noncurrent", "borrowings_current", "depreciation", "finance_costs"}
EXPECTED_UNIT = {"eps_diluted": "INR per share", "shares_outstanding": "shares"}


def _close(a: float, b: float, rel: float, abs_tol: float) -> bool:
    return abs(a - b) <= max(abs_tol, rel * max(abs(a), abs(b)))


def check_facts(facts: list, basis: str) -> list:
    issues = []
    seen = {}
    for f in facts:
        key = (f.name, f.period_type, f.period_end, f.basis)
        if key in seen and seen[key].value != f.value:
            issues.append(DataIssue("error", "duplicate_conflict",
                                    "%s %s %s given twice with different values (%s vs %s)"
                                    % (f.name, f.period_label, f.basis, seen[key].value, f.value), "financials"))
        seen[key] = f
        want = "INR crore" if f.name in AMOUNT_ITEMS else EXPECTED_UNIT.get(f.name)
        if want and f.unit != want:
            issues.append(DataIssue("error", "unit_mismatch", "%s %s has unit %s, expected %s"
                                    % (f.name, f.period_label, f.unit, want), "financials"))
        if f.name in NON_NEGATIVE and f.value is not None and f.value < 0:
            issues.append(DataIssue("error", "negative_value", "%s %s is negative (%s)" % (f.name, f.period_label, f.value),
                                    "financials"))
    # reconciliation, per basis in use
    idx = {(f.name, f.period_type, f.period_end): f for f in facts if f.basis in (basis, "n/a")}
    periods = sorted({(k[1], k[2]) for k in idx})
    v = lambda n, pt, pe: idx[(n, pt, pe)].value if (n, pt, pe) in idx else None  # noqa: E731
    for pt, pe in periods:
        lab = fy_label(pe, pt)
        pbt, tax, pat = v("pbt", pt, pe), v("tax_expense", pt, pe), v("pat", pt, pe)
        if None not in (pbt, tax, pat) and not _close(pbt - tax, pat, 0.01, 0.5):
            issues.append(DataIssue("warning", "pl_reconcile", "%s: PBT - tax = %.2f but PAT = %.2f (exceptional items, "
                                    "discontinued ops or associates may explain it)" % (lab, pbt - tax, pat), "financials"))
        parts = [v(n, pt, pe) for n in ("revenue", "other_income", "operating_expenses", "depreciation", "finance_costs")]
        if None not in parts and pbt is not None:
            calc = parts[0] + parts[1] - parts[2] - parts[3] - parts[4]
            if not _close(calc, pbt, 0.01, 0.5):
                issues.append(DataIssue("warning", "pbt_reconcile", "%s: revenue + other income - expenses = %.2f but PBT = %.2f "
                                        "(exceptional items?)" % (lab, calc, pbt), "financials"))
        ta, te, tl = v("total_assets", pt, pe), v("total_equity", pt, pe), v("total_liabilities", pt, pe)
        if te is None and v("equity_share_capital", pt, pe) is not None and v("other_equity", pt, pe) is not None:
            te = v("equity_share_capital", pt, pe) + v("other_equity", pt, pe)
        if None not in (ta, te, tl) and not _close(ta, te + tl, 0.005, 0.5):
            issues.append(DataIssue("error", "bs_reconcile", "%s: total assets %.2f != equity %.2f + liabilities %.2f"
                                    % (lab, ta, te, tl), "financials"))
        eps, shares, patx = v("eps_diluted", pt, pe), v("shares_outstanding", pt, pe), v("pat_attributable", pt, pe) or pat
        if None not in (eps, shares, patx) and shares > 0 and eps != 0:
            comp = patx * 1e7 / shares
            if not _close(comp, eps, 0.03, 0.05):
                issues.append(DataIssue("warning", "eps_reconcile", "%s: PAT / shares = %.2f vs reported diluted EPS %.2f "
                                        "(dilution, weighted shares or a unit error)" % (lab, comp, eps), "financials"))
    # four quarters vs the fiscal year
    fys = sorted({pe for pt, pe in periods if pt == "FY"})
    for fy in fys:
        qs = [dt.date(fy.year - 1, 6, 30), dt.date(fy.year - 1, 9, 30), dt.date(fy.year - 1, 12, 31), dt.date(fy.year, 3, 31)]
        for n in ("revenue", "pat"):
            vals = [v(n, "Q", q) for q in qs]
            total = v(n, "FY", fy)
            if None in vals or total is None:
                continue
            if not _close(sum(vals), total, 0.01, 1.0):
                issues.append(DataIssue("warning", "quarter_sum", "%s %s: four quarters sum to %.2f vs annual %.2f"
                                        % (fy_label(fy, "FY"), n, sum(vals), total), "financials"))
    return issues


def _age(as_of: dt.date, d: Optional[dt.date]) -> Optional[int]:
    return (as_of - d).days if d else None


def staleness(as_of: dt.date, limits: dict, latest: dict) -> tuple:
    """latest: dataset -> date of newest data point (or None). Returns (issues, ages)."""
    issues, ages = [], {}
    for ds, d in latest.items():
        age = _age(as_of, d)
        ages[ds] = age
        if d is None:
            issues.append(DataIssue("warning", "missing", "%s: no data available" % ds, ds))
            continue
        if d > as_of:
            issues.append(DataIssue("error", "future_date", "%s: newest data point %s is after the analysis date %s"
                                    % (ds, d, as_of), ds))
            continue
        limit = limits.get(ds)
        if limit is not None and age > limit:
            issues.append(DataIssue("warning", "stale", "%s: newest data is %s (%d days old; limit %d)"
                                    % (ds, d, age, limit), ds))
    return issues, ages


def check_prices(series) -> list:
    issues = []
    if not series or not series.bars:
        return issues
    gaps = defaultdict(int)
    for a, b in zip(series.bars, series.bars[1:]):
        if (b.date - a.date).days > 7:
            gaps["gap"] += 1
            issues.append(DataIssue("warning", "price_gap", "prices: %d-day gap between %s and %s"
                                    % ((b.date - a.date).days, a.date, b.date), "prices"))
        if a.close > 0 and abs(b.close / a.close - 1) > 0.35:
            issues.append(DataIssue("warning", "price_jump", "prices: %.0f%% move on %s; check for an unadjusted split/bonus"
                                    % ((b.close / a.close - 1) * 100, b.date), "prices"))
    if series.adjusted is None:
        issues.append(DataIssue("info", "adjustment_unknown", "prices: unknown whether history is adjusted for "
                                "corporate actions", "prices"))
    if not series.source.official:
        issues.append(DataIssue("info", "unofficial_prices", "prices from %s, not an exchange source"
                                % (series.source.publisher or series.source.provider), "prices"))
    return issues
