"""Credible-news adapter: RSS/Atom feeds you configure, restricted to an allowlist
of publisher domains. Headlines are leads, not facts; the report says so.

STATUS: parser tested on a hand-written RSS fixture; live feeds not verified.
"""

from __future__ import annotations

import email.utils
import re
import urllib.parse
import xml.etree.ElementTree as ET

from ..models import Announcement, Security, Source, now_ist, parse_date
from .base import Provider
from .http import FetchError, HttpClient


def _domain_allowed(url: str, allowed: list) -> bool:
    host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
    return any(host == d or host.endswith("." + d) for d in allowed)


def _date(text: str):
    if not text:
        return None
    try:
        return email.utils.parsedate_to_datetime(text).date()
    except (TypeError, ValueError):
        try:
            return parse_date(text[:10])
        except ValueError:
            return None


def parse_feed(xml_bytes: bytes, allowed: list, retrieved_at: str) -> list:
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        get = {c.tag.split("}")[-1]: c for c in it}
        title = (get["title"].text or "").strip() if "title" in get else ""
        link = ""
        if "link" in get:
            link = (get["link"].text or get["link"].get("href") or "").strip()
        # explicit None checks: an Element with no children is falsy
        stamp = next((get[k].text for k in ("pubDate", "published", "updated") if get.get(k) is not None), None)
        d = _date(stamp or "")
        if not title or not link or not d or not _domain_allowed(link, allowed):
            continue
        host = urllib.parse.urlsplit(link).netloc
        src = Source(url=link, title=title, publisher=host, official=False, provider="rss",
                     retrieved_at=retrieved_at, published=d.isoformat(), note="news headline; verify in full text")
        items.append((d, title, link, host, src))
    return items


def mentions(title: str, sec: Security) -> bool:
    words = [w for w in re.split(r"\W+", (sec.name or "").lower()) if w and w not in ("ltd", "limited", "the", "india")]
    low = title.lower()
    if sec.nse_symbol and re.search(r"\b%s\b" % re.escape(sec.nse_symbol.lower()), low):
        return True
    return bool(words) and all(w in low for w in words[:2])


class RSSProvider(Provider):
    name = "rss"
    official = False
    capabilities = frozenset(["news"])

    def __init__(self, http: HttpClient, feeds: list, allowed_domains: list):
        self.http, self.feeds, self.allowed = http, feeds, allowed_domains

    def news(self, sec: Security, since=None) -> list:
        out = []
        for feed in self.feeds:
            try:
                items = parse_feed(self.http.get(feed, provider=self.name), self.allowed, now_ist().isoformat())
            except (FetchError, ET.ParseError):
                continue
            for d, title, link, host, src in items:
                if (since and d < since) or not mentions(title, sec):
                    continue
                out.append(Announcement(date=d, exchange=host, subject=title, category="news", url=link, source=src))
        return sorted(out, key=lambda a: a.date, reverse=True)
