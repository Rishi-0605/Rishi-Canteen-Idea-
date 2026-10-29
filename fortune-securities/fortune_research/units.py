"""Unit normalisation. Amounts become INR crore; per-share values stay INR per share.

An unknown unit raises UnitError instead of being guessed.
"""

from __future__ import annotations

CRORE = 1e7

AMOUNT_TO_CRORE = {
    "inr crore": 1.0, "crore": 1.0, "cr": 1.0, "rs crore": 1.0, "₹ crore": 1.0,
    "inr lakh": 0.01, "lakh": 0.01, "rs lakh": 0.01, "₹ lakh": 0.01,
    "inr million": 0.1, "million": 0.1, "inr mn": 0.1, "rs million": 0.1,
    "inr billion": 100.0, "billion": 100.0, "inr bn": 100.0,
    "inr thousand": 1e-4, "thousand": 1e-4,
    "inr": 1e-7, "rs": 1e-7, "rupees": 1e-7, "₹": 1e-7,
}
PER_SHARE = {"inr per share": "INR per share", "inr/share": "INR per share", "rs per share": "INR per share",
             "₹ per share": "INR per share"}
COUNTS = {"shares": 1.0, "number": 1.0, "lakh shares": 1e5, "crore shares": 1e7, "million shares": 1e6}
DIMENSIONLESS = {"%": "%", "percent": "%", "x": "x", "ratio": "x", "days": "days"}

CANONICAL_AMOUNT = "INR crore"


class UnitError(ValueError):
    pass


def normalise(value, unit: str):
    """Return (value, canonical_unit). Raises UnitError for unknown units."""
    if value is None:
        return None, unit
    u = (unit or "").strip().lower()
    if u in AMOUNT_TO_CRORE:
        return float(value) * AMOUNT_TO_CRORE[u], CANONICAL_AMOUNT
    if u in PER_SHARE:
        return float(value), PER_SHARE[u]
    if u in COUNTS:
        return float(value) * COUNTS[u], "shares"
    if u in DIMENSIONLESS:
        return float(value), DIMENSIONLESS[u]
    raise UnitError("unknown unit %r" % unit)
