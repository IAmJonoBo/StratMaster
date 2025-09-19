# pyright: reportMissingImports=false
from fastapi.testclient import TestClient
from stratmaster_api.app import create_app


def test_healthz():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
