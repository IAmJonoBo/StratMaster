"""StratMaster Security & Compliance - Authentication, authorization, and privacy controls."""

from .audit_logger import AuditEvent, AuditEventType, AuditLogger
from .keycloak_auth import KeycloakAuth, OIDCConfig, UserInfo
from .privacy_controls import PIIRedactor, PrivacySettings, WorkspacePrivacyManager

__version__ = "0.1.0"

__all__ = [
    "KeycloakAuth",
    "OIDCConfig",
    "UserInfo",
    "PrivacySettings",
    "PIIRedactor",
    "WorkspacePrivacyManager",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
]
