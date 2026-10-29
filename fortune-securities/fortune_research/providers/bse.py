"""BSE adapter. Official source.

STATUS: written against BSE's observed API field names, NOT verified against
the live API (blocked in the development sandbox). Parser tests use
hand-written format fixtures.

Endpoints:
  announcements  https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?...&strScrip=<code>
                 JSON {"Table": [{NEWSSUB, NEWS_DT, CATEGORYNAME, ATTACHMENTNAME, HEADLINE, SCRIP_CD}]}
  attachments    https://www.bseindia.com/xml-data/corpfiling/AttachLive/<ATTACHMENTNAME>
  scrip master   https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active
                 JSON list [{SCRIP_CD, Scrip_Name, ISIN_NUMBER, scrip_id, FACE_VALUE, Status, GROUP}]
"""

from __future__ import annotations

import datetime as dt

from ..models import Announcement, Security, Source, now_ist, parse_date
from .base import Provider, ProviderError
from .http import FetchError, HttpClient, parse_json

ANN_URL = ("https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1"
           "&strPrevDate=%s&strScrip=%s&strSearch=P&strToDate=%s&strType=C&subcategory=-1")
ATTACH_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/%s"
MASTER_URL = ("https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity"
              "&status=Active")
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


def parse_scrip_master(payload, retrieved_at: str) -> list:
    src = Source(url=MASTER_URL, title="BSE list of scrips (equity, active)", publisher="BSE", official=True, provider="bse",
                 retrieved_at=retrieved_at)
    rows = payload if isinstance(payload, list) else (payload or {}).get("Table") or []
    out = []
    for r in rows:
        code = str(r.get("SCRIP_CD") or r.get("Scrip_Cd") or "").strip()
        if not code:
            continue
        fv = r.get("FACE_VALUE")
        try:
            fv = float(fv) if fv not in (None, "") else None
        except ValueError:
            fv = None
        out.append({"name": (r.get("Issuer_Name") or r.get("Scrip_Name") or "").strip(), "isin": (r.get("ISIN_NUMBER") or "").strip() or None,
                    "nse_symbol": None, "bse_code": code, "bse_id": (r.get("scrip_id") or "").strip() or None,
                    "series": None, "face_value": fv, "synthetic": False, "source": src})
    return out


class BSEProvider(Provider):
    name = "bse"
    official = True
    capabilities = frozenset(["master", "announcements"])

    def __init__(self, http: HttpClient, lookback_days: int = 120):
        self.http = http
        self.lookback = lookback_days
        http.set_min_interval("api.bseindia.com", 1.5)

    def securities_master(self) -> list:
        try:
            rows = parse_scrip_master(parse_json(self.http.get(MASTER_URL, headers=HEADERS, provider=self.name), MASTER_URL),
                                      now_ist().isoformat())
        except FetchError as exc:
            raise ProviderError("BSE scrip master unavailable: %s" % exc)
        if not rows:
            raise ProviderError("BSE scrip master parsed but empty (format changed?)")
        return rows

    def announcements(self, sec: Security, since=None) -> list:
        if not sec.bse_code:
            return []
        to = now_ist().date()
        frm = since or (to - dt.timedelta(days=self.lookback))
        url = ANN_URL % (frm.strftime("%Y%m%d"), sec.bse_code, to.strftime("%Y%m%d"))
        try:
            payload = parse_json(self.http.get(url, headers=HEADERS, provider=self.name), url)
        except FetchError as exc:
            raise ProviderError("BSE announcements unavailable: %s" % exc)
        return parse_announcements(payload, sec.bse_code, now_ist().isoformat())
