"""Company investor-relations websites: annual reports, results, presentations,
transcripts.

Reads `investor_relations` from the company profile (company.json):

    "investor_relations": {
      "pages": ["https://<company domain>/investors/financials"],   # scanned for PDF links
      "documents": [{"url": "...pdf", "kind": "results", "period": "Q2FY26", "published": "2025-11-10"}],
      "allowed_domains": ["<company domain>"]                        # links elsewhere are ignored
    }

Downloads are cached (HTTP cache) and text is extracted page by page
(fortune_research/documents.py). Company websites change layout often and
many publish scanned PDFs, so a page that yields no PDF links or a PDF without
text is reported, not guessed at.

STATUS: not verified live (company websites are blocked in the build sandbox).
"""

from __future__ import annotations

from .. import documents as D
from ..models import Security
from .base import Provider, ProviderError
from .http import FetchError, HttpClient


class IRProvider(Provider):
    name = "ir"
    official = True  # the company's own publication
    capabilities = frozenset(["documents"])

    def __init__(self, http: HttpClient, max_documents: int = 12):
        self.http = http
        self.max_documents = max_documents
        self.diagnostics: dict = {}

    def documents(self, sec: Security, profile=None) -> list:
        ir = (profile or {}).get("investor_relations") or {}
        if not ir:
            return []
        allowed = ir.get("allowed_domains") or []
        listed = list(ir.get("documents") or [])
        diag = self.diagnostics["documents"] = {"pages": [], "errors": []}
        for page in ir.get("pages") or []:
            try:
                html = self.http.get(page, provider=self.name).decode("utf-8", "replace")
            except FetchError as exc:
                diag["errors"].append("%s: %s" % (page, exc))
                continue
            links = D.pdf_links(html, page, allowed)
            diag["pages"].append({"url": page, "pdf_links": len(links)})
            listed += [l for l in links if l["url"] not in {d["url"] for d in listed}]
        if not listed:
            if diag["errors"]:
                raise ProviderError("investor-relations pages unavailable: " + "; ".join(diag["errors"]))
            return []
        out = []
        for d in listed[: self.max_documents]:
            try:
                data = self.http.get(d["url"], provider=self.name)
            except FetchError as exc:
                diag["errors"].append("%s: %s" % (d["url"], exc))
                continue
            host = d["url"].split("/")[2]
            out.append(D.build(data, d["url"], title=d.get("text") or d.get("title") or "", kind=d.get("kind"),
                               period=d.get("period"), published=d.get("published"), official=True, publisher=host))
        return out
