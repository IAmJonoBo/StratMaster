"""Runtime configuration helpers for the StratMaster API service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict


def _truthy(value: str | None, default: bool = False) -> bool:
    """Coerce an environment variable into a boolean flag."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_headers(raw_value: str | None) -> Dict[str, str]:
    """Parse OTLP-style header strings (k=v,k2=v2)."""
    headers: Dict[str, str] = {}
    if not raw_value:
        return headers
    for part in raw_value.split(","):
        if not part.strip() or "=" not in part:
            continue
        key, value = part.split("=", 1)
        headers[key.strip()] = value.strip()
    return headers


@dataclass(slots=True)
class OIDCSettings:
    """Keycloak/OpenID Connect configuration."""

    enabled: bool = False
    server_url: str | None = None
    realm_name: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "OIDCSettings":
        """Load OIDC configuration from environment variables."""
        enabled_flag = _truthy(os.getenv("STRATMASTER_OIDC_ENABLED"))
        server_url = os.getenv("STRATMASTER_OIDC_SERVER_URL")
        realm_name = os.getenv("STRATMASTER_OIDC_REALM")
        client_id = os.getenv("STRATMASTER_OIDC_CLIENT_ID")
        client_secret = os.getenv("STRATMASTER_OIDC_CLIENT_SECRET")
        verify_ssl = _truthy(os.getenv("STRATMASTER_OIDC_VERIFY_SSL"), True)

        # Enable automatically if all required fields are present
        auto_enable = all((server_url, realm_name, client_id))
        enabled = enabled_flag or auto_enable

        return cls(
            enabled=enabled,
            server_url=server_url,
            realm_name=realm_name,
            client_id=client_id,
            client_secret=client_secret,
            verify_ssl=verify_ssl,
        )


@dataclass(slots=True)
class ObservabilitySettings:
    """OpenTelemetry and tracing configuration."""

    enable_fastapi_instrumentation: bool = True
    otlp_endpoint: str | None = None
    otlp_headers: Dict[str, str] | None = None
    sample_ratio: float = 1.0
    service_name: str = "stratmaster-api"

    @classmethod
    def from_env(cls) -> "ObservabilitySettings":
        """Load observability configuration from environment variables."""
        enable_fastapi = _truthy(os.getenv("STRATMASTER_OTEL_ENABLED"), True)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        otlp_headers = _parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))

        ratio_raw = os.getenv("STRATMASTER_OTEL_TRACE_SAMPLE_RATIO", "1.0")
        try:
            ratio = float(ratio_raw)
        except ValueError:
            ratio = 1.0
        ratio = max(0.0, min(1.0, ratio))

        service_name = os.getenv("STRATMASTER_SERVICE_NAME", "stratmaster-api")

        return cls(
            enable_fastapi_instrumentation=enable_fastapi,
            otlp_endpoint=otlp_endpoint,
            otlp_headers=otlp_headers,
            sample_ratio=ratio,
            service_name=service_name,
        )


@dataclass(slots=True)
class SecuritySettings:
    """Security and privacy configuration."""

    oidc: OIDCSettings
    audit_log_path: str = "/var/log/stratmaster/audit.log"
    audit_log_to_file: bool = False
    audit_redis_url: str | None = None
    default_workspace_id: str = "system"
    enable_redaction: bool = True

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        """Load security configuration from environment variables."""
        oidc_settings = OIDCSettings.from_env()
        audit_log_path = os.getenv("STRATMASTER_AUDIT_LOG_PATH", "/var/log/stratmaster/audit.log")
        audit_log_to_file = _truthy(os.getenv("STRATMASTER_AUDIT_LOG_TO_FILE"))
        audit_redis_url = os.getenv("STRATMASTER_AUDIT_REDIS_URL" )
        default_workspace = os.getenv("STRATMASTER_PRIVACY_DEFAULT_WORKSPACE", "system")
        enable_redaction = _truthy(os.getenv("STRATMASTER_PRIVACY_REDACTION_ENABLED"), True)

        return cls(
            oidc=oidc_settings,
            audit_log_path=audit_log_path,
            audit_log_to_file=audit_log_to_file,
            audit_redis_url=audit_redis_url,
            default_workspace_id=default_workspace,
            enable_redaction=enable_redaction,
        )


@dataclass(slots=True)
class AppConfig:
    """Aggregated runtime configuration."""

    observability: ObservabilitySettings
    security: SecuritySettings


def load_app_config() -> AppConfig:
    """Materialise runtime configuration from the current environment."""
    return AppConfig(
        observability=ObservabilitySettings.from_env(),
        security=SecuritySettings.from_env(),
    )
