import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from stratmaster_api.models.schema_export import SCHEMA_VERSION

app = FastAPI(title="StratMaster API", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _schemas_dir() -> Path:
    here = Path(__file__).resolve()
    packages_dir = here.parents[2]
    return packages_dir / "api" / "schemas"


def _schema_name_from_stem(stem: str) -> str:
    suffix = f"-{SCHEMA_VERSION}"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem


def _load_model_schemas() -> dict[str, dict[str, Any]]:
    schemas_path = _schemas_dir()
    if not schemas_path.exists() or not schemas_path.is_dir():
        raise HTTPException(
            status_code=500, detail=f"Schemas directory not found: {schemas_path}"
        )

    schemas: dict[str, dict[str, Any]] = {}
    for json_file in sorted(schemas_path.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - surfaced as 500 for ops visibility
            raise HTTPException(
                status_code=500, detail=f"Failed to parse {json_file.name}: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=500, detail=f"Schema must be a JSON object: {json_file.name}"
            )
        schemas[_schema_name_from_stem(json_file.stem)] = data
    if not schemas:
        raise HTTPException(status_code=500, detail="No model schemas found")
    return schemas


@app.get("/schemas/models")
def list_model_schemas() -> dict[str, Any]:
    schemas = _load_model_schemas()
    return {"version": SCHEMA_VERSION, "schemas": schemas, "count": len(schemas)}


@app.get("/schemas/models/{name}")
def get_model_schema(name: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise HTTPException(status_code=400, detail="invalid name")
    safe_name = name
    schemas = _load_model_schemas()
    schema = schemas.get(safe_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema not found: {safe_name}")
    return schema
