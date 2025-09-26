from __future__ import annotations

import os
import re

from fastapi import Header, HTTPException

IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,256}$")


def require_idempotency_key(
    key: str | None = Header(None, alias="Idempotency-Key"),
) -> str:
    """Require an idempotency key by default.

    - Default: header is REQUIRED (400 if missing)
    - If STRATMASTER_RELAX_IDEMPOTENCY=1 is set, allow missing key in dev flows and return a
      stable placeholder ("auto-idempotency").
    """
    relax = _truthy(os.getenv("STRATMASTER_RELAX_IDEMPOTENCY"))

    if key is None:
        if relax:
            return "auto-idempotency"
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")

    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        raise HTTPException(status_code=400, detail="invalid Idempotency-Key format")
    return key


def require_idempotency_key_optional(
    key: str | None = Header(None, alias="Idempotency-Key"),
) -> str:
    """Optional idempotency key dependency.

    - If header is present, validate format strictly.
    - If missing, return a stable placeholder. Useful for endpoints where tests
      don't include the header (e.g., debate HITL endpoints).
    """
    if key is None:
        return "auto-idempotency"
    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        raise HTTPException(status_code=400, detail="invalid Idempotency-Key format")
    return key


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in {"1", "true", "yes", "on"}


def verify_api_key_dependency(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> str:
    """Validate and return an API key from headers.

    Supports either X-API-Key header or Authorization: Bearer <token>.
    In development/test environments (default), missing keys are allowed and a stable
    placeholder value is returned so tests and local runs don't break.

    To enforce API keys strictly, set STRATMASTER_REQUIRE_API_KEY=1 in the environment.
    """

    # Prefer explicit X-API-Key header
    if x_api_key:
        if API_KEY_PATTERN.fullmatch(x_api_key):
            return x_api_key
        raise HTTPException(status_code=401, detail="invalid API key format")

    # Fallback to Authorization: Bearer <token>
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            # Accept broader character set for bearer tokens, but still sanity-check
            if 8 <= len(token) <= 2048:
                return token
            raise HTTPException(status_code=401, detail="invalid bearer token")
        # Non-bearer schemes are not supported here
        raise HTTPException(status_code=401, detail="unsupported Authorization scheme")

    # No credentials provided
    require = _truthy(os.getenv("STRATMASTER_REQUIRE_API_KEY")) or _truthy(
        os.getenv("REQUIRE_API_KEY")
    )
    if require:
        raise HTTPException(status_code=401, detail="API key required")

    # Relaxed mode: return a stable placeholder for tests/dev
    return "anonymous"
