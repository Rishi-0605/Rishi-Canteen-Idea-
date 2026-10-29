"""Command line.

    python -m fortune_research ask "Analyse SAMPLEMFG"
    python -m fortune_research ask "Analyse my portfolio"
    python -m fortune_research ask "What has changed?"
    python -m fortune_research analyse SAMPLEMFG [--as-of 2026-10-20] [--json]
    python -m fortune_research portfolio
    python -m fortune_research changes [SYMBOL] [--no-refresh]
    python -m fortune_research import-portfolio            # validate + reconcile only
    python -m fortune_research resolve "sample manufacturing"
    python -m fortune_research history SAMPLEMFG
    python -m fortune_research show SAMPLEMFG --section forensic   # from the latest saved record
    python -m fortune_research health --symbol BEL [--only nse,bse] [--capture DIR] [--json]
    python -m fortune_research documents BEL [--find "Revenue from operations"]
    python -m fortune_research verify BEL [--record FILE.csv]
    python -m fortune_research providers [--check]
    python -m fortune_research sources [--limit 30]

Add --sample to any command to use the synthetic sample data and a separate
sample database (data/sample/), so tests never mix with your real research.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .agent import ResearchAgent, ResolutionError
from .config import ConfigError, Settings
from .models import parse_date


def parse_command(text: str) -> tuple:
    """Natural-language command -> (action, argument). Raises ValueError if not understood."""
    t = " ".join(text.strip().split()).rstrip("?.! ")
    low = t.lower()
    if re.fullmatch(r"(please )?(analy[sz]e|review|check) (my )?(whole )?portfolio", low):
        return "portfolio", None
    m = re.fullmatch(r"(please )?what (has|have|'s) changed( (for|in|with|on) (?P<q>.+))?", low)
    if m:
        q = m.group("q")
        return "changes", (t[m.start("q"):] if q else None)
    m = re.fullmatch(r"(please )?(analy[sz]e|research|investigate|look at) (?P<q>.+)", low)
    if m:
        return "analyse", t[m.start("q"):]
    raise ValueError("not understood: say 'Analyse <company or symbol>', 'Analyse my portfolio' or 'What has changed?'")


def _settings(args) -> Settings:
    return Settings.load(path=args.config, sample=args.sample)


def _agent(args) -> ResearchAgent:
    as_of = parse_date(args.as_of) if args.as_of else None
    return ResearchAgent(_settings(args), as_of=as_of)


SECTIONS = {
    "summary": ("summary", "company", "data_as_of"),
    "identity": ("company", "providers_used", "data_as_of", "data_ages"),
    "financials": ("basis", "annual", "quarterly", "growth", "financial_notes"),
    "forensic": ("findings", "shareholding"),
    "valuation": ("valuation", "assumptions"),
    "technical": ("technical",),
    "risk": ("risk", "conditions", "state", "findings"),
    "news": ("news",),
    "portfolio": ("portfolio_fit", "holdings_comparison", "portfolio_summary"),
    "comparison": ("comparison",),
    "sources": ("sources",),
    "quality": ("data_issues",),
}


def _section(rec: dict, name: str) -> dict:
    out = {k: rec.get(k) for k in SECTIONS[name]}
    if name in ("forensic", "risk"):
        out["findings"] = [f for f in rec["findings"] if f["module"] == ("forensic" if name == "forensic" else "risk")]
    if name == "financials":
        out["annual"] = {lab: {k: m["value"] for k, m in row.items()} for lab, row in rec["annual"].items()}
        out["quarterly"] = {lab: {k: m["value"] for k, m in row.items()} for lab, row in rec["quarterly"].items()}
    return out


def _print_company(rec: dict) -> None:
    s, c = rec["summary"], rec["company"]
    print("%s (%s)%s" % (c["name"], c["nse_symbol"] or c["bse_code"], "  [SYNTHETIC SAMPLE DATA]" if rec.get("synthetic") else ""))
    fv = s.get("fair_value")
    print("  fundamentals: %s | governance: %s | trend: %s | risk: %s | confidence: %s"
          % (s["fundamentals"], s["governance"], s["trend"], rec["risk"]["level"], s["confidence"]))
    if fv:
        print("  price %.2f vs model range %.2f - %.2f (mid %.2f): %s" % (s["price"], fv["low"], fv["high"], fv["mid"], s["valuation_position"]))
    for f in [f for f in rec["findings"] if f["severity"] in ("critical", "high", "medium")][:6]:
        print("  [%s] %s" % (f["severity"], f["message"]))
    if rec.get("comparison"):
        print("  since previous analysis: %s" % rec["comparison"]["headline"])
    errs = [i for i in rec["data_issues"] if i["severity"] == "error"]
    if errs:
        print("  data errors: %d (see the report's data-quality section)" % len(errs))
    if rec.get("report_md_path"):
        print("  report: %s\n  excel:  %s" % (rec["report_md_path"], rec["report_xlsx_path"]))


def _print_changes(out: dict) -> None:
    cmp_ = out.get("comparison")
    if not cmp_:
        print(out.get("message", "nothing to compare"))
        return
    from .report.markdown import render_comparison
    print("%s: %s" % (out["company"]["name"], cmp_["headline"]))
    print("\n".join(render_comparison(cmp_)))


def _print_portfolio(rep: dict) -> None:
    v = rep["view"]
    t = v["total"]
    print("Portfolio as of %s%s" % (rep["as_of"], "  [SYNTHETIC SAMPLE DATA]" if rep.get("synthetic") else ""))
    print("  priced value INR %s across %d positions (%d unpriced)" % ("{:,.0f}".format(t["market_value"]), t["positions"], t["unpriced"]))
    if t["xirr"] is not None:
        print("  XIRR %.2f%%%s" % (t["xirr"] * 100, (" vs benchmark %.2f%%" % (t["benchmark_xirr"] * 100)) if t["benchmark_xirr"] is not None else ""))
    for a, x in v["accounts"].items():
        print("  account %s: INR %s (%d positions)" % (a, "{:,.0f}".format(x["market_value"]), x["positions"]))
    for b in v["breaches"]:
        print("  limit breach: %s %s at %.1f%%" % (b["type"], b.get("symbol") or b.get("sector"), b["weight"] * 100))
    print("  validation issues: %d" % len(rep["issues"]))
    if rep.get("report_md_path"):
        print("  report: %s\n  excel:  %s" % (rep["report_md_path"], rep["report_xlsx_path"]))


def _health(args, agent) -> int:
    from . import health
    from .identity import resolve
    from .models import Security
    from .providers.registry import Registry
    reg = Registry(agent.settings, on_fetch=lambda e: agent.store.log_fetch(e, "health"))
    if args.capture:
        reg.http.capture_dir = Path(args.capture)
    master = reg.fetch_all("master")
    res = resolve(args.symbol, master) if master else None
    if res is not None and res.status == "resolved":
        sec = res.security
        note = "resolved via securities master"
    else:
        sec = Security(args.symbol, None, nse_symbol=args.symbol.upper())
        note = "NOT resolved via any master (%s): probing with the symbol as given" % (res.status if res else "no master available")
    profile, _ = reg.fetch("profile", sec)
    only = [x.strip() for x in args.only.split(",")] if args.only else None
    results = health.run(reg, sec, only=only, profile=profile, benchmark=agent.settings.get("portfolio.benchmark", "NIFTY50"))
    agent.store.save_health(args.symbol, results)
    if args.json:
        print(json.dumps({"target": sec.to_dict(), "resolution": note, "results": [r.to_dict() for r in results]}, default=str, indent=1))
    else:
        print("Target: %s (%s)" % (args.symbol, note))
        print(health.render(results, sec, agent.as_of))
        out = agent.settings.path("general.data_dir") / "health" / ("health_%s_%s.md" % (args.symbol, agent.as_of.isoformat()))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(health.render(results, sec, agent.as_of), encoding="utf-8")
        print("saved: %s" % out)
    return 0 if all(r.status in ("OPERATIONAL", "PARTIAL") for r in results if r.provider != "local") else 4


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fortune_research", description="FORTUNE SECURITIES Indian equity research agent")
    ap.add_argument("--sample", action="store_true", help="use the synthetic sample data and sample database")
    ap.add_argument("--config", help="settings TOML (default config/settings.toml if present)")
    ap.add_argument("--as-of", help="analysis date YYYY-MM-DD (default: today, IST)")
    ap.add_argument("--json", action="store_true", help="print the full JSON record")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ask")
    p.add_argument("text", nargs="+")
    p = sub.add_parser("analyse", aliases=["analyze"])
    p.add_argument("query", nargs="+")
    p.add_argument("--position-value-cr", type=float, help="intended position size (INR crore) for liquidity checks")
    sub.add_parser("portfolio")
    p = sub.add_parser("changes")
    p.add_argument("query", nargs="*")
    p.add_argument("--no-refresh", action="store_true", help="compare the two latest saved analyses without fetching")
    sub.add_parser("import-portfolio")
    p = sub.add_parser("resolve")
    p.add_argument("query", nargs="+")
    p = sub.add_parser("history")
    p.add_argument("query", nargs="+")
    p = sub.add_parser("health", help="check every enabled data source with a real retrieval for a test company")
    p.add_argument("--symbol", required=True, help="NSE symbol (or BSE code / ISIN) of the test company, e.g. BEL")
    p.add_argument("--only", help="comma-separated provider names")
    p.add_argument("--capture", help="save raw live responses (with URL, timestamp, sha256) into this folder as fixtures")
    p = sub.add_parser("documents", help="list company documents and locate a line item in them")
    p.add_argument("query", nargs="+")
    p.add_argument("--find", help="line-item text to locate, e.g. 'Revenue from operations'")
    p = sub.add_parser("verify", help="independent check of extracted figures against the original documents")
    p.add_argument("query", nargs="+")
    p.add_argument("--record", help="filled worksheet CSV to store")
    p = sub.add_parser("show", help="print one section of the latest saved analysis (no fetching)")
    p.add_argument("query", nargs="+")
    p.add_argument("--section", choices=sorted(SECTIONS), default="summary")
    p = sub.add_parser("providers")
    p.add_argument("--check", action="store_true", help="try each enabled network provider once")
    p = sub.add_parser("sources")
    p.add_argument("--limit", type=int, default=30)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "ask":
            action, q = parse_command(" ".join(args.text))
            args.cmd, args.query, args.no_refresh, args.position_value_cr = action, ([q] if q else []), False, None
        agent = _agent(args)
        if args.cmd in ("analyse", "analyze"):
            rec = agent.analyse_company(" ".join(args.query), position_value_cr=getattr(args, "position_value_cr", None))
            print(json.dumps(rec, default=str, indent=1)) if args.json else _print_company(rec)
        elif args.cmd == "portfolio":
            rep = agent.analyse_portfolio()
            print(json.dumps(rep, default=str, indent=1)) if args.json else _print_portfolio(rep)
        elif args.cmd == "changes":
            out = agent.what_changed(" ".join(args.query) or None, refresh=not args.no_refresh)
            print(json.dumps(out.get("comparison"), default=str, indent=1)) if args.json else _print_changes(out)
        elif args.cmd == "import-portfolio":
            loaded = agent.load_portfolio(save=True)
            if not loaded:
                print("no holdings file found (set [portfolio] holdings_files)")
                return 1
            imp, rec = loaded["import"], loaded["reconciliation"]
            print("imported %d holdings, %d transactions, %d notes from %d files; %d positions reconcile exactly"
                  % (len(imp.holdings), len(imp.transactions), len(imp.notes), len(imp.files), rec.matched))
            for i in imp.issues + rec.issues:
                print("  [%s] %s" % (i.severity, i.message))
        elif args.cmd == "resolve":
            res = agent.resolve(" ".join(args.query))
            sec = res.security
            print("%s | NSE %s | BSE %s | ISIN %s%s" % (sec.name, sec.nse_symbol, sec.bse_code, sec.isin, " | SYNTHETIC" if sec.synthetic else ""))
            for x in sec.verification:
                print("  ok: %s" % x)
            for w in res.warnings:
                print("  warning: %s" % w)
        elif args.cmd == "history":
            c = agent.store.find_company(" ".join(args.query))
            if not c:
                print("no saved analyses")
                return 1
            for a in agent.store.analyses_for(c["key"]):
                s = json.loads(a["summary_json"])
                print("#%d  %s  as of %s  %s / %s / risk %s  %s" % (a["id"], a["created_at"], a["as_of"], s["fundamentals"], s["valuation_position"],
                                                                 s["risk_level"], a["report_md_path"] or ""))
        elif args.cmd == "health":
            return _health(args, agent)
        elif args.cmd == "documents":
            b = agent.bundle(" ".join(args.query))
            if not b.documents:
                print("no documents: add PDFs under companies/<SYMBOL>/documents/ (with documents.json) or enable [providers.ir]")
                return 1
            from . import documents as D
            for d in b.documents:
                s = d.summary()
                print("%-13s %-50s period %-8s pages %-4s units %s %s" % (s["kind"], s["title"][:50], s["period"] or "n/a", s["pages"],
                                                                         ",".join(s["units_detected"]) or "not found", s["error"] or ""))
                print("              %s  sha256 %s" % (s["url"], s["sha256"][:16]))
                if args.find:
                    for h in D.locate(d, args.find):
                        print("    p.%-4s %-90s numbers=%s unit=%s [%s]" % (h["page"], h["line"][:90], h["numbers"], h["unit"], h["status"]))
        elif args.cmd == "verify":
            from . import verify as V
            c = agent.store.find_company(" ".join(args.query))
            if not c:
                print("no saved analyses for %s: run 'analyse' first" % " ".join(args.query), file=sys.stderr)
                return 1
            rec = agent.store.latest_analysis(c["key"])
            if args.record:
                rows, problems = V.read_worksheet(Path(args.record))
                for pr in problems:
                    print("  skipped %s" % pr)
                n = agent.store.save_verifications(c["key"], rec["_id"], rows)
                bad = [r for r in rows if not r["matches"]]
                print("recorded %d checked figures (%d mismatches)" % (n, len(bad)))
                for r in bad:
                    print("  MISMATCH %s %s: extracted %s, document %s (%s)" % (r["figure"], r["period"], r["extracted_value"], r["checked_value"], r["source_url"]))
                return 0 if not bad else 3
            out = agent.settings.path("general.data_dir") / "verification" / ("%s_record%d.csv" % (c["nse_symbol"] or c["bse_code"], rec["_id"]))
            V.write_worksheet(rec, out)
            print("worksheet with %d reported figures: %s" % (len(V.worksheet_rows(rec)), out))
            print("open each source_url, find the figure at `locator`, fill checked_value, checked_by, checked_on; then run:")
            print("  python -m fortune_research verify %s --record %s" % (" ".join(args.query), out))
        elif args.cmd == "show":
            c = agent.store.find_company(" ".join(args.query))
            if not c:
                print("no saved analyses for %s: run 'analyse' first" % " ".join(args.query), file=sys.stderr)
                return 1
            rec = agent.store.latest_analysis(c["key"])
            print("# record #%s, analysis date %s%s" % (rec["_id"], rec["as_of"], ", SYNTHETIC" if rec.get("synthetic") else ""))
            print(json.dumps(_section(rec, args.section), default=str, indent=1))
        elif args.cmd == "providers":
            for row in agent.registry.describe():
                print("%-6s official=%-5s serves=%s" % (row["provider"], row["official"], ",".join(row["serves"]) or "-"))
            if args.check:
                for name, p in agent.registry.providers.items():
                    if name == "local":
                        continue
                    try:
                        rows = p.securities_master() if "master" in p.capabilities else None
                        print("%s: ok%s" % (name, (" (%d securities)" % len(rows)) if rows is not None else ""))
                    except Exception as exc:  # report, don't crash
                        print("%s: FAILED %s" % (name, exc))
        elif args.cmd == "sources":
            for r in agent.store.source_log(args.limit):
                print("%s %-6s %s %s%s" % (r["ts"], r["provider"], r["status"], r["url"], " (cache)" if r["cache_hit"] else ""))
    except ResolutionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (ValueError, LookupError, FileNotFoundError, ConfigError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0
