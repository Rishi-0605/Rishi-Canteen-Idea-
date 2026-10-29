#!/usr/bin/env python3
"""Generate the SYNTHETIC sample dataset used by the tests and the demo.

Everything here is fictional: company names, ISINs (issuer codes Z9xx, which
do not follow the real NSDL scheme), BSE codes (99xxxx), prices, filings and
URLs (the reserved .invalid domain). Nothing describes a real security.

    python3 sample_data/generate.py          # rewrites sample_data/ in place

Two stages are written so "what has changed" can be demonstrated:
  stage 1  (analysis date 2026-10-20): the base files
  stage 2  (analysis date 2026-10-29): sample_data/updates/stage2/ holds rows
           appended on top (Q2FY27 results, Sep-2026 shareholding, a pledge
           disclosure, a CFO resignation, eight more trading days)
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from fortune_research.identity import isin_check_digit  # noqa: E402

RETRIEVED = "2026-10-20T18:00:00+05:30"
RETRIEVED2 = "2026-10-29T18:00:00+05:30"
STAGE1_END = dt.date(2026, 10, 20)
STAGE2_END = dt.date(2026, 10, 28)
PRICE_START = dt.date(2025, 7, 1)
BASE = "https://example.invalid/sample"


def isin(issuer: str) -> str:
    first = "INE" + issuer + "01" + "01"
    return first + str(isin_check_digit(first))


COMPANIES = {
    # symbol: name, issuer, bse, sector, industry, beta
    "SAMPLEMFG": ("Sample Manufacturing Limited", "Z9M1", "990001", "Capital Goods", "Industrial Machinery", 1.05),
    "SAMPLEPEERA": ("Sample Peer Alpha Limited", "Z9A1", "990002", "Capital Goods", "Industrial Machinery", 0.95),
    "SAMPLEPEERB": ("Sample Peer Beta Industries Limited", "Z9B1", "990003", "Capital Goods", "Industrial Machinery", 1.10),
    "SAMPLEPEERC": ("Sample Peer Gamma Engineering Limited", "Z9C1", "990004", "Capital Goods", "Industrial Machinery", 1.20),
    "SAMPLEBANK": ("Sample Bank Limited", "Z9K1", "990005", "Banks", "Private Sector Bank", 1.15),
    "SAMPLEIT": ("Sample Infotech Limited", "Z9T1", "990006", "Information Technology", "IT Services", 0.80),
    "SAMPLEFMCG": ("Sample Consumer Products Limited", "Z9F1", "990007", "FMCG", "Personal Care", 0.60),
    "SAMPLEPHARMA": ("Sample Pharmaceuticals Limited", "Z9P1", "990008", "Healthcare", "Pharmaceuticals", 0.70),
    "SAMPLENODATA": ("Sample No Data Limited", "Z9N1", "990009", "Unclassified", "", 1.0),
}
# last close at stage-1 end (chosen so multiples are plausible)
TARGET = {"SAMPLEMFG": 690.0, "SAMPLEPEERA": 410.0, "SAMPLEPEERB": 1180.0, "SAMPLEPEERC": 255.0, "SAMPLEBANK": 1420.0,
          "SAMPLEIT": 1650.0, "SAMPLEFMCG": 2380.0, "SAMPLEPHARMA": 940.0}
START = {"SAMPLEMFG": 540.0, "SAMPLEPEERA": 380.0, "SAMPLEPEERB": 1010.0, "SAMPLEPEERC": 230.0, "SAMPLEBANK": 1300.0,
         "SAMPLEIT": 1750.0, "SAMPLEFMCG": 2150.0, "SAMPLEPHARMA": 860.0}
VOL = {"SAMPLEMFG": 150_000, "SAMPLEPEERA": 220_000, "SAMPLEPEERB": 60_000, "SAMPLEPEERC": 400_000, "SAMPLEBANK": 900_000,
       "SAMPLEIT": 300_000, "SAMPLEFMCG": 80_000, "SAMPLEPHARMA": 120_000}


def w(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(header)
        wr.writerows(rows)


def wj(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def weekdays(a: dt.date, b: dt.date) -> list:
    out, d = [], a
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


# ---------------------------------------------------------------- prices
def bench_returns(days: list) -> list:
    rnd = random.Random(9)
    return [rnd.gauss(0.00015, 0.009) for _ in days]


def price_path(sym: str, days: list, rb: list, start: float, target: float, n_bridge: int) -> list:
    """Correlated with the benchmark (beta), bridged so close n_bridge-1 == target."""
    rnd = random.Random(sym)
    beta = COMPANIES[sym][5]
    eps = [rnd.gauss(0, 0.014) for _ in days]
    lr = [beta * r + e for r, e in zip(rb, eps)]
    drift = (math.log(target / start) - sum(lr[1:n_bridge])) / (n_bridge - 1)
    closes, c = [start], start
    for i in range(1, len(days)):
        c *= math.exp(lr[i] + (drift if i < n_bridge else 0))
        closes.append(c)
    return closes


def bars(sym: str, days: list, closes: list) -> list:
    rnd = random.Random(sym + "ohlc")
    rows, prev = [], closes[0]
    for d, c in zip(days, closes):
        o = prev * (1 + rnd.gauss(0, 0.004))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.006)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.006)))
        v = int(VOL[sym] * math.exp(rnd.gauss(0, 0.35)))
        rows.append([d.isoformat(), round(o, 2), round(h, 2), round(lo, 2), round(c, 2), v])
        prev = c
    return rows


# ---------------------------------------------------------------- financials
def src_cols(kind: str, sym: str, period: str, published: str, retrieved=RETRIEVED) -> list:
    return ["%s/%s/%s-%s" % (BASE, sym.lower(), kind, period), "%s %s (synthetic)" % (kind.replace("-", " ").title(), period),
            "Sample Exchange (synthetic)", "true", published, retrieved]


FIN_HEADER = ["period_end", "period_type", "basis", "line_item", "value", "unit", "source_url", "source_title", "publisher",
              "official", "published", "retrieved_at"]


def fy_rows(sym: str, fy: dt.date, v: dict, published: str) -> list:
    lab = "FY%02d" % (fy.year % 100)
    sc = src_cols("annual-results", sym, lab, published)
    units = {"eps_diluted": "INR per share", "shares_outstanding": "shares"}
    return [[fy.isoformat(), "FY", "consolidated", k, val, units.get(k, "INR crore")] + sc for k, val in v.items()]


def q_rows(sym: str, q: dt.date, v: dict, published: str, retrieved=RETRIEVED) -> list:
    m = {6: 1, 9: 2, 12: 3, 3: 4}[q.month]
    lab = "Q%dFY%02d" % (m, (q.year + (1 if q.month > 3 else 0)) % 100)
    sc = src_cols("quarterly-results", sym, lab, published, retrieved)
    units = {"eps_diluted": "INR per share"}
    return [[q.isoformat(), "Q", "consolidated", k, val, units.get(k, "INR crore")] + sc for k, val in v.items()]


def pl(rev, oi, ebitda, dep, fin, tax, shares):
    pbt = ebitda + oi - dep - fin
    pat = pbt - tax
    return {"revenue": rev, "other_income": oi, "operating_expenses": rev - ebitda, "depreciation": dep, "finance_costs": fin,
            "pbt": pbt, "tax_expense": tax, "pat": pat, "eps_diluted": round(pat * 1e7 / shares, 2)}


def mfg_financials() -> tuple:
    shares = 100_000_000
    fys = [dt.date(y, 3, 31) for y in range(2022, 2027)]
    rev = [1200, 1380, 1550, 1720, 1950]
    oi = [15, 18, 20, 22, 30]
    ebitda = [192, 235, 271, 310, 361]
    dep = [40, 45, 50, 55, 62]
    fin = [20, 22, 21, 19, 18]
    tax = [37, 47, 55, 65, 78]
    oeq = [600, 697, 812, 947, 1110]
    bnc = [150, 170, 140, 120, 100]
    bc = [70, 70, 70, 70, 70]
    cash = [40, 55, 70, 95, 140]
    rec = [180, 215, 250, 290, 360]
    inv = [150, 170, 185, 200, 225]
    pay = [120, 135, 150, 160, 180]
    oliab = [60, 70, 75, 85, 95]
    cfo = [130, 150, 185, 205, 225]
    capex = [-80, -85, -70, -75, -80]
    div = [-33, -42, -50, -58, -70]
    cont = [None, None, 60, 70, 85]
    rows = []
    for i, fy in enumerate(fys):
        v = pl(rev[i], oi[i], ebitda[i], dep[i], fin[i], tax[i], shares)
        te = 100 + oeq[i]
        tl = bnc[i] + bc[i] + pay[i] + oliab[i]
        ta = te + tl
        other_assets = ta - cash[i] - rec[i] - inv[i]
        v.update({"cost_of_goods_sold": round(rev[i] * 0.6, 1), "equity_share_capital": 100, "other_equity": oeq[i],
                  "borrowings_noncurrent": bnc[i], "borrowings_current": bc[i], "cash_and_equivalents": cash[i],
                  "trade_receivables": rec[i], "inventories": inv[i], "trade_payables": pay[i],
                  "current_assets": round(cash[i] + rec[i] + inv[i] + other_assets * 0.25, 1),
                  "current_liabilities": round(pay[i] + bc[i] + oliab[i] * 0.7, 1), "total_liabilities": tl, "total_assets": ta,
                  "cfo": cfo[i], "capex": capex[i], "dividends_paid": div[i], "shares_outstanding": shares})
        if cont[i] is not None:
            v["contingent_liabilities"] = cont[i]
        rows += fy_rows("SAMPLEMFG", fy, v, "%d-05-15" % fy.year)
    qs = [(dt.date(2025, 6, 30), (455, 7, 82, 15, 5, 17), "2025-08-08"), (dt.date(2025, 9, 30), (480, 7, 88, 15, 5, 19), "2025-11-10"),
          (dt.date(2025, 12, 31), (495, 8, 92, 16, 4, 20), "2026-02-10"), (dt.date(2026, 3, 31), (520, 8, 99, 16, 4, 22), "2026-05-15"),
          (dt.date(2026, 6, 30), (515, 8, 93, 17, 4, 20), "2026-08-08")]
    for q, (r, o, e, d, f, t), pub in qs:
        rows += q_rows("SAMPLEMFG", q, pl(r, o, e, d, f, t, shares), pub)
    stage2 = q_rows("SAMPLEMFG", dt.date(2026, 9, 30), pl(498, 9, 80, 17, 5, 17, shares), "2026-10-27", RETRIEVED2)
    return rows, stage2


def simple_financials(sym: str, rev26: float, growth: float, margin: float, de: float, shares: int, roe_target: float) -> list:
    """Three fiscal years, internally consistent, for peers / holdings."""
    rows = []
    for k, y in enumerate((2024, 2025, 2026)):
        rev = round(rev26 / (1 + growth) ** (2 - k), 1)
        ebitda = round(rev * (margin - 0.005 * (2 - k)), 1)
        dep = round(rev * 0.03, 1)
        oi = round(rev * 0.012, 1)
        eq = round(rev * 0.7 * (0.85 + 0.075 * k), 1)
        debt = round(eq * de, 1)
        fin = round(debt * 0.085, 1)
        pbt = ebitda + oi - dep - fin
        tax = round(pbt * 0.25, 1)
        v = pl(rev, oi, ebitda, dep, fin, tax, shares)
        cash = round(rev * 0.05, 1)
        v.update({"equity_share_capital": round(shares * 10 / 1e7, 1), "other_equity": round(eq - shares * 10 / 1e7, 1),
                  "borrowings_noncurrent": round(debt * 0.7, 1), "borrowings_current": round(debt - round(debt * 0.7, 1), 1),
                  "cash_and_equivalents": cash, "trade_receivables": round(rev * 0.16, 1), "inventories": round(rev * 0.12, 1),
                  "trade_payables": round(rev * 0.09, 1), "cfo": round(v["pat"] * 1.05 + dep * 0.5, 1), "capex": round(-rev * 0.045, 1),
                  "dividends_paid": round(-v["pat"] * 0.25, 1), "shares_outstanding": shares})
        rows += fy_rows(sym, dt.date(y, 3, 31), v, "%d-05-20" % y)
    return rows


# ---------------------------------------------------------------- main
def main() -> None:
    days1 = weekdays(PRICE_START, STAGE1_END)
    days2 = weekdays(PRICE_START, STAGE2_END)
    rb = bench_returns(days2)
    bench = [24000.0]
    for r in rb[1:]:
        bench.append(bench[-1] * math.exp(r))
    w(HERE / "benchmarks" / "NIFTY50.csv", ["date", "close"], [[d.isoformat(), round(c, 2)] for d, c in zip(days1, bench)])
    # stage 2 re-retrieves the series, so its source metadata carries the later retrieval time
    for base, when in ((HERE, RETRIEVED), (HERE / "updates" / "stage2", RETRIEVED2)):
        wj(base / "benchmarks" / "NIFTY50.source.json", {"url": BASE + "/benchmarks/nifty50", "title": "SAMPLE benchmark index (synthetic stand-in for NIFTY 50)",
                                                          "publisher": "Sample Index Provider (synthetic)", "official": False, "synthetic": True,
                                                          "retrieved_at": when, "exchange": "NSE", "adjusted": True})
    w(HERE / "updates" / "stage2" / "benchmarks" / "NIFTY50.csv", ["date", "close"],
      [[d.isoformat(), round(c, 2)] for d, c in zip(days2, bench) if d > STAGE1_END])
    # master
    w(HERE / "master.csv", ["name", "isin", "nse_symbol", "bse_code", "series", "synthetic", "source_url", "publisher", "official", "retrieved_at"],
      [[n, isin(iss), s, b, "EQ", "true", BASE + "/master", "Sample Exchange (synthetic)", "false", RETRIEVED]
       for s, (n, iss, b, *_r) in COMPANIES.items()])
    closes_all = {}
    for sym in TARGET:
        n, iss, b, sector, industry, beta = COMPANIES[sym]
        cdir = HERE / "companies" / sym
        closes = price_path(sym, days2, rb, START[sym], TARGET[sym], len(days1))
        if sym == "SAMPLEMFG":  # weak Q2 reaction in stage 2
            k = len(days1)
            for i in range(k, len(closes)):
                closes[i] = closes[k - 1] * (1 - 0.016 * (i - k + 1))
        closes_all[sym] = dict(zip(days2, closes))
        allbars = bars(sym, days2, closes)
        w(cdir / "prices.csv", ["date", "open", "high", "low", "close", "volume"], allbars[:len(days1)])
        w(HERE / "updates" / "stage2" / "companies" / sym / "prices.csv", ["date", "open", "high", "low", "close", "volume"], allbars[len(days1):])
        for base, when in ((cdir, RETRIEVED), (HERE / "updates" / "stage2" / "companies" / sym, RETRIEVED2)):
            wj(base / "prices.source.json", {"url": "%s/%s/prices" % (BASE, sym.lower()), "title": "Daily prices %s (synthetic)" % sym,
                                             "publisher": "Sample Exchange (synthetic)", "official": True, "synthetic": True,
                                             "retrieved_at": when, "exchange": "NSE", "adjusted": True})
        prof = {"name": n, "isin": isin(iss), "nse_symbol": sym, "bse_code": b, "sector": sector, "industry": industry,
                "face_value": 10, "synthetic": True, "description": "Fictional company used to test the research agent."}
        if sym == "SAMPLEMFG":
            prof["peers"] = ["SAMPLEPEERA", "SAMPLEPEERB", "SAMPLEPEERC"]
            prof["description"] = ("Fictional maker of industrial machinery components (synthetic test company; "
                                   "not a real business).")
        wj(cdir / "company.json", prof)
    # SAMPLENODATA: profile only, no prices
    n, iss, b, sector, industry, _ = COMPANIES["SAMPLENODATA"]
    wj(HERE / "companies" / "SAMPLENODATA" / "company.json", {"name": n, "isin": isin(iss), "nse_symbol": "SAMPLENODATA", "bse_code": b,
                                                              "sector": sector, "synthetic": True})
    # financials
    mfg, mfg2 = mfg_financials()
    w(HERE / "companies" / "SAMPLEMFG" / "financials.csv", FIN_HEADER, mfg)
    w(HERE / "updates" / "stage2" / "companies" / "SAMPLEMFG" / "financials.csv", FIN_HEADER, mfg2)
    for sym, args in {"SAMPLEPEERA": (2400, 0.10, 0.165, 0.30, 150_000_000, 0),
                      "SAMPLEPEERB": (1600, 0.14, 0.19, 0.10, 30_000_000, 0),
                      "SAMPLEPEERC": (900, 0.18, 0.15, 0.60, 140_000_000, 0),
                      "SAMPLEIT": (5200, 0.08, 0.24, 0.0, 120_000_000, 0)}.items():
        w(HERE / "companies" / sym / "financials.csv", FIN_HEADER, simple_financials(sym, *args))
    # shareholding
    sh = [("2025-09-30", 58.20, 0.0, 14.1, 11.8, "2025-10-21"), ("2025-12-31", 58.20, 0.0, 14.6, 11.5, "2026-01-21"),
          ("2026-03-31", 57.90, 2.0, 14.9, 11.4, "2026-04-21"), ("2026-06-30", 57.50, 4.5, 15.3, 11.2, "2026-07-21")]
    hdr = ["quarter_end", "promoter_pct", "promoter_pledged_pct", "fii_pct", "dii_pct", "public_pct", "source_url", "source_title",
           "publisher", "official", "published", "retrieved_at"]
    w(HERE / "companies" / "SAMPLEMFG" / "shareholding.csv", hdr,
      [[q, p, pl_, f, d, round(100 - p - f - d, 2), "%s/samplemfg/shareholding-%s" % (BASE, q), "Shareholding pattern %s (synthetic)" % q,
        "Sample Exchange (synthetic)", "true", pub, RETRIEVED] for q, p, pl_, f, d, pub in sh])
    w(HERE / "updates" / "stage2" / "companies" / "SAMPLEMFG" / "shareholding.csv", hdr,
      [["2026-09-30", 56.80, 12.0, 15.0, 11.6, round(100 - 56.8 - 15.0 - 11.6, 2), BASE + "/samplemfg/shareholding-2026-09-30",
        "Shareholding pattern 2026-09-30 (synthetic)", "Sample Exchange (synthetic)", "true", "2026-10-21", RETRIEVED2]])
    # announcements
    ahdr = ["date", "exchange", "category", "subject", "source_url", "publisher", "official", "published", "retrieved_at"]
    ann = [("2025-11-10", "Unaudited financial results for the quarter ended 30-Sep-2025"),
           ("2026-01-05", "Closure of trading window"),
           ("2026-02-10", "Outcome of board meeting - unaudited financial results Q3"),
           ("2026-03-02", "Order received from a fictional customer worth INR 120 crore"),
           ("2026-04-10", "Disclosure under Regulation 31(1) of SEBI SAST - creation of pledge by promoter"),
           ("2026-05-15", "Audited financial results for the year ended 31-Mar-2026; dividend recommended"),
           ("2026-06-12", "Credit rating reaffirmed by a fictional rating agency"),
           ("2026-07-15", "Disclosure under Regulation 31(1) of SEBI SAST - additional pledge of promoter shares"),
           ("2026-08-08", "Unaudited financial results for the quarter ended 30-Jun-2026"),
           ("2026-08-20", "Notice of 31st annual general meeting"),
           ("2026-09-25", "Voting results of AGM")]
    rows = [[d, "NSE", "", s, "%s/samplemfg/ann-%s" % (BASE, d), "Sample Exchange (synthetic)", "true", d, RETRIEVED] for d, s in ann]
    w(HERE / "companies" / "SAMPLEMFG" / "announcements.csv", ahdr, rows)
    ann2 = [("2026-10-22", "Disclosure under Regulation 31(1) of SEBI SAST - pledge of promoter shares"),
            ("2026-10-24", "Resignation of Chief Financial Officer (CFO)"),
            ("2026-10-27", "Unaudited financial results for the quarter ended 30-Sep-2026")]
    w(HERE / "updates" / "stage2" / "companies" / "SAMPLEMFG" / "announcements.csv", ahdr,
      [[d, "NSE", "", s, "%s/samplemfg/ann-%s" % (BASE, d), "Sample Exchange (synthetic)", "true", d, RETRIEVED2] for d, s in ann2])
    w(HERE / "companies" / "SAMPLEMFG" / "news.csv", ["date", "publisher", "headline", "source_url", "official", "published", "retrieved_at"],
      [["2026-08-09", "Sample Business Daily (synthetic)", "Sample Manufacturing Q1 profit rises on machinery demand",
        BASE + "/news/samplemfg-q1", "false", "2026-08-09", RETRIEVED]])
    # governance (annual report)
    wj(HERE / "companies" / "SAMPLEMFG" / "governance.json", {"fiscal_years": {
        "FY25": {"auditor": "Sample & Co LLP (fictional)", "audit_opinion": "unmodified", "emphasis_of_matter": None,
                 "auditor_changed": False, "auditor_resigned": False, "caro_adverse_remarks": [], "rpt_total_cr": 95,
                 "rpt_note": "purchases from a promoter-group entity",
                 "source": {"url": BASE + "/samplemfg/annual-report-fy25", "title": "Annual report FY25 (synthetic)",
                            "publisher": "Sample Manufacturing Limited (synthetic)", "official": True, "published": "2025-08-01",
                            "page": "112-118", "retrieved_at": RETRIEVED}},
        "FY26": {"auditor": "Sample & Co LLP (fictional)", "audit_opinion": "unmodified", "emphasis_of_matter": None,
                 "auditor_changed": False, "auditor_resigned": False, "caro_adverse_remarks": [], "rpt_total_cr": 140,
                 "rpt_note": "purchases from a promoter-group entity",
                 "source": {"url": BASE + "/samplemfg/annual-report-fy26", "title": "Annual report FY26 (synthetic)",
                            "publisher": "Sample Manufacturing Limited (synthetic)", "official": True, "published": "2026-08-01",
                            "page": "118-125", "retrieved_at": RETRIEVED}}}})
    # portfolio
    portfolio(closes_all, days1)
    print("sample data written to", HERE)


def portfolio(closes: dict, days1: list) -> None:
    pdir = HERE / "portfolio"
    A, B = "ZRD-AB12345", "HDF-XY98765"
    px = lambda s, d: round(closes[s][d] * 1.002, 2)  # noqa: E731  fills near the synthetic close
    D = {k: days1[i] for k, i in {"t1": 20, "t2": 45, "t3": 70, "t4": 100, "t5": 130, "t6": 160, "t7": 200, "t8": 240, "t9": 280}.items()}
    txns = [  # date, account, symbol, side, qty
        ("t1", A, "SAMPLEPEERA", "BUY", 300), ("t1", A, "SAMPLEBANK", "BUY", 800), ("t2", A, "SAMPLEIT", "BUY", 100),
        ("t3", A, "SAMPLEFMCG", "BUY", 60), ("t4", A, "SAMPLEPEERA", "BUY", 100), ("t5", A, "SAMPLEBANK", "SELL", 200),
        ("t6", A, "SAMPLEIT", "BUY", 50), ("t2", B, "SAMPLEPHARMA", "BUY", 200), ("t3", B, "SAMPLEIT", "BUY", 50),
        ("t7", B, "SAMPLEMFG", "BUY", 100), ("t8", A, "SAMPLEMFG", "BUY", 0)]
    rows, tid = [], 1000
    for k, acct, sym, side, qty in txns:
        if qty == 0:
            continue
        tid += 1
        rows.append([D[k].isoformat(), acct, sym, isin(COMPANIES[sym][1]), "NSE", side, qty, px(sym, D[k]), round(qty * px(sym, D[k]) * 0.0005, 2), "T%d" % tid])
    rows.append(list(rows[2]))  # an exact duplicate row (same trade id) the importer must catch
    w(pdir / "transactions.csv", ["trade_date", "account_id", "symbol", "isin", "exchange", "trade_type", "quantity", "price", "charges", "trade_id"], rows)
    # holdings derived from the same transactions (weighted average cost incl. charges)
    pos = {}
    for r in rows[:-1]:
        k = (r[1], r[2])
        q, c = pos.get(k, (0, 0.0))
        if r[5] == "BUY":
            c = (c * q + r[6] * r[7] + r[8]) / (q + r[6])
            q += r[6]
        else:
            q -= r[6]
        pos[k] = (q, c)
    hold_a = [[A, s, isin(COMPANIES[s][1]), "NSE", q, round(c, 2), COMPANIES[s][0]] for (a, s), (q, c) in sorted(pos.items()) if a == A]
    for h in hold_a:
        if h[1] == "SAMPLEFMCG":
            h[4] = 120  # a 1:1 bonus the transactions file does not show -> reconciliation must flag it
    hold_a.append([A, "SAMPLENODATA", isin(COMPANIES["SAMPLENODATA"][1]), "NSE", 100, 150.0, COMPANIES["SAMPLENODATA"][0]])
    w(pdir / "holdings.csv", ["Account ID", "Symbol", "ISIN", "Exchange", "Quantity", "Avg Cost", "Company"], hold_a)
    # account B as a broker-style XLSX: preamble rows, different headers, a cost that differs by >1%, an unknown symbol
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Holdings"
    ws.append(["Holdings statement (SYNTHETIC SAMPLE)"])
    ws.append(["Client ID: %s" % B])
    ws.append([])
    ws.append(["Client ID", "Instrument", "ISIN", "Qty.", "Avg. cost", "LTP"])
    for (a, s), (q, c) in sorted(pos.items()):
        if a != B:
            continue
        cost = round(c * (1.03 if s == "SAMPLEPHARMA" else 1.0), 2)
        ws.append([B, s, isin(COMPANIES[s][1]), q, cost, None])
    ws.append([B, "UNKNOWNXYZ", "", 10, 99.0, None])
    pdir.mkdir(parents=True, exist_ok=True)
    wb.save(pdir / "holdings_broker2.xlsx")
    w(pdir / "research_notes.csv", ["Date", "Symbol", "Analyst", "Title", "Notes", "View", "Link"],
      [["2026-03-15", "SAMPLEMFG", "R. Analyst (sample)", "Initial look", "Capacity expansion should support growth; watch receivables.",
        "watch", BASE + "/notes/1"],
       ["2026-06-01", "SAMPLEIT", "R. Analyst (sample)", "Margins", "Deal pipeline steady; margin pressure from wage hikes.", "hold-review", ""]])


if __name__ == "__main__":
    main()
