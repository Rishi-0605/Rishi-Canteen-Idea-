"""Splits, bonus issues and consolidations.

- `parse_subject` turns an exchange corporate-action subject ("Bonus 1:2",
  "Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share")
  into a kind and a share-count factor (shares after / shares before).
- `adjust_prices` back-adjusts an UNADJUSTED price history so a split does not
  look like a crash. Already-adjusted series are left alone; a series of unknown
  adjustment is checked for the tell-tale gap on the ex-date.
- `adjust_per_share` restates EPS and share counts from filings published BEFORE
  an ex-date, so growth is like-for-like. Filings published after the ex-date
  are left alone: Ind AS 33 already requires them to restate prior periods.
- Only actions with ex-date on or before the analysis date are applied (no look-ahead).
"""

from __future__ import annotations

import dataclasses
import re
from typing import Optional

from ..models import DataIssue, PriceBar

BONUS = re.compile(r"\bbonus\b[^0-9]*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", re.I)
FV_CHANGE = re.compile(r"from\s*(?:rs|re|inr|₹)?\.?\s*([\d.]+)\s*/?-?.*?\bto\s*(?:rs|re|inr|₹)?\.?\s*([\d.]+)", re.I | re.S)


def parse_subject(text: str) -> tuple:
    """-> (kind, factor). factor is None when the action does not change the share count
    or cannot be parsed (then kind says so)."""
    t = " ".join((text or "").split())
    low = t.lower()
    m = BONUS.search(t)
    if m:
        new, held = float(m.group(1)), float(m.group(2))
        return ("bonus", (new + held) / held) if held > 0 else ("bonus_unparsed", None)
    if "split" in low or "sub-division" in low or "subdivision" in low or "consolidation" in low:
        m = FV_CHANGE.search(t)
        if m:
            old, new = float(m.group(1)), float(m.group(2))
            if old > 0 and new > 0 and old != new:
                return ("split" if old > new else "consolidation"), old / new
        return ("split_unparsed", None)
    if "dividend" in low:
        return "dividend", None
    if "rights" in low:
        return "rights", None  # changes share count by subscription, not a pure factor
    return "other", None


def applicable(actions: list, as_of) -> list:
    return sorted([a for a in actions if a.factor and a.ex_date <= as_of], key=lambda a: a.ex_date)


def adjust_prices(series, actions: list, as_of) -> list:
    """Mutates series.bars in place when adjustment is needed. Returns DataIssues explaining what was done."""
    issues = []
    acts = applicable(actions, as_of)
    if not series or not series.bars or not acts:
        return issues
    if series.adjusted is True:
        return issues
    to_apply = []
    for a in acts:
        if a.ex_date <= series.bars[0].date or a.ex_date > series.bars[-1].date:
            continue
        if series.adjusted is None:
            # unknown: look for the gap. Unadjusted data drops by about 1/factor on the ex-date.
            idx = next((i for i, b in enumerate(series.bars) if b.date >= a.ex_date), None)
            if idx is None or idx == 0:
                continue
            ratio = series.bars[idx].close / series.bars[idx - 1].close
            if abs(ratio * a.factor - 1) < 0.25:
                to_apply.append(a)
            else:
                issues.append(DataIssue("info", "ca_already_adjusted", "%s on %s: no price gap at the ex-date, history treated as "
                                        "already adjusted" % (a.description, a.ex_date), "prices"))
        else:
            to_apply.append(a)
    for a in to_apply:
        cut = a.ex_date
        series.bars = [PriceBar(b.date, b.open / a.factor, b.high / a.factor, b.low / a.factor, b.close / a.factor, b.volume * a.factor)
                       if b.date < cut else b for b in series.bars]
        issues.append(DataIssue("info", "ca_price_adjusted", "prices before %s divided by %g for %s (volumes multiplied)"
                                % (cut, a.factor, a.description), "prices"))
    if to_apply:
        series.adjusted = True
    return issues


def adjust_per_share(facts: list, actions: list, as_of) -> tuple:
    """Return (new fact list, issues). Restates eps and share counts from filings published before an ex-date."""
    acts = applicable(actions, as_of)
    if not acts:
        return facts, []
    out, issues, unknown = [], [], 0
    for f in facts:
        if f.name not in ("eps_diluted", "eps_basic", "shares_outstanding") or f.value is None:
            out.append(f)
            continue
        pub = f.source.published[:10] if f.source.published else None
        factor, applied = 1.0, []
        for a in acts:
            if f.period_end >= a.ex_date:
                continue  # period already after the action
            if pub is None:
                unknown += 1
                continue
            if pub < a.ex_date.isoformat():
                factor *= a.factor
                applied.append("%s (ex %s)" % (a.description, a.ex_date))
        if factor != 1.0:
            v = f.value / factor if f.name.startswith("eps") else f.value * factor
            f = dataclasses.replace(f, value=v, note="restated for " + "; ".join(applied))
        out.append(f)
    if unknown:
        issues.append(DataIssue("warning", "ca_publication_unknown", "%d per-share figures predate a split/bonus but have no "
                                "publication date, so it is unknown whether they are already restated; left as reported" % unknown,
                                "financials"))
    n = sum(1 for f in out if f.note.startswith("restated"))
    if n:
        issues.append(DataIssue("info", "ca_per_share_restated", "%d per-share figures restated for splits/bonuses" % n, "financials"))
    return out, issues


def explain_quantity(held: float, from_txns: float, actions: list, after) -> Optional[str]:
    """If a holdings/transactions quantity gap equals the product of later split/bonus factors, say so."""
    acts = [a for a in actions if a.factor and (after is None or a.ex_date > after)]
    f = 1.0
    for a in sorted(acts, key=lambda a: a.ex_date):
        f *= a.factor
        if from_txns and abs(held - from_txns * f) < 1e-6:
            return "explained by %s" % "; ".join("%s (ex %s)" % (x.description, x.ex_date)
                                                   for x in sorted(acts, key=lambda a: a.ex_date) if x.ex_date <= a.ex_date)
    return None
