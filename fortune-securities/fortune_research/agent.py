"""Research agent orchestrator.

    agent = ResearchAgent(Settings.load())
    agent.analyse_company("SAMPLEMFG")      # "Analyse [company]"
    agent.analyse_portfolio()               # "Analyse my portfolio"
    agent.what_changed("SAMPLEMFG")         # "What has changed?"
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from . import __version__
from .analysis import corporate_actions as ca_mod
from .analysis import financials as fin_mod
from .analysis import lookahead
from .analysis import forensic as forensic_mod
from .analysis import news as news_mod
from .analysis import portfolio as port_mod
from .analysis import quality
from .analysis import risk as risk_mod
from .analysis import technical as tech_mod
from .analysis import valuation as val_mod
from .analysis.calc import given
from .config import Settings
from .identity import Resolution, check_profile, resolve
from .memory.diff import compare
from .memory.store import Store
from .models import DataIssue, Metric, PriceSeries, Source, fy_label, now_ist
from .portfolio import reader, reconcile
from .providers.registry import Registry


class ResolutionError(Exception):
    def __init__(self, res: Resolution, master_failures: list = ()):
        self.resolution = res
        self.master_failures = list(master_failures)
        if res.status == "not_found" and master_failures:
            msg = ("'%s' could not be resolved because securities masters failed to load (%s). Nothing was analysed; "
                   "run `health --symbol %s` for details." % (res.query, "; ".join(master_failures), res.query))
            super().__init__(msg)
            return
        if res.status == "ambiguous":
            msg = "'%s' matches several securities: %s. Use the NSE symbol, BSE code or ISIN." % (
                res.query, "; ".join("%s (%s, %s)" % (c.name, c.display_symbol, c.isin) for c in res.candidates))
        else:
            msg = "'%s' was not found in the securities master. Check the symbol, or add the company to a master file." % res.query
        super().__init__(msg)


@dataclass
class Bundle:
    """Everything fetched for one security, with provenance."""
    security: object
    resolution: Resolution
    profile: Optional[dict]
    facts: list
    series: Optional[PriceSeries]
    shareholding: list = field(default_factory=list)
    governance: Optional[dict] = None
    announcements: list = field(default_factory=list)
    news: list = field(default_factory=list)
    providers: dict = field(default_factory=dict)
    full: bool = False
    corporate_actions: list = field(default_factory=list)
    documents: list = field(default_factory=list)
    issues: list = field(default_factory=list)  # DataIssues raised while assembling the bundle


class ResearchAgent:
    def __init__(self, settings: Settings, as_of: Optional[dt.date] = None, store: Optional[Store] = None,
                 registry: Optional[Registry] = None):
        self.settings = settings
        self.as_of = as_of or now_ist().date()
        self.store = store or Store(settings.path("general.database"))
        self.registry = registry or Registry(settings, on_fetch=lambda e: self.store.log_fetch(e))
        self._master = None
        self._bundles = {}

    # -- data access ----------------------------------------------------------------
    @property
    def master(self) -> list:
        if self._master is None:
            self._master = self.registry.fetch_all("master")
        return self._master

    def resolve(self, query: str) -> Resolution:
        res = resolve(query, self.master)
        if res.status != "resolved":
            failures = ["%s: %s" % (p, msg[:120]) for cap, p, msg in self.registry.errors if cap == "master"]
            raise ResolutionError(res, failures)
        return res

    def bundle(self, query: str, full: bool = True) -> Bundle:
        res = self.resolve(query)
        sec = res.security
        if sec.key in self._bundles and (self._bundles[sec.key].full or not full):
            return self._bundles[sec.key]
        reg = self.registry
        prov = {}
        profile, prov["profile"] = reg.fetch("profile", sec)
        check_profile(sec, profile, res)
        facts, prov["financials"] = reg.fetch("financials", sec)
        series, prov["prices"] = reg.fetch("prices", sec, None, self.as_of)
        if series:
            series.bars = [b for b in series.bars if b.date <= self.as_of]
        b = Bundle(sec, res, profile, facts or [], series, providers=prov, full=full)
        # point-in-time: nothing published after the analysis date (see analysis/lookahead.py)
        b.facts, la_issues, _ = lookahead.filter_facts(b.facts, self.as_of)
        b.issues += la_issues
        acts, prov["corporate_actions"] = reg.fetch("corporate_actions", sec)
        b.corporate_actions = [a for a in (acts or []) if a.ex_date <= self.as_of]
        if b.corporate_actions:
            if prov["corporate_actions"] == "yahoo":
                b.issues.append(DataIssue("warning", "ca_unofficial", "split/bonus history from Yahoo (unofficial): confirm against "
                                          "the exchange corporate-action record", "corporate_actions"))
            b.facts, ca_issues = ca_mod.adjust_per_share(b.facts, b.corporate_actions, self.as_of)
            b.issues += ca_issues + ca_mod.adjust_prices(b.series, b.corporate_actions, self.as_of)
        if full:
            sh, prov["shareholding"] = reg.fetch("shareholding", sec)
            b.shareholding, sh_issues = lookahead.filter_shareholding(sh or [], self.as_of)
            b.issues += sh_issues
            b.governance, prov["governance"] = reg.fetch("governance", sec)
            since = self.as_of - dt.timedelta(days=365)
            b.announcements = [a for a in reg.fetch_all("announcements", sec, since) if a.date <= self.as_of]
            b.news = [a for a in reg.fetch_all("news", sec, since) if a.date <= self.as_of]
            docs, prov["documents"] = reg.fetch("documents", sec, profile=profile)
            b.documents = [d for d in (docs or []) if not d.published or d.published[:10] <= self.as_of.isoformat()]
            for d in b.documents:
                if d.error:
                    b.issues.append(DataIssue("warning", "document_unreadable", "%s: %s" % (d.title, d.error), "documents"))
        self._bundles[sec.key] = b
        return b

    def benchmark(self) -> Optional[PriceSeries]:
        name = self.settings.get("portfolio.benchmark", "NIFTY50")
        s, _ = self.registry.fetch("benchmark", name, None, self.as_of)
        if s:
            s.bars = [b for b in s.bars if b.date <= self.as_of]
        return s

    def _shares(self, facts: list) -> Optional[Metric]:
        sh = sorted((f for f in facts if f.name == "shares_outstanding" and f.value), key=lambda f: f.period_end)
        if not sh:
            return None
        f = sh[-1]
        return given("shares_outstanding", f.period_end.isoformat(), f.value, "shares", "reported", [f.source.id])

    def _price(self, series: Optional[PriceSeries]) -> Optional[Metric]:
        if not series or not series.last:
            return None
        return given("price", series.last.date.isoformat(), series.last.close, "INR", "last close", [series.source.id],
                     "" if series.source.official else "unofficial price source")

    def quick_profile(self, query: str) -> Optional[dict]:
        """Headline metrics for a peer or holding (same calculations as the main analysis)."""
        try:
            b = self.bundle(query, full=False)
        except ResolutionError:
            return None
        fa = fin_mod.analyse(b.facts)
        price, shares = self._price(b.series), self._shares(b.facts)
        mm = val_mod.market_multiples(price, shares, fa) if fa.fy_periods else {}
        v = lambda m: m.value if m is not None else None  # noqa: E731
        return {"symbol": b.security.display_symbol, "name": b.security.name, "isin": b.security.isin,
                "sector": (b.profile or {}).get("sector"), "price": v(price),
                "price_date": b.series.last.date.isoformat() if b.series and b.series.last else None,
                "market_cap": v(mm.get("market_cap")), "pe": v(mm.get("pe")), "pb": v(mm.get("pb")),
                "ev_ebitda": v(mm.get("ev_ebitda")), "ev_sales": v(mm.get("ev_sales")),
                "roe": v(fa.fy("roe")), "roce": v(fa.fy("roce")), "revenue_growth": v(fa.fy("revenue_growth")),
                "ebitda_margin": v(fa.ttm.get("ebitda_margin")), "debt_to_equity": v(fa.fy("debt_to_equity")),
                "latest_fy": fa.latest_fy, "synthetic": b.security.synthetic,
                "source_ids": sorted({f.source.id for f in b.facts} | ({b.series.source.id} if b.series else set())),
                "_sources": [f.source for f in b.facts] + ([b.series.source] if b.series else [])}

    # -- portfolio --------------------------------------------------------------------
    def load_portfolio(self, save: bool = False) -> Optional[dict]:
        s = self.settings
        hf, tf, nf = s.paths("portfolio.holdings_files"), s.paths("portfolio.transaction_files"), s.paths("portfolio.research_note_files")
        if not any(p.exists() for p in hf):
            return None
        imp = reader.import_all(hf, tf, nf)
        imp.transactions = [t for t in imp.transactions if t.date <= self.as_of]
        rec = reconcile.reconcile(imp.holdings, imp.transactions)
        if save:
            self.store.save_portfolio_import(imp.files, imp.holdings, imp.transactions, imp.issues + rec.issues, rec.status)
            if imp.notes:
                self.store.add_notes(imp.notes)
        return {"import": imp, "reconciliation": rec}

    def _pricing(self, symbol, isin):
        for q in (isin, symbol):
            if not q:
                continue
            try:
                b = self.bundle(q, full=False)
            except ResolutionError:
                continue
            return {"security": b.security, "series": b.series, "profile": b.profile}
        return None

    def portfolio_view(self, loaded: dict) -> dict:
        imp, rec = loaded["import"], loaded["reconciliation"]
        s = self.settings
        return port_mod.analyse(imp.holdings, rec, self._pricing, self.as_of, self.benchmark(), imp.transactions,
                                s.get("portfolio.mask_account_ids", True), s.get("portfolio.max_single_stock_weight", 0.15),
                                s.get("portfolio.max_sector_weight", 0.35), s.get("staleness.prices", 5))

    def analyse_portfolio(self, write: bool = True) -> dict:
        from .report import excel, markdown
        loaded = self.load_portfolio(save=True)
        if not loaded:
            raise FileNotFoundError("no holdings file found; set [portfolio] holdings_files in config/settings.toml")
        view = self.portfolio_view(loaded)
        imp, rec = loaded["import"], loaded["reconciliation"]
        holdings_metrics = []
        for sym in view["by_symbol"]:
            qp = self.quick_profile(sym)
            if qp:
                holdings_metrics.append({k: v for k, v in qp.items() if not k.startswith("_")})
        out = {"created_at": now_ist().isoformat(), "as_of": self.as_of.isoformat(), "agent_version": __version__,
               "settings_origin": self.settings.origin, "view": view, "files": imp.files,
               "issues": [i.to_dict() for i in imp.issues + rec.issues],
               "reconciliation": {"matched": rec.matched, "status": {"%s|%s" % (port_mod.mask(k[0], self.settings.get("portfolio.mask_account_ids", True)), k[1]): v
                                                                     for k, v in rec.status.items()}},
               "holdings_metrics": holdings_metrics, "synthetic": view["synthetic"] or self.settings.synthetic,
               "transactions": len(imp.transactions), "notes_imported": len(imp.notes),
               "benchmark": self.settings.get("portfolio.benchmark", "benchmark")}
        if write:
            d = self.settings.path("general.reports_dir")
            d.mkdir(parents=True, exist_ok=True)
            stem = "portfolio_%s" % self.as_of.isoformat()
            out["report_md_path"] = str(markdown.write_portfolio(out, d / (stem + ".md")))
            out["report_xlsx_path"] = str(excel.write_portfolio(out, d / (stem + ".xlsx")))
        summary = {"total": view["total"], "concentration": view["concentration"], "sectors": view["sectors"],
                   "breaches": view["breaches"], "issues": len(out["issues"])}
        out["id"] = self.store.save_portfolio_report(self.as_of.isoformat(), summary, out.get("report_md_path"), out.get("report_xlsx_path"))
        return out

    # -- company --------------------------------------------------------------------
    def analyse_company(self, query: str, write: bool = True, position_value_cr: Optional[float] = None) -> dict:
        from .report import excel, markdown
        s = self.settings
        b = self.bundle(query)
        sec, res, prof = b.security, b.resolution, b.profile or {}
        issues: list = list(b.issues)
        for where, msg in self.registry.local.issues:
            issues.append(DataIssue("warning", "rejected_row", "%s: %s" % (where, msg), "input"))
        self.registry.local.issues.clear()
        for cap, pname, msg in self.registry.errors:
            issues.append(DataIssue("warning", "provider_error", "%s via %s failed: %s" % (cap, pname, msg), cap))
        self.registry.errors.clear()
        # financials
        fa = fin_mod.analyse(b.facts, s.get("analysis.prefer_basis", "consolidated"))
        issues += quality.check_facts(b.facts, fa.basis)
        if not b.facts:
            issues.append(DataIssue("error", "no_financials", "no financial statements available", "financials"))
        # prices / technical
        issues += quality.check_prices(b.series)
        bench = self.benchmark()
        tcfg = s.get("technical", {})
        ta = tech_mod.analyse(b.series, bench, tuple(tcfg.get("sma_windows", (20, 50, 200))), tcfg.get("rsi_period", 14),
                              tuple(tcfg.get("macd", (12, 26, 9))), tcfg.get("pivot_window", 5), tcfg.get("min_bars", 30))
        # staleness
        latest = {
            "prices": b.series.last.date if b.series and b.series.last else None,
            "quarterly_results": fa.q_periods[-1] if fa.q_periods else None,
            "annual_results": fa.fy_periods[-1] if fa.fy_periods else None,
            "shareholding": b.shareholding[-1].quarter_end if b.shareholding else None,
        }
        st_issues, ages = quality.staleness(self.as_of, s.get("staleness", {}), latest)
        issues += st_issues
        # forensic
        forensic = forensic_mod.analyse(fa, b.shareholding, b.governance)
        # news (governance disclosures feed the forensic findings)
        seen = self.store.seen_fingerprints(sec.key)
        nw = news_mod.analyse(b.announcements, b.news, seen)
        forensic += news_mod.governance_findings(nw["items"], self.as_of)
        if not b.announcements:
            issues.append(DataIssue("warning", "no_announcements", "no exchange announcements retrieved for the last 12 months",
                                    "announcements"))
        # peers
        peers, peer_sources = [], []
        for p in prof.get("peers", []) or []:
            qp = self.quick_profile(p)
            if qp is None:
                issues.append(DataIssue("warning", "peer_not_found", "peer %s not found in the securities master" % p, "peers"))
                continue
            if qp["price_date"] and (self.as_of - dt.date.fromisoformat(qp["price_date"])).days > s.get("staleness.prices", 5):
                issues.append(DataIssue("warning", "peer_stale", "peer %s price is from %s" % (p, qp["price_date"]), "peers"))
            peer_sources += qp.pop("_sources")
            peers.append(qp)
        # valuation
        price, shares = self._price(b.series), self._shares(b.facts)
        if shares is None:
            issues.append(DataIssue("error", "no_shares", "shares outstanding not available: market cap and per-share values not computed",
                                    "financials"))
        vr = val_mod.analyse(price, shares, fa, peers, sec.sector, sec.industry, ta.values.get("beta_1y"), s.get("valuation", {}))
        # portfolio context
        port, fit, holdings_cmp, pos_value = None, None, [], position_value_cr
        loaded = self.load_portfolio()
        if loaded:
            port = self.portfolio_view(loaded)
            fit = port_mod.fit({"symbol": sec.display_symbol, "isin": sec.isin, "sector": sec.sector, "series": b.series}, port)
            if pos_value is None and fit["already_held"]:
                pos_value = sum(r["market_value"] for r in port["positions"] if r["symbol"] == sec.display_symbol) / 1e7
            for sym in port["by_symbol"]:
                if sym == sec.display_symbol:
                    continue
                qp = self.quick_profile(sym)
                if qp:
                    qp.pop("_sources")
                    holdings_cmp.append(qp)
        # risk
        rr = risk_mod.analyse(fa, ta, vr, forensic, s.get("risk", {}), pos_value)
        state = risk_mod.state_snapshot(fa, ta, b.shareholding, b.governance, price.value if price else None)
        conditions = risk_mod.build_conditions(state, ta)
        # sources
        srcs = {}
        for src in ([f.source for f in b.facts] + ([b.series.source] if b.series else []) + ([bench.source] if bench else [])
                    + [r.source for r in b.shareholding] + [a.source for a in b.announcements + b.news] + list(res.sources)
                    + peer_sources):
            srcs.setdefault(src.id, src)
        for rec_ in ((b.governance or {}).get("fiscal_years") or {}).values():
            if rec_.get("_source"):
                srcs.setdefault(rec_["_source"].id, rec_["_source"])
        for a in b.corporate_actions:
            srcs.setdefault(a.source.id, a.source)
        doc_rows = []
        for d in b.documents:
            ds = Source(url=d.url, title=d.title, publisher=d.publisher, official=d.official, provider="documents",
                        retrieved_at=now_ist().isoformat(), published=d.published, period=d.period, synthetic=sec.synthetic,
                        locator="sha256 %s" % d.sha256[:16])
            srcs.setdefault(ds.id, ds)
            doc_rows.append({**d.summary(), "source_id": ds.id})
        issues += quality.check_sources(srcs.values())
        # assemble
        metrics = {k: m.to_dict() for k, m in fa.flat().items()}
        for k, m in vr.multiples.items():
            if m is not None:
                metrics["val." + k] = m.to_dict()
        for k, v in ta.values.items():
            metrics["tech." + k] = Metric(k, v, "", ta.as_of or "", "technical", [ta.source_id] if ta.source_id else []).to_dict()
        if b.shareholding:
            last = b.shareholding[-1]
            for k in ("promoter_pct", "promoter_pledged_pct", "fii_pct", "dii_pct", "public_pct"):
                metrics["own." + k] = Metric(k, getattr(last, k), "%", fy_label(last.quarter_end, "Q"), "shareholding pattern",
                                             [last.source.id], [] if getattr(last, k) is not None else [k], kind="reported").to_dict()
        findings = [f.to_dict() for f in forensic + rr.findings]
        key_figures = self._key_figures(metrics, vr, rr)
        ver = self.store.verification_summary(sec.key)
        if sec.synthetic:
            ver["status"] = "not applicable (synthetic sample data)"
        elif ver["mismatched"]:
            ver["status"] = "MISMATCHES FOUND"
            issues.append(DataIssue("error", "verification_mismatch", "%d extracted figures did not match the original document when "
                                    "checked by hand (see the verifications table)" % ver["mismatched"], "verification"))
        elif ver["checked"]:
            ver["status"] = "%d figures checked against original documents, all matched" % ver["checked"]
        else:
            ver["status"] = "UNVERIFIED: no figure has yet been checked against the original documents"
        summary = self._summary(fa, vr, ta, rr, forensic, issues, ages, sec)
        summary["independent_verification"] = ver["status"]
        rec = {
            "created_at": now_ist().isoformat(), "as_of": self.as_of.isoformat(), "agent_version": __version__,
            "settings_origin": s.origin, "synthetic": sec.synthetic or s.synthetic,
            "company": {"key": sec.key, "name": sec.name, "isin": sec.isin, "nse_symbol": sec.nse_symbol, "bse_code": sec.bse_code,
                        "series": sec.series, "sector": sec.sector, "industry": sec.industry, "synthetic": sec.synthetic,
                        "yahoo_symbols": [x for x in (sec.yahoo_symbol("NSE"), sec.yahoo_symbol("BSE")) if x],
                        "verification": sec.verification, "warnings": res.warnings, "query": query,
                        "description": prof.get("description", "")},
            "providers_used": {k: v for k, v in b.providers.items() if v},
            "data_as_of": {k: (v.isoformat() if v else None) for k, v in latest.items()}, "data_ages": ages,
            "periods": [fy_label(p, "FY") for p in fa.fy_periods] + [fy_label(p, "Q") for p in fa.q_periods],
            "basis": fa.basis, "financial_notes": fa.notes,
            "annual": {lab: {k: m.to_dict() for k, m in row.items()} for lab, row in fa.annual.items()},
            "quarterly": {lab: {k: m.to_dict() for k, m in row.items()} for lab, row in fa.quarterly.items()},
            "growth": {k: m.to_dict() for k, m in fa.growth.items()},
            "metrics": metrics, "findings": findings,
            "valuation": {"price": vr.price, "price_date": price.period if price else None, "peer_stats": vr.peer_stats,
                          "implied": vr.implied, "fair_value": vr.fair_value, "position": vr.position, "skipped": vr.skipped,
                          "dcf": ({k: v for k, v in vr.dcf.items() if k != "path"} | {"path": vr.dcf["path"]}) if vr.dcf else None,
                          "peers": peers, "is_financial": val_mod.is_financial(sec.sector, sec.industry)},
            "technical": {"as_of": ta.as_of, "bars": ta.bars, "source_id": ta.source_id, "last_close": ta.last_close, "values": ta.values,
                          "support": ta.support, "resistance": ta.resistance, "signals": ta.signals, "insufficient": ta.insufficient,
                          "benchmark": self.settings.get("portfolio.benchmark") if bench else None},
            "risk": {"level": rr.level, "scenarios": rr.scenarios, "liquidity": rr.liquidity},
            "conditions": conditions, "state": state, "news": nw,
            "corporate_actions": [{"ex_date": a.ex_date.isoformat(), "kind": a.kind, "factor": a.factor, "description": a.description,
                                   "official": a.source.official, "source_id": a.source.id} for a in b.corporate_actions],
            "documents": doc_rows,
            "shareholding": [{"quarter": fy_label(r.quarter_end, "Q"), "quarter_end": r.quarter_end.isoformat(),
                              "promoter_pct": r.promoter_pct, "promoter_pledged_pct": r.promoter_pledged_pct, "fii_pct": r.fii_pct,
                              "dii_pct": r.dii_pct, "public_pct": r.public_pct, "source_id": r.source.id} for r in b.shareholding],
            "portfolio_fit": fit, "holdings_comparison": holdings_cmp,
            "portfolio_summary": ({"total_value": port["total"]["market_value"], "positions": port["total"]["positions"],
                                   "sectors": port["sectors"]} if port else None),
            "assumptions": [a.to_dict() for a in vr.assumptions] + [
                {"name": "adv_participation", "value": s.get("risk.adv_participation", 0.10), "source": "settings [risk]"},
                {"name": "bear_eps_decline", "value": s.get("risk.bear_eps_decline", 0.20), "source": "settings [risk]"}],
            "data_issues": [i.to_dict() for i in issues],
            "sources": [x.to_dict() for x in srcs.values()],
            "research_notes": self.store.notes_for(sec.display_symbol),
            "summary": summary, "confidence": summary["confidence"], "key_figures": key_figures, "verification": ver,
        }
        prev = self.store.latest_analysis(sec.key)
        rec["comparison"] = compare(prev, rec) if prev else None
        aid = self.store.save_analysis(rec)
        rec["id"] = aid
        if write:
            d = self.settings.path("general.reports_dir")
            d.mkdir(parents=True, exist_ok=True)
            stem = "%s_%s_%d" % (sec.display_symbol.replace(":", "_"), self.as_of.isoformat(), aid)
            rec["report_md_path"] = str(markdown.write_company(rec, d / (stem + ".md")))
            rec["report_xlsx_path"] = str(excel.write_company(rec, d / (stem + ".xlsx")))
            self.store.set_report_paths(aid, rec["report_md_path"], rec["report_xlsx_path"])
        return rec

    def what_changed(self, query: Optional[str] = None, refresh: bool = True, write: bool = True) -> dict:
        """Compare the latest verified findings with the previous saved analysis.

        refresh=True re-runs the analysis on current data (the new run is saved and
        compared with the previous one). refresh=False compares the two most recent
        saved analyses without fetching anything."""
        if query is None:
            cos = [c for c in self.store.companies() if c["n_analyses"]]
            if not cos:
                raise LookupError("no saved analyses yet: run 'analyse <company>' first")
            query = cos[0]["isin"] or cos[0]["nse_symbol"] or cos[0]["bse_code"]
        if refresh:
            rec = self.analyse_company(query, write=write)
            if rec["comparison"] is None:
                return {"company": rec["company"], "comparison": None, "message": "first analysis of this company: nothing to compare yet",
                        "record": rec}
            return {"company": rec["company"], "comparison": rec["comparison"], "record": rec}
        c = self.store.find_company(query)
        if not c:
            raise LookupError("no saved analyses for %s" % query)
        cur = self.store.latest_analysis(c["key"])
        prev = self.store.latest_analysis(c["key"], before_id=cur["_id"]) if cur else None
        if not prev:
            return {"company": cur["company"] if cur else c, "comparison": None, "message": "only one saved analysis: nothing to compare"}
        return {"company": cur["company"], "comparison": compare(prev, cur), "record": cur}

    @staticmethod
    def _key_figures(metrics: dict, vr, rr) -> list:
        """The figures a reader acts on, each with its kind, formula and evidence."""
        rows = []
        for key, label in (("ttm.revenue", "Revenue, TTM"), ("ttm.pat", "Net profit (PAT), TTM"), ("ttm.eps", "EPS, TTM"),
                           ("ttm.ebitda_margin", "EBITDA margin, TTM"), ("fy.revenue", "Revenue, latest FY"),
                           ("fy.pat", "PAT, latest FY"), ("fy.roe", "ROE, latest FY"), ("fy.roce", "ROCE, latest FY"),
                           ("fy.debt_to_equity", "Debt / equity, latest FY"), ("fy.cfo", "Cash from operations, latest FY"),
                           ("val.price", "Share price"), ("val.market_cap", "Market capitalisation"), ("val.pe", "P/E (TTM)"),
                           ("val.ev_ebitda", "EV / EBITDA (TTM)"), ("own.promoter_pct", "Promoter holding"),
                           ("own.promoter_pledged_pct", "Promoter shares pledged")):
            m = metrics.get(key)
            if m is None:
                continue
            rows.append({"label": label, "key": key, "value": m["value"], "unit": m["unit"], "period": m["period"],
                         "kind": m.get("kind", "calculated"), "formula": m["formula"], "source_ids": m["source_ids"],
                         "missing": m["missing"], "note": m.get("note", "")})
        if vr.fair_value:
            rows.append({"label": "Model fair value (mid)", "key": "valuation.fair_value", "value": vr.fair_value["mid"], "unit": "INR",
                         "period": "current", "kind": "estimate", "formula": "median of %s" % ", ".join(vr.fair_value["methods"]),
                         "source_ids": [], "missing": [], "note": "depends on the assumptions listed"})
        bear = rr.scenarios.get("bear")
        if bear:
            rows.append({"label": "Bear-case price", "key": "risk.bear", "value": bear["price"], "unit": "INR", "period": "scenario",
                         "kind": "estimate", "formula": bear["basis"], "source_ids": [], "missing": [], "note": ""})
        return rows

    # -- summary ----------------------------------------------------------------------
    @staticmethod
    def _summary(fa, vr, ta, rr, forensic, issues, ages, sec) -> dict:
        v = lambda m: m.value if m is not None else None  # noqa: E731
        checks = []
        roce = v(fa.fy("roce"))
        if roce is not None:
            checks.append(roce >= 15)
        g = fa.growth.get("revenue_cagr_3y")
        if g is not None and g.value is not None:
            checks.append(g.value >= 10)
        cp = [v(fa.fy("cfo_to_pat", i)) for i in range(3)]
        if None not in cp:
            checks.append(sum(cp) / 3 >= 0.8)
        de = v(fa.fy("debt_to_equity"))
        if de is not None:
            checks.append(de <= 0.5)
        m0, m1 = v(fa.fy("ebitda_margin")), v(fa.fy("ebitda_margin", 1))
        if m0 is not None and m1 is not None:
            checks.append(m0 >= m1)
        if len(checks) < 3:
            fundamentals = "insufficient data"
        else:
            score = sum(checks) / len(checks)
            fundamentals = "strong" if score >= 0.8 else "moderate" if score >= 0.4 else "weak"
        sev = [f.severity for f in forensic]
        governance = ("serious flags" if ("critical" in sev or "high" in sev) else
                      "flags to investigate" if "medium" in sev else "no material flags found in the data reviewed")
        s200, s50, last = ta.values.get("sma_200"), ta.values.get("sma_50"), ta.last_close
        if None in (s200, s50, last):
            trend = "insufficient history"
        elif last > s200 and s50 > s200:
            trend = "uptrend"
        elif last < s200 and s50 < s200:
            trend = "downtrend"
        else:
            trend = "mixed"
        errors = sum(1 for i in issues if i.severity == "error")
        stale = [i.dataset for i in issues if i.code in ("stale", "missing") and i.dataset in ("prices", "quarterly_results", "annual_results")]
        warnings = sum(1 for i in issues if i.severity == "warning")
        if errors or not fa.fy_periods or ta.last_close is None:
            conf = "low"
        elif stale or warnings > 3:
            conf = "medium"
        else:
            conf = "high"
        return {"fundamentals": fundamentals, "fundamental_checks_passed": "%d/%d" % (sum(checks), len(checks)),
                "governance": governance, "valuation_position": vr.position or "not determined", "fair_value": vr.fair_value,
                "price": vr.price, "trend": trend, "risk_level": rr.level, "confidence": conf,
                "data_errors": errors, "stale_core_datasets": stale, "synthetic": sec.synthetic}
