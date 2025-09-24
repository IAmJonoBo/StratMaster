#!/usr/bin/env python3
"""
Quick API smoke tests using in-process ASGI transport.
"""
from __future__ import annotations

import sys

import anyio
import httpx

try:
    from stratmaster_api.app import create_app
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(2)


async def main() -> int:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # /healthz
        r = await client.get("/healthz")
        if r.status_code != 200:
            print(f"/healthz: FAIL status={r.status_code} body={r.text}")
            return 1
        try:
            data = r.json()
        except Exception:
            print(f"/healthz: FAIL (invalid JSON) body={r.text}")
            return 1
        if data.get("status") != "ok":
            print(f"/healthz: FAIL body={r.text}")
            return 1
        print("/healthz: ok")

        # /docs
        r = await client.get("/docs")
        if r.status_code != 200:
            print(f"/docs: FAIL status={r.status_code}")
            return 1
        text_lower = r.text.lower()
        if ("swagger-ui" not in text_lower) and ("openapi" not in text_lower):
            print("/docs: FAIL (swagger not detected)")
            return 1
        print("/docs: ok (swagger detected)")

        # Test experiment endpoint
        headers = {"Idempotency-Key": "smoke-test-exp-001"}
        payload = {
            "tenant_id": "smoke-test",
            "hypothesis_id": "smoke-hyp",
            "variants": [
                {"name": "control", "description": "Current version"},
                {"name": "treatment", "description": "New version"}
            ],
            "primary_metric": {
                "name": "conversion",
                "definition": "Conversion rate"
            }
        }
        r = await client.post("/experiments", headers=headers, json=payload)
        if r.status_code != 200:
            print(f"/experiments: FAIL status={r.status_code} body={r.text}")
            return 1
        try:
            data = r.json()
        except Exception:
            print(f"/experiments: FAIL (invalid JSON) body={r.text}")
            return 1
        if not data.get("experiment_id", "").startswith("exp-"):
            print(f"/experiments: FAIL invalid experiment_id body={r.text}")
            return 1
        print("/experiments: ok")

        # Test forecast endpoint
        headers = {"Idempotency-Key": "smoke-test-forecast-001"}
        payload = {
            "tenant_id": "smoke-test",
            "metric_id": "revenue",
            "horizon_days": 30
        }
        r = await client.post("/forecasts", headers=headers, json=payload)
        if r.status_code != 200:
            print(f"/forecasts: FAIL status={r.status_code} body={r.text}")
            return 1
        try:
            data = r.json()
        except Exception:
            print(f"/forecasts: FAIL (invalid JSON) body={r.text}")
            return 1
        forecast = data.get("forecast", {})
        if not forecast.get("id", "").startswith("forecast-"):
            print(f"/forecasts: FAIL invalid forecast_id body={r.text}")
            return 1
        print("/forecasts: ok")

        # Test debate escalate endpoint
        headers = {"Idempotency-Key": "smoke-test-debate-001"}
        payload = {
            "debate_id": "smoke-debate-123",
            "tenant_id": "smoke-test",
            "escalation_reason": "Need brand strategy expert review"
        }
        r = await client.post("/debate/escalate", headers=headers, json=payload)
        if r.status_code != 200:
            print(f"/debate/escalate: FAIL status={r.status_code} body={r.text}")
            return 1
        try:
            data = r.json()
        except Exception:
            print(f"/debate/escalate: FAIL (invalid JSON) body={r.text}")
            return 1
        if not data.get("escalation_id", "").startswith("esc-"):
            print(f"/debate/escalate: FAIL invalid escalation_id body={r.text}")
            return 1
        print("/debate/escalate: ok")

    print("Smoke: PASS")
    return 0


if __name__ == "__main__":
    try:
        code = anyio.run(main)
    except Exception as e:
        print(f"Unexpected error: {e}")
        code = 1
    sys.exit(code)
