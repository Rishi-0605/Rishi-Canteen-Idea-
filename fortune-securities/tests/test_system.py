"""Configuration, memory store, CLI parsing and safety properties."""

import os
import re
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, Workspace

from fortune_research import cli
from fortune_research.config import ConfigError, Settings, secret
from fortune_research.memory.diff import compare
from fortune_research.memory.store import Store


class Config(unittest.TestCase):
    def test_inline_credentials_refused(self):
        with self.assertRaises(ConfigError):
            Settings({"providers": {"vendor": {"api_key": "abc123"}}})
        Settings({"providers": {"vendor": {"api_key_env": "VENDOR_KEY"}}})  # naming an env var is fine

    def test_secret_from_env(self):
        os.environ["FORTUNE_TEST_KEY"] = "x"
        try:
            self.assertEqual(secret("FORTUNE_TEST_KEY"), "x")
        finally:
            del os.environ["FORTUNE_TEST_KEY"]
        self.assertIsNone(secret("FORTUNE_TEST_KEY"))

    def test_example_settings_leave_judgement_inputs_unset(self):
        s = Settings.load()
        self.assertIsNone(s.get("valuation.risk_free_rate"))
        self.assertIsNone(s.get("valuation.equity_risk_premium"))
        self.assertFalse(s.get("providers.yahoo.enabled"))


class Memory(unittest.TestCase):
    def rec(self, as_of, eps, findings):
        return {"created_at": as_of + "T10:00:00+05:30", "as_of": as_of, "company": {"key": "INEZ9M101010", "name": "S", "isin": "INEZ9M101010"},
                "metrics": {"ttm.eps": {"value": eps, "unit": "INR per share", "period": "p", "formula": "f", "source_ids": [], "missing": []}},
                "findings": findings, "conditions": [{"id": "c", "key": "ttm.eps", "op": "<", "threshold": 20, "text": "EPS below 20"}],
                "state": {"ttm.eps": eps}, "summary": {"risk_level": "low"}, "periods": ["FY26"], "news": {"items": []}, "sources": []}

    def test_append_only_and_compare(self):
        with tempfile.TemporaryDirectory() as d:
            st = Store(Path(d) / "r.db")
            f1 = [{"module": "risk", "code": "a", "severity": "medium", "message": "m", "evidence": {}, "source_ids": []}]
            a = st.save_analysis(self.rec("2026-10-01", 25.0, f1))
            b = st.save_analysis(self.rec("2026-10-29", 18.0, []))
            self.assertEqual((a, b), (1, 2))
            cur = st.latest_analysis("INEZ9M101010")
            prev = st.latest_analysis("INEZ9M101010", before_id=cur["_id"])
            self.assertEqual(prev["_id"], 1)
            d_ = compare(prev, cur)
            self.assertEqual(d_["metric_changes"][0]["metric"], "ttm.eps")
            self.assertEqual(d_["conditions"][0]["status"], "TRIGGERED")
            self.assertEqual([f["code"] for f in d_["findings_cleared"]], ["a"])
            self.assertEqual([h["value"] for h in st.metric_history("INEZ9M101010", "ttm.eps")], [25.0, 18.0])
            self.assertEqual(st.find_company("inez9m101010")["n_analyses"], 2)


class Commands(unittest.TestCase):
    def test_parse(self):
        p = cli.parse_command
        self.assertEqual(p("Analyse Infosys"), ("analyse", "Infosys"))
        self.assertEqual(p("analyze  RELIANCE."), ("analyse", "RELIANCE"))
        self.assertEqual(p("Analyse Mahindra & Mahindra"), ("analyse", "Mahindra & Mahindra"))
        self.assertEqual(p("Analyse my portfolio"), ("portfolio", None))
        self.assertEqual(p("What has changed?"), ("changes", None))
        self.assertEqual(p("What has changed for HDFCBANK?"), ("changes", "HDFCBANK"))
        with self.assertRaises(ValueError):
            p("buy 100 shares of INFY")

    def test_cli_end_to_end_with_config_file(self):
        ws = Workspace()
        try:
            s = ws.settings(1)
            cfg = ws.root / "s.toml"
            roots = s.get("providers.local.roots")[0]
            cfg.write_text('[general]\nsynthetic = true\ndatabase = "%s"\nreports_dir = "%s"\ndata_dir = "%s"\n'
                           '[providers.local]\nroots = ["%s"]\n[portfolio]\nholdings_files = []\n'
                           % (ws.root / "c.db", ws.root / "rep", ws.root, roots), encoding="utf-8")
            self.assertEqual(cli.main(["--config", str(cfg), "--as-of", "2026-10-20", "ask", "Analyse", "SAMPLEMFG"]), 0)
            self.assertEqual(cli.main(["--config", str(cfg), "ask", "Analyse sample peer"]), 2)  # ambiguous
            self.assertEqual(cli.main(["--config", str(cfg), "ask", "Analyse my portfolio"]), 1)  # no holdings file
            self.assertEqual(cli.main(["--config", str(cfg), "changes", "SAMPLEMFG", "--no-refresh"]), 0)
            for sec in sorted(cli.SECTIONS):
                self.assertEqual(cli.main(["--config", str(cfg), "show", "SAMPLEMFG", "--section", sec]), 0, sec)
            self.assertEqual(cli.main(["--config", str(cfg), "show", "NOTANALYSED"]), 1)
        finally:
            ws.cleanup()


class Safety(unittest.TestCase):
    """Properties the project promises: no order placement, no credential storage."""

    def code_files(self):
        return [p for p in (ROOT / "fortune_research").rglob("*.py")]

    def test_no_order_placement_or_broker_sdks(self):
        banned = re.compile(r"place_order|placeorder|kiteconnect|smartapi|upstox|dhanhq|alpaca|import\s+breeze|order_type|"
                            r"transaction_type\s*=\s*['\"]BUY", re.I)
        for p in self.code_files():
            self.assertIsNone(banned.search(p.read_text(encoding="utf-8")), p)

    def test_no_hardcoded_secrets(self):
        pat = re.compile(r"(api[_-]?key|secret|token|password)\s*=\s*['\"][A-Za-z0-9]{12,}['\"]", re.I)
        for p in self.code_files() + list((ROOT / "config").glob("*.toml")):
            self.assertIsNone(pat.search(p.read_text(encoding="utf-8")), p)

    def test_network_calls_only_in_provider_http(self):
        for p in self.code_files():
            text = p.read_text(encoding="utf-8")
            if p.name != "http.py":
                self.assertNotIn("requests.get", text, p)
                self.assertNotIn("urlopen", text, p)


if __name__ == "__main__":
    unittest.main()


class Skills(unittest.TestCase):
    MODULES = ["fortune-research", "fortune-portfolio-reader", "fortune-stock-researcher", "fortune-news-monitor",
               "fortune-financial-analyst", "fortune-forensic-analyst", "fortune-valuation-analyst", "fortune-technical-analyst",
               "fortune-portfolio-analyst", "fortune-risk-analyst", "fortune-research-memory", "fortune-report-generator"]

    def test_every_module_has_a_skill_with_the_safety_rules(self):
        d = ROOT.parent / ".claude" / "skills"
        self.assertEqual(sorted(p.name for p in d.iterdir() if (p / "SKILL.md").exists()), sorted(self.MODULES))
        for name in self.MODULES:
            text = (d / name / "SKILL.md").read_text(encoding="utf-8")
            m = re.match(r"^---\nname: (\S+)\ndescription: >-\n(.*?)\n---\n", text, re.S)
            self.assertIsNotNone(m, name)
            self.assertEqual(m.group(1), name)
            self.assertGreater(len(m.group(2)), 300, name)
            for rule in ("Never fabricate a number", "No orders, no trading credentials", "python3 -m fortune_research"):
                self.assertIn(rule, text, name)


class ProviderConfig(unittest.TestCase):
    def test_example_settings_only_list_providers_that_implement_the_capability(self):
        from fortune_research.providers import bse, ir, nse, rss, yahoo
        from fortune_research.providers.base import CAPABILITIES
        from fortune_research.providers.local_files import LocalFilesProvider
        caps = {"local": LocalFilesProvider.capabilities, "nse": nse.NSEProvider.capabilities, "bse": bse.BSEProvider.capabilities,
                "yahoo": yahoo.YahooProvider.capabilities, "rss": rss.RSSProvider.capabilities, "ir": ir.IRProvider.capabilities}
        s = Settings.load()
        for cap in CAPABILITIES:
            for name in s.get("providers.%s" % cap):
                self.assertIn(cap, caps[name], "%s listed for %s but does not implement it" % (name, cap))
