"""Company identity resolution and verification."""

import unittest

from helpers import src

from fortune_research.identity import check_profile, clean_symbol, isin_valid, merge_master, resolve


def rec(name, isin=None, nse=None, bse=None, official=True, synthetic=False, series="EQ"):
    return {"name": name, "isin": isin, "nse_symbol": nse, "bse_code": bse, "series": series, "synthetic": synthetic,
            "source": src("master-%s" % (nse or bse), official=official)}


# Real, public ISINs are used only to test the ISO 6166 check-digit arithmetic.
MASTER = [
    rec("Infosys Limited", "INE009A01021", nse="INFY"), rec("Infosys Limited", "INE009A01021", bse="500209"),
    rec("Reliance Industries Limited", "INE002A01018", nse="RELIANCE"),
    rec("HDFC Bank Limited", "INE040A01034", nse="HDFCBANK"),
    rec("Mahindra & Mahindra Limited", "INE101A01026", nse="M&M"),
    rec("Bajaj Auto Limited", "INE917I01010", nse="BAJAJ-AUTO"),
    rec("Bajaj Finance Limited", "INE296A01024", nse="BAJFINANCE"),
]


class Isin(unittest.TestCase):
    def test_check_digit(self):
        for good in ("INE009A01021", "INE002A01018", "INE040A01034", "US0378331005"):
            self.assertTrue(isin_valid(good), good)
        for bad in ("INE009A01022", "INE009A0102", "INE009A0102X", "", None):
            self.assertFalse(isin_valid(bad), bad)


class Resolve(unittest.TestCase):
    def test_symbol_forms(self):
        self.assertEqual(clean_symbol("nse: infy"), "INFY")
        self.assertEqual(clean_symbol("INFY.NS"), "INFY")
        self.assertEqual(clean_symbol("500209.BO"), "500209")
        for q in ("INFY", "infy.ns", "NSE:INFY", "500209", "500209.BO", "INE009A01021", "Infosys", "infosys ltd"):
            r = resolve(q, MASTER)
            self.assertEqual(r.status, "resolved", q)
            self.assertEqual((r.security.nse_symbol, r.security.bse_code, r.security.isin), ("INFY", "500209", "INE009A01021"), q)

    def test_merged_record_is_verified(self):
        r = resolve("INFY", MASTER)
        self.assertIn("NSE INFY and BSE 500209 map to the same ISIN", r.security.verification)
        self.assertTrue(any("valid check digit" in v for v in r.security.verification))
        self.assertEqual(r.security.yahoo_symbol("NSE"), "INFY.NS")
        self.assertEqual(r.security.yahoo_symbol("BSE"), "500209.BO")

    def test_special_characters(self):
        self.assertEqual(resolve("M&M", MASTER).security.isin, "INE101A01026")
        self.assertEqual(resolve("bajaj-auto", MASTER).security.isin, "INE917I01010")

    def test_ambiguous_is_not_guessed(self):
        r = resolve("Bajaj", MASTER)
        self.assertEqual(r.status, "ambiguous")
        self.assertEqual({c.nse_symbol for c in r.candidates}, {"BAJAJ-AUTO", "BAJFINANCE"})

    def test_not_found(self):
        self.assertEqual(resolve("Nonexistent Widgets", MASTER).status, "not_found")

    def test_conflicting_masters_are_reported(self):
        m = [rec("X Ltd", "INE009A01021", nse="XA"), rec("X Ltd", "INE009A01021", nse="XB")]
        self.assertEqual(len(merge_master(m)), 1)
        r = resolve("INE009A01021", m)
        self.assertTrue(any("disagree" in w for w in r.warnings))

    def test_warnings(self):
        m = [rec("Bad Isin Ltd", "INE009A01022", nse="BADI"), rec("Local Only Ltd", "INE002A01018", nse="LOCO", official=False),
             rec("Surv Ltd", "INE040A01034", nse="SURV", series="BE")]
        self.assertTrue(any("check digit" in w for w in resolve("BADI", m).warnings))
        self.assertTrue(any("not confirmed against an official" in w for w in resolve("LOCO", m).warnings))
        self.assertTrue(any("trade-for-trade" in w for w in resolve("SURV", m).warnings))

    def test_profile_cross_check(self):
        r = resolve("INFY", MASTER)
        check_profile(r.security, {"name": "Infosys Ltd", "isin": "INE002A01018", "sector": "IT"}, r)
        self.assertTrue(any("does not match master" in w for w in r.warnings))
        self.assertEqual(r.security.sector, "IT")


if __name__ == "__main__":
    unittest.main()
