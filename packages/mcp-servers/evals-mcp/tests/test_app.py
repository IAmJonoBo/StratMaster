from evals_mcp.app import create_app
from fastapi.testclient import TestClient


def client():
    return TestClient(create_app())


def test_healthz(client=client()):
    assert client.get("/healthz").status_code == 200


def test_info(client=client()):
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert "rag" in body["suites"]


def test_run_rag_suite(client=client()):
    resp = client.post(
        "/tools/run",
        json={"tenant_id": "tenant-a", "suite": "rag"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"].startswith("eval-")
    assert body["metrics"]["ragas"] >= 0.8


def test_run_with_custom_thresholds(client=client()):
    resp = client.post(
        "/tools/run",
        json={
            "tenant_id": "tenant-a",
            "suite": "truthfulqa",
            "thresholds": {"truthfulqa": 0.7},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is False
