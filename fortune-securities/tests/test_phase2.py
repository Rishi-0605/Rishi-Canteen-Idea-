"""Phase 2: real-data plumbing. Exchange-format fixtures in tests/fixtures/format/ are
HAND-WRITTEN for the fictional EXAMPLECO (see the README there): they test parsing of the
documented shapes, not the live endpoints.
"""

import csv
import datetime as dt
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import ROOT, Workspace, fact, src

from fortune_research import documents as D
from fortune_research import health
from fortune_research import verify as V
from fortune_research.agent import ResearchAgent, ResolutionError
from fortune_research.analysis import corporate_actions as CA
from fortune_research.analysis import financials as F
from fortune_research.analysis import lookahead, quality
from fortune_research.identity import resolve
from fortune_research.models import CorporateAction, PriceBar, PriceSeries, Security, fy_label
from fortune_research.providers import bse, nse, rss, xbrl, yahoo
from fortune_research.providers.base import ProviderError
from fortune_research.providers.http import FetchError, HttpClient, parse_json
from fortune_research.providers.ir import IRProvider

FIX = ROOT / "tests" / "fixtures" / "format"
EX = Security("Exampleco Limited", "INEZ9E101010", nse_symbol="EXAMPLECO", bse_code="999001")


def fx(name):
    return (FIX / name).read_bytes()


class Router:
    """Fake transport: url substring -> (status, body) or Exception. Records every call."""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        for key, resp in self.routes.items():
            if key in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        return 404, b""


def client(routes, log=None):
    r = Router(routes)
    return HttpClient("test", max_retries=0, transport=r, sleep=lambda s: None, on_fetch=(log.append if log is not None else None)), r


def pdf_bytes(pages):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for lines in pages:
        y = 800
        for line in lines:
            c.drawString(40, y, line)
            y -= 18
        c.showPage()
    c.save()
    return buf.getvalue()


class XBRL(unittest.TestCase):
    def setUp(self):
        self.res = xbrl.parse(fx("results_q2.xml"), "https://nsearchives.nseindia.com/corporate/xbrl/EXAMPLECO_Q2.xml",
                              "2025-11-08T10:00:00+05:30", "2025-11-07")
        self.by = {(f.name, f.period_type, f.period_end.isoformat()): f for f in self.res.facts}

    def test_values_units_periods(self):
        rev = self.by[("revenue", "Q", "2025-09-30")]
        self.assertAlmostEqual(rev.value, 1234.56)          # 12,345,600,000 rupees -> crore
        self.assertEqual(rev.unit, "INR crore")
        self.assertEqual(rev.period_start, dt.date(2025, 7, 1))
        self.assertEqual(rev.basis, "consolidated")
        self.assertEqual(rev.source.locator, "RevenueFromOperations @ OneD")
        self.assertEqual(rev.source.published, "2025-11-07")
        self.assertTrue(rev.source.official)
        self.assertEqual(rev.period_label, "Q2FY26")
        self.assertAlmostEqual(self.by[("revenue", "Q", "2024-09-30")].value, 1080.0)  # prior-year comparative
        self.assertEqual(self.by[("eps_diluted", "Q", "2025-09-30")].unit, "INR per share")
        self.assertAlmostEqual(self.by[("inventories", "POINT", "2025-09-30")].value, 310.0)

    def test_ytd_segment_and_unmapped_are_reported_not_used(self):
        reasons = {(e, c): why for e, c, why in self.res.skipped}
        self.assertIn("year-to-date", reasons[("RevenueFromOperations", "YTD")])
        self.assertIn("dimensional", reasons[("RevenueFromOperations", "SegA")])
        self.assertEqual([u[0] for u in self.res.unmapped], ["SomeNewTaxonomyElement"])
        self.assertEqual(sum(1 for f in self.res.facts if f.name == "revenue"), 2)

    def test_identity(self):
        self.assertEqual(xbrl.check_identity(self.res, "INEZ9E101010", "EXAMPLECO", "999001"), [])
        self.assertTrue(xbrl.check_identity(self.res, "INE000A01011", "OTHER", None))

    def test_reconciles_and_ebitda_from_total_expenses(self):
        issues = quality.check_facts(self.res.facts, "consolidated")
        self.assertNotIn("pbt_reconcile", [i.code for i in issues])
        self.assertNotIn("pl_reconcile", [i.code for i in issues])
        q = F.analyse(self.res.facts).quarterly["Q2FY26"]
        self.assertAlmostEqual(q["ebitda"].value, 1234.56 - (1058.01 - 4.5 - 21.0))
        self.assertAlmostEqual(q["revenue_yoy"].value, (1234.56 / 1080 - 1) * 100)

    def test_not_xbrl(self):
        with self.assertRaises(xbrl.XBRLError):
            xbrl.parse(b"<html>Access Denied</html>", "u", "t")
        with self.assertRaises(xbrl.XBRLError):
            xbrl.parse(b"not xml", "u", "t")


class NSE(unittest.TestCase):
    def test_financials_pipeline_and_identity_guard(self):
        wrong = fx("results_q2.xml").replace(b"INEZ9E101010", b"INE000A01011")
        http, r = client({"nseindia.com/\x00": (200, b""), "www.nseindia.com/api/corporates-financial-results": (200, fx("nse_results_index.json")),
                          "EXAMPLECO_Q2.xml": (200, fx("results_q2.xml")), "EXAMPLECO_Q1.xml": (200, wrong),
                          "www.nseindia.com/": (200, b"<html>home</html>")})
        p = nse.NSEProvider(http)
        facts = p.financials(EX)
        self.assertTrue(facts)
        self.assertEqual({f.source.url.rsplit("/", 1)[-1] for f in facts}, {"EXAMPLECO_Q2.xml"})  # Q1 names another company
        d = p.diagnostics["financials"]
        self.assertEqual(len(d["identity_problems"]), 1)
        self.assertEqual(d["no_xbrl"], 1)  # the "-" row; duplicates across the Quarterly/Annual indexes are merged
        self.assertEqual(len(facts), len({(f.name, f.period_type, f.period_end) for f in facts}))
        self.assertEqual({f.source.published for f in facts}, {"2025-11-07"})

    def test_html_block_page_is_a_failed_retrieval(self):
        http, _ = client({"www.nseindia.com/api/corporate-announcements": (200, b"<html><title>Access Denied</title></html>"),
                          "www.nseindia.com/": (200, b"<html></html>")})
        with self.assertRaises(ProviderError) as cm:
            nse.NSEProvider(http).announcements(EX)
        self.assertIn("bot-protection", str(cm.exception))
        with self.assertRaises(FetchError):
            parse_json(b"", "u")

    def test_bhavcopy_blocked_fails_fast_not_as_holidays(self):
        http, r = client({"BhavCopy": (403, b"")})
        with self.assertRaises(ProviderError):
            nse.NSEProvider(http).prices(EX, dt.date(2025, 10, 1), dt.date(2025, 10, 31))
        self.assertEqual(len(r.calls), 1)

    def test_bhavcopy_holidays_skipped(self):
        csv_text = ("TradDt,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n"
                    "2025-10-31,EXAMPLECO,EQ,100,102,99,101,5000\n").encode()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("bhav.csv", csv_text)
        http, r = client({"20251031": (200, buf.getvalue())})  # other days 404 (holiday / not published)
        s = nse.NSEProvider(http).prices(EX, dt.date(2025, 10, 20), dt.date(2025, 10, 31))
        self.assertEqual([b.close for b in s.bars], [101.0])
        self.assertIs(s.adjusted, False)
        self.assertTrue(s.source.official)

    def test_corporate_actions_and_shareholding(self):
        acts = nse.parse_corporate_actions(json.loads(fx("nse_corporate_actions.json")), "EXAMPLECO", "t")
        self.assertEqual([(a.kind, a.factor) for a in acts], [("split", 5.0), ("bonus", 1.5), ("dividend", None)])
        sh = nse.parse_shareholding(json.loads(fx("nse_shareholding.json")), "EXAMPLECO", "t")
        self.assertEqual([r.promoter_pct for r in sh], [51.14, 51.14])
        self.assertIsNone(sh[0].promoter_pledged_pct)  # not in this endpoint: unknown, never 0
        self.assertEqual(sh[-1].source.published, "2025-10-17")


class OtherProviders(unittest.TestCase):
    def test_bse_master_merges_with_nse(self):
        rows = bse.parse_scrip_master(json.loads(fx("bse_scrip_master.json")), "t")
        nse_rows = [{"name": "EXAMPLECO LIMITED", "isin": "INEZ9E101010", "nse_symbol": "EXAMPLECO", "bse_code": None, "series": "EQ",
                     "synthetic": False, "source": src("nse-master")}]
        r = resolve("999001", rows + nse_rows)
        self.assertEqual((r.status, r.security.nse_symbol, r.security.bse_code), ("resolved", "EXAMPLECO", "999001"))

    def test_yahoo_splits_unofficial(self):
        acts = yahoo.parse_splits(json.loads(fx("yahoo_chart_splits.json")), "u", "t")
        self.assertEqual([(a.ex_date.isoformat(), a.factor) for a in acts], [("2024-03-15", 1.5)])
        self.assertFalse(acts[0].source.official)

    def test_google_news_publisher_allowlist_and_dedupe(self):
        items = rss.parse_feed(fx("google_news.xml"), ["economictimes.indiatimes.com", "business-standard.com", "livemint.com"], "t")
        self.assertEqual([i[3] for i in items], ["economictimes.indiatimes.com", "www.business-standard.com", "www.livemint.com"])
        self.assertEqual(items[0][1], "Exampleco Q2 profit rises 15% on defence orders")  # publisher suffix stripped
        http, _ = client({"news.google.com": (200, fx("google_news.xml"))})
        p = rss.RSSProvider(http, ["https://news.google.com/rss/search?q={query}"], ["economictimes.indiatimes.com", "business-standard.com",
                                                                                     "livemint.com"])
        out = p.news(EX)
        self.assertEqual(len(out), 2)  # ET and BS carry the same story
        story = [a for a in out if "profit" in a.subject][0]
        self.assertIn("business-standard", story.details)
        self.assertTrue(all(not a.source.official for a in out))

    def test_all_feeds_failing_is_an_error(self):
        http, _ = client({"news.google.com": ConnectionError("blocked")})
        with self.assertRaises(ProviderError):
            rss.RSSProvider(http, ["https://news.google.com/rss/search?q={query}"], ["livemint.com"]).news(EX)


class Documents(unittest.TestCase):
    def test_pdf_text_units_and_locate(self):
        data = pdf_bytes([["EXAMPLECO LIMITED", "Statement of results for the quarter ended 30 September 2025", "(Rs. in crore)",
                           "Revenue from operations 1,234.56 1,080.00", "Profit for the period (149.60) 130.00"], ["Notes", "Nothing here"]])
        doc = D.build(data, "https://www.exampleco.invalid/docs/Q2FY26-results.pdf", title="Financial Results Q2 FY26")
        self.assertIsNone(doc.error)
        self.assertEqual((doc.kind, doc.period, len(doc.pages)), ("results", "Q2FY26", 2))
        self.assertEqual(doc.units_by_page[1], "INR crore")
        hits = D.locate(doc, "Revenue from operations")
        self.assertEqual(hits[0]["page"], 1)
        self.assertEqual(hits[0]["numbers"][:2], [1234.56, 1080.0])
        self.assertEqual(hits[0]["status"], "needs_review")
        self.assertEqual(D.locate(doc, "Profit for the period")[0]["numbers"][0], -149.6)  # (x) is negative

    def test_unreadable_documents_are_reported(self):
        self.assertIn("not a PDF", D.build(b"<html>login</html>", "u").error)
        blank = pdf_bytes([[]])
        self.assertIn("OCR", D.build(blank, "u").error)

    def test_ir_provider(self):
        page = fx("ir_page.html")
        links = D.pdf_links(page.decode(), "https://www.exampleco.invalid/investors", ["exampleco.invalid"])
        self.assertEqual([l["kind"] for l in links], ["annual_report", "results", "presentation", "transcript"])
        self.assertNotIn("elsewhere.invalid", " ".join(l["url"] for l in links))
        pdf = pdf_bytes([["(Rs. in crore)", "Revenue from operations 1,234.56"]])
        http, _ = client({"/investors": (200, page), ".pdf": (200, pdf)})
        docs = IRProvider(http).documents(EX, profile={"investor_relations": {"pages": ["https://www.exampleco.invalid/investors"],
                                                                                "allowed_domains": ["exampleco.invalid"]}})
        self.assertEqual(len(docs), 4)
        self.assertTrue(all(d.official and d.pages for d in docs))
        self.assertEqual(IRProvider(http).documents(EX, profile={}), [])


class CorporateActions(unittest.TestCase):
    def act(self, d, factor, kind="split", published=None):
        return CorporateAction(dt.date.fromisoformat(d), kind, factor, "%s %g" % (kind, factor), src("ca" + d))

    def test_parse(self):
        self.assertEqual(CA.parse_subject("Bonus 1:1"), ("bonus", 2.0))
        self.assertEqual(CA.parse_subject("Bonus issue 3:2"), ("bonus", 2.5))
        self.assertEqual(CA.parse_subject("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per Share"), ("split", 10.0))
        self.assertEqual(CA.parse_subject("Consolidation of shares From Rs 2/- To Rs 10/-")[0], "consolidation")
        self.assertEqual(CA.parse_subject("Stock split")[0], "split_unparsed")
        self.assertEqual(CA.parse_subject("Final Dividend - Rs 3 Per Share"), ("dividend", None))

    def series(self, adjusted):
        bars = [PriceBar(dt.date(2024, 3, d), 300, 302, 298, 300, 1000) for d in (11, 12, 13, 14)] + \
               [PriceBar(dt.date(2024, 3, d), 150, 152, 148, 150, 2000) for d in (15, 18)]
        return PriceSeries(bars, src("px"), adjusted=adjusted)

    def test_unadjusted_prices_back_adjusted(self):
        s = self.series(False)
        issues = CA.adjust_prices(s, [self.act("2024-03-15", 2.0, "bonus")], dt.date(2024, 4, 1))
        self.assertEqual([b.close for b in s.bars], [150.0] * 6)
        self.assertEqual(s.bars[0].volume, 2000)
        self.assertTrue(s.adjusted)
        self.assertEqual(issues[0].code, "ca_price_adjusted")

    def test_unknown_adjustment_detected_from_gap_and_lookahead(self):
        s = self.series(None)
        CA.adjust_prices(s, [self.act("2024-03-15", 2.0)], dt.date(2024, 4, 1))
        self.assertEqual(s.bars[0].close, 150.0)
        s = self.series(None)  # no gap matching the factor -> treated as already adjusted
        issues = CA.adjust_prices(s, [self.act("2024-03-15", 5.0)], dt.date(2024, 4, 1))
        self.assertEqual(s.bars[0].close, 300.0)
        self.assertEqual(issues[0].code, "ca_already_adjusted")
        s = self.series(False)  # ex-date after the analysis date: not applied
        CA.adjust_prices(s, [self.act("2024-03-15", 2.0)], dt.date(2024, 3, 14))
        self.assertEqual(s.bars[0].close, 300.0)

    def test_per_share_restated_only_when_filed_before_ex_date(self):
        old = fact("eps_diluted", 20.0, "2023-03-31", s=src("old", published="2023-05-20"))
        new = fact("eps_diluted", 10.0, "2024-03-31", s=src("new", published="2024-05-20"))
        shares = fact("shares_outstanding", 1e8, "2023-03-31", s=src("sh", published="2023-05-20"))
        out, issues = CA.adjust_per_share([old, new, shares], [self.act("2024-03-15", 2.0, "bonus")], dt.date(2024, 6, 1))
        vals = {(f.name, f.period_end.year): (f.value, f.note) for f in out}
        self.assertEqual(vals[("eps_diluted", 2023)][0], 10.0)
        self.assertIn("restated", vals[("eps_diluted", 2023)][1])
        self.assertEqual(vals[("eps_diluted", 2024)], (10.0, ""))  # period after ex-date
        self.assertEqual(vals[("shares_outstanding", 2023)][0], 2e8)

    def test_explain_quantity(self):
        acts = [self.act("2024-03-15", 2.0, "bonus")]
        self.assertIn("explained by", CA.explain_quantity(120, 60, acts, dt.date(2024, 1, 1)))
        self.assertIsNone(CA.explain_quantity(120, 60, acts, dt.date(2024, 6, 1)))


class PointInTime(unittest.TestCase):
    def test_publication_rules(self):
        self.assertEqual(lookahead.is_available("2025-11-07", dt.date(2025, 9, 30), "Q", dt.date(2025, 11, 6)), (False, False))
        self.assertEqual(lookahead.is_available(None, dt.date(2025, 9, 30), "Q", dt.date(2025, 11, 13)), (False, True))
        self.assertEqual(lookahead.is_available(None, dt.date(2025, 9, 30), "Q", dt.date(2025, 11, 14)), (True, True))
        self.assertEqual(lookahead.assumed_public(dt.date(2025, 3, 31), "Q"), dt.date(2025, 5, 30))  # Q4: 60 days
        kept, issues, dropped = lookahead.filter_facts([fact("revenue", 1, "2025-09-30", "Q")], dt.date(2025, 12, 1))
        self.assertEqual((len(kept), dropped, issues[0].code), (1, 0, "publication_assumed"))

    def test_restatement_uses_later_filing_and_warns(self):
        a = fact("revenue", 100.0, "2025-03-31", s=src("first", published="2025-05-20"))
        b = fact("revenue", 96.0, "2025-03-31", s=src("restated", published="2026-05-20"))
        self.assertEqual(F.analyse([b, a]).annual["FY25"]["revenue"].value, 96.0)
        issues = quality.check_facts([a, b], "consolidated")
        self.assertEqual([i.code for i in issues], ["restated"])

    def test_non_standard_period_and_labels(self):
        f = fact("revenue", 100.0, "2025-03-31")
        f15 = type(f)(f.name, f.value, f.unit, f.period_end, "FY", f.basis, f.source, period_start=dt.date(2024, 1, 1))
        self.assertIn("non_standard_period", [i.code for i in quality.check_facts([f15], "consolidated")])
        self.assertEqual(fy_label(dt.date(2025, 12, 31), "FY"), "FY2025-Dec")
        self.assertEqual(fy_label(dt.date(2025, 3, 31), "FY"), "FY25")


class Health(unittest.TestCase):
    def test_statuses_from_real_probe_shapes(self):
        from fortune_research.providers.registry import Registry
        ws = Workspace()
        try:
            s = ws.settings(1, {"providers": {"nse": {"enabled": True}}})
            log = []
            http, _ = client({"EQUITY_L.csv": (200, b"<html>Access Denied - Akamai</html>"),
                              "corporate-announcements": (200, b"<html>Access Denied</html>"),
                              "corporates-corporateActions": (200, fx("nse_corporate_actions.json")),
                              "corporate-share-holdings-master": (200, fx("nse_shareholding.json")),
                              "BhavCopy": (403, b""), "corporates-financial-results": (503, b""), "www.nseindia.com/": (200, b"<html/>")}, log)
            reg = Registry(s, http=http)
            reg.providers["nse"] = nse.NSEProvider(http)
            res = {(r.provider, r.capability): r for r in health.run(reg, EX, today=dt.date(2025, 12, 1))}
            m = res[("nse", "master")]
            self.assertEqual((m.connection, m.retrieval, m.status), ("ok", "failed", "CONNECTED_NO_DATA"))  # 200 is not data
            self.assertIn("HTML page", m.errors[0])
            p = res[("nse", "prices")]  # 403: the server answered, but no data
            self.assertEqual((p.status, p.http[0]["status"]), ("CONNECTED_NO_DATA", 403))
            self.assertEqual(res[("nse", "financials")].status, "CONNECTED_NO_DATA")  # 503 on the results index
            ca = res[("nse", "corporate_actions")]
            self.assertEqual((ca.retrieval, ca.records), ("ok", 3))
            self.assertTrue(ca.suitability["split/bonus adjustment"]["ok"])
            sh = res[("nse", "shareholding")]
            self.assertEqual(sh.status, "PARTIAL")
            self.assertFalse(sh.suitability["pledge check"]["ok"])
            self.assertIn("promoter_pledged_pct", sh.fields_missing)
            self.assertEqual(sh.newest_date, "2025-09-30")
            lf = res[("local", "financials")]  # no local files for EXAMPLECO: reported, not invented
            self.assertEqual((lf.status, lf.records), ("CONNECTED_NO_DATA", 0))
            self.assertIn("no records", lf.errors[0])
            text = health.render(list(res.values()), EX, dt.date(2025, 12, 1))
            self.assertIn("CONNECTED_NO_DATA", text)
        finally:
            ws.cleanup()

    def test_capture_writes_real_fixture_with_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            http, _ = client({"x.invalid": (200, b"{\"a\": 1}")})
            http.capture_dir = Path(d)
            http.get("https://x.invalid/api?symbol=A&apikey=SECRET", provider="nse")
            meta = json.loads(next(Path(d).glob("*.meta.json")).read_text())
            self.assertIn("apikey=REDACTED", meta["url"])
            self.assertEqual(len(meta["sha256"]), 64)
            self.assertEqual(next(Path(d).glob("*.body")).read_bytes(), b"{\"a\": 1}")


class Verification(unittest.TestCase):
    def test_worksheet_round_trip_and_status_in_report(self):
        ws = Workspace()
        try:
            s = ws.settings(1)
            ag = ResearchAgent(s, as_of=Workspace.as_of(1))
            rec = ag.analyse_company("SAMPLEMFG", write=False)
            self.assertEqual(rec["summary"]["independent_verification"], "not applicable (synthetic sample data)")
            rows = V.worksheet_rows(rec)
            self.assertTrue(rows)
            self.assertTrue(all(r["source_url"] and r["extracted_value"] is not None for r in rows))
            path = ws.root / "w.csv"
            V.write_worksheet(rec, path)
            with open(path, newline="") as fh:
                data = list(csv.DictReader(fh))
            data[0].update(checked_value=str(data[0]["extracted_value"]), checked_by="tester")
            data[1].update(checked_value="1", checked_by="tester")  # a mismatch
            data[2].update(checked_value="5")  # no checker: rejected
            with open(path, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=V.COLUMNS)
                w.writeheader()
                w.writerows(data)
            got, problems = V.read_worksheet(path)
            self.assertEqual([g["matches"] for g in got], [1, 0])
            self.assertEqual(len(problems), 1)
            ag.store.save_verifications(rec["company"]["key"], rec["id"], got)
            self.assertEqual(ag.store.verification_summary(rec["company"]["key"]), {"checked": 2, "matched": 1, "mismatched": 1})
        finally:
            ws.cleanup()


class AgentIntegration(unittest.TestCase):
    def test_corporate_action_restates_eps_without_lookahead(self):
        ws = Workspace()
        try:
            s = ws.settings(1)
            cdir = Path(s.get("providers.local.roots")[0]) / "companies" / "SAMPLEMFG"
            (cdir / "corporate_actions.csv").write_text(
                "ex_date,subject,source_url,official,publisher,retrieved_at\n"
                "2026-09-01,Bonus 1:1,https://example.invalid/ca1,true,Sample Exchange (synthetic),2026-10-20T18:00:00+05:30\n"
                "2026-12-01,Bonus 1:1,https://example.invalid/ca2,true,Sample Exchange (synthetic),2026-10-20T18:00:00+05:30\n",
                encoding="utf-8")
            rec = ResearchAgent(s, as_of=Workspace.as_of(1)).analyse_company("SAMPLEMFG", write=False)
            self.assertEqual([a["ex_date"] for a in rec["corporate_actions"]], ["2026-09-01"])  # December action is in the future
            self.assertAlmostEqual(rec["annual"]["FY26"]["eps"]["value"], 23.3 / 2)
            self.assertIn("ca_per_share_restated", [i["code"] for i in rec["data_issues"]])
            report = ResearchAgent(s, as_of=Workspace.as_of(1)).analyse_company("SAMPLEMFG")["report_md_path"]
            self.assertIn("Corporate actions", Path(report).read_text(encoding="utf-8"))
        finally:
            ws.cleanup()

    def test_live_failure_does_not_fall_back_to_synthetic(self):
        ws = Workspace()
        try:
            ag = ResearchAgent(ws.settings(1), as_of=Workspace.as_of(1))
            with self.assertRaises(ResolutionError):
                ag.analyse_company("BEL")
            self.assertEqual(ag.store.companies(), [])  # nothing saved
        finally:
            ws.cleanup()

    def test_master_failure_is_named_not_reported_as_unknown_company(self):
        from fortune_research.providers.base import Provider

        class DeadMaster(Provider):
            name = "nse"
            capabilities = frozenset(["master"])

            def securities_master(self):
                raise ProviderError("NSE master unavailable: network error")

        ws = Workspace()
        try:
            s = ws.settings(1, {"providers": {"master": ["nse", "local"]}})
            ag = ResearchAgent(s, as_of=Workspace.as_of(1))
            ag.registry.providers["nse"] = DeadMaster()
            with self.assertRaises(ResolutionError) as cm:
                ag.analyse_company("BEL")
            self.assertIn("securities masters failed to load", str(cm.exception))
            self.assertIn("NSE master unavailable", str(cm.exception))
        finally:
            ws.cleanup()

    def test_key_figures_carry_kind_and_evidence(self):
        ws = Workspace()
        try:
            rec = ResearchAgent(ws.settings(1), as_of=Workspace.as_of(1)).analyse_company("SAMPLEMFG", write=False)
            kinds = {k["key"]: k["kind"] for k in rec["key_figures"]}
            self.assertEqual(kinds["fy.revenue"], "reported")
            self.assertEqual(kinds["fy.roe"], "calculated")
            self.assertEqual(kinds["valuation.fair_value"], "estimate")
            self.assertTrue(all(k["source_ids"] for k in rec["key_figures"] if k["kind"] != "estimate"))
        finally:
            ws.cleanup()


if __name__ == "__main__":
    unittest.main()


class CLI(unittest.TestCase):
    def test_documents_and_verify_commands(self):
        from contextlib import redirect_stdout

        from fortune_research import cli
        ws = Workspace()
        try:
            s = ws.settings(1)
            root = Path(s.get("providers.local.roots")[0])
            ddir = root / "companies" / "SAMPLEMFG" / "documents"
            ddir.mkdir()
            (ddir / "q1.pdf").write_bytes(pdf_bytes([["(Rs. in crore)", "Revenue from operations 515.00 455.00"]]))
            (ddir / "documents.json").write_text(json.dumps([{"file": "q1.pdf", "url": "https://example.invalid/sample/q1.pdf",
                                                              "kind": "results", "period": "Q1FY27", "published": "2026-08-08"}]))
            cfg = ws.root / "s.toml"
            cfg.write_text('[general]\nsynthetic = true\ndatabase = "%s"\nreports_dir = "%s"\ndata_dir = "%s"\n'
                           '[providers.local]\nroots = ["%s"]\n[portfolio]\nholdings_files = []\n'
                           % (ws.root / "c.db", ws.root / "rep", ws.root, root), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(cli.main(["--config", str(cfg), "--as-of", "2026-10-20", "documents", "SAMPLEMFG", "--find",
                                           "Revenue from operations"]), 0)
                self.assertEqual(cli.main(["--config", str(cfg), "--as-of", "2026-10-20", "analyse", "SAMPLEMFG"]), 0)
                self.assertEqual(cli.main(["--config", str(cfg), "verify", "SAMPLEMFG"]), 0)
            out = buf.getvalue()
            self.assertIn("p.1", out)
            self.assertIn("[515.0, 455.0]", out)
            self.assertIn("INR crore", out)
            sheet = next((ws.root / "verification").glob("SAMPLEMFG_record*.csv"))
            self.assertGreater(len(sheet.read_text().splitlines()), 10)
            md = next((ws.root / "rep").glob("SAMPLEMFG_*.md")).read_text(encoding="utf-8")
            self.assertIn("### Company documents", md)
        finally:
            ws.cleanup()
