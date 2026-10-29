"""Portfolio analyst: account-aware valuation, allocation, concentration, sector
exposure, money-weighted return (XIRR) against a benchmark, and how a company
under research fits the existing portfolio.

Positions without a usable price are listed as unpriced and excluded from
weights. They are never valued at cost.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Callable, Optional

from ..portfolio.reconcile import positions_from_transactions
from .technical import correlation


def mask(account: str, enabled: bool = True) -> str:
    if not enabled or len(account) <= 4:
        return account
    return "*" * min(6, len(account) - 4) + account[-4:]


def xnpv(rate: float, flows: list) -> float:
    t0 = flows[0][0]
    return sum(cf / (1 + rate) ** ((d - t0).days / 365.0) for d, cf in flows)


def xirr(flows: list) -> Optional[float]:
    """flows: [(date, amount)], investments negative. Bisection on [-0.99, 10]."""
    flows = sorted(flows)
    if len(flows) < 2 or not any(cf < 0 for _, cf in flows) or not any(cf > 0 for _, cf in flows):
        return None
    if (flows[-1][0] - flows[0][0]).days < 1:
        return None
    lo, hi = -0.99, 10.0
    flo, fhi = xnpv(lo, flows), xnpv(hi, flows)
    if flo * fhi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = xnpv(mid, flows)
        if abs(fm) < 1e-7:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def _close_on_or_before(bars: list, d: dt.date) -> Optional[float]:
    best = None
    for b in bars:
        if b.date <= d:
            best = b.close
        else:
            break
    return best


def benchmark_pme(txns: list, bench_bars: list, as_of: dt.date) -> tuple:
    """Replay the same cash flows into the benchmark ('public market equivalent').
    Returns (benchmark XIRR, terminal value, skipped flows)."""
    units, flows, skipped = 0.0, [], 0
    for t in sorted(txns, key=lambda x: x.date):
        px = _close_on_or_before(bench_bars, t.date)
        if px is None:
            skipped += 1
            continue
        amt = t.quantity * t.price + (t.charges or 0) * (1 if t.side == "BUY" else -1)
        if t.side == "BUY":
            units += amt / px
            flows.append((t.date, -amt))
        else:
            units -= amt / px
            flows.append((t.date, amt))
    last = _close_on_or_before(bench_bars, as_of)
    if last is None or not flows:
        return None, None, skipped
    tv = units * last
    flows.append((as_of, tv))
    return xirr(flows), tv, skipped


def analyse(holdings: list, recon, pricing: Callable, as_of: dt.date, bench=None, txns: list = (),
            mask_ids: bool = True, max_stock: float = 0.15, max_sector: float = 0.35, stale_days: int = 5) -> dict:
    """pricing(symbol, isin) -> dict(security, series, profile) or None."""
    rows, unpriced = [], []
    for h in holdings:
        info = pricing(h.symbol, h.isin)
        series = info.get("series") if info else None
        last = series.last if series else None
        if last is None or last.date > as_of:
            unpriced.append({"account": mask(h.account, mask_ids), "symbol": h.symbol, "quantity": h.quantity,
                             "reason": "no price data" if info else "symbol not found in securities master / local data"})
            continue
        sec = info["security"]
        prof = info.get("profile") or {}
        age = (as_of - last.date).days
        mv = h.quantity * last.close
        cost = h.quantity * h.avg_cost if h.avg_cost is not None else None
        rows.append({"account": h.account, "account_masked": mask(h.account, mask_ids), "symbol": h.symbol,
                     "name": sec.name, "isin": sec.isin, "sector": prof.get("sector") or "Unclassified",
                     "quantity": h.quantity, "avg_cost": h.avg_cost, "last_price": last.close, "price_date": last.date.isoformat(),
                     "price_official": series.source.official, "price_source_id": series.source.id,
                     "price_stale": age > stale_days, "market_value": mv, "cost_value": cost,
                     "unrealised_pnl": (mv - cost) if cost is not None else None,
                     "unrealised_pct": ((mv / cost - 1) * 100) if cost else None,
                     "recon_status": recon.status.get((h.account, h.symbol), "not_checked") if recon else "not_checked",
                     "synthetic": sec.synthetic, "_series": series})
    total = sum(r["market_value"] for r in rows)
    for r in rows:
        r["weight"] = r["market_value"] / total if total else None
    accounts = {}
    for acct in sorted({r["account"] for r in rows}):
        rs = [r for r in rows if r["account"] == acct]
        v = sum(r["market_value"] for r in rs)
        c = sum(r["cost_value"] for r in rs if r["cost_value"] is not None)
        for r in rs:
            r["weight_in_account"] = r["market_value"] / v if v else None
        acct_txns = [t for t in txns if t.account == acct]
        accounts[mask(acct, mask_ids)] = {"market_value": v, "cost_value": c, "unrealised_pnl": v - c if c else None,
                                          "positions": len(rs), "share_of_total": v / total if total else None,
                                          **_performance(acct_txns, rs, bench, as_of)}
    weights = sorted((r["weight"] for r in rows if r["weight"] is not None), reverse=True)
    hhi = sum(w * w for w in weights)
    sectors = defaultdict(float)
    for r in rows:
        sectors[r["sector"]] += r["weight"] or 0
    by_symbol = defaultdict(float)
    for r in rows:
        by_symbol[r["symbol"]] += r["weight"] or 0
    breaches = [{"type": "single_stock", "symbol": s, "weight": w, "limit": max_stock} for s, w in by_symbol.items() if w > max_stock]
    breaches += [{"type": "sector", "sector": s, "weight": w, "limit": max_sector} for s, w in sectors.items() if w > max_sector]
    cost_total = sum(r["cost_value"] for r in rows if r["cost_value"] is not None)
    return {
        "as_of": as_of.isoformat(), "positions": rows, "unpriced": unpriced, "accounts": accounts,
        "total": {"market_value": total, "cost_value": cost_total, "unrealised_pnl": total - cost_total if cost_total else None,
                  "positions": len(rows), "unpriced": len(unpriced), **_performance(list(txns), rows, bench, as_of)},
        "concentration": {"top1": weights[0] if weights else None, "top5": sum(weights[:5]) if weights else None,
                          "hhi": hhi if weights else None, "effective_positions": (1 / hhi) if hhi else None},
        "by_symbol": dict(sorted(by_symbol.items(), key=lambda t: -t[1])),
        "sectors": dict(sorted(sectors.items(), key=lambda t: -t[1])),
        "breaches": breaches, "synthetic": any(r["synthetic"] for r in rows),
        "stale_prices": [r["symbol"] for r in rows if r["price_stale"]],
    }


def _performance(txns: list, rows: list, bench, as_of: dt.date) -> dict:
    out = {"xirr": None, "benchmark_xirr": None, "excess_xirr": None, "performance_note": ""}
    if not txns:
        out["performance_note"] = "no transactions: money-weighted return not computable"
        return out
    priced = {(r["account"], r["symbol"]): r["last_price"] for r in rows}
    flows = []
    for t in txns:
        amt = t.quantity * t.price
        flows.append((t.date, -(amt + (t.charges or 0)) if t.side == "BUY" else amt - (t.charges or 0)))
    # terminal value: current priced holdings that the transactions explain
    pos, _ = positions_from_transactions(txns)
    tv, missing = 0.0, []
    for k, p in pos.items():
        if p.quantity <= 0:
            continue
        px = priced.get(k)
        if px is None:
            missing.append(k[1])
            continue
        tv += p.quantity * px
    if missing:
        out["performance_note"] = "terminal value excludes unpriced positions: %s" % ", ".join(sorted(set(missing)))
    flows.append((as_of, tv))
    out["xirr"] = xirr(flows)
    if bench and bench.bars:
        b, _, skipped = benchmark_pme(txns, bench.bars, as_of)
        out["benchmark_xirr"] = b
        if skipped:
            out["performance_note"] += "; %d flows before benchmark history skipped" % skipped
    if out["xirr"] is not None and out["benchmark_xirr"] is not None:
        out["excess_xirr"] = out["xirr"] - out["benchmark_xirr"]
    return out


def fit(company: dict, port: dict) -> dict:
    """How a researched company relates to the current portfolio."""
    sym, sector, series = company["symbol"], company.get("sector") or "Unclassified", company.get("series")
    held = [r for r in port["positions"] if r["symbol"] == sym or (company.get("isin") and r["isin"] == company.get("isin"))]
    corr = []
    if series and series.bars:
        seen = set()
        for r in port["positions"]:
            if r["symbol"] in seen or r["symbol"] == sym:
                continue
            seen.add(r["symbol"])
            c = correlation(series.bars[-253:], r["_series"].bars[-253:])
            if c is not None:
                corr.append({"symbol": r["symbol"], "correlation": c, "weight": port["by_symbol"].get(r["symbol"])})
    corr.sort(key=lambda x: -x["correlation"])
    wsum = sum(c["weight"] or 0 for c in corr)
    return {
        "already_held": bool(held), "held_weight": sum(r["weight"] or 0 for r in held),
        "held_accounts": sorted({r["account_masked"] for r in held}), "sector": sector,
        "sector_weight_now": port["sectors"].get(sector, 0.0),
        "same_sector_holdings": sorted({r["symbol"] for r in port["positions"] if r["sector"] == sector and r["symbol"] != sym}),
        "correlations": corr[:5],
        "weighted_avg_correlation": (sum(c["correlation"] * (c["weight"] or 0) for c in corr) / wsum) if wsum else None,
    }
