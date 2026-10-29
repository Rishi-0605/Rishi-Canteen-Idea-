"""BSE adapter. Official source.

STATUS: written against BSE's observed API field names, NOT verified against
the live API (blocked in the development sandbox). Parser tests use
hand-written format fixtures.

Endpoints:
  announcements  https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?...&strScrip=<code>
                 JSON {"Table": [{NEWSSUB, NEWS_DT, CATEGORYNAME, ATTACHMENTNAME, HEADLINE, SCRIP_CD}]}
  attachments    https://www.bseindia.com/xml-data/corpfiling/AttachLive/<ATTACHMENTNAME>
"""

from __future__ import annotations

import datetime as dt
import json

from ..models import Announcement, Security, Source, now_ist, parse_date
from .base import Provider, ProviderError
from .http import FetchError, HttpClient

ANN_URL = ("https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1"
           "&strPrevDate=%s&strScrip=%s&strSearch=P&strToDate=%s&strType=C&subcategory=-1")
ATTACH_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/%s"
HEADERS = {"Referer": "https://www.bseindia.com/", "Accept": "application/json"}


def parse_announcements(payload: dict, scrip: str, retrieved_at: str) -> list:
    out = []
    for r in (payload or {}).get("Table") or []:
        if str(r.get("SCRIP_CD", scrip)) != str(scrip):
            continue
        try:
            d = parse_date((r.get("NEWS_DT") or r.get("DT_TM") or "")[:10])
        except ValueError:
            continue
        att = r.get("ATTACHMENTNAME")
        url = ATTACH_URL % att if att else "https://www.bseindia.com/corporates/ann.html"
        subject = r.get("NEWSSUB") or r.get("HEADLINE") or ""
        src = Source(url=url, title="BSE announcement: %s" % subject, publisher="BSE", official=True,
                     provider="bse", retrieved_at=retrieved_at, published=d.isoformat())
        out.append(Announcement(date=d, exchange="BSE", subject=subject,
                                category=r.get("CATEGORYNAME") or "", url=url, source=src,
                                details=(r.get("HEADLINE") or "")[:500]))
    return sorted(out, key=lambda a: a.date, reverse=True)


class BSEProvider(Provider):
    name = "bse"
    official = True
    capabilities = frozenset(["announcements"])

    def __init__(self, http: HttpClient, lookback_days: int = 120):
        self.http = http
        self.lookback = lookback_days
        http.set_min_interval("api.bseindia.com", 1.5)

    def announcements(self, sec: Security, since=None) -> list:
        if not sec.bse_code:
            return []
        to = now_ist().date()
        frm = since or (to - dt.timedelta(days=self.lookback))
        url = ANN_URL % (frm.strftime("%Y%m%d"), sec.bse_code, to.strftime("%Y%m%d"))
        try:
            payload = json.loads(self.http.get(url, headers=HEADERS, provider=self.name))
        except (FetchError, ValueError) as exc:
            raise ProviderError("BSE announcements unavailable: %s" % exc)
        return parse_announcements(payload, sec.bse_code, now_ist().isoformat())
