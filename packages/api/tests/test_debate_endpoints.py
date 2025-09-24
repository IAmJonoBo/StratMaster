import json

from fastapi.testclient import TestClient

from stratmaster_api.app import create_app

IDEMPOTENCY_HEADERS = {"Idempotency-Key": "debate-test-key"}


def client():
    app = create_app()
    return TestClient(app)


def test_debate_escalate_endpoint():
    c = client()
    resp = c.post(
        "/debate/escalate",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "debate_id": "deb-test-123",
            "tenant_id": "tenant-a",
            "escalation_reason": "Complex brand strategy question requires expert input",
            "specialist_domain": "brand",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["escalation_id"].startswith("esc-")
    assert body["debate_id"] == "deb-test-123"
    assert body["status"] == "escalated"
    assert body["specialist_assigned"] == "brand-specialist"
    assert isinstance(body["estimated_response_time"], int)
    assert body["estimated_response_time"] > 0


def test_debate_accept_endpoint():
    c = client()
    resp = c.post(
        "/debate/accept",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "debate_id": "deb-test-456",
            "tenant_id": "tenant-a",
            "acceptance_type": "full",
            "notes": "Agreed with the recommendation as presented",
            "action_items": ["Implement A/B test", "Update brand guidelines"],
            "quality_rating": 4,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["acceptance_id"].startswith("acc-")
    assert body["debate_id"] == "deb-test-456"
    assert body["status"] == "accepted"
    assert isinstance(body["exported_artifacts"], list)
    assert isinstance(body["next_steps"], list)


def test_debate_status_endpoint():
    c = client()
    # First create a debate by escalating it
    escalate_resp = c.post(
        "/debate/escalate",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "debate_id": "deb-test-789",
            "tenant_id": "tenant-a",
            "escalation_reason": "Need strategy expert review",
        },
    )
    assert escalate_resp.status_code == 200

    # Now check the status
    status_resp = c.get("/debate/deb-test-789/status")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["debate_id"] == "deb-test-789"
    assert body["status"] in ["escalated", "in_progress", "paused", "accepted", "rejected"]


def test_debate_pause_endpoint():
    c = client()
    resp = c.post(
        "/debate/deb-test-999/pause",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "debate_id": "deb-test-999",
            "tenant_id": "tenant-a",
            "pause_reason": "Need additional market research data",
            "timeout_minutes": 60,
            "required_input_type": "clarification",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pause_id"].startswith("pause-")
    assert body["debate_id"] == "deb-test-999"
    assert body["status"] == "paused"
    assert "timeout_at" in body
    assert isinstance(body["fallback_action"], str)


def test_debate_escalate_infers_domain_from_reason():
    c = client()
    resp = c.post(
        "/debate/escalate",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "debate_id": "deb-test-domain",
            "tenant_id": "tenant-a",
            "escalation_reason": "Need research and data analysis expert review",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["specialist_assigned"] == "research-specialist"


def test_debate_accept_partial_acceptance():
    c = client()
    resp = c.post(
        "/debate/accept",
        headers=IDEMPOTENCY_HEADERS,
        json={
            "debate_id": "deb-test-partial",
            "tenant_id": "tenant-a",
            "acceptance_type": "partial",
            "notes": "Accept recommendation but with modifications to timeline",
            "action_items": ["Revise timeline", "Get budget approval"],
            "quality_rating": 3,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "accepted"
    assert len(body["exported_artifacts"]) > 0