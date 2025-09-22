import pytest
from fastapi.testclient import TestClient
from research_mcp.app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_MCP_CACHE_DIR", str(tmp_path))
    monkeypatch.delenv("RESEARCH_MCP_ENABLE_NETWORK", raising=False)
    return TestClient(create_app())


def test_healthz_ok(client: TestClient):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_info_endpoint(client: TestClient):
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("name") == "research-mcp"
    assert "health" in body.get("capabilities", [])


def test_metasearch_endpoint_returns_results(client: TestClient):
    resp = client.post(
        "/tools/metasearch",
        json={"tenant_id": "tenant-a", "query": "strategy", "limit": 2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 2
    assert body["results"][0]["url"].startswith("https://example.com")


def test_crawl_endpoint_enforces_allowlist(client: TestClient):
    ok = client.post(
        "/tools/crawl",
        json={
            "tenant_id": "tenant-a",
            "spec": {"url": "https://example.com/page", "max_depth": 1},
        },
    )
    assert ok.status_code == 200

    blocked = client.post(
        "/tools/crawl",
        json={
            "tenant_id": "tenant-a",
            "spec": {"url": "https://evil.invalid", "max_depth": 1},
        },
    )
    assert blocked.status_code == 403


def test_provenance_resource_available_after_crawl(client: TestClient):
    crawl_resp = client.post(
        "/tools/crawl",
        json={
            "tenant_id": "tenant-a",
            "spec": {"url": "https://example.com/resource", "max_depth": 1},
        },
    )
    assert crawl_resp.status_code == 200
    cache_key = crawl_resp.json()["cache_key"]

    provenance = client.get(f"/resources/provenance/{cache_key}")
    assert provenance.status_code == 200
    assert provenance.json()["cache_key"] == cache_key

    cached_page = client.get(f"/resources/cached_page/{cache_key}")
    assert cached_page.status_code == 200
    assert "Synthetic content" in cached_page.json()["content"]
