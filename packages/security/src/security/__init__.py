"""StratMaster Security & Compliance - Authentication, authorization, and privacy controls."""

from .keycloak_auth import KeycloakAuth, OIDCConfig, UserInfo
from .privacy_controls import PrivacySettings, PIIRedactor, WorkspacePrivacyManager
from .audit_logger import AuditLogger, AuditEvent, AuditEventType

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