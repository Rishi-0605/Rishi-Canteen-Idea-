"""Reconcile holdings against transactions.

Average cost follows the convention Indian brokers display: weighted average of
buys (including charges when given); sells reduce quantity at the running
average and do not change it. Realised P&L is computed on that basis (it is
not a tax computation).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..models import DataIssue

QTY_TOL = 1e-6
COST_TOL = 0.01  # 1%


@dataclass
class Position:
    account: str
    symbol: str
    quantity: float = 0.0
    avg_cost: float = 0.0
    realised_pnl: float = 0.0
    invested: float = 0.0
    first_buy: object = None
    oversold: bool = False


@dataclass
class Reconciliation:
    positions: dict = field(default_factory=dict)  # (account, symbol) -> Position
    issues: list = field(default_factory=list)
    matched: int = 0
    status: dict = field(default_factory=dict)  # (account, symbol) -> matched | qty_mismatch | ...


def positions_from_transactions(txns: list) -> tuple:
    pos, issues = {}, []
    for t in sorted(txns, key=lambda x: (x.date, x.row)):
        k = (t.account, t.symbol)
        p = pos.setdefault(k, Position(t.account, t.symbol))
        if t.side == "BUY":
            cost = t.quantity * t.price + (t.charges or 0)
            total = p.avg_cost * p.quantity + cost
            p.quantity += t.quantity
            p.avg_cost = total / p.quantity
            p.invested += cost
            p.first_buy = p.first_buy or t.date
        else:
            if t.quantity > p.quantity + QTY_TOL:
                issues.append(DataIssue("error", "oversold", "%s %s: sell of %g on %s exceeds held %g (missing buy, bonus or split?)"
                                        % (t.account, t.symbol, t.quantity, t.date, p.quantity), "transactions"))
                p.oversold = True
                sold = p.quantity
            else:
                sold = t.quantity
            p.realised_pnl += sold * (t.price - p.avg_cost) - (t.charges or 0)
            p.quantity -= sold
            if p.quantity <= QTY_TOL:
                p.quantity, p.avg_cost = 0.0, 0.0
    return pos, issues


def reconcile(holdings: list, txns: list) -> Reconciliation:
    rec = Reconciliation()
    pos, issues = positions_from_transactions(txns)
    rec.positions, rec.issues = pos, issues
    accounts_with_txns = {t.account for t in txns}
    held = defaultdict(float)
    cost = {}
    for h in holdings:
        held[(h.account, h.symbol)] += h.quantity
        cost[(h.account, h.symbol)] = h.avg_cost
    for k, q in held.items():
        p = pos.get(k)
        if p is None:
            if k[0] in accounts_with_txns:
                rec.issues.append(DataIssue("warning", "no_transactions", "%s %s: held %g but no transactions found "
                                            "(transferred in, IPO allotment or older history?)" % (k[0], k[1], q), "reconcile"))
            rec.status[k] = "no_transactions"
            continue
        if abs(p.quantity - q) > QTY_TOL:
            ratio = q / p.quantity if p.quantity else None
            hint = ""
            if ratio and abs(ratio - round(ratio)) < 1e-6 and round(ratio) > 1:
                hint = " (holding is exactly %dx: bonus or split not in transactions?)" % round(ratio)
            elif ratio and abs(1 / ratio - round(1 / ratio)) < 1e-6 and ratio < 1:
                hint = " (consolidation?)"
            rec.issues.append(DataIssue("error", "qty_mismatch", "%s %s: holdings file shows %g, transactions give %g%s"
                                        % (k[0], k[1], q, p.quantity, hint), "reconcile"))
            rec.status[k] = "qty_mismatch"
            continue
        c = cost.get(k)
        if c is not None and p.avg_cost and abs(c / p.avg_cost - 1) > COST_TOL:
            rec.issues.append(DataIssue("warning", "cost_mismatch", "%s %s: average cost %.2f in holdings vs %.2f from transactions "
                                        "(charges treatment or a cost-basis adjustment?)" % (k[0], k[1], c, p.avg_cost), "reconcile"))
            rec.status[k] = "cost_mismatch"
            continue
        rec.status[k] = "matched"
        rec.matched += 1
    for k, p in pos.items():
        if p.quantity > QTY_TOL and k not in held:
            rec.issues.append(DataIssue("warning", "missing_holding", "%s %s: transactions leave %g shares but the holdings file "
                                        "has none (sold outside these records or holdings file out of date?)" % (k[0], k[1], p.quantity),
                                        "reconcile"))
            rec.status[k] = "missing_holding"
    return rec
