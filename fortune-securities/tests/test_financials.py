"""Financial calculations checked against hand-computed values."""

import unittest

from helpers import fact

from fortune_research.analysis import financials as F
from fortune_research.analysis.calc import cagr, derive, median, percentile


def year(pe, rev, opex, oi, dep, fin, pbt, tax, pat, eq_cap, oeq, bnc, bc, cash, rec, inv, pay, cfo, capex, shares=None, eps=None):
    rows = dict(revenue=rev, operating_expenses=opex, other_income=oi, depreciation=dep, finance_costs=fin, pbt=pbt,
                tax_expense=tax, pat=pat, equity_share_capital=eq_cap, other_equity=oeq, borrowings_noncurrent=bnc,
                borrowings_current=bc, cash_and_equivalents=cash, trade_receivables=rec, inventories=inv, trade_payables=pay,
                cfo=cfo, capex=capex)
    if shares:
        rows["shares_outstanding"] = shares
    if eps is not None:
        rows["eps_diluted"] = eps
    return [fact(k, v, pe) for k, v in rows.items()]


FY25 = year("2025-03-31", 1000, 820, 10, 30, 20, 140, 35, 105, 50, 450, 200, 50, 30, 150, 100, 80, 120, -60, 50_000_000, 21.0)
FY26 = year("2026-03-31", 1200, 960, 12, 36, 22, 194, 49, 145, 50, 550, 180, 40, 60, 200, 110, 90, 150, 70, 50_000_000, 29.0)


class Calc(unittest.TestCase):
    def test_cagr(self):
        self.assertAlmostEqual(cagr(100, 121, 2), 0.10, places=10)
        self.assertIsNone(cagr(-5, 10, 2))  # not meaningful across a sign change
        with self.assertRaises(ZeroDivisionError):
            cagr(1, 2, 0)

    def test_median_percentile(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([4, 1, 2, 3]), 2.5)
        self.assertIsNone(median([None]))
        self.assertAlmostEqual(percentile([10, 20, 30, 40], 25), 17.5)
        self.assertEqual(percentile([7], 75), 7)

    def test_missing_input_gives_none_and_names_it(self):
        m = derive("x", "FY26", "%", "a / b", {"a": fact("a", 1, "2026-03-31"), "b": None}, lambda a, b: a / b)
        self.assertIsNone(m.value)
        self.assertEqual(m.missing, ["b"])

    def test_zero_denominator(self):
        m = derive("x", "FY26", "x", "a / b", {"a": fact("a", 1, "2026-03-31"), "b": fact("b", 0, "2026-03-31")}, lambda a, b: a / b)
        self.assertIsNone(m.value)
        self.assertIn("zero", m.note)


class Annual(unittest.TestCase):
    def setUp(self):
        self.fa = F.analyse(FY25 + FY26)
        self.y = self.fa.annual["FY26"]

    def test_labels(self):
        self.assertEqual(self.fa.latest_fy, "FY26")
        self.assertEqual(list(self.fa.annual), ["FY25", "FY26"])

    def test_pl(self):
        self.assertEqual(self.y["ebitda"].value, 240)                     # 1200 - 960
        self.assertAlmostEqual(self.y["ebitda_margin"].value, 20.0)
        self.assertEqual(self.y["ebit"].value, 216)                       # 194 + 22
        self.assertAlmostEqual(self.y["revenue_growth"].value, 20.0)
        self.assertAlmostEqual(self.y["pat_growth"].value, (145 / 105 - 1) * 100)
        self.assertAlmostEqual(self.y["effective_tax_rate"].value, 49 / 194 * 100)
        self.assertAlmostEqual(self.y["eps_computed"].value, 145e7 / 50e6)  # 29.0
        self.assertEqual(self.y["eps"].value, 29.0)                         # reported preferred

    def test_returns_use_average_balances(self):
        # equity 500 -> 600, avg 550; debt 250 -> 220
        self.assertAlmostEqual(self.y["roe"].value, 145 / 550 * 100)
        self.assertAlmostEqual(self.y["roce"].value, 216 / ((600 + 220 + 500 + 250) / 2) * 100)
        # first year: closing balances, and it says so
        self.assertIn("closing", self.fa.annual["FY25"]["roe"].note)

    def test_leverage_and_cash(self):
        self.assertAlmostEqual(self.y["debt_to_equity"].value, 220 / 600)
        self.assertEqual(self.y["net_debt"].value, 160)
        self.assertAlmostEqual(self.y["interest_coverage"].value, 216 / 22)
        self.assertEqual(self.y["capex"].value, -70)  # positive input normalised to an outflow
        self.assertEqual(self.y["fcf"].value, 80)
        self.assertAlmostEqual(self.y["cfo_to_pat"].value, 150 / 145)

    def test_working_capital(self):
        self.assertAlmostEqual(self.y["receivable_days"].value, 200 / 1200 * 365)
        self.assertAlmostEqual(self.y["inventory_days"].value, 110 / 1200 * 365)  # no COGS -> on revenue
        self.assertIn("COGS not given", self.y["inventory_days"].note)
        self.assertAlmostEqual(self.y["cash_conversion_cycle"].value, (200 + 110 - 90) / 1200 * 365)

    def test_metrics_carry_sources(self):
        self.assertEqual(len(self.y["roe"].source_ids), 5)  # pat + 2x(capital, other equity)
        self.assertTrue(all(s.startswith("S") for s in self.y["roce"].source_ids))

    def test_missing_items_stay_missing(self):
        self.assertIsNone(self.y["current_ratio"].value)
        self.assertEqual(self.y["current_ratio"].missing, ["ca", "cl"])

    def test_ebitda_fallback_when_opex_absent(self):
        facts = [f for f in FY26 if f.name != "operating_expenses"]
        y = F.analyse(facts).annual["FY26"]
        self.assertEqual(y["ebitda"].value, 194 + 22 + 36 - 12)
        self.assertIn("pbt + finance_costs", y["ebitda"].formula)

    def test_negative_pbt_tax_rate_not_meaningful(self):
        facts = [f for f in FY26 if f.name not in ("pbt", "tax_expense")] + [fact("pbt", -10, "2026-03-31"), fact("tax_expense", 1, "2026-03-31")]
        y = F.analyse(facts).annual["FY26"]
        self.assertIsNone(y["effective_tax_rate"].value)

    def test_standalone_used_only_when_no_consolidated(self):
        sa = [fact(f.name, f.value, f.period_end, basis="standalone") for f in FY26]
        self.assertEqual(F.analyse(sa).basis, "standalone")
        mixed = F.analyse(FY26 + [fact("revenue", 999, "2026-03-31", basis="standalone")])
        self.assertEqual(mixed.basis, "consolidated")
        self.assertEqual(mixed.annual["FY26"]["revenue"].value, 1200)
        self.assertTrue(mixed.notes)


class Quarterly(unittest.TestCase):
    def q(self, pe, rev, pat, eps=None):
        out = [fact("revenue", rev, pe, "Q"), fact("pat", pat, pe, "Q"), fact("operating_expenses", rev * 0.8, pe, "Q")]
        if eps is not None:
            out.append(fact("eps_diluted", eps, pe, "Q"))
        return out

    def test_yoy_qoq_and_ttm(self):
        facts = []
        for pe, rev, pat in (("2025-06-30", 100, 10), ("2025-09-30", 110, 11), ("2025-12-31", 120, 12), ("2026-03-31", 130, 13),
                             ("2026-06-30", 125, 9)):
            facts += self.q(pe, rev, pat, pat / 10)
        fa = F.analyse(facts)
        self.assertEqual(fa.latest_q, "Q1FY27")
        last = fa.quarterly["Q1FY27"]
        self.assertAlmostEqual(last["revenue_yoy"].value, 25.0)
        self.assertAlmostEqual(last["pat_yoy"].value, -10.0)
        self.assertAlmostEqual(last["revenue_qoq"].value, (125 / 130 - 1) * 100)
        self.assertEqual(fa.ttm["revenue"].value, 110 + 120 + 130 + 125)
        self.assertAlmostEqual(fa.ttm["eps"].value, 1.1 + 1.2 + 1.3 + 0.9)
        self.assertIn("Q1FY27", fa.ttm["revenue"].period)

    def test_ttm_falls_back_to_fy_when_quarters_have_a_gap(self):
        facts = FY26
        for pe in ("2025-06-30", "2025-12-31", "2026-03-31", "2026-06-30"):  # Sep quarter missing
            facts = facts + self.q(pe, 100, 10)
        fa = F.analyse(facts)
        self.assertEqual(fa.ttm["revenue"].value, 1200)
        self.assertIn("latest FY", fa.ttm["revenue"].period)


class Growth(unittest.TestCase):
    def test_three_year_cagr(self):
        facts = []
        for y, rev, pat in ((2023, 1000, 100), (2024, 1100, 110), (2025, 1210, 121), (2026, 1331, 133.1)):
            facts += [fact("revenue", rev, "%d-03-31" % y), fact("pat", pat, "%d-03-31" % y)]
        fa = F.analyse(facts)
        self.assertAlmostEqual(fa.growth["revenue_cagr_3y"].value, 10.0, places=6)
        self.assertEqual(fa.growth["revenue_cagr_3y"].period, "FY23-FY26")
        self.assertNotIn("revenue_cagr_5y", fa.growth)


if __name__ == "__main__":
    unittest.main()
