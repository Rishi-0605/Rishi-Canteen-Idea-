"""Portfolio import, validation, reconciliation and portfolio maths."""

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from helpers import src

from fortune_research.analysis import portfolio as P
from fortune_research.models import PriceBar, PriceSeries, Security
from fortune_research.portfolio import reader, reconcile
from fortune_research.portfolio.reader import Holding, Transaction


def txn(d, side, qty, price, acct="A1", sym="X", charges=0.0, row=0):
    return Transaction(dt.date.fromisoformat(d), acct, sym, None, "NSE", side, qty, price, charges, row=row)


class Reader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_aliases_preamble_and_validation(self):
        p = self.write("h.csv", "Holdings statement\nClient: X\n\nClient ID,Trading Symbol,ISIN,Qty.,Avg. cost\n"
                                "AC0001,INFY.NS,INE009A01021,10,1500.5\nAC0001,BADQ,,-3,10\nAC0001,BADISIN,INE009A01022,5,10\n"
                                "AC0001,NOCOST,,4,\nAC0001,INFY,INE009A01021,2,1400\nTotal,,,,\n")
        res = reader.read_holdings(p)
        syms = [(h.symbol, h.quantity) for h in res.holdings]
        self.assertEqual(syms, [("INFY", 10), ("BADISIN", 5), ("NOCOST", 4), ("INFY", 2)])
        codes = sorted(i.code for i in res.issues)
        self.assertEqual(codes, ["bad_isin", "bad_quantity", "duplicate_holding", "no_cost"])
        self.assertEqual(res.holdings[0].account, "AC0001")
        self.assertEqual(res.holdings[0].row, 5)

    def test_missing_account_column_uses_default_and_warns(self):
        p = self.write("acct.csv", "Symbol,Quantity,Average Price\nTCS,3,3000\n")
        res = reader.read_holdings(p, default_account="MYACCT")
        self.assertEqual(res.holdings[0].account, "MYACCT")
        self.assertIn("no_account_column", [i.code for i in res.issues])

    def test_unmappable_header(self):
        p = self.write("bad.csv", "foo,bar\n1,2\n")
        res = reader.read_holdings(p)
        self.assertEqual(res.holdings, [])
        self.assertEqual(res.issues[0].code, "header_not_found")

    def test_transactions(self):
        p = self.write("t.csv", "Trade Date,Account,Symbol,Type,Qty,Price,Charges,Trade ID\n"
                                "2026-01-05,A,INFY,B,10,1500,5,T1\n05-02-2026,A,INFY,SELL,4,1600,3,T2\n"
                                "2026-02-06,A,INFY,HOLD,1,1,0,T3\n2026-02-07,A,INFY,BUY,1,1600,0,T2\n")
        res = reader.read_transactions(p)
        self.assertEqual([(t.side, t.quantity, t.date.isoformat()) for t in res.transactions],
                         [("BUY", 10, "2026-01-05"), ("SELL", 4, "2026-02-05")])
        self.assertEqual(sorted(i.code for i in res.issues), ["bad_side", "duplicate_trade"])

    def test_xlsx(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["Report"])
        ws.append(["Account ID", "Instrument", "Quantity", "Avg Cost"])
        ws.append(["Z1", "HDFCBANK", 7, 1600])
        p = self.dir / "h.xlsx"
        wb.save(p)
        res = reader.read_holdings(p)
        self.assertEqual([(h.account, h.symbol, h.quantity, h.avg_cost) for h in res.holdings], [("Z1", "HDFCBANK", 7, 1600)])
        self.assertEqual(len(res.files[0]["sha256"]), 64)


class Reconcile(unittest.TestCase):
    def test_average_cost_and_realised(self):
        pos, issues = reconcile.positions_from_transactions(
            [txn("2026-01-01", "BUY", 10, 100, charges=10), txn("2026-02-01", "BUY", 10, 120), txn("2026-03-01", "SELL", 5, 150, charges=2)])
        p = pos[("A1", "X")]
        self.assertEqual(p.quantity, 15)
        self.assertAlmostEqual(p.avg_cost, (1010 + 1200) / 20)  # sells do not change average cost
        self.assertAlmostEqual(p.realised_pnl, 5 * (150 - 110.5) - 2)
        self.assertEqual(issues, [])

    def test_oversell(self):
        _, issues = reconcile.positions_from_transactions([txn("2026-01-01", "BUY", 5, 100), txn("2026-02-01", "SELL", 8, 100)])
        self.assertEqual(issues[0].code, "oversold")

    def test_statuses(self):
        h = [Holding("A1", "X", None, "NSE", 20, 100), Holding("A1", "Y", None, "NSE", 5, 50), Holding("A1", "Z", None, "NSE", 3, 10),
             Holding("A1", "W", None, "NSE", 4, 10)]
        t = [txn("2026-01-01", "BUY", 10, 100, sym="X"), txn("2026-01-01", "BUY", 5, 50, sym="Y"), txn("2026-01-01", "BUY", 3, 12, sym="Z"),
             txn("2026-01-01", "BUY", 9, 10, sym="V")]
        r = reconcile.reconcile(h, t)
        self.assertEqual(r.status, {("A1", "X"): "qty_mismatch", ("A1", "Y"): "matched", ("A1", "Z"): "cost_mismatch",
                                    ("A1", "W"): "no_transactions", ("A1", "V"): "missing_holding"})
        self.assertTrue(any("exactly 2x" in i.message for i in r.issues))
        self.assertEqual(r.matched, 1)


class Maths(unittest.TestCase):
    def test_xirr(self):
        r = P.xirr([(dt.date(2025, 1, 1), -100), (dt.date(2026, 1, 1), 110)])
        self.assertAlmostEqual(r, 0.10, places=6)
        two = P.xirr([(dt.date(2024, 1, 1), -100), (dt.date(2025, 1, 1), -100), (dt.date(2026, 1, 1), 231)])
        self.assertAlmostEqual(P.xnpv(two, [(dt.date(2024, 1, 1), -100), (dt.date(2025, 1, 1), -100), (dt.date(2026, 1, 1), 231)]), 0, places=5)
        self.assertIsNone(P.xirr([(dt.date(2025, 1, 1), -100)]))
        self.assertIsNone(P.xirr([(dt.date(2025, 1, 1), 100), (dt.date(2026, 1, 1), 100)]))

    def test_mask(self):
        self.assertEqual(P.mask("ZRD-AB12345"), "******2345")
        self.assertEqual(P.mask("ZRD-AB12345", enabled=False), "ZRD-AB12345")

    def test_benchmark_pme(self):
        bars = [PriceBar(dt.date(2025, 1, 1), 100, 100, 100, 100, 0), PriceBar(dt.date(2026, 1, 1), 110, 110, 110, 110, 0)]
        b, tv, skipped = P.benchmark_pme([txn("2025-01-01", "BUY", 1, 100)], bars, dt.date(2026, 1, 1))
        self.assertAlmostEqual(tv, 110)
        self.assertAlmostEqual(b, 0.10, places=6)
        self.assertEqual(skipped, 0)

    def test_weights_unpriced_and_breaches(self):
        def series(px, d=dt.date(2026, 10, 20)):
            return PriceSeries([PriceBar(d, px, px, px, px, 1)], src("p%s" % px))

        prices = {"A": (100, "IT"), "B": (50, "IT"), "C": (10, "Banks")}

        def pricing(sym, isin):
            if sym not in prices:
                return None
            px, sector = prices[sym]
            return {"security": Security(sym, None, nse_symbol=sym), "series": series(px), "profile": {"sector": sector}}

        h = [Holding("ACCT0001", "A", None, "NSE", 10, 90), Holding("ACCT0001", "B", None, "NSE", 10, None),
             Holding("ACCT0002", "C", None, "NSE", 50, 12), Holding("ACCT0002", "D", None, "NSE", 5, 1)]
        out = P.analyse(h, None, pricing, dt.date(2026, 10, 21), max_stock=0.5, max_sector=0.7)
        self.assertEqual(out["total"]["market_value"], 1000 + 500 + 500)
        self.assertAlmostEqual(sum(r["weight"] for r in out["positions"]), 1.0)
        self.assertEqual([u["symbol"] for u in out["unpriced"]], ["D"])  # never valued at cost
        self.assertAlmostEqual(out["sectors"]["IT"], 0.75)
        self.assertEqual({b.get("sector") for b in out["breaches"] if b["type"] == "sector"}, {"IT"})
        self.assertAlmostEqual(out["concentration"]["hhi"], 0.5 ** 2 + 0.25 ** 2 + 0.25 ** 2)
        self.assertIsNone(next(r for r in out["positions"] if r["symbol"] == "B")["unrealised_pnl"])
        self.assertIn("****0001", out["accounts"])


if __name__ == "__main__":
    unittest.main()
