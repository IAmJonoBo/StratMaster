from __future__ import annotations

import json
from pathlib import Path
from stratmaster_api.models.schema_export import MODELS, SCHEMA_BASE_URL, SCHEMA_VERSION


def test_exported_schemas_have_versioned_ids() -> None:
    schemas_dir = Path("packages/api/schemas")
    assert schemas_dir.exists()
    files = list(schemas_dir.glob("*.json"))
    expected_names = {
        f"{name}-{SCHEMA_VERSION}.json" for name in MODELS.keys()
    }
    assert {f.name for f in files} == expected_names

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        schema_name = path.stem.replace(f"-{SCHEMA_VERSION}", "")
        expected_id = f"{SCHEMA_BASE_URL}/{schema_name}/{SCHEMA_VERSION}"
        assert data["$id"] == expected_id
        assert data["$schema"] == "https://json-schema.org/draft/2020-12/schema"
