# pyright: reportMissingImports=false
import os
from contextlib import contextmanager

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


def test_debug_config_enabled_returns_yaml():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        resp = client.get("/debug/config/retrieval/hybrid")
        assert resp.status_code == 200
        body = resp.json()
        assert body["section"] == "retrieval"
        assert body["name"] == "hybrid"
        # sanity check a few expected keys from configs/retrieval/hybrid.yaml
        cfg = body["config"]
        assert "dense" in cfg and "sparse" in cfg and "reranker" in cfg
        assert cfg["dense"]["model"]


def test_debug_config_disabled_returns_404():
    app = create_app()
    client = TestClient(app)
    # ensure not enabled
    os.environ.pop("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", None)
    resp = client.get("/debug/config/retrieval/hybrid")
    assert resp.status_code == 404


def test_debug_config_missing_file_returns_404():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        resp = client.get("/debug/config/retrieval/does-not-exist")
        assert resp.status_code == 404


def test_debug_config_rejects_traversal():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        resp = client.get("/debug/config/retrieval/..%2Fsecret")
        assert resp.status_code == 400


def test_debug_config_schema_validation_error():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        resp = client.get("/debug/config/retrieval/invalid_hybrid")
        assert resp.status_code == 400
        body = resp.json()
        assert "schema validation error" in body.get("detail", "")


def test_debug_config_compression_valid_and_invalid():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        # valid
        ok = client.get("/debug/config/compression/llmlingua")
        assert ok.status_code == 200
        cfg = ok.json()["config"]
        assert isinstance(cfg["enabled"], bool)
        assert isinstance(cfg["target_token_ratio"], float)
        assert isinstance(cfg["safety_keywords"], list)

        # invalid
        bad = client.get("/debug/config/compression/invalid_llmlingua")
        assert bad.status_code == 400
        assert "schema validation error" in bad.json().get("detail", "")


def test_debug_config_privacy_valid_and_invalid():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        ok = client.get("/debug/config/privacy/redaction")
        assert ok.status_code == 200
        cfg = ok.json()["config"]
        assert "patterns" in cfg and "policy" in cfg

        bad = client.get("/debug/config/privacy/invalid_redaction")
        assert bad.status_code == 400
        assert "schema validation error" in bad.json().get("detail", "")


def test_debug_config_evals_valid_and_invalid():
    app = create_app()
    client = TestClient(app)
    with envvar("STRATMASTER_ENABLE_DEBUG_ENDPOINTS", "1"):
        ok = client.get("/debug/config/evals/thresholds")
        assert ok.status_code == 200
        cfg = ok.json()["config"]
        for section in [
            "ingestion",
            "retrieval",
            "reasoning",
            "recommendations",
            "egress",
        ]:
            assert isinstance(cfg[section], dict)

        bad = client.get("/debug/config/evals/invalid_thresholds")
        assert bad.status_code == 400
        assert "schema validation error" in bad.json().get("detail", "")
