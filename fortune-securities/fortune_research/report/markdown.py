"""Markdown research reports with numbered citations.

Every table row and finding that rests on data cites its sources as [n], and
the numbered source list at the end gives URL, publisher, official or not,
publication date, period and retrieval time.
"""

from __future__ import annotations

from pathlib import Path

DISCLAIMER = ("Research tooling output, not investment advice. It reports filed and supplied data, the arithmetic done on it, "
              "and model estimates under the stated assumptions. Verify material figures against the original filings before acting. "
              "This system does not and cannot place orders.")
SYNTHETIC_BANNER = ("> **SYNTHETIC SAMPLE DATA.** This report was built from fictional test data. The company, prices and "
                    "filings are not real, and nothing in it describes a real security.")


def n(x, d=2, pct=False, unit=""):
    if x is None:
        return "n/a"
    if isinstance(x, (int, float)):
        s = "{:,.{d}f}".format(x, d=d)
        return s + ("%" if pct else "") + ((" " + unit) if unit else "")
    return str(x)


class Cite:
    def __init__(self, sources: list):
        self.order = {s["id"]: i + 1 for i, s in enumerate(sources)}

    def __call__(self, ids) -> str:
        nums = sorted({self.order[i] for i in (ids or []) if i in self.order})
        if not nums:
            return ""
        if len(nums) > 6:
            return "[%d-%d]" % (nums[0], nums[-1]) if nums == list(range(nums[0], nums[-1] + 1)) else "[" + "][".join(map(str, nums[:6])) + "][...]"
        return "".join("[%d]" % x for x in nums)


def _table(headers: list, rows: list) -> list:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/") for c in r) + " |")
    return out


ANNUAL_ROWS = [("Revenue (INR cr)", "revenue", 1), ("Revenue growth", "revenue_growth", "%"), ("EBITDA (INR cr)", "ebitda", 1),
               ("EBITDA margin", "ebitda_margin", "%"), ("PAT (INR cr)", "pat", 1), ("PAT margin", "pat_margin", "%"),
               ("EPS (INR)", "eps", 1), ("EPS growth", "eps_growth", "%"), ("ROE", "roe", "%"), ("ROCE", "roce", "%"),
               ("Debt / equity (x)", "debt_to_equity", 1), ("Net debt (INR cr)", "net_debt", 1), ("Interest coverage (x)", "interest_coverage", 1),
               ("CFO (INR cr)", "cfo", 1), ("FCF (INR cr)", "fcf", 1), ("CFO / PAT (x)", "cfo_to_pat", 1),
               ("Receivable days", "receivable_days", 0), ("Inventory days", "inventory_days", 0), ("Payable days", "payable_days", 0),
               ("Cash conversion cycle (days)", "cash_conversion_cycle", 0), ("Current ratio (x)", "current_ratio", 1)]
QUARTER_ROWS = [("Revenue (INR cr)", "revenue", 1), ("Revenue YoY", "revenue_yoy", "%"), ("Revenue QoQ", "revenue_qoq", "%"),
                ("EBITDA margin", "ebitda_margin", "%"), ("PAT (INR cr)", "pat", 1), ("PAT YoY", "pat_yoy", "%"), ("EPS (INR)", "eps", 1)]


def _fmt_metric(m: dict, kind) -> str:
    if not m:
        return "n/a"
    if m["value"] is None:
        return "n/a"
    if kind == "%":
        return n(m["value"], 1, pct=True)
    return n(m["value"], kind if isinstance(kind, int) and kind != 1 else 2)


def _period_table(data: dict, rows: list, cite: Cite, max_cols: int) -> list:
    labels = list(data.keys())[-max_cols:]
    out = _table(["Metric"] + labels, [[name] + [_fmt_metric(data[l].get(key), kind) for l in labels] for name, key, kind in rows])
    ids = []
    for l in labels:
        for _, key, _ in rows:
            ids += (data[l].get(key) or {}).get("source_ids", [])
    out.append("")
    out.append("Sources: %s. Basis and formulas: see the Method notes section." % (cite(ids) or "none"))
    return out


def write_company(rec: dict, path: Path) -> Path:
    path.write_text(render_company(rec), encoding="utf-8")
    return path


def render_company(rec: dict) -> str:
    c, s, v, t, r = rec["company"], rec["summary"], rec["valuation"], rec["technical"], rec["risk"]
    cite = Cite(rec["sources"])
    L = []
    codes = " | ".join(x for x in (("NSE: %s" % c["nse_symbol"]) if c["nse_symbol"] else "", ("BSE: %s" % c["bse_code"]) if c["bse_code"] else "",
                                   ("ISIN: %s" % c["isin"]) if c["isin"] else "") if x)
    L += ["# %s (%s)" % (c["name"], codes), "", "**FORTUNE SECURITIES Equity Research** | analysis date %s | generated %s | agent v%s | record #%s"
          % (rec["as_of"], rec["created_at"], rec["agent_version"], rec.get("id", "-")), ""]
    if rec.get("synthetic"):
        L += [SYNTHETIC_BANNER, ""]
    # 1 summary
    L += ["## 1. Summary", ""]
    fv = s.get("fair_value")
    L += _table(["Dimension", "Assessment"], [
        ["Fundamentals", "%s (%s checks passed: ROCE >= 15%%, 3y revenue CAGR >= 10%%, 3y CFO/PAT >= 0.8, D/E <= 0.5, margin not falling)"
         % (s["fundamentals"], s["fundamental_checks_passed"])],
        ["Governance / forensic", s["governance"]],
        ["Valuation", "price %s vs model range %s-%s (mid %s): %s" % (n(s["price"]), n(fv["low"]) if fv else "n/a", n(fv["high"]) if fv else "n/a",
                                                                       n(fv["mid"]) if fv else "n/a", s["valuation_position"].replace("_", " "))],
        ["Price trend", s["trend"]], ["Risk level", r["level"]],
        ["Data confidence", "%s (%d data errors; stale core data: %s)" % (s["confidence"], s["data_errors"], ", ".join(s["stale_core_datasets"]) or "none")],
    ])
    cmp_ = rec.get("comparison")
    L += ["", "**Since the previous analysis:** %s" % (cmp_["headline"] if cmp_ else "first analysis of this company.")]
    top = [f for f in rec["findings"] if f["severity"] in ("critical", "high", "medium")]
    if top:
        L += ["", "Key flags:"] + ["- **%s** %s %s" % (f["severity"].upper(), f["message"], cite(f["source_ids"])) for f in top[:8]]
    L += [""]
    # 2 identity
    L += ["## 2. Company identity and verification", ""]
    L += ["- Name: %s; sector: %s; industry: %s; NSE series: %s" % (c["name"], c["sector"] or "n/a", c["industry"] or "n/a", c["series"] or "n/a")]
    if c.get("description"):
        L += ["- Business: %s" % c["description"]]
    L += ["- Checks passed: %s" % ("; ".join(c["verification"]) or "none")]
    for w in c["warnings"]:
        L += ["- Warning: %s" % w]
    if c["yahoo_symbols"]:
        L += ["- Yahoo Finance tickers (unofficial price source only): %s" % ", ".join(c["yahoo_symbols"])]
    L += ["- Data providers used: %s" % ", ".join("%s=%s" % kv for kv in rec["providers_used"].items()), ""]
    L += _table(["Dataset", "Newest data", "Age (days)"], [[k.replace("_", " "), rec["data_as_of"][k] or "missing",
                                                           n(rec["data_ages"].get(k), 0)] for k in rec["data_as_of"]])
    L += [""]
    # 3 financials
    L += ["## 3. Financial performance (%s, INR crore unless stated)" % rec["basis"], ""]
    if rec["annual"]:
        L += ["### Annual", ""] + _period_table(rec["annual"], ANNUAL_ROWS, cite, 5) + [""]
    else:
        L += ["No annual statements available.", ""]
    if rec["growth"]:
        L += _table(["Growth", "Period", "Value"], [[k.replace("_", " "), m["period"], _fmt_metric(m, "%")] for k, m in rec["growth"].items()]) + [""]
    if rec["quarterly"]:
        L += ["### Quarterly", ""] + _period_table(rec["quarterly"], QUARTER_ROWS, cite, 6) + [""]
    ttm = {k[4:]: m for k, m in rec["metrics"].items() if k.startswith("ttm.")}
    if ttm:
        L += ["TTM (%s): revenue %s cr, EBITDA %s cr, PAT %s cr, EPS INR %s %s" % (
            ttm.get("revenue", {}).get("period", ""), n(ttm.get("revenue", {}).get("value")), n(ttm.get("ebitda", {}).get("value")),
            n(ttm.get("pat", {}).get("value")), n(ttm.get("eps", {}).get("value")), cite(ttm.get("revenue", {}).get("source_ids"))), ""]
    for note in rec["financial_notes"]:
        L += ["- Note: %s" % note]
    # 4 forensic
    L += ["## 4. Governance and forensic review", ""]
    fz = [f for f in rec["findings"] if f["module"] == "forensic"]
    L += _table(["Severity", "Finding", "Evidence"], [[f["severity"], f["message"], cite(f["source_ids"]) or "-"] for f in fz]) if fz else ["No findings."]
    if rec["shareholding"]:
        L += ["", "Shareholding pattern (%):", ""]
        L += _table(["Quarter", "Promoter", "Pledged (of promoter)", "FII", "DII", "Public", "Source"],
                    [[x["quarter"], n(x["promoter_pct"]), n(x["promoter_pledged_pct"]), n(x["fii_pct"]), n(x["dii_pct"]), n(x["public_pct"]),
                      cite([x["source_id"]])] for x in rec["shareholding"][-6:]])
    L += ["", "Flags are prompts for investigation drawn from the data shown, not findings of wrongdoing.", ""]
    # 5 valuation
    L += ["## 5. Valuation", ""]
    mm = {k[4:]: m for k, m in rec["metrics"].items() if k.startswith("val.")}
    L += _table(["Multiple", "Value", "Basis", "Sources"], [[k.replace("_", " "), n(m["value"]), m["formula"], cite(m["source_ids"])]
                                                            for k, m in mm.items() if k not in ("roe",)])
    if v["peers"]:
        L += ["", "Peers (same calculations, latest data available):", ""]
        L += _table(["Peer", "Price date", "Mkt cap (cr)", "P/E", "P/B", "EV/EBITDA", "ROE %", "ROCE %", "Rev growth %", "Sources"],
                    [[p["symbol"], p["price_date"] or "n/a", n(p["market_cap"], 0), n(p["pe"], 1), n(p["pb"], 1), n(p["ev_ebitda"], 1), n(p["roe"], 1),
                      n(p["roce"], 1), n(p["revenue_growth"], 1), cite(p["source_ids"])] for p in v["peers"]])
        if v["peer_stats"]:
            L += [""] + _table(["Peer multiple", "25th pct", "Median", "75th pct", "n"],
                               [[k, n(x["p25"], 1), n(x["median"], 1), n(x["p75"], 1), x["n"]] for k, x in v["peer_stats"].items()])
    if v["implied"]:
        L += ["", "Implied value per share (INR):", ""]
        L += _table(["Method", "Low", "Mid", "High", "Basis"], [[k, n(x["low"]), n(x["mid"]), n(x["high"]), x["note"]] for k, x in v["implied"].items()])
    if v.get("dcf"):
        d = v["dcf"]
        L += ["", "DCF: WACC %s, terminal growth %s, value per share INR %s; terminal value is %s of EV (a high share means the result "
              "rests mostly on the terminal assumptions)." % (n(d["wacc"] * 100, 2, True), n(d["terminal_growth"] * 100, 2, True), n(d["per_share"]),
                                                              n(d["terminal_value_share_of_ev"] * 100, 0, True)), ""]
        L += _table(["WACC / g", "Value per share"], [[k.replace("|", " / "), n(x)] for k, x in d["sensitivity"].items()])
    for m, why in v["skipped"]:
        L += ["- Not run: %s (%s)" % (m, why)]
    L += ["", "Model values depend on the assumptions in section 11 and are not price targets.", ""]
    # 6 technical
    L += ["## 6. Technical picture (as of %s, %s bars)" % (t["as_of"], t["bars"]), ""]
    tv = t["values"]
    if tv:
        keys = [("Last close", t["last_close"]), ("SMA 20", tv.get("sma_20")), ("SMA 50", tv.get("sma_50")), ("SMA 200", tv.get("sma_200")),
                ("RSI 14", tv.get("rsi_14")), ("MACD / signal / hist", "%s / %s / %s" % (n(tv.get("macd")), n(tv.get("macd_signal")), n(tv.get("macd_hist")))),
                ("52w high / low", "%s / %s" % (n(tv.get("high_52w")), n(tv.get("low_52w")))), ("From 52w high", n(tv.get("pct_from_52w_high"), 1, True)),
                ("Avg traded value 20d (INR cr)", tv.get("avg_traded_value_20d_cr")), ("Volatility (ann.)", n((tv.get("volatility_ann") or 0) * 100, 1, True) if tv.get("volatility_ann") is not None else "n/a"),
                ("Max drawdown 1y", n((tv.get("max_drawdown_1y") or 0) * 100, 1, True) if tv.get("max_drawdown_1y") is not None else "n/a"),
                ("Return 1m / 6m / 1y", "%s / %s / %s" % (n(tv.get("return_1m"), 1, True), n(tv.get("return_6m"), 1, True), n(tv.get("return_1y"), 1, True))),
                ("Beta 1y vs %s" % (t.get("benchmark") or "benchmark"), tv.get("beta_1y"))]
        L += _table(["Indicator", "Value"], [[k, n(x) if not isinstance(x, str) else x] for k, x in keys])
        L += ["", "Support: %s" % (", ".join("%s (%d touches)" % (lv, k) for lv, k in t["support"]) or "none identified"),
              "Resistance: %s" % (", ".join("%s (%d touches)" % (lv, k) for lv, k in t["resistance"]) or "none identified"), ""]
        L += ["- %s" % x for x in t["signals"]]
    for x in t["insufficient"]:
        L += ["- Insufficient data: %s" % x]
    L += ["", "Price source: %s. Indicators describe past prices; they are not forecasts." % (cite([t.get("source_id")]) or "n/a"), ""]
    # 7 risk
    L += ["## 7. Risk", "", "Overall risk level: **%s**" % r["level"], ""]
    rz = [f for f in rec["findings"] if f["module"] == "risk"]
    if rz:
        L += _table(["Severity", "Risk", "Evidence"], [[f["severity"], f["message"], cite(f["source_ids"]) or "-"] for f in rz]) + [""]
    if r["scenarios"]:
        L += _table(["Scenario", "Price (INR)", "Change", "Basis"], [[k, n(x["price"]), n(x["change_pct"], 1, True), x["basis"]] for k, x in r["scenarios"].items()]) + [""]
    liq = r["liquidity"]
    if liq.get("days_to_exit") is not None:
        L += ["Position of INR %s would take ~%s trading days to exit at %s of average traded value." % (n(liq["position_value_cr"] * 1e7, 0), n(liq["days_to_exit"], 2), n(liq["participation"] * 100, 0, True)), ""]
    L += ["Thesis-invalidation conditions (re-tested on the next analysis):", ""]
    L += ["- %s" % x["text"] for x in rec["conditions"]] or ["- none could be set from the available data"]
    L += [""]
    # 8 news
    L += ["## 8. Announcements and news (last 12 months)", ""]
    items = rec["news"]["items"]
    if items:
        L += _table(["Date", "Source", "Category", "Materiality", "Subject", "New?", "Ref"],
                    [[i["date"], i["exchange"], i["category"], i["materiality"], i["subject"][:110], "yes" if i["new"] else "", cite([i["source_id"]])]
                     for i in items[:25]])
        L += ["", "%d item(s), %d new since the previous analysis. Exchange filings are primary; publisher headlines are leads to verify." % (len(items), rec["news"]["new_count"])]
    else:
        L += ["No announcements retrieved."]
    L += [""]
    # 9 portfolio
    L += ["## 9. Fit with the current portfolio", ""]
    fit = rec.get("portfolio_fit")
    if fit:
        ps = rec["portfolio_summary"]
        L += ["- Already held: %s%s" % ("yes" if fit["already_held"] else "no",
                                        (" (%s of portfolio, accounts %s)" % (n(fit["held_weight"] * 100, 1, True), ", ".join(fit["held_accounts"]))) if fit["already_held"] else ""),
              "- Sector %s is %s of the priced portfolio now; same-sector holdings: %s" % (fit["sector"], n(fit["sector_weight_now"] * 100, 1, True), ", ".join(fit["same_sector_holdings"]) or "none"),
              "- Weighted average daily-return correlation with holdings (1y): %s" % n(fit["weighted_avg_correlation"]),
              "- Most correlated: %s" % (", ".join("%s %.2f" % (x["symbol"], x["correlation"]) for x in fit["correlations"]) or "n/a"),
              "- Portfolio priced value INR %s across %d positions" % (n(ps["total_value"], 0), ps["positions"]), ""]
        if rec["holdings_comparison"]:
            me = [p for p in [{"symbol": c["nse_symbol"] or c["bse_code"], "pe": mm.get("pe", {}).get("value"), "roe": rec["metrics"].get("fy.roe", {}).get("value"),
                               "roce": rec["metrics"].get("fy.roce", {}).get("value"), "revenue_growth": rec["metrics"].get("fy.revenue_growth", {}).get("value"),
                               "debt_to_equity": rec["metrics"].get("fy.debt_to_equity", {}).get("value"), "sector": c["sector"]}]]
            L += _table(["Company", "Sector", "P/E", "ROE %", "ROCE %", "Rev growth %", "D/E"],
                        [["**%s**" % me[0]["symbol"], me[0]["sector"] or "", n(me[0]["pe"], 1), n(me[0]["roe"], 1), n(me[0]["roce"], 1), n(me[0]["revenue_growth"], 1), n(me[0]["debt_to_equity"], 2)]]
                        + [[h["symbol"], h["sector"] or "", n(h["pe"], 1), n(h["roe"], 1), n(h["roce"], 1), n(h["revenue_growth"], 1), n(h["debt_to_equity"], 2)]
                           for h in rec["holdings_comparison"]])
            L += ["", "Holdings without financial data show n/a.", ""]
    else:
        L += ["No portfolio loaded (set [portfolio] holdings_files).", ""]
    if rec.get("research_notes"):
        L += ["Previous research notes on file:", ""] + ["- %s %s: %s (%s)" % (x["date"], x["author"], x["note"][:200], x["stance"]) for x in rec["research_notes"][:5]] + [""]
    # 10 changes
    L += ["## 10. Changes since the previous analysis", ""]
    if cmp_:
        L += render_comparison(cmp_, cite)
    else:
        L += ["First analysis of this company. Nothing to compare yet.", ""]
    # 11 assumptions
    L += ["## 11. Assumptions", ""]
    L += _table(["Assumption", "Value", "Source"], [[a["name"], a["value"], a["source"]] for a in rec["assumptions"]]) + [""]
    # 12 data quality
    L += ["## 12. Data quality and uncertainty", ""]
    di = rec["data_issues"]
    L += _table(["Severity", "Dataset", "Issue"], [[i["severity"], i["dataset"], i["message"]] for i in di]) if di else ["No data issues detected."]
    L += ["", "Method notes: EBITDA = revenue - operating expenses; EBIT = PBT + finance costs; ROE = PAT / average equity; ROCE = EBIT / "
          "average (equity + debt); FCF = CFO - capex; working-capital days use closing balances. TTM is the sum of the last four reported "
          "quarters when available. Missing inputs give n/a; nothing is estimated to fill a gap.", ""]
    # 13 sources
    L += ["## 13. Sources", ""]
    for i, src in enumerate(rec["sources"], start=1):
        L += ["%d. %s. %s. %s%s. Published %s; period %s; retrieved %s via %s. %s%s" % (
            i, src["title"], src["publisher"] or "publisher n/a", "official source" if src["official"] else "UNOFFICIAL source",
            " (SYNTHETIC)" if src.get("synthetic") else "", src.get("published") or "n/a", src.get("period") or "n/a", src["retrieved_at"],
            src["provider"], src["url"], (" (%s)" % src["note"]) if src.get("note") else "")]
    L += ["", "---", "", "_%s_" % DISCLAIMER, ""]
    return "\n".join(L)


def render_comparison(cmp_: dict, cite=None) -> list:
    cite = cite or (lambda ids: "")
    L = ["Compared with record #%s (analysis date %s): **%s**" % (cmp_["previous_id"], cmp_["previous_as_of"], cmp_["headline"]), ""]
    if cmp_["new_periods"]:
        L += ["- New reporting periods: %s" % ", ".join(cmp_["new_periods"])]
    for x in cmp_["summary_changes"]:
        L += ["- %s: %s -> %s" % (x["field"].replace("_", " "), x["previous"], x["current"])]
    if cmp_["metric_changes"]:
        L += ["", "Material metric moves:", ""]
        L += _table(["Metric", "Previous", "Current", "Unit", "Periods"], [[x["metric"], n(x["previous"]), n(x["current"]), x["unit"],
                                                                           "%s -> %s" % (x["previous_period"], x["current_period"])] for x in cmp_["metric_changes"]])
    if cmp_["conditions"]:
        L += ["", "Previous thesis-invalidation conditions, re-tested:", ""]
        L += _table(["Condition", "Status", "Current value"], [[x["text"], x["status"], n(x["value"])] for x in cmp_["conditions"]])
    for f in cmp_["findings_new"]:
        L += ["- New flag (%s): %s %s" % (f["severity"], f["message"], cite(f.get("source_ids")))]
    for f in cmp_["findings_cleared"]:
        L += ["- Cleared: %s" % f["message"]]
    for x in cmp_["severity_changes"]:
        L += ["- %s: %s" % (("Severity %s -> %s" % (x["previous"], x["current"])) if x["previous"] != x["current"] else "Updated", x["message"])]
    for a in cmp_["new_announcements"][:10]:
        L += ["- New announcement %s: %s (%s, %s)" % (a["date"], a["subject"], a["category"], a["materiality"])]
    L += [""]
    return L


def write_portfolio(rep: dict, path: Path) -> Path:
    path.write_text(render_portfolio(rep), encoding="utf-8")
    return path


def render_portfolio(rep: dict) -> str:
    v = rep["view"]
    L = ["# Portfolio report", "", "**FORTUNE SECURITIES** | as of %s | generated %s | agent v%s" % (rep["as_of"], rep["created_at"], rep["agent_version"]), ""]
    if rep.get("synthetic"):
        L += [SYNTHETIC_BANNER, ""]
    t, c = v["total"], v["concentration"]
    L += ["## 1. Summary", ""]
    L += _table(["Measure", "Value"], [
        ["Priced market value (INR)", n(t["market_value"], 0)], ["Cost of priced positions (INR)", n(t["cost_value"], 0)],
        ["Unrealised P&L (INR)", n(t["unrealised_pnl"], 0)], ["Positions priced / unpriced", "%d / %d" % (t["positions"], t["unpriced"])],
        ["XIRR (all accounts, from transactions)", n(t["xirr"] * 100 if t["xirr"] is not None else None, 2, True)],
        ["Benchmark XIRR, same cash flows (%s)" % rep.get("benchmark", "benchmark"), n(t["benchmark_xirr"] * 100 if t["benchmark_xirr"] is not None else None, 2, True)],
        ["Excess XIRR", n(t["excess_xirr"] * 100 if t["excess_xirr"] is not None else None, 2, True)],
        ["Largest position / top 5", "%s / %s" % (n((c["top1"] or 0) * 100, 1, True), n((c["top5"] or 0) * 100, 1, True))],
        ["HHI / effective number of positions", "%s / %s" % (n(c["hhi"], 3), n(c["effective_positions"], 1))],
    ])
    if t.get("performance_note"):
        L += ["", "Performance note: %s" % t["performance_note"].strip("; ")]
    L += ["", "## 2. Accounts", ""]
    L += _table(["Account", "Value (INR)", "Cost (INR)", "Unrealised P&L", "Share of total", "Positions", "XIRR", "Benchmark XIRR"],
                [[a, n(x["market_value"], 0), n(x["cost_value"], 0), n(x["unrealised_pnl"], 0), n((x["share_of_total"] or 0) * 100, 1, True), x["positions"],
                  n(x["xirr"] * 100 if x["xirr"] is not None else None, 2, True), n(x["benchmark_xirr"] * 100 if x["benchmark_xirr"] is not None else None, 2, True)]
                 for a, x in v["accounts"].items()])
    L += ["", "## 3. Positions", ""]
    L += _table(["Account", "Symbol", "Sector", "Qty", "Avg cost", "Last", "Price date", "Value (INR)", "P&L %", "Weight", "Reconciliation", "Notes"],
                [[r["account_masked"], r["symbol"], r["sector"], n(r["quantity"], 0), n(r["avg_cost"]), n(r["last_price"]), r["price_date"],
                  n(r["market_value"], 0), n(r["unrealised_pct"], 1, True), n(r["weight"] * 100, 1, True), r["recon_status"],
                  "; ".join(x for x in ("STALE PRICE" if r["price_stale"] else "", "unofficial price" if not r["price_official"] else "") if x)]
                 for r in sorted(v["positions"], key=lambda r: -r["market_value"])])
    if v["unpriced"]:
        L += ["", "Unpriced positions (excluded from weights, never valued at cost):", ""]
        L += ["- %s %s x%g: %s" % (u["account"], u["symbol"], u["quantity"], u["reason"]) for u in v["unpriced"]]
    L += ["", "## 4. Sector exposure", ""]
    L += _table(["Sector", "Weight"], [[k, n(w * 100, 1, True)] for k, w in v["sectors"].items()])
    if v["breaches"]:
        L += ["", "Limit breaches:", ""]
        L += ["- %s %s at %s (limit %s)" % (b["type"].replace("_", " "), b.get("symbol") or b.get("sector"), n(b["weight"] * 100, 1, True), n(b["limit"] * 100, 0, True))
              for b in v["breaches"]]
    if rep.get("holdings_metrics"):
        L += ["", "## 5. Holdings fundamentals (where data is available)", ""]
        L += _table(["Symbol", "Sector", "P/E", "P/B", "ROE %", "ROCE %", "Rev growth %", "D/E", "Latest FY"],
                    [[h["symbol"], h["sector"] or "", n(h["pe"], 1), n(h["pb"], 1), n(h["roe"], 1), n(h["roce"], 1), n(h["revenue_growth"], 1),
                      n(h["debt_to_equity"], 2), h["latest_fy"] or "n/a"] for h in rep["holdings_metrics"]])
    L += ["", "## 6. Data validation and reconciliation", ""]
    L += ["Files: " + "; ".join("%s (%s, %s rows, sha256 %s...)" % (Path(f["path"]).name, f["kind"], f.get("rows"), f["sha256"][:12]) for f in rep["files"]), ""]
    L += ["%d positions reconciled exactly against %d transactions." % (rep["reconciliation"]["matched"], rep["transactions"]), ""]
    L += _table(["Severity", "Issue"], [[i["severity"], i["message"]] for i in rep["issues"]]) if rep["issues"] else ["No validation issues."]
    L += ["", "---", "", "_%s_" % DISCLAIMER, ""]
    return "\n".join(L)
