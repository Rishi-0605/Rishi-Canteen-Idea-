"""Provider layer: HTTP retries/caching/logging, registry fallback, local files,
and the NSE/BSE/Yahoo/RSS parsers.

The exchange parser fixtures below are HAND-WRITTEN to the documented / observed
response shapes. They are not captured live responses, so passing them shows
the parsers work on that shape, not that the live endpoints still match it.
"""

import json
import tempfile
import unittest
from pathlib import Path

from helpers import Workspace

from fortune_research.config import Settings
from fortune_research.models import Security
from fortune_research.providers import bse, nse, rss, yahoo
from fortune_research.providers.base import Provider, ProviderError
from fortune_research.providers.http import FetchError, HttpClient, ResponseCache, redact
from fortune_research.providers.local_files import LocalFilesProvider
from fortune_research.providers.registry import Registry


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, url, headers, timeout):
        self.calls += 1
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class Http(unittest.TestCase):
    def client(self, responses, cache=None):
        self.log = []
        self.sleeps = []
        t = FakeTransport(responses)
        return HttpClient("test-agent", max_retries=3, backoff=1, cache=cache, on_fetch=self.log.append,
                          sleep=self.sleeps.append, transport=t), t

    def test_retries_then_succeeds_with_backoff(self):
        c, t = self.client([(503, b""), ConnectionError("x"), (200, b"ok")])
        self.assertEqual(c.get("https://h.invalid/a", provider="p"), b"ok")
        self.assertEqual(t.calls, 3)
        self.assertEqual(self.sleeps, [1, 2])
        self.assertEqual(self.log[-1]["status"], 200)
        self.assertEqual(len(self.log[-1]["sha256"]), 64)

    def test_no_retry_on_404_and_logs_failure(self):
        c, t = self.client([(404, b"")])
        with self.assertRaises(FetchError) as cm:
            c.get("https://h.invalid/missing")
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(t.calls, 1)
        self.assertIn("error", self.log[-1])

    def test_gives_up_after_max_retries(self):
        c, t = self.client([(429, b"")] * 4)
        with self.assertRaises(FetchError):
            c.get("https://h.invalid/x")
        self.assertEqual(t.calls, 4)

    def test_cache(self):
        with tempfile.TemporaryDirectory() as d:
            cache = ResponseCache(Path(d) / "c.db")
            c, t = self.client([(200, b"body")], cache)
            c.get("https://h.invalid/c")
            self.assertEqual(c.get("https://h.invalid/c"), b"body")
            self.assertEqual(t.calls, 1)
            self.assertTrue(self.log[-1]["cache_hit"])

    def test_redaction(self):
        self.assertEqual(redact("https://x.invalid/q?symbol=INFY&apikey=SECRET"), "https://x.invalid/q?symbol=INFY&apikey=REDACTED")


class Local(unittest.TestCase):
    def test_rows_without_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "companies" / "ABC"
            c.mkdir(parents=True)
            (c / "financials.csv").write_text(
                "period_end,period_type,basis,line_item,value,unit,source_url\n"
                "2026-03-31,FY,consolidated,revenue,100,INR crore,https://x.invalid/a\n"
                "2026-03-31,FY,consolidated,pat,10,INR crore,\n"
                "2026-03-31,FY,consolidated,cfo,5,USD,https://x.invalid/a\n"
                "2026-03-31,FY,consolidated,pbt,5000,INR lakh,https://x.invalid/a\n", encoding="utf-8")
            p = LocalFilesProvider([d])
            facts = p.financials(Security("ABC", None, nse_symbol="ABC"))
            self.assertEqual({f.name: f.value for f in facts}, {"revenue": 100.0, "pbt": 50.0})
            self.assertEqual(len(p.issues), 2)

    def test_price_file_needs_source_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "companies" / "ABC"
            c.mkdir(parents=True)
            (c / "prices.csv").write_text("date,close\n2026-10-01,10\n", encoding="utf-8")
            p = LocalFilesProvider([d])
            self.assertIsNone(p.prices(Security("ABC", None, nse_symbol="ABC")))
            (c / "prices.source.json").write_text(json.dumps({"url": "https://x.invalid/p", "official": False}), encoding="utf-8")
            s = p.prices(Security("ABC", None, nse_symbol="ABC"))
            self.assertEqual(s.last.close, 10)
            self.assertFalse(s.source.official)


class Failing(Provider):
    name = "failing"
    capabilities = frozenset(["prices"])

    def prices(self, sec, start=None, end=None):
        raise ProviderError("down")


class RegistryOrder(unittest.TestCase):
    def test_fallback_and_errors_recorded(self):
        ws = Workspace()
        try:
            s = ws.settings(1, {"providers": {"prices": ["failing", "local"]}})
            reg = Registry(s)
            reg.providers["failing"] = Failing()
            sec = Security("x", None, nse_symbol="SAMPLEMFG")
            series, used = reg.fetch("prices", sec)
            self.assertEqual(used, "local")
            self.assertTrue(series.bars)
            self.assertEqual(reg.errors, [("prices", "failing", "down")])
        finally:
            ws.cleanup()

    def test_network_providers_disabled_by_default(self):
        s = Settings.load()
        with tempfile.TemporaryDirectory() as d:
            s.data["general"]["data_dir"] = d
            self.assertEqual(sorted(Registry(s).providers), ["local"])


class Parsers(unittest.TestCase):
    def test_nse_master(self):
        text = ("SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE\n"
                "INFY,Infosys Limited,EQ,08-FEB-1995,5,1,INE009A01021,5\n")
        rows = nse.parse_equity_master(text, "2026-10-29T10:00:00+05:30")
        self.assertEqual((rows[0]["nse_symbol"], rows[0]["isin"], rows[0]["series"], rows[0]["face_value"]), ("INFY", "INE009A01021", "EQ", 5.0))
        self.assertTrue(rows[0]["source"].official)

    def test_nse_bhavcopy_udiff(self):
        text = ("TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"
                "2026-10-28,2026-10-28,CM,NSE,STK,1594,INE009A01021,INFY,EQ,1500,1520,1490,1510.5,123456\n"
                "2026-10-28,2026-10-28,CM,NSE,STK,1594,INE009A01021,INFY,BL,1500,1500,1500,1500,10\n")
        row = nse.parse_bhavcopy(text, "INFY")
        self.assertEqual((row["close"], row["volume"], row["date"].isoformat()), (1510.5, 123456.0, "2026-10-28"))
        self.assertIsNone(nse.parse_bhavcopy(text, "TCS"))

    def test_nse_announcements(self):
        payload = [{"symbol": "INFY", "desc": "Outcome of Board Meeting", "an_dt": "16-Oct-2026 17:05:00",
                    "attchmntFile": "https://nsearchives.nseindia.com/corporate/x.pdf", "attchmntText": "Results"},
                   {"symbol": "TCS", "desc": "other", "an_dt": "16-Oct-2026 10:00:00"}]
        out = nse.parse_announcements(payload, "INFY", "2026-10-29T10:00:00+05:30")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].date.isoformat(), "2026-10-16")
        self.assertTrue(out[0].source.official)

    def test_bse_announcements(self):
        payload = {"Table": [{"SCRIP_CD": 500209, "NEWSSUB": "Board Meeting Intimation", "NEWS_DT": "2026-10-01T18:00:00",
                              "CATEGORYNAME": "Board Meeting", "ATTACHMENTNAME": "abc.pdf"}]}
        out = bse.parse_announcements(payload, "500209", "2026-10-29T10:00:00+05:30")
        self.assertEqual(out[0].url, "https://www.bseindia.com/xml-data/corpfiling/AttachLive/abc.pdf")
        self.assertEqual(out[0].category, "Board Meeting")

    def test_yahoo_is_unofficial_and_skips_nulls(self):
        payload = {"chart": {"error": None, "result": [{"meta": {"symbol": "INFY.NS"}, "timestamp": [1792900800, 1792987200],
                                                        "indicators": {"quote": [{"open": [1, None], "high": [2, None], "low": [0.5, None],
                                                                                  "close": [1.5, None], "volume": [100, None]}]}}]}}
        s = yahoo.parse_chart(payload, "https://query2.finance.yahoo.com/x", "2026-10-29T10:00:00+05:30")
        self.assertEqual(len(s.bars), 1)
        self.assertFalse(s.source.official)
        with self.assertRaises(ProviderError):
            yahoo.parse_chart({"chart": {"error": {"code": "Not Found"}}}, "u", "t")

    def test_rss_allowlist_and_mentions(self):
        xml = (b"<rss><channel><item><title>Infosys Q2 profit rises</title><link>https://www.livemint.com/a</link>"
               b"<pubDate>Tue, 28 Oct 2026 10:00:00 +0530</pubDate></item><item><title>Infosys rumour</title>"
               b"<link>https://random-blog.invalid/b</link><pubDate>Tue, 28 Oct 2026 10:00:00 +0530</pubDate></item></channel></rss>")
        items = rss.parse_feed(xml, ["livemint.com"], "2026-10-29T10:00:00+05:30")
        self.assertEqual([i[2] for i in items], ["https://www.livemint.com/a"])
        self.assertTrue(rss.mentions("Infosys Q2 profit rises", Security("Infosys Limited", None, nse_symbol="INFY")))
        self.assertFalse(rss.mentions("Wipro results", Security("Infosys Limited", None, nse_symbol="INFY")))


if __name__ == "__main__":
    unittest.main()
