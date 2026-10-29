"""The provider interface. Add a data source by subclassing `Provider`,
declaring its capabilities and implementing the matching methods.

Capabilities:
  master         securities master (symbol / scrip code / ISIN / name)
  profile        company profile: sector, industry, shares outstanding, peers
  financials     list[Fact] from results / annual reports
  prices         PriceSeries (daily OHLCV)
  announcements  list[Announcement] (exchange disclosures)
  shareholding   list[ShareholdingRecord]
  governance     dict from the annual report (auditor, RPT, contingent liabilities)
  news           list[Announcement] with category "news" from credible publishers
  benchmark      PriceSeries for an index
  corporate_actions  list[CorporateAction] (splits, bonuses, dividends)
  documents      list[dict] of company documents (annual reports, results, presentations, transcripts)

A method returns None (or empty) when the provider has no data, and raises
ProviderError when it tried and failed. It never returns made-up values.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from ..models import PriceSeries, Security

CAPABILITIES = ("master", "profile", "financials", "prices", "announcements", "shareholding",
                "governance", "news", "benchmark", "corporate_actions", "documents")


class ProviderError(Exception):
    pass


class Provider:
    name = "base"
    official = False
    capabilities: frozenset = frozenset()

    def securities_master(self) -> list:
        """list[dict] with keys name, isin, nse_symbol, bse_code, series, synthetic, source (Source)."""
        raise NotImplementedError

    def profile(self, sec: Security) -> Optional[dict]:
        raise NotImplementedError

    def financials(self, sec: Security) -> list:
        raise NotImplementedError

    def prices(self, sec: Security, start: Optional[dt.date] = None,
               end: Optional[dt.date] = None) -> Optional[PriceSeries]:
        raise NotImplementedError

    def announcements(self, sec: Security, since: Optional[dt.date] = None) -> list:
        raise NotImplementedError

    def shareholding(self, sec: Security) -> list:
        raise NotImplementedError

    def governance(self, sec: Security) -> Optional[dict]:
        raise NotImplementedError

    def news(self, sec: Security, since: Optional[dt.date] = None) -> list:
        raise NotImplementedError

    def benchmark(self, name: str, start: Optional[dt.date] = None,
                  end: Optional[dt.date] = None) -> Optional[PriceSeries]:
        raise NotImplementedError

    def corporate_actions(self, sec: Security) -> list:
        raise NotImplementedError

    def documents(self, sec: Security) -> list:
        raise NotImplementedError
