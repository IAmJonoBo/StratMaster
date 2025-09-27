"""Tests for privacy middleware redaction behaviour."""

from __future__ import annotations

import sys
import types

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient

# Provide lightweight stubs for optional Presidio dependencies required during import
if "presidio_analyzer" not in sys.modules:
    analyzer_stub = types.ModuleType("presidio_analyzer")

    class AnalyzerEngine:  # pragma: no cover - simple stub
        def analyze(self, *args, **kwargs):
            return []

    analyzer_stub.AnalyzerEngine = AnalyzerEngine
    sys.modules["presidio_analyzer"] = analyzer_stub

if "presidio_anonymizer" not in sys.modules:
    anonymizer_stub = types.ModuleType("presidio_anonymizer")

    class AnonymizerEngine:  # pragma: no cover - simple stub
        def anonymize(self, *args, **kwargs):
            class Result:
                text = kwargs.get("text", "")

            return Result()

    anonymizer_stub.AnonymizerEngine = AnonymizerEngine
    sys.modules["presidio_anonymizer"] = anonymizer_stub

from stratmaster_api.middleware.privacy import PrivacyRedactionMiddleware
from stratmaster_api.tracing import tracing_manager


class DummyPrivacyManager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def process_text_for_privacy(self, workspace_id: str, text: str, data_source, language: str = "en"):
        self.calls.append((workspace_id, text))
        return {
            "original_text": text,
            "processed_text": text.replace("Alice", "[REDACTED]"),
            "redacted": "Alice" in text,
            "privacy_applied": ["pii_redaction"],
        }


def _build_app(privacy_manager: DummyPrivacyManager) -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        PrivacyRedactionMiddleware,
        privacy_manager=privacy_manager,
        default_workspace="workspace-123",
    )

    @app.post("/echo")
    async def echo(request: Request):  # pragma: no cover - exercised via client
        ctx = getattr(request.state, "privacy_request", {})
        return JSONResponse({
            "redacted": ctx.get("processed_text"),
            "workspace_id": getattr(request.state, "workspace_id", None),
        })

    return app


def test_privacy_middleware_redacts_request_body():
    manager = DummyPrivacyManager()
    app = _build_app(manager)
    client = TestClient(app)

    response = client.post("/echo", json={"name": "Alice"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_id"] == "workspace-123"
    assert payload["redacted"] == '{"name":"[REDACTED]"}'

    assert manager.calls


def test_privacy_middleware_respects_workspace_header():
    manager = DummyPrivacyManager()
    app = _build_app(manager)
    client = TestClient(app)

    response = client.post(
        "/echo",
        json={"name": "Alice"},
        headers={"X-Workspace-Id": "tenant-999"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_id"] == "tenant-999"
    assert manager.calls[0][0] == "tenant-999"


def test_tracing_manager_sanitises_metadata(monkeypatch):
    manager = DummyPrivacyManager()
    tracing_manager.enable_privacy_sanitiser(manager, default_workspace="default")

    token = tracing_manager.push_privacy_context("tenant-42")
    try:
        result = tracing_manager._apply_metadata_filter({"value": "Alice"})
    finally:
        tracing_manager.reset_privacy_context(token)
        tracing_manager.enable_privacy_sanitiser(None)

    assert result["value"] == "[REDACTED]"
