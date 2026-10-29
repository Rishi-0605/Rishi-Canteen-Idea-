"""Core data types. Every number carries where it came from.

A `Fact` is a figure taken from a source (a filing, an exchange file, a manual
input). A `Metric` is a figure computed from facts, and keeps its formula and
inputs. Neither ever holds an invented value: when an input is missing the
metric value is None and `missing` says what was absent.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")


def now_ist() -> dt.datetime:
    return dt.datetime.now(IST).replace(microsecond=0)


def parse_date(value: Any) -> Optional[dt.date]:
    """Accept date, datetime or ISO / dd-mm-yyyy / dd-Mon-yyyy strings."""
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value).strip()
    if not text or text.lower() in ("nan", "nat", "none"):
        return None
    try:
        return dt.datetime.fromisoformat(text).date()
    except ValueError:
        pass
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%d %b %Y", "%Y/%m/%d", "%d-%B-%Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("unrecognised date: %r" % value)


def parse_datetime(value: Any) -> Optional[dt.datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=IST)
    text = str(value).strip()
    try:
        out = dt.datetime.fromisoformat(text)
    except ValueError:
        d = parse_date(text)
        out = dt.datetime(d.year, d.month, d.day)
    return out if out.tzinfo else out.replace(tzinfo=IST)


def fy_label(period_end: dt.date, period_type: str) -> str:
    """Indian fiscal labels: FY ends 31 March. 2026-03-31 FY -> FY26, 2026-09-30 Q -> Q2FY27."""
    fy = period_end.year + (1 if period_end.month > 3 else 0)
    if period_type == "FY":
        return "FY%02d" % (fy % 100)
    if period_type == "Q":
        q = {6: 1, 9: 2, 12: 3, 3: 4}.get(period_end.month)
        return ("Q%dFY%02d" % (q, fy % 100)) if q else period_end.isoformat()
    return period_end.isoformat()


@dataclass(frozen=True)
class Source:
    url: str
    title: str
    publisher: str
    official: bool
    provider: str
    retrieved_at: str  # ISO timestamp, IST
    published: Optional[str] = None  # ISO date
    period: Optional[str] = None  # reporting period the source covers
    synthetic: bool = False
    note: str = ""

    @property
    def id(self) -> str:
        key = "|".join([self.url, self.title, self.period or "", self.published or ""])
        return "S" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["id"] = self.id
        return d


@dataclass(frozen=True)
class Fact:
    name: str
    value: Optional[float]
    unit: str
    period_end: dt.date
    period_type: str  # FY | Q | POINT
    basis: str  # consolidated | standalone | n/a
    source: Source

    @property
    def period_label(self) -> str:
        return fy_label(self.period_end, self.period_type)


@dataclass
class Metric:
    name: str
    value: Optional[float]
    unit: str
    period: str
    formula: str
    source_ids: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    note: str = ""

    @property
    def available(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict:
        return asdict(self)


SEVERITIES = ("info", "low", "medium", "high", "critical")


@dataclass
class Finding:
    module: str
    code: str
    severity: str
    message: str
    evidence: dict = field(default_factory=dict)
    source_ids: list = field(default_factory=list)

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError("bad severity %s" % self.severity)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DataIssue:
    severity: str  # info | warning | error
    code: str
    message: str
    dataset: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Security:
    name: str
    isin: Optional[str]
    nse_symbol: Optional[str] = None
    bse_code: Optional[str] = None
    series: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    face_value: Optional[float] = None
    synthetic: bool = False
    verification: list = field(default_factory=list)  # human-readable checks performed

    @property
    def key(self) -> str:
        """Stable identifier for storage: ISIN when known, else exchange code."""
        return self.isin or ("NSE:" + self.nse_symbol if self.nse_symbol else "BSE:%s" % self.bse_code)

    @property
    def display_symbol(self) -> str:
        return self.nse_symbol or ("BSE:%s" % self.bse_code)

    def yahoo_symbol(self, exchange: str = "NSE") -> Optional[str]:
        """Yahoo Finance tickers: NSE symbol + .NS, BSE scrip code + .BO. Unofficial use only."""
        if exchange == "NSE" and self.nse_symbol:
            return self.nse_symbol + ".NS"
        if exchange == "BSE" and self.bse_code:
            return str(self.bse_code) + ".BO"
        return None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PriceBar:
    date: dt.date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class PriceSeries:
    bars: list  # list[PriceBar], ascending
    source: Source
    exchange: str = "NSE"
    adjusted: Optional[bool] = None  # None = unknown

    @property
    def last(self) -> Optional[PriceBar]:
        return self.bars[-1] if self.bars else None

    def closes(self) -> list:
        return [b.close for b in self.bars]


@dataclass
class Announcement:
    date: dt.date
    exchange: str
    subject: str
    category: str
    url: str
    source: Source
    details: str = ""

    @property
    def fingerprint(self) -> str:
        key = "|".join([self.date.isoformat(), self.exchange, self.subject.strip().lower(), self.url])
        return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


@dataclass
class ShareholdingRecord:
    quarter_end: dt.date
    promoter_pct: Optional[float]
    promoter_pledged_pct: Optional[float]  # % of promoter holding that is pledged/encumbered
    fii_pct: Optional[float]
    dii_pct: Optional[float]
    public_pct: Optional[float]
    source: Source
