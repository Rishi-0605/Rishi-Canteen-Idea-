"""Derive metrics with lineage. If any input is missing the result is a Metric
with value None and `missing` listing what was absent; nothing is imputed."""

from __future__ import annotations

import math
from typing import Callable, Optional

from ..models import Fact, Metric


def source_ids_of(x) -> list:
    if x is None:
        return []
    if isinstance(x, Fact):
        return [x.source.id]
    if isinstance(x, Metric):
        return list(x.source_ids)
    return []


def derive(name: str, period: str, unit: str, formula: str, inputs: dict, fn: Callable,
           note: str = "") -> Metric:
    missing = [k for k, v in inputs.items() if v is None or getattr(v, "value", None) is None]
    ids = []
    for v in inputs.values():
        for s in source_ids_of(v):
            if s not in ids:
                ids.append(s)
    if missing:
        return Metric(name, None, unit, period, formula, ids, missing, note)
    try:
        value = fn(**{k: v.value for k, v in inputs.items()})
    except ZeroDivisionError:
        return Metric(name, None, unit, period, formula, ids, [], "denominator is zero")
    if value is None:
        return Metric(name, None, unit, period, formula, ids, [], note or "not meaningful for these inputs")
    if isinstance(value, complex) or math.isnan(value) or math.isinf(value):
        return Metric(name, None, unit, period, formula, ids, [], "not defined for these inputs")
    return Metric(name, value, unit, period, formula, ids, [], note)


def given(name: str, period: str, value: Optional[float], unit: str, formula: str, source_ids=None,
          note: str = "") -> Metric:
    return Metric(name, value, unit, period, formula, list(source_ids or []),
                  [] if value is not None else [name], note)


def cagr(start: float, end: float, years: float) -> Optional[float]:
    if years <= 0:
        raise ZeroDivisionError
    if start <= 0 or end <= 0:
        return None  # CAGR is not meaningful across a sign change or from zero
    return (end / start) ** (1.0 / years) - 1


def median(xs: list) -> Optional[float]:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def percentile(xs: list, p: float) -> Optional[float]:
    """Linear-interpolated percentile, p in [0, 100]."""
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p / 100.0
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)
