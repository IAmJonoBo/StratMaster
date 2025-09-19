from fastapi.testclient import TestClient
from stratmaster_api.app import create_app


def test_list_tools_raw_contains_expected_schema_keys():
    app = create_app()
    client = TestClient(app)
    r = client.get("/providers/openai/tools", params={"format": "raw"})
    assert r.status_code == 200
    data = r.json()
    assert "schemas" in data and isinstance(data["schemas"], dict)
    assert data["count"] == len(data["schemas"]) > 0
    assert "web_search" in data["schemas"], "expected web_search schema to be present"


def test_list_tools_openai_format():
    app = create_app()
    client = TestClient(app)
    r = client.get("/providers/openai/tools", params={"format": "openai"})
    assert r.status_code == 200
    data = r.json()
    assert "tools" in data and isinstance(data["tools"], list)
    assert data["count"] == len(data["tools"]) > 0
    sample = data["tools"][0]
    assert sample["type"] == "function"
    assert "function" in sample and "parameters" in sample["function"]


def test_get_single_tool_schema():
    app = create_app()
    client = TestClient(app)
    r = client.get("/providers/openai/tools/web_search")
    assert r.status_code == 200
    schema = r.json()
    assert isinstance(schema, dict)
    assert schema.get("type") in ("object", None)
