"""Company documents (annual reports, results, investor presentations, earnings-call
transcripts): PDF text extraction with page numbers, unit detection, and a
figure locator that returns candidate values WITH their page and line.

PDF figures are never fed into calculations automatically: layout extraction can
split columns, drop minus signs or mix periods. They are evidence to check, and
the verification worksheet records who confirmed each one against the page.
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Optional

KINDS = [  # (kind, patterns) first match wins
    ("transcript", [r"transcript", r"con[- ]?call", r"earnings call"]),
    ("presentation", [r"presentation", r"investor[- ]deck", r"analyst meet"]),
    ("annual_report", [r"annual[- ]report", r"\bar[- ]?20\d\d"]),
    ("results", [r"financial[- ]results?", r"\bresults?\b", r"quarter", r"\bq[1-4]\b"]),
    ("shareholding", [r"shareholding"]),
    ("disclosure", [r"disclosure", r"intimation", r"outcome"]),
]
UNIT_PATTERNS = [  # (canonical unit, pattern)
    ("INR crore", r"(?:₹|rs\.?|inr|rupees)\s*(?:in\s*)?crores?|in\s*(?:₹|rs\.?|inr)?\s*crores?|\(\s*(?:₹|rs\.?)?\s*cr(?:ore)?s?\.?\s*\)"),
    ("INR lakh", r"(?:₹|rs\.?|inr|rupees)\s*(?:in\s*)?lakhs?|in\s*(?:₹|rs\.?|inr)?\s*lakhs?|lacs"),
    ("INR million", r"(?:₹|rs\.?|inr)\s*(?:in\s*)?millions?|in\s*(?:₹|rs\.?|inr)?\s*millions?|(?:₹|inr)\s*mn\b"),
    ("INR thousand", r"(?:₹|rs\.?|inr)\s*(?:in\s*)?'?000s?|in\s*thousands"),
]
NUMBER = re.compile(r"\(?-?(?:\d{1,3}(?:,\d{2,3})+|\d+)(?:\.\d+)?\)?")
PERIOD = re.compile(r"(?:FY\s?'?(\d{2,4}))|(20\d\d)\s*[-–/]\s*(\d{2,4})|(Q[1-4])\s*FY\s?'?(\d{2,4})", re.I)


def classify(text: str) -> str:
    low = (text or "").lower()
    for kind, pats in KINDS:
        if any(re.search(p, low) for p in pats):
            return kind
    return "other"


def period_hint(text: str) -> Optional[str]:
    m = PERIOD.search(text or "")
    if not m:
        return None
    if m.group(4):
        return "%sFY%s" % (m.group(4).upper(), m.group(5)[-2:])
    if m.group(1):
        return "FY%s" % m.group(1)[-2:]
    return "FY%s" % m.group(3)[-2:]


def detect_unit(text: str) -> Optional[str]:
    low = (text or "").lower()
    found = [u for u, p in UNIT_PATTERNS if re.search(p, low)]
    return found[0] if len(found) == 1 else ("AMBIGUOUS: " + ", ".join(found) if found else None)


def to_number(token: str) -> Optional[float]:
    t = token.strip()
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


@dataclass
class Document:
    url: str
    kind: str
    title: str
    sha256: str
    pages: list = field(default_factory=list)  # page texts, index 0 = page 1
    period: Optional[str] = None
    published: Optional[str] = None
    official: bool = True
    publisher: str = ""
    units_by_page: dict = field(default_factory=dict)
    error: Optional[str] = None

    def summary(self) -> dict:
        return {"url": self.url, "kind": self.kind, "title": self.title, "sha256": self.sha256, "pages": len(self.pages),
                "period": self.period, "published": self.published, "official": self.official, "publisher": self.publisher,
                "units_detected": sorted({u for u in self.units_by_page.values() if u}), "error": self.error}


def extract_pdf(data: bytes) -> list:
    """Page texts. Raises ValueError if the bytes are not a PDF."""
    if not data.startswith(b"%PDF"):
        raise ValueError("not a PDF (first bytes %r)" % data[:8])
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return [(p.extract_text() or "") for p in reader.pages]


def build(data: bytes, url: str, title: str = "", kind: Optional[str] = None, period: Optional[str] = None,
          published: Optional[str] = None, official: bool = True, publisher: str = "") -> Document:
    sha = hashlib.sha256(data).hexdigest()
    doc = Document(url=url, kind=kind or classify(title + " " + url), title=title or url.rsplit("/", 1)[-1], sha256=sha,
                   period=period or period_hint(title + " " + url), published=published, official=official, publisher=publisher)
    try:
        doc.pages = extract_pdf(data)
    except Exception as exc:  # report, never guess content
        doc.error = "text extraction failed: %s" % exc
        return doc
    if not any(t.strip() for t in doc.pages):
        doc.error = "PDF has no extractable text (scanned image?): OCR needed"
    doc.units_by_page = {i + 1: detect_unit(t) for i, t in enumerate(doc.pages)}
    if not doc.period:
        doc.period = period_hint(" ".join(doc.pages[:2])[:3000])
    return doc


def locate(doc: Document, label: str, max_hits: int = 10) -> list:
    """Lines containing `label` with the numbers on them, the page, and that page's unit statement."""
    hits = []
    pat = re.compile(re.escape(label), re.I)
    for i, text in enumerate(doc.pages):
        for line in text.splitlines():
            if pat.search(line):
                nums = [n for n in (to_number(t) for t in NUMBER.findall(line[pat.search(line).end():])) if n is not None]
                hits.append({"page": i + 1, "line": line.strip()[:200], "numbers": nums, "unit": doc.units_by_page.get(i + 1),
                             "status": "needs_review"})
                if len(hits) >= max_hits:
                    return hits
    return hits


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def pdf_links(html: str, base_url: str, allowed_domains: list) -> list:
    """PDF links on an investor-relations page, restricted to the allowed domains."""
    import urllib.parse

    p = _Links()
    p.feed(html)
    out, seen = [], set()
    for href, text in p.links:
        url = urllib.parse.urljoin(base_url, href)
        host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
        if ".pdf" not in url.lower() or url in seen:
            continue
        if allowed_domains and not any(host == d or host.endswith("." + d) for d in allowed_domains):
            continue
        seen.add(url)
        out.append({"url": url, "text": text, "kind": classify(text + " " + url), "period": period_hint(text + " " + url)})
    return out
