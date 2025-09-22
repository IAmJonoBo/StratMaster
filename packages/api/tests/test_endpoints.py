from fastapi.testclient import TestClient

from stratmaster_api.app import create_app

IDEMPOTENCY_HEADERS = {"Idempotency-Key": "test-key-1234"}


def client():
    app = create_app()
    return TestClient(app)


def test_research_plan_endpoint_returns_tasks():
    c = client()
    resp = c.post(
        "/research/plan",
        headers=IDEMPOTENCY_HEADERS,
        json={"query": "brand strategy", "tenant_id": "tenant-a", "max_sources": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan_id"].startswith("plan-")
    assert len(body["tasks"]) == 3
    assert len(body["sources"]) == 3


def test_recommendations_endpoint_returns_decision_brief():
    c = client()
    resp = c.post(
        "/recommendations",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "tenant_id": "tenant-a",
            "cep_id": "cep-1",
            "jtbd_ids": ["jtbd-1"],
            "risk_tolerance": "medium",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision_brief"]["id"].startswith("brief-")
    assert body["workflow"]["tenant_id"] == "tenant-a"


def test_eval_run_endpoint_emits_metrics():
    c = client()
    resp = c.post(
        "/evals/run",
        headers=IDEMPOTENCY_HEADERS,
        json={"tenant_id": "tenant-a", "suite": "smoke"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"].startswith("eval-")
    assert body["passed"] is True
    assert "factscore" in body["metrics"]


def test_missing_idempotency_key_rejected():
    c = client()
    resp = c.post(
        "/research/plan",
        json={"query": "market", "tenant_id": "tenant-a"},
    )
    assert resp.status_code == 400
    assert "Idempotency-Key" in resp.json()["detail"]
