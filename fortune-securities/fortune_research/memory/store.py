"""Research memory: SQLite store for analyses, metrics, sources, findings,
assumptions, invalidation conditions, portfolio imports, research notes and
a global source log of every data retrieval.

Analyses are append-only: a new analysis never overwrites an old one, so
"what changed" can always compare against what was concluded at the time.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from ..models import now_ist

SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER);
CREATE TABLE IF NOT EXISTS companies (
  key TEXT PRIMARY KEY, name TEXT, isin TEXT, nse_symbol TEXT, bse_code TEXT, sector TEXT, industry TEXT,
  synthetic INTEGER, first_seen TEXT, last_seen TEXT);
CREATE TABLE IF NOT EXISTS analyses (
  id INTEGER PRIMARY KEY AUTOINCREMENT, company_key TEXT, created_at TEXT, as_of TEXT, agent_version TEXT,
  settings_origin TEXT, synthetic INTEGER, confidence TEXT, summary_json TEXT, data_as_of_json TEXT,
  report_md_path TEXT, report_xlsx_path TEXT, record_json TEXT,
  FOREIGN KEY(company_key) REFERENCES companies(key));
CREATE INDEX IF NOT EXISTS ix_analyses_company ON analyses(company_key, id);
CREATE TABLE IF NOT EXISTS metrics (analysis_id INTEGER, name TEXT, value REAL, unit TEXT, period TEXT, formula TEXT,
  source_ids_json TEXT, missing_json TEXT, note TEXT);
CREATE INDEX IF NOT EXISTS ix_metrics ON metrics(analysis_id, name);
CREATE TABLE IF NOT EXISTS sources (analysis_id INTEGER, source_id TEXT, url TEXT, title TEXT, publisher TEXT,
  official INTEGER, provider TEXT, published TEXT, period TEXT, retrieved_at TEXT, synthetic INTEGER, note TEXT);
CREATE TABLE IF NOT EXISTS findings (analysis_id INTEGER, module TEXT, code TEXT, severity TEXT, message TEXT,
  evidence_json TEXT, source_ids_json TEXT);
CREATE TABLE IF NOT EXISTS assumptions (analysis_id INTEGER, name TEXT, value TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS conditions (analysis_id INTEGER, cond_id TEXT, key TEXT, op TEXT, threshold REAL, text TEXT);
CREATE TABLE IF NOT EXISTS state (analysis_id INTEGER, key TEXT, value REAL);
CREATE TABLE IF NOT EXISTS data_issues (analysis_id INTEGER, severity TEXT, code TEXT, message TEXT, dataset TEXT);
CREATE TABLE IF NOT EXISTS announcements_seen (company_key TEXT, fingerprint TEXT, date TEXT, subject TEXT,
  first_seen_analysis INTEGER, PRIMARY KEY(company_key, fingerprint));
CREATE TABLE IF NOT EXISTS source_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, provider TEXT, url TEXT,
  status INTEGER, cache_hit INTEGER, bytes INTEGER, sha256 TEXT, error TEXT, context TEXT);
CREATE TABLE IF NOT EXISTS portfolio_imports (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, files_json TEXT,
  holdings_json TEXT, transactions_json TEXT, issues_json TEXT, reconciliation_json TEXT);
CREATE TABLE IF NOT EXISTS portfolio_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, as_of TEXT,
  summary_json TEXT, report_md_path TEXT, report_xlsx_path TEXT);
CREATE TABLE IF NOT EXISTS research_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, imported_at TEXT, date TEXT, symbol TEXT,
  author TEXT, title TEXT, note TEXT, stance TEXT, source_url TEXT, source_file TEXT,
  UNIQUE(date, symbol, title, note));
"""


def _j(x) -> str:
    return json.dumps(x, default=str, sort_keys=True)


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as db:
            db.executescript(SCHEMA)
            if not db.execute("SELECT version FROM schema_version").fetchone():
                db.execute("INSERT INTO schema_version VALUES (?)", (SCHEMA_VERSION,))

    @contextmanager
    def _conn(self):
        """Commit on success, roll back on error, and always close (sqlite3's own
        context manager commits but leaves the connection open)."""
        db = sqlite3.connect(self.path)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            with db:
                yield db
        finally:
            db.close()

    # -- source log ---------------------------------------------------------------
    def log_fetch(self, entry: dict, context: str = "") -> None:
        with self._conn() as db:
            db.execute("INSERT INTO source_log (ts, provider, url, status, cache_hit, bytes, sha256, error, context) "
                       "VALUES (?,?,?,?,?,?,?,?,?)",
                       (entry.get("retrieved_at") or now_ist().isoformat(), entry.get("provider"), entry.get("url"),
                        entry.get("status"), int(bool(entry.get("cache_hit"))), entry.get("bytes"), entry.get("sha256"),
                        entry.get("error"), context))

    def source_log(self, limit: int = 50) -> list:
        with self._conn() as db:
            return [dict(r) for r in db.execute("SELECT * FROM source_log ORDER BY id DESC LIMIT ?", (limit,))]

    # -- analyses -----------------------------------------------------------------
    def save_analysis(self, rec: dict) -> int:
        c = rec["company"]
        ts = rec["created_at"]
        with self._conn() as db:
            db.execute("INSERT INTO companies (key, name, isin, nse_symbol, bse_code, sector, industry, synthetic, first_seen, last_seen) "
                       "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET name=excluded.name, sector=excluded.sector, "
                       "industry=excluded.industry, last_seen=excluded.last_seen",
                       (c["key"], c["name"], c.get("isin"), c.get("nse_symbol"), c.get("bse_code"), c.get("sector"),
                        c.get("industry"), int(bool(c.get("synthetic"))), ts, ts))
            cur = db.execute("INSERT INTO analyses (company_key, created_at, as_of, agent_version, settings_origin, synthetic, "
                             "confidence, summary_json, data_as_of_json, report_md_path, report_xlsx_path, record_json) "
                             "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                             (c["key"], ts, rec["as_of"], rec.get("agent_version"), rec.get("settings_origin"),
                              int(bool(rec.get("synthetic"))), rec.get("confidence"), _j(rec.get("summary")),
                              _j(rec.get("data_as_of")), rec.get("report_md_path"), rec.get("report_xlsx_path"), _j(rec)))
            aid = cur.lastrowid
            db.executemany("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?)",
                           [(aid, k, m["value"], m["unit"], m["period"], m["formula"], _j(m["source_ids"]), _j(m["missing"]),
                             m.get("note", "")) for k, m in rec.get("metrics", {}).items()])
            db.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                           [(aid, s["id"], s["url"], s["title"], s["publisher"], int(s["official"]), s["provider"], s.get("published"),
                             s.get("period"), s["retrieved_at"], int(bool(s.get("synthetic"))), s.get("note", ""))
                            for s in rec.get("sources", [])])
            db.executemany("INSERT INTO findings VALUES (?,?,?,?,?,?,?)",
                           [(aid, f["module"], f["code"], f["severity"], f["message"], _j(f["evidence"]), _j(f["source_ids"]))
                            for f in rec.get("findings", [])])
            db.executemany("INSERT INTO assumptions VALUES (?,?,?,?)",
                           [(aid, a["name"], _j(a["value"]), a["source"]) for a in rec.get("assumptions", [])])
            db.executemany("INSERT INTO conditions VALUES (?,?,?,?,?,?)",
                           [(aid, x["id"], x["key"], x["op"], x["threshold"], x["text"]) for x in rec.get("conditions", [])])
            db.executemany("INSERT INTO state VALUES (?,?,?)", [(aid, k, v) for k, v in rec.get("state", {}).items()])
            db.executemany("INSERT INTO data_issues VALUES (?,?,?,?,?)",
                           [(aid, i["severity"], i["code"], i["message"], i.get("dataset", "")) for i in rec.get("data_issues", [])])
            for it in rec.get("news", {}).get("items", []):
                db.execute("INSERT OR IGNORE INTO announcements_seen VALUES (?,?,?,?,?)",
                           (c["key"], it["fingerprint"], it["date"], it["subject"], aid))
        return aid

    def set_report_paths(self, aid: int, md: Optional[str], xlsx: Optional[str]) -> None:
        with self._conn() as db:
            db.execute("UPDATE analyses SET report_md_path=?, report_xlsx_path=? WHERE id=?", (md, xlsx, aid))

    def analyses_for(self, company_key: str, limit: int = 10) -> list:
        with self._conn() as db:
            return [dict(r) for r in db.execute("SELECT id, created_at, as_of, confidence, summary_json, report_md_path FROM analyses "
                                                "WHERE company_key=? ORDER BY id DESC LIMIT ?", (company_key, limit))]

    def load_analysis(self, aid: int) -> Optional[dict]:
        with self._conn() as db:
            row = db.execute("SELECT record_json FROM analyses WHERE id=?", (aid,)).fetchone()
        return json.loads(row["record_json"]) if row else None

    def latest_analysis(self, company_key: str, before_id: Optional[int] = None) -> Optional[dict]:
        q = "SELECT id FROM analyses WHERE company_key=?" + (" AND id<?" if before_id else "") + " ORDER BY id DESC LIMIT 1"
        args = (company_key, before_id) if before_id else (company_key,)
        with self._conn() as db:
            row = db.execute(q, args).fetchone()
        if not row:
            return None
        rec = self.load_analysis(row["id"])
        rec["_id"] = row["id"]
        return rec

    def seen_fingerprints(self, company_key: str) -> set:
        with self._conn() as db:
            return {r["fingerprint"] for r in db.execute("SELECT fingerprint FROM announcements_seen WHERE company_key=?", (company_key,))}

    def companies(self) -> list:
        with self._conn() as db:
            return [dict(r) for r in db.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM analyses a WHERE a.company_key=c.key) AS n_analyses, "
                "(SELECT MAX(id) FROM analyses a WHERE a.company_key=c.key) AS last_id FROM companies c ORDER BY last_seen DESC")]

    def find_company(self, query: str) -> Optional[dict]:
        q = query.strip().upper()
        for c in self.companies():
            if q in ((c["nse_symbol"] or "").upper(), (c["bse_code"] or ""), (c["isin"] or "").upper(), c["key"].upper()) \
                    or q == (c["name"] or "").upper():
                return c
        return None

    def metric_history(self, company_key: str, name: str) -> list:
        with self._conn() as db:
            return [dict(r) for r in db.execute("SELECT a.id, a.as_of, m.value, m.period FROM metrics m JOIN analyses a ON a.id=m.analysis_id "
                                                "WHERE a.company_key=? AND m.name=? ORDER BY a.id", (company_key, name))]

    # -- portfolio ------------------------------------------------------------------
    def save_portfolio_import(self, files, holdings, txns, issues, recon_status) -> int:
        with self._conn() as db:
            cur = db.execute("INSERT INTO portfolio_imports (created_at, files_json, holdings_json, transactions_json, issues_json, "
                             "reconciliation_json) VALUES (?,?,?,?,?,?)",
                             (now_ist().isoformat(), _j(files), _j([h.__dict__ for h in holdings]), _j([t.__dict__ for t in txns]),
                              _j([i.to_dict() for i in issues]), _j({"%s|%s" % k: v for k, v in recon_status.items()})))
            return cur.lastrowid

    def save_portfolio_report(self, as_of: str, summary: dict, md: Optional[str], xlsx: Optional[str]) -> int:
        with self._conn() as db:
            cur = db.execute("INSERT INTO portfolio_reports (created_at, as_of, summary_json, report_md_path, report_xlsx_path) "
                             "VALUES (?,?,?,?,?)", (now_ist().isoformat(), as_of, _j(summary), md, xlsx))
            return cur.lastrowid

    def add_notes(self, notes: list) -> int:
        n = 0
        with self._conn() as db:
            for x in notes:
                cur = db.execute("INSERT OR IGNORE INTO research_notes (imported_at, date, symbol, author, title, note, stance, source_url, "
                                 "source_file) VALUES (?,?,?,?,?,?,?,?,?)",
                                 (now_ist().isoformat(), x["date"], x["symbol"], x["author"], x["title"], x["note"], x["stance"],
                                  x["source_url"], x["source_file"]))
                n += cur.rowcount
        return n

    def notes_for(self, symbol: str) -> list:
        with self._conn() as db:
            return [dict(r) for r in db.execute("SELECT * FROM research_notes WHERE symbol=? ORDER BY date DESC", (symbol.upper(),))]
