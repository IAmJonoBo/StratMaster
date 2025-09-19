from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from research_mcp.clients import CrawlerClient, MetasearchClient, ProvenanceEmitter
from research_mcp.config import CrawlerSettings, MetasearchSettings, ProvenanceSettings
from research_mcp.models import CachedPageResource


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, *, response):
        self.response = response
        self.requested = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None, headers=None):
        self.requested.append({"url": url, "params": params, "headers": headers})
        return DummyResponse(self.response)


@pytest.mark.parametrize(
    "payload",
    [
        [{"title": "A", "url": "https://example.com/a", "snippet": "text"}],
        {
            "results": [
                {"title": "B", "url": "https://example.com/b", "content": "content"}
            ]
        },
    ],
)
def test_metasearch_client_uses_network(monkeypatch, payload):
    settings = MetasearchSettings(
        endpoint="https://searx.local/search",
        api_key="token",
        timeout=5,
        use_network=True,
    )
    client = MetasearchClient(settings)

    dummy = DummyClient(response=payload)
    monkeypatch.setattr(
        "research_mcp.clients.httpx", SimpleNamespace(Client=lambda timeout: dummy)
    )

    results = client.search("brand strategy", limit=2)

    assert dummy.requested, "expected HTTP request to be made"
    first = dummy.requested[0]
    assert first["url"] == "https://searx.local/search"
    assert first["headers"]["Authorization"] == "Bearer token"
    assert len(results) == 1
    assert str(results[0].url).startswith("https://example.com")


def test_crawler_falls_back_when_playwright_missing(monkeypatch):
    settings = CrawlerSettings(use_network=True, use_playwright=True)
    monkeypatch.setattr("research_mcp.clients.sync_playwright", None)
    crawler = CrawlerClient(settings)
    content = crawler.fetch("https://example.com", render_js=True)
    assert "Synthetic content" in content


def test_provenance_emitter_logs_when_minio_missing(caplog):
    caplog.set_level("WARNING")
    emitter = ProvenanceEmitter(
        ProvenanceSettings(minio_endpoint="http://minio", minio_bucket="bucket")
    )
    page = CachedPageResource(
        url="https://example.com",
        content="data",
        fetched_at=datetime.now(timezone.utc),
        sha256="hash",
    )
    emitter.emit(page, "cache-1")
    assert any("MinIO" in record.message for record in caplog.records)
