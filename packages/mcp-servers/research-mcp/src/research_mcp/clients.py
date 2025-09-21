"""Client abstractions for external integrations used by the Research MCP server."""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlencode

from .config import (
    AppConfig,
    CrawlerSettings,
    MetasearchSettings,
    ProvenanceSettings,
    StorageSettings,
)
from .models import CachedPageResource, ProvenanceResource, SearchResult

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

try:  # pragma: no cover - optional dependency
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

try:  # pragma: no cover - optional dependency
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class MetasearchClient:
    def __init__(self, settings: MetasearchSettings):
        self.settings = settings

    def search(self, query: str, limit: int) -> List[SearchResult]:
        if self.settings.use_network and self.settings.endpoint and httpx is not None:
            try:
                params = {
                    "q": query,
                    "format": "json",
                    "timeout": self.settings.timeout,
                    "limit": limit,
                }
                headers: Dict[str, str] = {}
                if self.settings.api_key:
                    headers["Authorization"] = f"Bearer {self.settings.api_key}"
                with httpx.Client(timeout=self.settings.timeout) as client:
                    response = client.get(
                        self.settings.endpoint, params=params, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
            except Exception as exc:  # pragma: no cover - network failure path
                logger.warning(
                    "Metasearch network call failed; falling back to synthetic results",
                    exc_info=exc,
                )
                return self._synthetic(query, limit)
            return [
                SearchResult(
                    title=item.get("title") or f"Result {idx} for {query}",
                    url=item.get("url") or item.get("link") or "https://example.com",
                    snippet=item.get("content") or item.get("snippet") or "",
                    fetched_at=_utcnow(),
                )
                for idx, item in enumerate(
                    data if isinstance(data, list) else data.get("results", []), start=1
                )
            ][:limit]
        return self._synthetic(query, limit)

    def _synthetic(self, query: str, limit: int) -> List[SearchResult]:
        return [
            SearchResult(
                title=f"Synthetic result {idx}",
                url=f"https://example.com/{idx}?{urlencode({'q': query})}",
                snippet=f"Snippet for {query} #{idx}",
                fetched_at=_utcnow(),
            )
            for idx in range(1, limit + 1)
        ]


class CrawlerClient:
    def __init__(self, settings: CrawlerSettings):
        self.settings = settings

    def fetch(self, url: str, render_js: bool = False) -> str:
        wants_playwright = render_js and self.settings.use_playwright

        if wants_playwright:
            if not self.settings.use_network:
                logger.warning(
                    "Playwright rendering requested without network access; returning synthetic content"
                )
                return self._synthetic_content(url, render_js)

            if sync_playwright is None:
                logger.warning(
                    "Playwright not available; returning synthetic content instead of rendering"
                )
                return self._synthetic_content(url, render_js)

            with suppress(Exception):  # pragma: no cover - network path
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    try:
                        page = browser.new_page(user_agent=self.settings.user_agent)
                        page.goto(url, wait_until="networkidle")
                        return page.content()
                    finally:  # pragma: no cover
                        browser.close()
            logger.warning(
                "Playwright rendering failed; returning synthetic content"
            )
            return self._synthetic_content(url, render_js)

        if self.settings.use_network and httpx is not None:
            try:
                headers = {"User-Agent": self.settings.user_agent}
                with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Crawler network fetch failed; returning synthetic content",
                    exc_info=exc,
                )
        return self._synthetic_content(url, render_js)

    @staticmethod
    def _synthetic_content(url: str, render_js: bool) -> str:
        return f"Synthetic content for {url} (render_js={render_js})"


class StorageClient:
    def __init__(self, settings: StorageSettings):
        self.settings = settings
        self.base_path: Path = settings.base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store_page(self, cache_key: str, page: CachedPageResource) -> None:
        payload = {
            "url": str(page.url),
            "content": page.content,
            "fetched_at": page.fetched_at.isoformat(),
            "sha256": page.sha256,
        }
        file_path = self.base_path / f"{cache_key}.json"
        file_path.write_text(json.dumps(payload), encoding="utf-8")

    def get_page(self, cache_key: str) -> CachedPageResource:
        file_path = self.base_path / f"{cache_key}.json"
        if not file_path.exists():
            raise FileNotFoundError(cache_key)
        data: Dict[str, Any] = json.loads(file_path.read_text(encoding="utf-8"))
        return CachedPageResource(
            url=data["url"],
            content=data["content"],
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
            sha256=data["sha256"],
        )

    def get_provenance(self, cache_key: str) -> ProvenanceResource:
        page = self.get_page(cache_key)
        return ProvenanceResource(
            url=page.url,
            sha256=page.sha256,
            fetched_at=page.fetched_at,
            cache_key=cache_key,
        )


class ClientBundle:
    """Helper container to construct clients from config."""

    def __init__(self, config: AppConfig):
        self.metasearch = MetasearchClient(config.metasearch)
        self.crawler = CrawlerClient(config.crawler)
        self.storage = StorageClient(config.storage)
        self.provenance = ProvenanceEmitter(config.provenance)


class ProvenanceEmitter:
    """Writes provenance artefacts to external sinks (MinIO/OpenLineage)."""

    def __init__(self, settings: ProvenanceSettings):
        self.settings = settings

    def emit(self, page: CachedPageResource, cache_key: str) -> None:
        self._upload_minio(page, cache_key)
        self._emit_openlineage(page, cache_key)

    def _upload_minio(self, page: CachedPageResource, cache_key: str) -> None:
        if not (self.settings.minio_endpoint and self.settings.minio_bucket):
            return
        if boto3 is None:  # pragma: no cover - dependency missing
            logger.warning("boto3 not available; skipping MinIO provenance upload")
            return
        try:
            s3 = boto3.resource(  # type: ignore[attr-defined]
                "s3",
                endpoint_url=self.settings.minio_endpoint,
                aws_access_key_id=self.settings.minio_access_key,
                aws_secret_access_key=self.settings.minio_secret_key,
            )
            body = json.dumps(
                {
                    "url": str(page.url),
                    "fetched_at": page.fetched_at.isoformat(),
                    "sha256": page.sha256,
                    "cache_key": cache_key,
                }
            ).encode("utf-8")
            s3.Object(self.settings.minio_bucket, f"provenance/{cache_key}.json").put(  # type: ignore[attr-defined]
                Body=body,
                ContentType="application/json",
            )
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("failed to upload provenance to MinIO", exc_info=exc)

    def _emit_openlineage(self, page: CachedPageResource, cache_key: str) -> None:
        if not self.settings.enable_openlineage:
            return
        logger.debug(
            "openlineage-event",
            extra={
                "event": "provenance",
                "cache_key": cache_key,
                "sha256": page.sha256,
            },
        )
