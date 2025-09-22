import json
from pathlib import Path

from stratmaster_api.models.schema_export import SCHEMA_BASE_URL, SCHEMA_VERSION, MODELS


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
        expected_id = f"{SCHEMA_BASE_URL}/{path.stem.replace(f'-{SCHEMA_VERSION}', '')}/{SCHEMA_VERSION}"
        assert data["$id"] == expected_id
        assert data["$schema"] == "https://json-schema.org/draft/2020-12/schema"
