import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

app = FastAPI(title="StratMaster API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _schemas_dir() -> Path:
    """Resolve the absolute path to the OpenAI tool schemas directory.

    Starting from this file (packages/api/app/main.py), navigate up to the
    'packages' directory and then into providers/openai/tool-schemas.
    """
    here = Path(__file__).resolve()
    # parents[2] -> .../StratMaster/packages
    packages_dir = here.parents[2]
    return packages_dir / "providers" / "openai" / "tool-schemas"


def _load_tool_schemas() -> dict[str, dict[str, Any]]:
    """Load all JSON schemas from the schemas directory into a dict keyed by tool name.

    The tool name is the filename stem (e.g., web_search.json -> web_search).
    """
    schemas_path = _schemas_dir()
    if not schemas_path.exists() or not schemas_path.is_dir():
        # Fail with 500 to signal misconfiguration in deployment
        raise HTTPException(
            status_code=500, detail=f"Schemas directory not found: {schemas_path}"
        )

    tools: dict[str, dict[str, Any]] = {}
    for json_file in sorted(schemas_path.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (
            Exception
        ) as e:  # pragma: no cover - surfaced as 500 for operational visibility
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse {json_file.name}: {e}",
            ) from e
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Schema must be a JSON object: {json_file.name}",
            )
        tools[json_file.stem] = data
    if not tools:
        raise HTTPException(status_code=500, detail="No tool schemas found")
    return tools


@app.get("/providers/openai/tools")
def list_openai_tool_schemas(format: str = "raw") -> dict[str, Any]:
    """List available OpenAI tool schemas.

    Query params:
        - format=raw (default): returns { schemas: {name: schema}, count }
        - format=openai: returns tools in OpenAI function format with name, description,
            and parameters fields
    """
    tools = _load_tool_schemas()
    if format not in ("raw", "openai"):
        raise HTTPException(status_code=400, detail="format must be 'raw' or 'openai'")
    if format == "raw":
        return {"schemas": tools, "count": len(tools)}

    # Convert to OpenAI client-mode tools format
    oa_tools: list[dict[str, Any]] = []
    for name, schema in tools.items():
        oa_tools.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": schema.get("description", ""),
                    "parameters": schema,
                },
            }
        )
    return {"tools": oa_tools, "count": len(oa_tools)}


@app.get("/providers/openai/tools/{name}")
def get_openai_tool_schema(name: str) -> dict[str, Any]:
    """Fetch a single tool schema by name (filename stem)."""
    tools = _load_tool_schemas()
    schema = tools.get(name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Tool schema not found: {name}")
    return schema
