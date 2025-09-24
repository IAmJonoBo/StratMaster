import base64

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


def test_ingestion_endpoint_returns_chunks():
    c = client()
    resp = c.post(
        "/ingestion/ingest",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "tenant_id": "tenant-a",
            "filename": "notes.txt",
            "content": base64.b64encode(b"Evidence backed insight").decode(),
            "mimetype": "text/plain",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["needs_clarification"] is True
    assert body["metrics"]["overall_confidence"] < 0.7
    assert len(body["chunks"]) == 1


def test_clarify_endpoint_generates_prompts():
    c = client()
    ingest = c.post(
        "/ingestion/ingest",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "tenant_id": "tenant-a",
            "filename": "scan.txt",
            "content": base64.b64encode(b"XXXX 000 ???").decode(),
            "mimetype": "text/plain",
        },
    )
    assert ingest.status_code == 200
    body = ingest.json()
    chunk = body["chunks"][0]
    chunk["confidence"] = 0.1
    clarify = c.post(
        "/ingestion/clarify",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "document_id": body["document_id"],
            "chunks": [
                {
                    "id": chunk["id"],
                    "index": 0,
                    "text": chunk["text"],
                    "confidence": chunk["confidence"],
                    "kind": chunk["kind"],
                }
            ],
            "threshold": 0.7,
        },
    )
    assert clarify.status_code == 200
    prompts = clarify.json()["prompts"]
    assert prompts
    assert "noisy" in prompts[0]["question"].lower()


def test_experiment_endpoint_creates_experiment():
    c = client()
    resp = c.post(
        "/experiments",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "tenant_id": "tenant-a",
            "hypothesis_id": "hyp-1",
            "variants": [
                {"name": "control", "description": "Current approach"},
                {"name": "treatment", "description": "New premium positioning"},
            ],
            "primary_metric": {
                "name": "conversion_rate",
                "definition": "Percentage of visitors who convert",
                "unit": "percent",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["experiment_id"].startswith("exp-")


def test_forecast_endpoint_creates_forecast():
    c = client()
    resp = c.post(
        "/forecasts",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "tenant_id": "tenant-a",
            "metric_id": "revenue",
            "horizon_days": 90,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    forecast = body["forecast"]
    assert forecast["id"].startswith("forecast-")
    assert forecast["metric"]["id"] == "revenue"
    assert forecast["horizon_days"] == 90
    assert forecast["point_estimate"] == 1.0
    assert len(forecast["intervals"]) == 2
    assert forecast["intervals"][0]["confidence"] == 50
    assert forecast["intervals"][1]["confidence"] == 90
