"""Portfolio reader: holdings, transactions and historical research notes from
CSV or XLSX, with column-alias mapping, header-row detection and row validation.

Nothing is dropped silently: every rejected row becomes a DataIssue that names
the file and row.
"""

from __future__ import annotations

import csv
import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config import PROJECT_ROOT
from ..identity import isin_valid
from ..models import DataIssue, parse_date

COLUMN_MAPS = PROJECT_ROOT / "config" / "column_maps.toml"
REQUIRED = {"holdings": ["symbol", "quantity"], "transactions": ["date", "symbol", "side", "quantity", "price"],
            "research_notes": ["date", "symbol", "note"]}


@dataclass
class Holding:
    account: str
    symbol: str
    isin: Optional[str]
    exchange: str
    quantity: float
    avg_cost: Optional[float]
    name: str = ""
    source_file: str = ""
    row: int = 0


@dataclass
class Transaction:
    date: object
    account: str
    symbol: str
    isin: Optional[str]
    exchange: str
    side: str
    quantity: float
    price: float
    charges: float = 0.0
    trade_id: str = ""
    source_file: str = ""
    row: int = 0


@dataclass
class ImportResult:
    holdings: list = field(default_factory=list)
    transactions: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    files: list = field(default_factory=list)  # {path, sha256, kind, rows}

    def extend(self, other: "ImportResult") -> None:
        self.holdings += other.holdings
        self.transactions += other.transactions
        self.notes += other.notes
        self.issues += other.issues
        self.files += other.files


def _key(s) -> str:
    return re.sub(r"[\s._\-/()]", "", str(s).lower())


def load_maps(path: Path = COLUMN_MAPS) -> dict:
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def _num(v) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("₹", "")
    if s == "" or s.lower() in ("nan", "none", "-"):
        return None
    return float(s)


def _read_raw(path: Path) -> list:
    """Rows as lists of strings (header not yet identified)."""
    suffix = path.suffix.lower()
    if suffix in (".csv", ".txt"):
        # stdlib csv copes with ragged preamble rows that broker exports put above the header
        with open(path, newline="", encoding="utf-8-sig") as fh:
            return [[c.strip() for c in row] for row in csv.reader(fh)]
    if suffix in (".xlsx", ".xlsm", ".xls"):
        import pandas as pd

        df = pd.read_excel(path, header=None, dtype=str, sheet_name=0).fillna("")
        return [[_cell_text(x) for x in row] for row in df.values.tolist()]
    raise ValueError("unsupported file type %s (use CSV or XLSX)" % path.suffix)


def _cell_text(x) -> str:
    s = str(x).strip()
    return s[:-2] if s.endswith(".0") and s[:-2].lstrip("-").isdigit() else s  # Excel integers read as "10.0"


def _map_header(header: list, aliases: dict) -> dict:
    """canonical name -> column index."""
    keyed = {_key(h): i for i, h in enumerate(header) if h}
    out = {}
    for canon, names in aliases.items():
        for n in [canon] + list(names):
            if _key(n) in keyed:
                out[canon] = keyed[_key(n)]
                break
    return out


def read_table(path: Path, kind: str, maps: Optional[dict] = None) -> tuple:
    """Return (rows as dicts keyed by canonical names, issues, header map, first data row number)."""
    maps = maps or load_maps()
    aliases = maps[kind]
    raw = _read_raw(path)
    issues = []
    best, best_i = {}, None
    for i, row in enumerate(raw[:30]):  # brokers often put a preamble above the header
        m = _map_header(row, aliases)
        if len(m) > len(best):
            best, best_i = m, i
    missing = [c for c in REQUIRED[kind] if c not in best]
    if best_i is None or missing:
        issues.append(DataIssue("error", "header_not_found", "%s: could not find columns %s (add aliases in "
                                "config/column_maps.toml)" % (path.name, ", ".join(missing or REQUIRED[kind])), kind))
        return [], issues, best, None
    rows = []
    for j, row in enumerate(raw[best_i + 1:], start=best_i + 2):
        if not any(row):
            continue
        d = {c: (row[i] if i < len(row) else "") for c, i in best.items()}
        d["_row"] = j
        rows.append(d)
    return rows, issues, best, best_i + 2


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _norm_symbol(s: str) -> str:
    s = s.strip().upper()
    s = re.sub(r"\.(NS|BO)$", "", s)
    s = re.sub(r"-(EQ|BE|BZ)$", "", s)  # some exports append the series
    return s


def read_holdings(path: Path, default_account: Optional[str] = None, maps=None) -> ImportResult:
    path = Path(path)
    res = ImportResult(files=[{"path": str(path), "sha256": _sha(path), "kind": "holdings"}])
    rows, issues, header, _ = read_table(path, "holdings", maps)
    res.issues += issues
    if "account" not in header:
        acct = default_account or path.stem
        res.issues.append(DataIssue("warning", "no_account_column", "%s: no account column; all rows assigned to account %r"
                                    % (path.name, acct), "holdings"))
    for r in rows:
        where = "%s row %d" % (path.name, r["_row"])
        sym = _norm_symbol(r.get("symbol", ""))
        if not sym or sym.lower() in ("total", "grand total"):
            continue
        try:
            qty = _num(r.get("quantity"))
            cost = _num(r.get("avg_cost")) if "avg_cost" in header else None
        except ValueError:
            res.issues.append(DataIssue("error", "bad_number", "%s: non-numeric quantity/cost" % where, "holdings"))
            continue
        if qty is None or qty <= 0:
            res.issues.append(DataIssue("error", "bad_quantity", "%s: %s quantity %r is not positive" % (where, sym, r.get("quantity")),
                                        "holdings"))
            continue
        if qty != int(qty):
            res.issues.append(DataIssue("warning", "fractional_quantity", "%s: %s quantity %s is fractional" % (where, sym, qty), "holdings"))
        if cost is not None and cost < 0:
            res.issues.append(DataIssue("error", "bad_cost", "%s: %s negative average cost" % (where, sym), "holdings"))
            continue
        if cost is None:
            res.issues.append(DataIssue("warning", "no_cost", "%s: %s has no average cost; P&L not computable" % (where, sym), "holdings"))
        isin = (r.get("isin") or "").upper() or None
        if isin and not isin_valid(isin):
            res.issues.append(DataIssue("error", "bad_isin", "%s: %s ISIN %s fails the check digit" % (where, sym, isin), "holdings"))
        acct = (r.get("account") or "").strip() or default_account or path.stem
        res.holdings.append(Holding(account=acct, symbol=sym, isin=isin, exchange=(r.get("exchange") or "NSE").upper()[:3],
                                    quantity=qty, avg_cost=cost, name=r.get("name", ""), source_file=path.name, row=r["_row"]))
    res.files[0]["rows"] = len(res.holdings)
    seen = {}
    for h in res.holdings:
        k = (h.account, h.symbol)
        if k in seen:
            res.issues.append(DataIssue("warning", "duplicate_holding", "%s: %s appears twice for account %s (rows %d and %d)"
                                        % (path.name, h.symbol, h.account, seen[k], h.row), "holdings"))
        seen[k] = h.row
    return res


def read_transactions(path: Path, default_account: Optional[str] = None, maps=None) -> ImportResult:
    path = Path(path)
    res = ImportResult(files=[{"path": str(path), "sha256": _sha(path), "kind": "transactions"}])
    rows, issues, header, _ = read_table(path, "transactions", maps)
    res.issues += issues
    seen_ids = set()
    for r in rows:
        where = "%s row %d" % (path.name, r["_row"])
        sym = _norm_symbol(r.get("symbol", ""))
        side = (r.get("side") or "").strip().upper()
        side = {"B": "BUY", "S": "SELL", "PURCHASE": "BUY", "SALE": "SELL"}.get(side, side)
        try:
            d = parse_date(r.get("date"))
            qty, price = _num(r.get("quantity")), _num(r.get("price"))
            charges = _num(r.get("charges")) or 0.0
        except ValueError as exc:
            res.issues.append(DataIssue("error", "bad_value", "%s: %s" % (where, exc), "transactions"))
            continue
        if side not in ("BUY", "SELL"):
            res.issues.append(DataIssue("error", "bad_side", "%s: side %r is not BUY/SELL" % (where, r.get("side")), "transactions"))
            continue
        if not sym or d is None or not qty or qty <= 0 or price is None or price <= 0:
            res.issues.append(DataIssue("error", "incomplete", "%s: missing or invalid date/symbol/quantity/price" % where, "transactions"))
            continue
        tid = (r.get("trade_id") or "").strip()
        if tid:
            if tid in seen_ids:
                res.issues.append(DataIssue("warning", "duplicate_trade", "%s: trade id %s repeated; second row skipped" % (where, tid),
                                            "transactions"))
                continue
            seen_ids.add(tid)
        isin = (r.get("isin") or "").upper() or None
        if isin and not isin_valid(isin):
            res.issues.append(DataIssue("error", "bad_isin", "%s: ISIN %s fails the check digit" % (where, isin), "transactions"))
        res.transactions.append(Transaction(date=d, account=(r.get("account") or "").strip() or default_account or path.stem,
                                            symbol=sym, isin=isin, exchange=(r.get("exchange") or "NSE").upper()[:3], side=side,
                                            quantity=qty, price=price, charges=charges, trade_id=tid, source_file=path.name,
                                            row=r["_row"]))
    res.transactions.sort(key=lambda t: (t.date, t.row))
    res.files[0]["rows"] = len(res.transactions)
    return res


def read_notes(path: Path, maps=None) -> ImportResult:
    path = Path(path)
    res = ImportResult(files=[{"path": str(path), "sha256": _sha(path), "kind": "research_notes"}])
    rows, issues, _, _ = read_table(path, "research_notes", maps)
    res.issues += issues
    for r in rows:
        try:
            d = parse_date(r.get("date"))
        except ValueError:
            res.issues.append(DataIssue("error", "bad_date", "%s row %d: bad date" % (path.name, r["_row"]), "research_notes"))
            continue
        res.notes.append({"date": d.isoformat() if d else None, "symbol": _norm_symbol(r.get("symbol", "")),
                          "author": r.get("author", ""), "title": r.get("title", ""), "note": r.get("note", ""),
                          "stance": r.get("stance", ""), "source_url": r.get("source_url", ""), "source_file": path.name})
    res.files[0]["rows"] = len(res.notes)
    return res


def import_all(holdings_files: list, transaction_files: list, note_files: list = ()) -> ImportResult:
    res = ImportResult()
    maps = load_maps()
    for p in holdings_files:
        if Path(p).exists():
            res.extend(read_holdings(Path(p), maps=maps))
        else:
            res.issues.append(DataIssue("warning", "file_missing", "holdings file not found: %s" % p, "holdings"))
    for p in transaction_files:
        if Path(p).exists():
            res.extend(read_transactions(Path(p), maps=maps))
        else:
            res.issues.append(DataIssue("info", "file_missing", "transactions file not found: %s" % p, "transactions"))
    for p in note_files:
        if Path(p).exists():
            res.extend(read_notes(Path(p), maps=maps))
    return res
