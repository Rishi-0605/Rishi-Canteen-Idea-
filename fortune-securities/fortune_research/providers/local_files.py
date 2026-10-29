"""Local-file provider: data you entered or exported yourself, in the layout
documented in docs/DATA_FORMATS.md. The sample data uses it too.

Each row must name its source (URL, publisher, publication date, retrieval
time). Rows without a source URL are rejected, not silently accepted.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from ..models import (Announcement, Fact, PriceBar, PriceSeries, Security, ShareholdingRecord, Source,
                      fy_label, now_ist, parse_date)
from ..units import UnitError, normalise
from .base import Provider, ProviderError


def _bool(v) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "y")


def _float(v) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s == "" or s.lower() in ("na", "n/a", "nan", "-", "none"):
        return None
    return float(s)


def _read_csv(path: Path) -> list:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                for row in csv.DictReader(fh)]


class LocalFilesProvider(Provider):
    name = "local"
    official = False  # the files are manual copies; each row says whether ITS source is official
    capabilities = frozenset(["master", "profile", "financials", "prices", "announcements", "shareholding",
                              "governance", "news", "benchmark"])

    def __init__(self, roots: list):
        self.roots = [Path(r) for r in roots]
        self.issues = []  # rows rejected while reading, reported as data issues

    # -- helpers -------------------------------------------------------------
    def _company_dir(self, sec: Security) -> Optional[Path]:
        for root in self.roots:
            for key in (sec.nse_symbol, sec.bse_code, sec.isin):
                if key and (root / "companies" / str(key)).is_dir():
                    return root / "companies" / str(key)
        return None

    def _source(self, row: dict, default_title: str, synthetic: bool, period: Optional[str] = None) -> Source:
        url = row.get("source_url") or row.get("url") or ""
        if not url:
            raise ProviderError("row has no source_url")
        return Source(url=url, title=row.get("source_title") or default_title,
                      publisher=row.get("publisher") or "", official=_bool(row.get("official", "")),
                      provider=self.name, retrieved_at=row.get("retrieved_at") or now_ist().isoformat(),
                      published=row.get("published") or None, period=period, synthetic=synthetic,
                      note="manual/local file entry")

    def _json(self, path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def _synthetic(self, sec: Security) -> bool:
        d = self._company_dir(sec)
        meta = self._json(d / "company.json") if d else None
        return bool(meta and meta.get("synthetic")) or sec.synthetic

    # -- capabilities --------------------------------------------------------
    def securities_master(self) -> list:
        out = []
        for root in self.roots:
            path = root / "master.csv"
            if not path.exists():
                continue
            for row in _read_csv(path):
                syn = _bool(row.get("synthetic", ""))
                out.append({
                    "name": row["name"], "isin": row.get("isin") or None,
                    "nse_symbol": row.get("nse_symbol") or None, "bse_code": row.get("bse_code") or None,
                    "series": row.get("series") or None, "synthetic": syn,
                    "source": self._source(row, "Securities master (local)", syn),
                })
        return out

    def profile(self, sec: Security) -> Optional[dict]:
        d = self._company_dir(sec)
        return self._json(d / "company.json") if d else None

    def financials(self, sec: Security) -> list:
        d = self._company_dir(sec)
        if not d or not (d / "financials.csv").exists():
            return []
        syn = self._synthetic(sec)
        facts = []
        for i, row in enumerate(_read_csv(d / "financials.csv"), start=2):
            try:
                pe = parse_date(row["period_end"])
                ptype = row["period_type"].upper()
                if ptype not in ("FY", "Q", "POINT"):
                    raise ProviderError("period_type must be FY, Q or POINT")
                value, unit = normalise(_float(row.get("value")), row.get("unit", ""))
                src = self._source(row, "Financial statements", syn, fy_label(pe, ptype))
            except (KeyError, ValueError, UnitError, ProviderError) as exc:
                self.issues.append(("financials.csv line %d" % i, str(exc)))
                continue
            facts.append(Fact(name=row["line_item"].strip(), value=value, unit=unit, period_end=pe,
                              period_type=ptype, basis=(row.get("basis") or "consolidated").lower(),
                              source=src))
        return facts

    def _series(self, csv_path: Path, meta_path: Path, synthetic: bool, title: str,
                start=None, end=None) -> Optional[PriceSeries]:
        if not csv_path.exists():
            return None
        meta = self._json(meta_path) or {}
        if not meta.get("url"):
            self.issues.append((str(meta_path.name), "price file has no source metadata (url)"))
            return None
        bars = []
        for i, row in enumerate(_read_csv(csv_path), start=2):
            try:
                d = parse_date(row["date"])
                close = _float(row["close"])
                if close is None or close <= 0:
                    raise ValueError("non-positive close")
                o = _float(row.get("open")) or close
                h = _float(row.get("high")) or max(o, close)
                lo = _float(row.get("low")) or min(o, close)
                v = _float(row.get("volume")) or 0.0
                if h < max(o, close) - 1e-9 or lo > min(o, close) + 1e-9:
                    raise ValueError("high/low inconsistent with open/close")
            except (KeyError, ValueError) as exc:
                self.issues.append(("%s line %d" % (csv_path.name, i), str(exc)))
                continue
            if (start and d < start) or (end and d > end):
                continue
            bars.append(PriceBar(d, o, h, lo, close, v))
        bars.sort(key=lambda b: b.date)
        dedup = {}
        for b in bars:
            dedup[b.date] = b
        bars = list(dedup.values())
        src = Source(url=meta["url"], title=meta.get("title", title), publisher=meta.get("publisher", ""),
                     official=bool(meta.get("official")), provider=self.name,
                     retrieved_at=meta.get("retrieved_at") or now_ist().isoformat(),
                     published=bars[-1].date.isoformat() if bars else None,
                     period=("%s to %s" % (bars[0].date, bars[-1].date)) if bars else None,
                     synthetic=synthetic or bool(meta.get("synthetic")), note="manual/local file entry")
        return PriceSeries(bars=bars, source=src, exchange=meta.get("exchange", "NSE"),
                           adjusted=meta.get("adjusted"))

    def prices(self, sec: Security, start=None, end=None) -> Optional[PriceSeries]:
        d = self._company_dir(sec)
        if not d:
            return None
        return self._series(d / "prices.csv", d / "prices.source.json", self._synthetic(sec),
                            "Daily prices", start, end)

    def benchmark(self, name: str, start=None, end=None) -> Optional[PriceSeries]:
        for root in self.roots:
            p = root / "benchmarks" / ("%s.csv" % name)
            if p.exists():
                return self._series(p, root / "benchmarks" / ("%s.source.json" % name), False,
                                    "Benchmark %s" % name, start, end)
        return None

    def _announcement_rows(self, path: Path, sec: Security, since, category_default: str) -> list:
        if not path.exists():
            return []
        syn = self._synthetic(sec)
        out = []
        for i, row in enumerate(_read_csv(path), start=2):
            try:
                d = parse_date(row["date"])
                src = self._source(row, row.get("subject") or row.get("headline") or "", syn)
            except (KeyError, ValueError, ProviderError) as exc:
                self.issues.append(("%s line %d" % (path.name, i), str(exc)))
                continue
            if since and d < since:
                continue
            out.append(Announcement(date=d, exchange=row.get("exchange") or row.get("publisher") or "",
                                    subject=row.get("subject") or row.get("headline") or "",
                                    category=row.get("category") or category_default,
                                    url=src.url, source=src, details=row.get("details", "")))
        return sorted(out, key=lambda a: a.date, reverse=True)

    def announcements(self, sec: Security, since=None) -> list:
        d = self._company_dir(sec)
        return self._announcement_rows(d / "announcements.csv", sec, since, "") if d else []

    def news(self, sec: Security, since=None) -> list:
        d = self._company_dir(sec)
        return self._announcement_rows(d / "news.csv", sec, since, "news") if d else []

    def shareholding(self, sec: Security) -> list:
        d = self._company_dir(sec)
        if not d or not (d / "shareholding.csv").exists():
            return []
        syn = self._synthetic(sec)
        out = []
        for i, row in enumerate(_read_csv(d / "shareholding.csv"), start=2):
            try:
                q = parse_date(row["quarter_end"])
                rec = ShareholdingRecord(
                    quarter_end=q, promoter_pct=_float(row.get("promoter_pct")),
                    promoter_pledged_pct=_float(row.get("promoter_pledged_pct")),
                    fii_pct=_float(row.get("fii_pct")), dii_pct=_float(row.get("dii_pct")),
                    public_pct=_float(row.get("public_pct")),
                    source=self._source(row, "Shareholding pattern", syn, fy_label(q, "Q")))
            except (KeyError, ValueError, ProviderError) as exc:
                self.issues.append(("shareholding.csv line %d" % i, str(exc)))
                continue
            out.append(rec)
        return sorted(out, key=lambda r: r.quarter_end)

    def governance(self, sec: Security) -> Optional[dict]:
        d = self._company_dir(sec)
        g = self._json(d / "governance.json") if d else None
        if not g:
            return None
        syn = self._synthetic(sec)
        for fy, rec in (g.get("fiscal_years") or {}).items():
            s = rec.get("source") or {}
            if not s.get("url"):
                self.issues.append(("governance.json %s" % fy, "no source url"))
                rec["_source"] = None
                continue
            rec["_source"] = Source(url=s["url"], title=s.get("title", "Annual report %s" % fy),
                                    publisher=s.get("publisher", ""), official=bool(s.get("official")),
                                    provider=self.name, retrieved_at=s.get("retrieved_at") or now_ist().isoformat(),
                                    published=s.get("published"), period=fy, synthetic=syn,
                                    note=("page %s" % s["page"]) if s.get("page") else "manual/local file entry")
        return g
