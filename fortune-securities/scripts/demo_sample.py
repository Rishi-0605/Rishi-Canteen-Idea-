#!/usr/bin/env python3
"""Run the whole minimum workflow on the SYNTHETIC sample data, in a temp folder:

  1. import holdings   2. validate and reconcile   3. analyse one company
  4. cited report      5. save the record          6. re-analyse after new disclosures and compare

    python3 scripts/demo_sample.py [--keep DIR]

Nothing here touches data/ or your real research database.
"""

import argparse
import datetime as dt
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fortune_research.agent import ResearchAgent  # noqa: E402
from fortune_research.config import Settings  # noqa: E402
from fortune_research.report.markdown import render_comparison  # noqa: E402
from sample_data import stages  # noqa: E402


def settings(ws: Path, stage: int) -> Settings:
    data = stages.build(ws / ("stage%d" % stage), stage)
    out = ws / "out"
    return Settings.load(sample=True, overrides={
        "general": {"database": str(out / "research.db"), "reports_dir": str(out / "reports"), "data_dir": str(out)},
        "providers": {"local": {"roots": [str(data)]}},
        "portfolio": {"holdings_files": [str(data / "portfolio/holdings.csv"), str(data / "portfolio/holdings_broker2.xlsx")],
                      "transaction_files": [str(data / "portfolio/transactions.csv")],
                      "research_note_files": [str(data / "portfolio/research_notes.csv")]}})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", help="write into this folder instead of a temp folder")
    args = ap.parse_args()
    tmp = None if args.keep else tempfile.TemporaryDirectory(prefix="fortune-demo-")
    ws = Path(args.keep or tmp.name)
    ws.mkdir(parents=True, exist_ok=True)
    print("SYNTHETIC SAMPLE DATA: fictional companies, prices and filings.\n")

    a1 = ResearchAgent(settings(ws, 1), as_of=dt.date.fromisoformat(stages.STAGE_DATES[1]))
    loaded = a1.load_portfolio(save=True)
    imp, rec = loaded["import"], loaded["reconciliation"]
    print("1-2. imported %d holdings / %d transactions; %d positions reconcile exactly; %d issues:"
          % (len(imp.holdings), len(imp.transactions), rec.matched, len(imp.issues) + len(rec.issues)))
    for i in imp.issues + rec.issues:
        print("     [%s] %s" % (i.severity, i.message))
    port = a1.analyse_portfolio()
    print("     portfolio report: %s" % port["report_md_path"])

    r1 = a1.analyse_company("SAMPLEMFG")
    print("\n3-5. analysed %s as of %s -> record #%d" % (r1["company"]["name"], r1["as_of"], r1["id"]))
    print("     %s" % {k: r1["summary"][k] for k in ("fundamentals", "governance", "valuation_position", "trend", "risk_level", "confidence")})
    print("     report: %s\n     excel:  %s" % (r1["report_md_path"], r1["report_xlsx_path"]))

    a2 = ResearchAgent(settings(ws, 2), as_of=dt.date.fromisoformat(stages.STAGE_DATES[2]))
    out = a2.what_changed("SAMPLEMFG")
    print("\n6. what has changed (as of %s, record #%d):" % (out["record"]["as_of"], out["record"]["id"]))
    print("\n".join("   " + line for line in render_comparison(out["comparison"])))
    print("   report: %s" % out["record"]["report_md_path"])
    if tmp:
        print("\n(temp folder removed; use --keep DIR to keep the reports)")
        tmp.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
