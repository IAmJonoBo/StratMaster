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
    print("Smoke: PASS")
    return 0


if __name__ == "__main__":
    try:
        code = anyio.run(main)
    except Exception as e:
        print(f"Unexpected error: {e}")
        code = 1
    sys.exit(code)
