import os
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from stratmaster_api.app import create_app


@contextmanager
def envvar(key: str, value: str):
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


def test_openai_tools_malformed_json_returns_500(monkeypatch, tmp_path: Path):
    app = create_app()
    client = TestClient(app)
    # Prepare a temporary schemas directory with one malformed file
    bad_dir = tmp_path / "tool-schemas"
    bad_dir.mkdir(parents=True)
    (bad_dir / "bad.json").write_text("{", encoding="utf-8")  # invalid JSON

    # Monkeypatch the schemas directory used by the endpoint
    monkeypatch.setattr("stratmaster_api.app._schemas_dir", lambda: bad_dir)

    resp = client.get("/providers/openai/tools")
    assert resp.status_code == 500
    detail = resp.json().get("detail", "")
    assert "Failed to parse bad.json" in detail


def test_openai_tools_raw_happy_path(monkeypatch, tmp_path: Path):
    app = create_app()
    client = TestClient(app)

    good_dir = tmp_path / "tool-schemas"
    good_dir.mkdir(parents=True)
    json_content = '{"description": "ok", "type": "object", "properties": {}}'
    (good_dir / "ok.json").write_text(json_content, encoding="utf-8")
    monkeypatch.setattr("stratmaster_api.app._schemas_dir", lambda: good_dir)

    resp = client.get("/providers/openai/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert "schemas" in data and "count" in data
    assert data["count"] == 1
