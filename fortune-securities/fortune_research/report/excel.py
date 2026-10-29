"""Excel (.xlsx) export via openpyxl. Values are written as numbers (not text)
so they can be re-used in formulas; every sheet that holds data carries a
source-reference column pointing at the Sources sheet."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEAD = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="1F3864")
WARN = PatternFill("solid", fgColor="FCE4D6")


def _sheet(wb, title, headers, rows, widths=None):
    ws = wb.create_sheet(title[:31])
    ws.append(headers)
    for c in ws[1]:
        c.font, c.fill = HEAD, FILL
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([_cell(x) for x in r])
    ws.freeze_panes = "A2"
    for i, h in enumerate(headers, start=1):
        w = (widths or {}).get(h) or min(60, max(10, len(str(h)) + 2, *[len(str(r[i - 1])) + 2 for r in rows[:200] if i - 1 < len(r)] or [10]))
        ws.column_dimensions[get_column_letter(i)].width = w
    return ws


def _cell(x):
    if x is None:
        return None
    if isinstance(x, (int, float, str)):
        return x
    return str(x)


def _refs(order, ids):
    return " ".join("[%d]" % order[i] for i in sorted(set(ids or []), key=lambda i: order.get(i, 0)) if i in order)


def write_company(rec: dict, path: Path) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    order = {s["id"]: i + 1 for i, s in enumerate(rec["sources"])}
    c, s = rec["company"], rec["summary"]
    fv = s.get("fair_value") or {}
    rows = [["Company", c["name"]], ["NSE symbol", c["nse_symbol"]], ["BSE code", c["bse_code"]], ["ISIN", c["isin"]],
            ["Sector", c["sector"]], ["Analysis date", rec["as_of"]], ["Generated", rec["created_at"]], ["Record id", rec.get("id")],
            ["SYNTHETIC DATA", "YES - not a real company" if rec.get("synthetic") else "no"],
            ["Fundamentals", s["fundamentals"]], ["Governance", s["governance"]], ["Valuation position", s["valuation_position"]],
            ["Price", s["price"]], ["Fair value low", fv.get("low")], ["Fair value mid", fv.get("mid")], ["Fair value high", fv.get("high")],
            ["Trend", s["trend"]], ["Risk level", rec["risk"]["level"]], ["Confidence", s["confidence"]],
            ["Change since previous", (rec.get("comparison") or {}).get("headline", "first analysis")]]
    ws = _sheet(wb, "Summary", ["Field", "Value"], rows, {"Field": 24, "Value": 70})
    if rec.get("synthetic"):
        ws["B10"].fill = WARN
    for tab, data in (("Annual", rec["annual"]), ("Quarterly", rec["quarterly"])):
        if not data:
            continue
        labels = list(data.keys())
        names = list(next(iter(data.values())).keys())
        out = []
        for nme in names:
            row = [nme, (data[labels[-1]].get(nme) or {}).get("unit", "")]
            ids = []
            for l in labels:
                m = data[l].get(nme) or {}
                row.append(m.get("value"))
                ids += m.get("source_ids", [])
            row += [(data[labels[-1]].get(nme) or {}).get("formula", ""), _refs(order, ids)]
            out.append(row)
        _sheet(wb, tab, ["Metric", "Unit"] + labels + ["Formula", "Sources"], out, {"Formula": 45, "Sources": 30})
    _sheet(wb, "Metrics", ["Key", "Value", "Unit", "Period", "Formula", "Missing inputs", "Note", "Sources"],
           [[k, m["value"], m["unit"], m["period"], m["formula"], ", ".join(m["missing"]), m.get("note", ""), _refs(order, m["source_ids"])]
            for k, m in rec["metrics"].items()])
    v = rec["valuation"]
    _sheet(wb, "Valuation", ["Method", "Low", "Mid", "High", "Basis"],
           [[k, x["low"], x["mid"], x["high"], x["note"]] for k, x in v["implied"].items()] + [["not run: " + m, None, None, None, why] for m, why in v["skipped"]])
    if v["peers"]:
        cols = ["symbol", "name", "price", "price_date", "market_cap", "pe", "pb", "ev_ebitda", "ev_sales", "roe", "roce", "revenue_growth",
                "ebitda_margin", "debt_to_equity", "latest_fy"]
        _sheet(wb, "Peers", cols + ["sources"], [[p.get(k) for k in cols] + [_refs(order, p["source_ids"])] for p in v["peers"]])
    if v.get("dcf"):
        d = v["dcf"]
        _sheet(wb, "DCF", ["Year", "Growth", "Revenue (cr)", "FCFF (cr)"], [[p["year"], p["growth"], p["revenue"], p["fcff"]] for p in d["path"]]
               + [[], ["WACC", d["wacc"]], ["Terminal growth", d["terminal_growth"]], ["Value per share", d["per_share"]],
                  ["TV share of EV", d["terminal_value_share_of_ev"]], []] + [["Sensitivity " + k, x] for k, x in d["sensitivity"].items()])
    _sheet(wb, "Findings", ["Module", "Severity", "Code", "Finding", "Sources"],
           [[f["module"], f["severity"], f["code"], f["message"], _refs(order, f["source_ids"])] for f in rec["findings"]], {"Finding": 90})
    _sheet(wb, "Shareholding", ["Quarter", "Promoter %", "Pledged % of promoter", "FII %", "DII %", "Public %", "Source"],
           [[x["quarter"], x["promoter_pct"], x["promoter_pledged_pct"], x["fii_pct"], x["dii_pct"], x["public_pct"], _refs(order, [x["source_id"]])]
            for x in rec["shareholding"]])
    t = rec["technical"]
    _sheet(wb, "Technical", ["Indicator", "Value"], [[k, x] for k, x in t["values"].items()]
           + [["support", ", ".join(str(a) for a, _ in t["support"])], ["resistance", ", ".join(str(a) for a, _ in t["resistance"])]]
           + [["signal", x] for x in t["signals"]] + [["insufficient", x] for x in t["insufficient"]])
    _sheet(wb, "Risk", ["Scenario", "Price", "Change %", "Basis"], [[k, x["price"], x["change_pct"], x["basis"]] for k, x in rec["risk"]["scenarios"].items()])
    _sheet(wb, "Conditions", ["Id", "Condition", "Key", "Op", "Threshold"], [[x["id"], x["text"], x["key"], x["op"], x["threshold"]] for x in rec["conditions"]])
    _sheet(wb, "News", ["Date", "Source", "Category", "Materiality", "Subject", "New", "URL"],
           [[i["date"], i["exchange"], i["category"], i["materiality"], i["subject"], "yes" if i["new"] else "", i["url"]] for i in rec["news"]["items"]])
    cmp_ = rec.get("comparison")
    if cmp_:
        _sheet(wb, "Changes", ["Type", "Item", "Previous", "Current", "Detail"],
               [["metric", x["metric"], x["previous"], x["current"], "%s -> %s" % (x["previous_period"], x["current_period"])] for x in cmp_["metric_changes"]]
               + [["condition", x["text"], None, x["value"], x["status"]] for x in cmp_["conditions"]]
               + [["new flag", f["code"], None, f["severity"], f["message"]] for f in cmp_["findings_new"]]
               + [["cleared flag", f["code"], f["severity"], None, f["message"]] for f in cmp_["findings_cleared"]]
               + [["summary", x["field"], str(x["previous"]), str(x["current"]), ""] for x in cmp_["summary_changes"]])
    _sheet(wb, "Assumptions", ["Assumption", "Value", "Source"], [[a["name"], a["value"] if isinstance(a["value"], (int, float)) else str(a["value"]), a["source"]]
                                                                  for a in rec["assumptions"]])
    _sheet(wb, "Data quality", ["Severity", "Code", "Dataset", "Issue"], [[i["severity"], i["code"], i["dataset"], i["message"]] for i in rec["data_issues"]],
           {"Issue": 100})
    _sheet(wb, "Sources", ["Ref", "Title", "Publisher", "Official", "Synthetic", "Published", "Period", "Retrieved", "Provider", "URL", "Note"],
           [[i + 1, x["title"], x["publisher"], "yes" if x["official"] else "NO", "YES" if x.get("synthetic") else "", x.get("published"), x.get("period"),
             x["retrieved_at"], x["provider"], x["url"], x.get("note", "")] for i, x in enumerate(rec["sources"])])
    wb.save(path)
    return path


def write_portfolio(rep: dict, path: Path) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    v = rep["view"]
    t = v["total"]
    _sheet(wb, "Summary", ["Measure", "Value"], [["As of", rep["as_of"]], ["SYNTHETIC DATA", "YES" if rep.get("synthetic") else "no"],
                                                 ["Market value (INR)", t["market_value"]], ["Cost (INR)", t["cost_value"]],
                                                 ["Unrealised P&L (INR)", t["unrealised_pnl"]], ["XIRR", t["xirr"]], ["Benchmark XIRR", t["benchmark_xirr"]],
                                                 ["Excess XIRR", t["excess_xirr"]], ["Top 1 weight", v["concentration"]["top1"]],
                                                 ["Top 5 weight", v["concentration"]["top5"]], ["HHI", v["concentration"]["hhi"]],
                                                 ["Effective positions", v["concentration"]["effective_positions"]], ["Unpriced positions", len(v["unpriced"])]])
    cols = ["account_masked", "symbol", "name", "isin", "sector", "quantity", "avg_cost", "last_price", "price_date", "price_official", "price_stale",
            "market_value", "cost_value", "unrealised_pnl", "unrealised_pct", "weight", "weight_in_account", "recon_status"]
    _sheet(wb, "Positions", cols, [[r.get(k) if not isinstance(r.get(k), bool) else ("yes" if r[k] else "no") for k in cols] for r in v["positions"]])
    _sheet(wb, "Accounts", ["Account", "Market value", "Cost", "Unrealised P&L", "Share of total", "Positions", "XIRR", "Benchmark XIRR", "Note"],
           [[a, x["market_value"], x["cost_value"], x["unrealised_pnl"], x["share_of_total"], x["positions"], x["xirr"], x["benchmark_xirr"],
             x["performance_note"]] for a, x in v["accounts"].items()])
    _sheet(wb, "Sectors", ["Sector", "Weight"], [[k, w] for k, w in v["sectors"].items()])
    _sheet(wb, "Unpriced", ["Account", "Symbol", "Quantity", "Reason"], [[u["account"], u["symbol"], u["quantity"], u["reason"]] for u in v["unpriced"]])
    if rep.get("holdings_metrics"):
        hc = ["symbol", "name", "sector", "price", "price_date", "market_cap", "pe", "pb", "ev_ebitda", "roe", "roce", "revenue_growth", "debt_to_equity", "latest_fy"]
        _sheet(wb, "Fundamentals", hc, [[h.get(k) for k in hc] for h in rep["holdings_metrics"]])
    _sheet(wb, "Validation", ["Severity", "Code", "Issue"], [[i["severity"], i["code"], i["message"]] for i in rep["issues"]], {"Issue": 110})
    _sheet(wb, "Files", ["Path", "Kind", "Rows", "SHA-256"], [[f["path"], f["kind"], f.get("rows"), f["sha256"]] for f in rep["files"]])
    wb.save(path)
    return path
