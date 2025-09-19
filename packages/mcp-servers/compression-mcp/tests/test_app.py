from compression_mcp.app import create_app
from fastapi.testclient import TestClient


def client():
    return TestClient(create_app())


def test_healthz(client=client()):
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_compress_endpoint_falls_back(monkeypatch):
    monkeypatch.setenv("COMPRESSION_MCP_ENABLE_LLMLINGUA", "0")
    resp = client().post(
        "/tools/compress",
        json={
            "tenant_id": "tenant-a",
            "text": "one two three four five six seven eight nine ten",
            "target_tokens": 20,
            "mode": "summary",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["compressed_tokens"] <= 20
