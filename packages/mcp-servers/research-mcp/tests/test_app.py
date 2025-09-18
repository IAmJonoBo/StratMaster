from fastapi.testclient import TestClient
from research_mcp.app import create_app


def test_healthz_ok():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_info_endpoint():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("name") == "research-mcp"
    assert "health" in body.get("capabilities", [])
