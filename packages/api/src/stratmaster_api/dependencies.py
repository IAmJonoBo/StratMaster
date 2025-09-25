from __future__ import annotations

import re

from fastapi import Header, HTTPException, status

IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


def require_idempotency_key(
    key: str | None = Header(None, alias="Idempotency-Key"),
) -> str:
    if key is None:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")
    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        raise HTTPException(status_code=400, detail="invalid Idempotency-Key format")
    return key


def verify_api_key_dependency(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    api_key: str | None = Header(default=None, alias="API-Key"),
) -> str:
    """Basic API key verification dependency.

    Accepts either X-API-Key or API-Key headers and returns the provided key.
    In tests, endpoints may not require actual validation, but this ensures
    import-time availability for routers that depend on it.
    """
    key = x_api_key or api_key
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    return key