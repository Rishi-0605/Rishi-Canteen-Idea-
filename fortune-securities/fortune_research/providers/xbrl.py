"""XBRL instance parser for Indian financial-results filings (SEBI LODR Reg. 33,
published by NSE/BSE).

Generic XBRL 2.1 handling: contexts (duration / instant, with or without
dimensions), units (INR, INR per share, shares), numeric facts with their
contextRef. Element names map to canonical line items through
config/xbrl_map.toml; anything numeric that does not map is reported in
`unmapped` so the mapping can be corrected, never silently dropped.

Rules:
- Only contexts WITHOUT dimensions (segment/scenario members) become facts:
  dimensional contexts are segment or component breakdowns, not totals.
- Duration of ~3 months -> Q, ~12 months -> FY; 6- and 9-month year-to-date
  contexts are kept out of the quarterly series (reported as "skipped_ytd").
- Monetary values in XBRL are in absolute rupees (the `decimals` attribute is
  precision, not scale) and are converted to INR crore.
- Each Fact's Source locator names the element and context, so every figure
  can be found again in the original document.

STATUS: tested on a hand-written instance in the documented structure, not yet
on a live filing.
"""

from __future__ import annotations

import datetime as dt
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config import PROJECT_ROOT
from ..models import Fact, Source, fy_label

XBRLI = "http://www.xbrl.org/2003/instance"
XBRLDI = "http://xbrl.org/2006/xbrldi"
MAP_FILE = PROJECT_ROOT / "config" / "xbrl_map.toml"
NON_FACT = {"context", "unit", "schemaRef", "linkbaseRef", "roleRef", "arcroleRef", "footnoteLink"}


class XBRLError(Exception):
    pass


@dataclass
class Context:
    id: str
    start: Optional[dt.date]
    end: Optional[dt.date]  # for instants: the instant
    instant: bool
    dimensional: bool

    @property
    def days(self) -> Optional[int]:
        return (self.end - self.start).days + 1 if self.start and self.end and not self.instant else None

    @property
    def period_type(self) -> Optional[str]:
        if self.instant:
            return "POINT"
        d = self.days
        if d is None:
            return None
        if 80 <= d <= 100:
            return "Q"
        if 350 <= d <= 380:
            return "FY"
        return None  # 6M / 9M year-to-date, or a non-standard period


@dataclass
class XBRLResult:
    facts: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    unmapped: list = field(default_factory=list)  # (element, contextRef, value)
    skipped: list = field(default_factory=list)  # (element, contextRef, reason)
    nonstandard_periods: list = field(default_factory=list)


def load_map(path: Path = MAP_FILE) -> dict:
    with open(path, "rb") as fh:
        m = tomllib.load(fh)
    item_of = {}
    for item, names in m["line_items"].items():
        for rank, n in enumerate(names):
            item_of.setdefault(n, (item, rank))
    meta_of = {n: k for k, names in m["metadata"].items() for n in names}
    return {"items": item_of, "meta": meta_of}


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _date(text: Optional[str]) -> Optional[dt.date]:
    return dt.date.fromisoformat(text.strip()[:10]) if text and text.strip() else None


def parse(xml_bytes: bytes, url: str, retrieved_at: str, published: Optional[str] = None,
          basis_hint: Optional[str] = None, mapping: Optional[dict] = None) -> XBRLResult:
    mapping = mapping or load_map()
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise XBRLError("not an XML document: %s" % exc)
    if _local(root.tag) != "xbrl":
        raise XBRLError("root element is <%s>, not <xbrl>" % _local(root.tag))
    contexts, units = {}, {}
    for c in root.iter("{%s}context" % XBRLI):
        per = c.find("{%s}period" % XBRLI)
        inst = per.find("{%s}instant" % XBRLI) if per is not None else None
        dim = c.find(".//{%s}segment" % XBRLI) is not None or c.find(".//{%s}scenario" % XBRLI) is not None
        if inst is not None:
            d = _date(inst.text)
            contexts[c.get("id")] = Context(c.get("id"), None, d, True, dim)
        elif per is not None:
            contexts[c.get("id")] = Context(c.get("id"), _date(per.findtext("{%s}startDate" % XBRLI)),
                                            _date(per.findtext("{%s}endDate" % XBRLI)), False, dim)
    for u in root.iter("{%s}unit" % XBRLI):
        meas = [m.text.split(":")[-1].strip() for m in u.iter("{%s}measure" % XBRLI) if m.text]
        div = u.find("{%s}divide" % XBRLI)
        units[u.get("id")] = ("per_share" if div is not None and "shares" in [x.lower() for x in meas]
                              else "shares" if [x.lower() for x in meas] == ["shares"]
                              else "INR" if "INR" in meas else (meas[0] if meas else "?"))
    res = XBRLResult()
    candidates = {}
    for el in root:
        name = _local(el.tag)
        if name in NON_FACT:
            continue
        ctx = contexts.get(el.get("contextRef"))
        text = (el.text or "").strip()
        if name in mapping["meta"]:
            key = mapping["meta"][name]
            if ctx is None or not ctx.dimensional:
                res.metadata.setdefault(key, text)
            continue
        if el.get("unitRef") is None:
            continue  # non-numeric, not metadata
        if ctx is None:
            res.skipped.append((name, el.get("contextRef"), "unknown context"))
            continue
        if el.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true" or text == "":
            continue
        try:
            val = float(text)
        except ValueError:
            res.skipped.append((name, ctx.id, "not a number: %r" % text[:30]))
            continue
        if name not in mapping["items"]:
            if not ctx.dimensional:
                res.unmapped.append((name, ctx.id, val))
            continue
        if ctx.dimensional:
            res.skipped.append((name, ctx.id, "dimensional (segment/component) context"))
            continue
        ptype = ctx.period_type
        if ptype is None:
            reason = "year-to-date or non-standard period (%s days)" % ctx.days
            res.skipped.append((name, ctx.id, reason))
            if ctx.days and ctx.days > 380:
                res.nonstandard_periods.append((name, ctx.id, ctx.days))
            continue
        item, rank = mapping["items"][name]
        unit = units.get(el.get("unitRef"), "?")
        if unit == "INR":
            value, cunit = val / 1e7, "INR crore"
        elif unit == "per_share":
            value, cunit = val, "INR per share"
        elif unit == "shares":
            value, cunit = val, "shares"
        else:
            res.skipped.append((name, ctx.id, "unsupported unit %s" % unit))
            continue
        key = (item, ptype, ctx.end)
        if key not in candidates or rank < candidates[key][0]:
            candidates[key] = (rank, name, ctx, value, cunit)
    basis = (res.metadata.get("basis") or basis_hint or "").strip().lower()
    basis = "consolidated" if basis.startswith("consol") else "standalone" if basis.startswith(("stand", "non")) else (basis or "unknown")
    res.metadata["basis_normalised"] = basis
    publisher = "NSE" if "nseindia" in url else "BSE" if "bseindia" in url else "exchange filing"
    for (item, ptype, end), (rank, name, ctx, value, cunit) in sorted(candidates.items(), key=lambda kv: (kv[0][2], kv[0][0])):
        src = Source(url=url, title="Financial results XBRL (%s, %s)" % (basis, fy_label(end, ptype)), publisher=publisher,
                     official=True, provider="xbrl", retrieved_at=retrieved_at, published=published,
                     period=fy_label(end, ptype), locator="%s @ %s" % (name, ctx.id))
        res.facts.append(Fact(item, value, cunit, end, ptype, basis, src, period_start=ctx.start))
    return res


def check_identity(res: XBRLResult, isin: Optional[str], nse_symbol: Optional[str], bse_code: Optional[str]) -> list:
    """Problems if the document names a different company than the one being researched."""
    out = []
    m = res.metadata
    if m.get("isin") and isin and m["isin"].strip().upper() != isin.upper():
        out.append("document ISIN %s does not match %s" % (m["isin"], isin))
    if m.get("symbol") and nse_symbol and m["symbol"].strip().upper() != nse_symbol.upper():
        out.append("document symbol %s does not match %s" % (m["symbol"], nse_symbol))
    if m.get("scrip_code") and bse_code and m["scrip_code"].strip() != str(bse_code):
        out.append("document scrip code %s does not match %s" % (m["scrip_code"], bse_code))
    if not any(m.get(k) for k in ("isin", "symbol", "scrip_code")):
        out.append("document carries no ISIN, symbol or scrip code: identity not confirmed")
    return out
