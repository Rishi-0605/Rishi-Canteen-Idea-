"""Valuation, forensic, news classification and risk rules."""

import datetime as dt
import unittest

from helpers import fact, src

from fortune_research.analysis import financials as F
from fortune_research.analysis import forensic, news, risk
from fortune_research.analysis import valuation as V
from fortune_research.analysis.calc import given
from fortune_research.models import Announcement, ShareholdingRecord


def company(years=(2023, 2024, 2025, 2026), rev0=1000.0, g=0.12):
    facts = []
    for k, y in enumerate(years):
        pe = "%d-03-31" % y
        rev = rev0 * (1 + g) ** k
        pat = rev * 0.10
        for n, v in dict(revenue=rev, operating_expenses=rev * 0.8, other_income=rev * 0.01, depreciation=rev * 0.03,
                         finance_costs=10, pbt=pat / 0.75, tax_expense=pat / 0.75 * 0.25, pat=pat, equity_share_capital=100,
                         other_equity=rev * 0.5, borrowings_noncurrent=100, borrowings_current=50, cash_and_equivalents=50,
                         cfo=pat * 1.1, capex=-rev * 0.03).items():
            facts.append(fact(n, v, pe))
        facts.append(fact("shares_outstanding", 100_000_000, pe))
    return F.analyse(facts)


SH = given("shares_outstanding", "x", 100_000_000, "shares", "reported", ["S1"])
PX = given("price", "x", 300.0, "INR", "last close", ["S2"])


class Multiples(unittest.TestCase):
    def test_market_multiples(self):
        fa = company()
        m = V.market_multiples(PX, SH, fa)
        self.assertAlmostEqual(m["market_cap"].value, 3000.0)
        self.assertAlmostEqual(m["pe"].value, 300 / fa.ttm["eps"].value)
        eq = fa.fy("total_equity").value
        self.assertAlmostEqual(m["pb"].value, 3000 / eq)
        self.assertAlmostEqual(m["ev"].value, 3000 + 100)  # debt 150 - cash 50
        self.assertAlmostEqual(m["ev_ebitda"].value, 3100 / fa.ttm["ebitda"].value)

    def test_negative_earnings_pe_is_none(self):
        facts = [fact("revenue", 100, "2026-03-31"), fact("pat", -5, "2026-03-31"), fact("eps_diluted", -0.5, "2026-03-31")]
        m = V.market_multiples(PX, SH, F.analyse(facts))
        self.assertIsNone(m["pe"].value)

    def test_no_price_no_multiples(self):
        m = V.market_multiples(None, SH, company())
        self.assertIsNone(m["market_cap"].value)
        self.assertIn("p", m["market_cap"].missing)


class Methods(unittest.TestCase):
    PEERS = [{"symbol": "A", "pe": 20, "pb": 3, "ev_ebitda": 12}, {"symbol": "B", "pe": 25, "pb": 4, "ev_ebitda": 14},
             {"symbol": "C", "pe": 30, "pb": 5, "ev_ebitda": None}]

    def test_peer_comps_and_dcf_skipped_without_assumptions(self):
        fa = company()
        vr = V.analyse(PX, SH, fa, self.PEERS, "Capital Goods", "", 1.0, {"min_peers": 2})
        self.assertEqual(vr.peer_stats["pe"]["median"], 25)
        self.assertEqual(vr.peer_stats["ev_ebitda"]["n"], 2)
        eps = fa.ttm["eps"].value
        self.assertAlmostEqual(vr.implied["peer_pe"]["mid"], 25 * eps)
        self.assertAlmostEqual(vr.implied["peer_pe"]["low"], 22.5 * eps)
        self.assertTrue(any(m == "dcf" and "risk_free_rate" in why for m, why in vr.skipped))
        self.assertNotIn("peer_pb", vr.implied)  # P/B not used for a non-financial

    def test_dcf_runs_with_assumptions_and_grid_brackets_base(self):
        fa = company()
        vr = V.analyse(PX, SH, fa, [], "Capital Goods", "", 1.0, {"risk_free_rate": 0.07, "equity_risk_premium": 0.06,
                                                                  "terminal_growth": 0.05, "forecast_years": 5})
        d = vr.dcf
        self.assertIsNotNone(d)
        self.assertLessEqual(min(d["sensitivity"].values()), d["per_share"])
        self.assertGreaterEqual(max(d["sensitivity"].values()), d["per_share"])
        self.assertEqual(len(d["path"]), 5)
        self.assertAlmostEqual(d["path"][-1]["growth"], 0.05)  # fades to terminal growth
        names = {a.name for a in vr.assumptions}
        self.assertTrue({"risk_free_rate", "wacc", "beta", "fcf_margin"} <= names)
        # higher WACC -> lower value
        keys = sorted(d["sensitivity"], key=lambda k: float(k.split("%")[0]))
        lo_w = [d["sensitivity"][k] for k in keys if k.endswith("|5.0%")]
        self.assertGreater(lo_w[0], lo_w[-1])

    def test_financial_sector_uses_book_methods(self):
        vr = V.analyse(PX, SH, company(), self.PEERS, "Banks", "Private Sector Bank", 1.0,
                       {"risk_free_rate": 0.07, "equity_risk_premium": 0.06, "terminal_growth": 0.05})
        self.assertIsNone(vr.dcf)
        self.assertIn("peer_pb", vr.implied)
        self.assertIn("justified_pb", vr.implied)
        self.assertNotIn("peer_ev_ebitda", vr.implied)

    def test_too_few_peers(self):
        vr = V.analyse(PX, SH, company(), self.PEERS[:1], "Capital Goods", "", 1.0, {"min_peers": 2})
        self.assertEqual(vr.peer_stats, {})
        self.assertIsNone(vr.fair_value)


def sh(q, prom, pledge, s=None):
    return ShareholdingRecord(dt.date.fromisoformat(q), prom, pledge, 10, 10, 100 - prom - 20, s or src("sh" + q))


class Forensic(unittest.TestCase):
    def codes(self, fs):
        return {f.code: f.severity for f in fs}

    def test_pledge_levels_and_trend(self):
        c = self.codes(forensic.shareholding_flags([sh("2026-03-31", 60, 5), sh("2026-06-30", 59, 30)]))
        self.assertEqual(c["promoter_pledge"], "high")
        self.assertEqual(c["pledge_rising"], "medium")
        self.assertNotIn("promoter_pledge", self.codes(forensic.shareholding_flags([sh("2026-06-30", 60, 0)])))

    def test_promoter_selling_and_mps(self):
        c = self.codes(forensic.shareholding_flags([sh("2025-06-30", 62, 0), sh("2026-06-30", 59.5, 0)]))
        self.assertEqual(c["promoter_selling"], "medium")
        self.assertIn("mps_breach", self.codes(forensic.shareholding_flags([sh("2026-06-30", 80, 0)])))

    def test_auditor_and_rpt(self):
        rev = {"FY26": given("revenue", "FY26", 1000, "INR crore", "reported", ["S9"])}
        gov = {"fiscal_years": {"FY26": {"audit_opinion": "qualified", "qualification_text": "inventory not verified",
                                         "auditor_resigned": True, "rpt_total_cr": 250, "caro_adverse_remarks": ["delay in statutory dues"],
                                         "_source": src("ar")}}}
        c = self.codes(forensic.governance_flags(gov, rev))
        self.assertEqual(c["audit_qualified"], "high")
        self.assertEqual(c["auditor_resigned"], "critical")
        self.assertEqual(c["related_party"], "high")  # 25% of revenue
        self.assertEqual(c["caro_remark"], "medium")
        self.assertIn("no_governance", self.codes(forensic.governance_flags(None, rev)))

    def test_findings_cite_their_sources(self):
        s = src("shq")
        f = forensic.shareholding_flags([sh("2026-06-30", 60, 30, s)])
        self.assertIn(s.id, f[0].source_ids)

    def test_weak_cash_conversion(self):
        facts = []
        for y in (2024, 2025, 2026):
            pe = "%d-03-31" % y
            facts += [fact("revenue", 1000, pe), fact("pat", 100, pe), fact("cfo", 30, pe)]
        c = self.codes(forensic.accounting_flags(F.analyse(facts)))
        self.assertEqual(c["weak_cash_conversion"], "high")


class News(unittest.TestCase):
    def test_classification(self):
        cases = {
            "Outcome of Board Meeting - Financial Results for Q2": ("financial_results", "high"),
            "Intimation of Board Meeting": ("board_meeting", "low"),
            "Resignation of Statutory Auditor": ("auditor_change", "high"),
            "Disclosure under Regulation 31(1) SAST - pledge": ("pledge", "high"),
            "Resignation of Chief Financial Officer": ("kmp_change", "high"),
            "Credit Rating - downgrade": ("credit_rating", "medium"),
            "Closure of Trading Window": ("compliance_routine", "info"),
            "Something unusual": ("other", "low"),
        }
        for text, want in cases.items():
            self.assertEqual(news.classify(text), want, text)

    def test_dedupe_new_and_governance_findings(self):
        s = src("ann")
        a = Announcement(dt.date(2026, 10, 1), "NSE", "Resignation of Statutory Auditor", "", s.url, s)
        out = news.analyse([a, a], [], set())
        self.assertEqual(len(out["items"]), 1)
        self.assertTrue(out["items"][0]["new"])
        self.assertEqual(news.analyse([a], [], {a.fingerprint})["new_count"], 0)
        g = news.governance_findings(out["items"], dt.date(2026, 10, 29))
        self.assertEqual([(f.code, f.severity) for f in g], [("disclosure_auditor_change", "critical")])
        self.assertEqual(news.governance_findings(out["items"], dt.date(2027, 10, 29)), [])  # outside window


class Risk(unittest.TestCase):
    def test_conditions_round_trip(self):
        state = {"q.pat_yoy": 12.0, "promoter_pledged_pct": 2.0, "fy.debt_to_equity": 0.4}
        conds = risk.build_conditions(state, None)
        ids = {c["id"]: c for c in conds}
        self.assertEqual(ids["pledge_rise"]["threshold"], 10.0)
        self.assertEqual(ids["leverage_up"]["threshold"], 1.0)
        res = {c["id"]: c["status"] for c in risk.evaluate_conditions(conds, {"q.pat_yoy": -3, "promoter_pledged_pct": 4})}
        self.assertEqual(res, {"pat_decline": "TRIGGERED", "pledge_rise": "holds", "leverage_up": "unknown"})


if __name__ == "__main__":
    unittest.main()
