from __future__ import annotations

import re

from fastapi import Header, HTTPException

IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


def require_idempotency_key(
    key: str | None = Header(None, alias="Idempotency-Key"),
) -> str:
    if key is None:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")
    if not IDEMPOTENCY_PATTERN.fullmatch(key):
        raise HTTPException(status_code=400, detail="invalid Idempotency-Key format")
    return key

