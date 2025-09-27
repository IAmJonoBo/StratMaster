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
        async def complete(self, prompt, max_tokens, model=None, temperature=None, **kwargs):
            return {
                "text": "provider text",
                "tokens": 10,
                "provider": "litellm",
                "model": model or "gpt",
                "cost_usd": 0.01,
                "latency_ms": 12.5,
            }

        def embed(self, inputs, model=None):
            selected = model or "bge"
            return {"embeddings": [[0.1]], "provider": "litellm", "model": selected}

        def rerank(self, query, documents, top_k, model=None):
            return {"results": documents, "provider": "litellm", "model": "rerank"}

    from router_mcp import service as service_module

    monkeypatch.setattr(
        service_module,
        "ProviderAdapter",
        lambda config, **kwargs: DummyProvider(),
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


def test_complete_bandit_record(monkeypatch):
    events: list[dict] = []

    class DummyTelemetry:
        def record_attempt(self, **kwargs):
            class _Ctx:
                def __enter__(self_inner):
                    return {"latency_ms": 42}

                def __exit__(self_inner, exc_type, exc, tb):
                    events.append(kwargs)

            return _Ctx()

    class DummyChoice:
        def __init__(self, text: str) -> None:
            self.message = {"content": text}

    class DummyCompletionResponse:
        def __init__(self) -> None:
            self.choices = [DummyChoice("ok")]
            self.usage = {"total_tokens": 5}
            self.model = "test-model"
            self.cost = 0.02

    class DummyLitellm:
        def completion(self, *args, **kwargs):
            return DummyCompletionResponse()

    from router_mcp import providers as providers_module
    monkeypatch.setattr(providers_module, "litellm", DummyLitellm())

    from router_mcp import telemetry as telemetry_module

    def _factory():
        return telemetry_module.RoutingTelemetry(
            telemetry_module.MetricSink([lambda payload: events.append(payload)])
        )

    monkeypatch.setattr(telemetry_module, "build_telemetry_from_env", _factory)
    from router_mcp import service as service_module
    monkeypatch.setattr(service_module, "build_telemetry_from_env", _factory)

    resp = client().post(
        "/tools/complete",
        json={
            "tenant_id": "tenant-a",
            "prompt": "short",
            "max_tokens": 20,
            "task": "reasoning",
        },
    )
    assert resp.status_code == 200
    assert events, "Expected telemetry to capture events"


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
