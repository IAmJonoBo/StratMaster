"""Tests for StratMaster API configuration helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("presidio_analyzer")
pytest.importorskip("presidio_anonymizer")

from stratmaster_api.config import load_app_config
from stratmaster_api.tracing import TracingManager


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch):
    """Ensure config-related environment variables are cleared between tests."""
    keys = [
        "STRATMASTER_OIDC_ENABLED",
        "STRATMASTER_OIDC_SERVER_URL",
        "STRATMASTER_OIDC_REALM",
        "STRATMASTER_OIDC_CLIENT_ID",
        "STRATMASTER_OIDC_CLIENT_SECRET",
        "STRATMASTER_OIDC_VERIFY_SSL",
        "STRATMASTER_OTEL_ENABLED",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_HEADERS",
        "STRATMASTER_OTEL_TRACE_SAMPLE_RATIO",
        "STRATMASTER_SERVICE_NAME",
        "STRATMASTER_AUDIT_LOG_PATH",
        "STRATMASTER_AUDIT_LOG_TO_FILE",
        "STRATMASTER_AUDIT_REDIS_URL",
        "STRATMASTER_PRIVACY_DEFAULT_WORKSPACE",
        "STRATMASTER_PRIVACY_REDACTION_ENABLED",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    yield


def test_config_defaults():
    config = load_app_config()
    assert config.security.oidc.enabled is False
    assert config.security.audit_log_path.endswith("/var/log/stratmaster/audit.log")
    assert config.observability.sample_ratio == 1.0
    assert config.observability.enable_fastapi_instrumentation is True


def test_config_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRATMASTER_OIDC_SERVER_URL", "https://keycloak.example")
    monkeypatch.setenv("STRATMASTER_OIDC_REALM", "stratmaster")
    monkeypatch.setenv("STRATMASTER_OIDC_CLIENT_ID", "api")
    monkeypatch.setenv("STRATMASTER_OIDC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("STRATMASTER_OTEL_TRACE_SAMPLE_RATIO", "0.25")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "grpc://otel:4317")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "authorization=bearer")
    monkeypatch.setenv("STRATMASTER_PRIVACY_REDACTION_ENABLED", "0")

    config = load_app_config()

    assert config.security.oidc.enabled is True
    assert config.security.oidc.client_secret == "secret"
    assert config.observability.sample_ratio == 0.25
    assert config.observability.otlp_endpoint == "grpc://otel:4317"
    assert config.observability.otlp_headers == {"authorization": "bearer"}
    assert config.security.enable_redaction is False


def test_tracing_metadata_filter_guard():
    manager = TracingManager()

    manager.set_metadata_filter(lambda data: {"masked": "***"})
    assert manager._apply_metadata_filter({"masked": "secret"}) == {"masked": "***"}

    def _broken(_data):
        raise RuntimeError("boom")

    manager.set_metadata_filter(_broken)
    assert manager._apply_metadata_filter({"masked": "secret"}) == {"masked": "secret"}
