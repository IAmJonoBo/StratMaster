import json
from pathlib import Path

from fastapi.testclient import TestClient

from stratmaster_api.app import create_app
from stratmaster_api.models.schema_export import SCHEMA_VERSION


def test_model_schemas_invalid_json(monkeypatch, tmp_path: Path) -> None:
    app = create_app()
    client = TestClient(app)

    bad_dir = tmp_path / "schemas"
    bad_dir.mkdir(parents=True)
    (bad_dir / f"bad-{SCHEMA_VERSION}.json").write_text("{", encoding="utf-8")

    monkeypatch.setattr("stratmaster_api.app._model_schemas_dir", lambda: bad_dir)

    resp = client.get("/schemas/models")
    assert resp.status_code == 500
    detail = resp.json().get("detail", "")
    assert "Failed to parse" in detail


def test_model_schemas_list_and_detail(monkeypatch, tmp_path: Path) -> None:
    app = create_app()
    client = TestClient(app)

    good_dir = tmp_path / "schemas"
    good_dir.mkdir(parents=True)
    schema_content = {"$id": "urn:test", "$schema": "https://example", "title": "Source"}
    (good_dir / f"source-{SCHEMA_VERSION}.json").write_text(
        json.dumps(schema_content), encoding="utf-8"
    )

    monkeypatch.setattr("stratmaster_api.app._model_schemas_dir", lambda: good_dir)

    listing = client.get("/schemas/models")
    assert listing.status_code == 200
    data = listing.json()
    assert data["version"] == SCHEMA_VERSION
    assert data["count"] == 1
    assert "source" in data["schemas"]
    assert data["schemas"]["source"] == schema_content

    detail = client.get("/schemas/models/source")
    assert detail.status_code == 200
    assert detail.json() == schema_content

    missing = client.get("/schemas/models/unknown")
    assert missing.status_code == 404


def test_model_schema_rejects_invalid_name(monkeypatch, tmp_path: Path) -> None:
    app = create_app()
    client = TestClient(app)

    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / f"source-{SCHEMA_VERSION}.json").write_text(
        json.dumps({"$id": "urn:test", "$schema": "https://example"}), encoding="utf-8"
    )
    monkeypatch.setattr("stratmaster_api.app._model_schemas_dir", lambda: schemas_dir)

    resp = client.get("/schemas/models/not%20allowed")
    assert resp.status_code == 400
