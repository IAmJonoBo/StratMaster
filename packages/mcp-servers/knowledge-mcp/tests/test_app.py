from fastapi.testclient import TestClient
from knowledge_mcp.app import create_app


def client():
    return TestClient(create_app())


def test_healthz(client=client()):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_info_lists_capabilities(client=client()):
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert "knowledge-mcp" in body["name"]
    assert "vector.search" in body["capabilities"]


def test_hybrid_query_returns_hits(client=client()):
    resp = client.post(
        "/tools/hybrid_query",
        json={"tenant_id": "tenant-a", "query": "brand strategy", "top_k": 3},
    )
    assert resp.status_code == 200
    hits = resp.json()["hits"]
    assert len(hits) == 3
    assert all(hit["method"] == "hybrid" for hit in hits)
    assert hits[0]["metadata"]["hybrid_rank"] == "1"
    assert "dense_score" in hits[0]["metadata"]


def test_rerank_returns_in_order(client=client()):
    resp = client.post(
        "/tools/rerank_bge",
        json={
            "tenant_id": "tenant-a",
            "query": "premium positioning",
            "documents": ["doc a", "doc b"],
        },
    )
    assert resp.status_code == 200
    reranked = resp.json()["reranked"]
    assert reranked[0]["document_id"].startswith("rerank-")


def test_community_summaries_endpoint(client=client()):
    resp = client.get(
        "/resources/graph/community_summaries", params={"tenant_id": "tenant-a"}
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["summaries"]) >= 1


def test_hybrid_query_with_connectors_enabled(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_MCP_VECTOR_ENABLE", "1")
    monkeypatch.setenv("KNOWLEDGE_MCP_KEYWORD_ENABLE", "1")
    monkeypatch.setenv("KNOWLEDGE_MCP_GRAPH_ENABLE", "1")
    resp = client().post(
        "/tools/hybrid_query",
        json={"tenant_id": "tenant-a", "query": "brand strategy", "top_k": 2},
    )
    assert resp.status_code == 200
    assert resp.json()["hits"]
