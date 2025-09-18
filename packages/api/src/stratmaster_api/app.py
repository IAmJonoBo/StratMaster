import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from .schemas import (
    CompressionConfig,
    EvalsThresholds,
    PrivacyConfig,
    RetrievalHybridConfig,
)


ALLOWED_SECTIONS = {"router", "retrieval", "evals", "privacy", "compression"}


def _safe_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise HTTPException(status_code=400, detail="invalid name")
    return name


def _load_yaml_file(section: str, name: str) -> Any:
    root = Path(__file__).resolve().parents[4]
    cfg_path = root / "configs" / section / f"{name}.yaml"
    if not cfg_path.is_file():
        raise HTTPException(status_code=404, detail="config not found")
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"yaml parse error: {e}") from e
    return data


def _validate_retrieval_config(data: Any) -> dict:
    try:
        validated = RetrievalHybridConfig.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    return validated.model_dump()


def _validate_compression_config(data: Any) -> dict:
    try:
        validated = CompressionConfig.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    return validated.model_dump()


def _validate_privacy_config(data: Any) -> dict:
    try:
        validated = PrivacyConfig.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    return validated.model_dump()


def _validate_evals_thresholds(data: Any) -> dict:
    try:
        validated = EvalsThresholds.model_validate(data)
    except ValidationError as ve:
        raise HTTPException(
            status_code=400,
            detail=f"schema validation error: {ve.errors()}",
        ) from ve
    return validated.model_dump()


VALIDATORS: dict[str, Callable[[Any], dict]] = {
    "retrieval": _validate_retrieval_config,
    "compression": _validate_compression_config,
    "privacy": _validate_privacy_config,
    "evals": _validate_evals_thresholds,
}


def create_app() -> FastAPI:
    app = FastAPI(title="StratMaster API", version="0.1.0")

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/debug/config/{section}/{name:path}")
    async def get_config(section: str, name: str):
        if os.getenv("STRATMASTER_ENABLE_DEBUG_ENDPOINTS") != "1":
            raise HTTPException(status_code=404, detail="not found")
        if section not in ALLOWED_SECTIONS:
            raise HTTPException(status_code=400, detail="invalid section")
        safe = _safe_name(name)
        data = _load_yaml_file(section, safe)

        validator = VALIDATORS.get(section)
        if validator is not None:
            cfg = validator(data)
        else:
            cfg = data
        return {"section": section, "name": safe, "config": cfg}

    return app
