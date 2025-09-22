from fastapi.testclient import TestClient
from stratmaster_api.app import create_app
from stratmaster_api.models.schema_export import SCHEMA_VERSION
def test_list_model_schemas_includes_recommendation_contracts():
    app = create_app()
    client = TestClient(app)
    response = client.get("/schemas/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == len(payload["schemas"]) > 0
    assert "recommendation-outcome" in payload["schemas"]


def test_get_single_model_schema():
    app = create_app()
    client = TestClient(app)
    response = client.get("/schemas/models/recommendation-outcome")
    assert response.status_code == 200
    schema = response.json()
    assert schema["$id"].endswith(f"/{SCHEMA_VERSION}")
    assert schema["$schema"].startswith("https://json-schema.org/")
