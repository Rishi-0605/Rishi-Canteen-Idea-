"""Data validation, reconciliation and staleness."""

import datetime as dt
import unittest

from helpers import fact

from fortune_research.analysis import quality
from fortune_research.models import PriceBar, PriceSeries
from fortune_research.units import UnitError, normalise
from helpers import src


def codes(issues):
    return sorted(i.code for i in issues)


class Units(unittest.TestCase):
    def test_amounts_to_crore(self):
        self.assertEqual(normalise(250, "INR lakh"), (2.5, "INR crore"))
        self.assertEqual(normalise(1500, "INR million"), (150.0, "INR crore"))
        self.assertEqual(normalise(3, "INR billion"), (300.0, "INR crore"))
        self.assertAlmostEqual(normalise(12_345_678, "INR")[0], 1.2345678)
        self.assertEqual(normalise(2, "crore shares"), (2e7, "shares"))
        self.assertEqual(normalise(23.3, "INR per share"), (23.3, "INR per share"))

    def test_unknown_unit_is_rejected(self):
        with self.assertRaises(UnitError):
            normalise(1, "USD million")


class Reconcile(unittest.TestCase):
    PE = "2026-03-31"

    def base(self):
        return [fact("revenue", 1000, self.PE), fact("other_income", 10, self.PE), fact("operating_expenses", 800, self.PE),
                fact("depreciation", 30, self.PE), fact("finance_costs", 20, self.PE), fact("pbt", 160, self.PE),
                fact("tax_expense", 40, self.PE), fact("pat", 120, self.PE), fact("total_assets", 900, self.PE),
                fact("total_equity", 600, self.PE), fact("total_liabilities", 300, self.PE),
                fact("eps_diluted", 12.0, self.PE), fact("shares_outstanding", 100_000_000, self.PE)]

    def test_clean_statements_pass(self):
        self.assertEqual(quality.check_facts(self.base(), "consolidated"), [])

    def test_pl_mismatch(self):
        f = [x for x in self.base() if x.name != "pat"] + [fact("pat", 100, self.PE)]
        self.assertIn("pl_reconcile", codes(quality.check_facts(f, "consolidated")))

    def test_pbt_mismatch(self):
        f = [x for x in self.base() if x.name != "operating_expenses"] + [fact("operating_expenses", 700, self.PE)]
        self.assertIn("pbt_reconcile", codes(quality.check_facts(f, "consolidated")))

    def test_balance_sheet_mismatch_is_an_error(self):
        f = [x for x in self.base() if x.name != "total_assets"] + [fact("total_assets", 950, self.PE)]
        issues = quality.check_facts(f, "consolidated")
        self.assertEqual([i.severity for i in issues if i.code == "bs_reconcile"], ["error"])

    def test_eps_unit_error_detected(self):
        # PAT 120 cr / 10 cr shares = 12; a reported 120 suggests a units mistake
        f = [x for x in self.base() if x.name != "eps_diluted"] + [fact("eps_diluted", 120.0, self.PE)]
        self.assertIn("eps_reconcile", codes(quality.check_facts(f, "consolidated")))

    def test_quarters_must_sum_to_year(self):
        f = [fact("revenue", 1000, self.PE)] + [fact("revenue", v, pe, "Q") for v, pe in
                                                ((240, "2025-06-30"), (250, "2025-09-30"), (250, "2025-12-31"), (200, "2026-03-31"))]
        self.assertIn("quarter_sum", codes(quality.check_facts(f, "consolidated")))
        f[-1] = fact("revenue", 260, "2026-03-31", "Q")
        self.assertNotIn("quarter_sum", codes(quality.check_facts(f, "consolidated")))

    def test_conflicting_duplicates_and_bad_units(self):
        f = self.base() + [fact("revenue", 1001, self.PE), fact("cfo", 5, self.PE, unit="INR per share"),
                           fact("trade_receivables", -3, self.PE)]
        c = codes(quality.check_facts(f, "consolidated"))
        self.assertIn("duplicate_conflict", c)
        self.assertIn("unit_mismatch", c)
        self.assertIn("negative_value", c)


class Staleness(unittest.TestCase):
    def test_stale_missing_and_future(self):
        as_of = dt.date(2026, 10, 29)
        issues, ages = quality.staleness(as_of, {"prices": 5, "quarterly_results": 140},
                                         {"prices": dt.date(2026, 10, 20), "quarterly_results": dt.date(2026, 6, 30),
                                          "shareholding": None, "annual_results": dt.date(2026, 11, 1)})
        self.assertEqual(ages["prices"], 9)
        by = {i.dataset: i.code for i in issues}
        self.assertEqual(by, {"prices": "stale", "shareholding": "missing", "annual_results": "future_date"})

    def test_price_checks(self):
        bars = [PriceBar(dt.date(2026, 1, d), 100, 101, 99, 100, 1) for d in (1, 2)] + [PriceBar(dt.date(2026, 1, 20), 50, 51, 49, 50, 1)]
        s = PriceSeries(bars, src("p", official=False), adjusted=None)
        c = codes(quality.check_prices(s))
        self.assertEqual(c, ["adjustment_unknown", "price_gap", "price_jump", "unofficial_prices"])


if __name__ == "__main__":
    unittest.main()
