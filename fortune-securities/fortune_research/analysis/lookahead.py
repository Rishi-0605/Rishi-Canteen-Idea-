"""Point-in-time availability, to keep look-ahead bias out of historical research.

A figure is usable on the analysis date only if it had been published by then:
- with a publication date: published <= as_of;
- without one: it is assumed to have become public on the SEBI LODR filing
  deadline after its period end (Reg. 33: 45 days for a quarter, 60 days for the
  fourth quarter and the annual results; Reg. 31: 21 days for the shareholding
  pattern). The report states how many figures relied on that assumption.
Prices are cut at the analysis date and corporate actions apply only from their ex-date.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from ..models import DataIssue

RESULTS_DEADLINE_DAYS = {"Q": 45, "Q4": 60, "FY": 60, "POINT": 60}
SHAREHOLDING_DEADLINE_DAYS = 21


def assumed_public(period_end: dt.date, period_type: str) -> dt.date:
    key = "Q4" if period_type == "Q" and period_end.month == 3 else period_type
    return period_end + dt.timedelta(days=RESULTS_DEADLINE_DAYS.get(key, 60))


def is_available(published: Optional[str], period_end: dt.date, period_type: str, as_of: dt.date) -> tuple:
    """-> (available, assumed). `assumed` is True when the publication date was unknown."""
    if period_end > as_of:
        return False, False
    if published:
        return published[:10] <= as_of.isoformat(), False
    return assumed_public(period_end, period_type) <= as_of, True


def filter_facts(facts: list, as_of: dt.date) -> tuple:
    kept, assumed, dropped = [], 0, 0
    for f in facts:
        ok, assumed_flag = is_available(f.source.published, f.period_end, f.period_type, as_of)
        if ok:
            kept.append(f)
            assumed += assumed_flag
        else:
            dropped += 1
    issues = []
    if assumed:
        issues.append(DataIssue("info", "publication_assumed", "%d figures have no publication date; each was assumed public on the "
                                "LODR filing deadline after its period end" % assumed, "financials"))
    return kept, issues, dropped


def filter_shareholding(records: list, as_of: dt.date) -> tuple:
    kept, assumed = [], 0
    for r in records:
        if r.quarter_end > as_of:
            continue
        if r.source.published:
            if r.source.published[:10] <= as_of.isoformat():
                kept.append(r)
        elif r.quarter_end + dt.timedelta(days=SHAREHOLDING_DEADLINE_DAYS) <= as_of:
            kept.append(r)
            assumed += 1
    issues = [DataIssue("info", "publication_assumed", "%d shareholding records have no filing date; assumed filed 21 days after "
                        "quarter end (Reg. 31)" % assumed, "shareholding")] if assumed else []
    return kept, issues
