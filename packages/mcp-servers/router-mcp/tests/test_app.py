from fastapi.testclient import TestClient
from router_mcp.app import create_app


def client():
    return TestClient(create_app())


def test_healthz(client=client()):
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_info(client=client()):
    resp = client.get("/info")
    assert resp.status_code == 200
    assert "router-mcp" in resp.json()["name"]


def test_complete_endpoint(client=client()):
    resp = client.post(
        "/tools/complete",
        json={
            "tenant_id": "tenant-a",
            "prompt": "Summarise brand strategy",
            "max_tokens": 50,
            "task": "reasoning",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # structured decoding fallback returns JSON string
    assert body["text"].startswith("{")


def test_complete_endpoint_with_provider(monkeypatch):
    class DummyProvider:
        def complete(self, prompt, max_tokens, model=None, temperature=None):
            return {
                "text": "provider text",
                "tokens": 10,
                "provider": "litellm",
                "model": model or "gpt",
            }

        def embed(self, inputs, model=None):
            selected = model or "bge"
            return {"embeddings": [[0.1]], "provider": "litellm", "model": selected}

        def rerank(self, query, documents, top_k, model=None):
            return {"results": documents, "provider": "litellm", "model": "rerank"}

    from router_mcp import service as service_module

    monkeypatch.setattr(
        service_module, "ProviderAdapter", lambda config: DummyProvider()
    )
    resp = client().post(
        "/tools/complete",
        json={
            "tenant_id": "tenant-a",
            "prompt": "Summarise",
            "max_tokens": 20,
            "task": "reasoning",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "litellm"
    assert body["text"].startswith("{")


def test_embed_endpoint(client=client()):
    resp = client.post(
        "/tools/embed",
        json={
            "tenant_id": "tenant-a",
            "input": ["doc one", "doc two"],
            "task": "embedding",
        },
    )
    assert resp.status_code == 200
    embeddings = resp.json()["embeddings"]
    assert len(embeddings) == 2


def test_rerank_endpoint(client=client()):
    resp = client.post(
        "/tools/rerank",
        json={
            "tenant_id": "tenant-a",
            "query": "premium positioning",
            "documents": [
                {"id": "a", "text": "We propose premium positioning"},
                {"id": "b", "text": "Cost leadership strategy"},
            ],
            "task": "rerank",
        },
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results[0]["id"] in {"a", "b"}


def test_complete_rejects_when_temperature_too_high(client=client()):
    resp = client.post(
        "/tools/complete",
        json={
            "tenant_id": "tenant-a",
            "prompt": "Summarise",
            "max_tokens": 100,
            "temperature": 0.99,
            "task": "reasoning",
        },
    )
    assert resp.status_code == 400


def test_unknown_task_rejected(client=client()):
    resp = client.post(
        "/tools/complete",
        json={
            "tenant_id": "tenant-a",
            "prompt": "Summarise",
            "max_tokens": 100,
            "task": "unsupported-task",
        },
    )
    assert resp.status_code == 400
