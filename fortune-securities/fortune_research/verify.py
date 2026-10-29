"""Independent verification of extracted figures against the original documents.

    python -m fortune_research verify BEL                    # writes data/verification/BEL_<record>.csv
    (open each source URL, find the figure at the locator, fill checked_value / checked_by / checked_on)
    python -m fortune_research verify BEL --record FILE.csv  # stores the result

Live research is reported as UNVERIFIED until figures have been checked this way.
A mismatch is reported as a data error in every later analysis of the company.
"""

from __future__ import annotations

import csv
from pathlib import Path

COLUMNS = ["figure", "period", "extracted_value", "unit", "source_url", "locator", "published", "checked_value", "matches",
           "checked_by", "checked_on", "notes"]
REPORTED_ROWS = ("revenue", "other_income", "pbt", "tax_expense", "pat", "finance_costs", "depreciation", "eps_reported", "cfo")
TOLERANCE = 0.005  # 0.5%: rounding in the published document


def worksheet_rows(rec: dict) -> list:
    srcs = {s["id"]: s for s in rec["sources"]}
    rows, seen = [], set()

    def add(figure, period, m):
        if not m or m.get("value") is None or m.get("kind", "calculated") != "reported":
            return
        for sid in m["source_ids"][:1]:
            s = srcs.get(sid, {})
            key = (figure, period, s.get("url"))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"figure": figure, "period": period, "extracted_value": m["value"], "unit": m["unit"],
                         "source_url": s.get("url", ""), "locator": s.get("locator", "") or s.get("note", ""),
                         "published": s.get("published") or "", "checked_value": "", "matches": "", "checked_by": "",
                         "checked_on": "", "notes": ""})

    for table in ("annual", "quarterly"):
        labels = list(rec.get(table, {}))[-4:]
        for lab in labels:
            for name in REPORTED_ROWS:
                add(name, lab, rec[table][lab].get(name))
    for k in rec.get("key_figures", []):
        if k["kind"] == "reported":
            add(k["key"], k["period"], {"value": k["value"], "unit": k["unit"], "source_ids": k["source_ids"], "kind": "reported"})
    return rows


def write_worksheet(rec: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(worksheet_rows(rec))
    return path


def read_worksheet(path: Path) -> tuple:
    """-> (checked rows ready to store, problems). Rows without a checked_value are skipped."""
    rows, problems = [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for i, r in enumerate(csv.DictReader(fh), start=2):
            cv = (r.get("checked_value") or "").replace(",", "").strip()
            if not cv:
                continue
            try:
                checked, extracted = float(cv), float(r["extracted_value"])
            except (ValueError, KeyError):
                problems.append("row %d: checked_value / extracted_value not numeric" % i)
                continue
            if not (r.get("checked_by") or "").strip():
                problems.append("row %d: checked_by is required" % i)
                continue
            m = (r.get("matches") or "").strip().upper()
            if m in ("Y", "YES", "1", "TRUE"):
                matches = 1
            elif m in ("N", "NO", "0", "FALSE"):
                matches = 0
            else:
                matches = 1 if abs(checked - extracted) <= TOLERANCE * max(1.0, abs(checked)) else 0
            rows.append({"figure": r["figure"], "period": r["period"], "extracted_value": extracted, "unit": r.get("unit", ""),
                         "source_url": r.get("source_url", ""), "locator": r.get("locator", ""), "published": r.get("published", ""),
                         "checked_value": checked, "matches": matches, "checked_by": r["checked_by"].strip(),
                         "checked_on": r.get("checked_on", ""), "notes": r.get("notes", "")})
    return rows, problems
