"""High-level research service orchestrating metasearch, crawling, and caching."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

from .clients import ClientBundle
from .config import AppConfig
from .models import (
    CachedPageResource,
    CrawlRequest,
    CrawlResponse,
    MetasearchRequest,
    MetasearchResponse,
    ProvenanceResource,
)


class ResearchService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.clients = ClientBundle(config)

    def metasearch(self, payload: MetasearchRequest) -> MetasearchResponse:
        results = self.clients.metasearch.search(payload.query, payload.limit)
        return MetasearchResponse(query=payload.query, results=results)

    def crawl(self, payload: CrawlRequest) -> CrawlResponse:
        url = str(payload.spec.url)
        self._ensure_allowlisted(url)
        content = self.clients.crawler.fetch(url, render_js=payload.spec.render_js)
        sha = hashlib.sha256(url.encode("utf-8") + content.encode("utf-8")).hexdigest()
        cache_key = f"cache-{sha[:16]}"
        page = CachedPageResource(
            url=url,
            content=content,
            fetched_at=datetime.now(tz=timezone.utc),
            sha256=sha,
        )
        self.clients.storage.store_page(cache_key, page)
        self.clients.provenance.emit(page, cache_key)
        return CrawlResponse(
            url=url,
            status="fetched",
            content=content,
            sha256=sha,
            fetched_at=page.fetched_at,
            cache_key=cache_key,
        )

    def cached_page(self, cache_key: str) -> CachedPageResource:
        return self.clients.storage.get_page(cache_key)

    def provenance(self, cache_key: str) -> ProvenanceResource:
        return self.clients.storage.get_provenance(cache_key)

    def _ensure_allowlisted(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            raise ValueError("invalid url")
        allowlist = {domain.lower() for domain in self.config.crawler.allowlist}
        blocklist = {domain.lower() for domain in self.config.crawler.blocklist}
        if any(self._matches(host, domain) for domain in blocklist):
            raise PermissionError("domain not allow-listed")
        if not any(self._matches(host, domain) for domain in allowlist):
            raise PermissionError("domain not allow-listed")

    @staticmethod
    def _matches(host: str, domain: str) -> bool:
        return host == domain or host.endswith(f".{domain}")
