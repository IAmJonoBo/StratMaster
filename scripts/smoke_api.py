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
        assert r.status_code == 200, f"/healthz status={r.status_code} body={r.text}"
        assert r.json().get("status") == "ok", f"/healthz body={r.text}"
        print("/healthz: ok")
        # /docs
        r = await client.get("/docs")
        assert r.status_code == 200, f"/docs status={r.status_code}"
        assert ("swagger-ui" in r.text) or (
            "openapi" in r.text.lower()
        ), "Swagger UI not detected in /docs"
        print("/docs: ok (swagger detected)")
    return 0


if __name__ == "__main__":
    try:
        code = anyio.run(main)
    except AssertionError as ae:
        print(f"Smoke failed: {ae}")
        code = 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        code = 1
    sys.exit(code)
