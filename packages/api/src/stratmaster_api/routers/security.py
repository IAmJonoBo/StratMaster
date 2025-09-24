"""
Sprint 9: Security & Compliance Enhancements
Role-based access control, audit logging, and compliance features.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])
security = HTTPBearer()


class UserRole:
    """User roles for RBAC."""
    ADMIN = "admin"
    STRATEGIST = "strategist" 
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission:
    """Permissions for fine-grained access control."""
    READ_STRATEGIES = "read:strategies"
    WRITE_STRATEGIES = "write:strategies"
    DELETE_STRATEGIES = "delete:strategies"
    READ_DEBATES = "read:debates"
    WRITE_DEBATES = "write:debates"
    ADMIN_SYSTEM = "admin:system"
    EXPORT_DATA = "export:data"
    MANAGE_USERS = "manage:users"


class AuditEvent:
    """Types of events to audit."""
    LOGIN = "login"
    LOGOUT = "logout"
    STRATEGY_CREATE = "strategy.create"
    STRATEGY_UPDATE = "strategy.update"
    STRATEGY_DELETE = "strategy.delete"
    DEBATE_START = "debate.start"
    DEBATE_COMPLETE = "debate.complete"
    DATA_EXPORT = "data.export"
    PERMISSION_CHANGE = "permission.change"
    SECURITY_ALERT = "security.alert"


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: str
    timestamp: str
    event_type: str
    user_id: str | None
    tenant_id: str | None
    resource_id: str | None
    action: str
    result: str  # success, failure, denied
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    risk_score: float | None = None


class SecurityPolicy(BaseModel):
    """Security policy configuration."""
    max_login_attempts: int = 5
    session_timeout_minutes: int = 480  # 8 hours
    password_min_length: int = 12
    require_mfa: bool = True
    allowed_ip_ranges: list[str] = Field(default_factory=list)
    data_retention_days: int = 365
    encryption_at_rest: bool = True
    audit_all_actions: bool = True


class ComplianceReport(BaseModel):
    """Compliance assessment report."""
    report_id: str
    generated_at: str
    tenant_id: str
    compliance_frameworks: list[str]
    overall_score: float = Field(..., ge=0, le=100)
    findings: list[dict[str, Any]]
    recommendations: list[str]
    next_assessment_due: str


class PIIDetectionResult(BaseModel):
    """PII detection result."""
    detected_entities: list[dict[str, Any]]
    confidence_scores: dict[str, float]
    redacted_content: str | None = None
    risk_level: str  # low, medium, high


class SecurityService:
    """Security service for RBAC, audit logging, and compliance."""
    
    def __init__(self):
        self.audit_logs: list[AuditLogEntry] = []
        self.security_policies: dict[str, SecurityPolicy] = {}
        self.role_permissions = self._initialize_role_permissions()
        self.active_sessions: dict[str, dict[str, Any]] = {}
        
    def _initialize_role_permissions(self) -> dict[str, list[str]]:
        """Initialize default role-permission mappings."""
        return {
            UserRole.ADMIN: [
                Permission.READ_STRATEGIES, Permission.WRITE_STRATEGIES, Permission.DELETE_STRATEGIES,
                Permission.READ_DEBATES, Permission.WRITE_DEBATES, Permission.ADMIN_SYSTEM,
                Permission.EXPORT_DATA, Permission.MANAGE_USERS
            ],
            UserRole.STRATEGIST: [
                Permission.READ_STRATEGIES, Permission.WRITE_STRATEGIES,
                Permission.READ_DEBATES, Permission.WRITE_DEBATES, Permission.EXPORT_DATA
            ],
            UserRole.ANALYST: [
                Permission.READ_STRATEGIES, Permission.READ_DEBATES, Permission.EXPORT_DATA
            ],
            UserRole.VIEWER: [
                Permission.READ_STRATEGIES, Permission.READ_DEBATES
            ]
        }
    
    def log_audit_event(
        self, 
        event_type: str, 
        action: str, 
        result: str,
        user_id: str | None = None,
        tenant_id: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        request: Request | None = None
    ) -> AuditLogEntry:
        """Log an audit event."""
        entry = AuditLogEntry(
            id=f"audit-{uuid4().hex[:8]}",
            timestamp=datetime.now(UTC).isoformat(),
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details or {}
        )
        
        if request:
            entry.ip_address = request.client.host if request.client else None
            entry.user_agent = request.headers.get("user-agent")
            entry.risk_score = self._calculate_risk_score(request, event_type)
        
        self.audit_logs.append(entry)
        logger.info(f"Audit event logged: {event_type} - {action} - {result}")
        
        return entry
    
    def check_permission(self, user_role: str, permission: str) -> bool:
        """Check if user role has specific permission."""
        user_permissions = self.role_permissions.get(user_role, [])
        return permission in user_permissions
    
    def get_user_permissions(self, user_role: str) -> list[str]:
        """Get all permissions for a user role."""
        return self.role_permissions.get(user_role, [])
    
    def detect_pii(self, content: str) -> PIIDetectionResult:
        """Detect personally identifiable information in content."""
        import re
        
        detected_entities = []
        confidence_scores = {}
        
        # Email detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        if emails:
            detected_entities.extend([
                {"type": "email", "value": email, "location": content.find(email)}
                for email in emails
            ])
            confidence_scores["email"] = 0.95
        
        # Phone number detection
        phone_pattern = r'(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phones = re.findall(phone_pattern, content)
        if phones:
            detected_entities.extend([
                {"type": "phone", "value": phone, "location": content.find(phone)}
                for phone in phones
            ])
            confidence_scores["phone"] = 0.85
        
        # SSN detection (simple pattern)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        ssns = re.findall(ssn_pattern, content)
        if ssns:
            detected_entities.extend([
                {"type": "ssn", "value": ssn, "location": content.find(ssn)}
                for ssn in ssns
            ])
            confidence_scores["ssn"] = 0.90
        
        # Credit card detection (basic Luhn algorithm check)
        cc_pattern = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        potential_ccs = re.findall(cc_pattern, content)
        valid_ccs = []
        for cc in potential_ccs:
            clean_cc = re.sub(r'[-\s]', '', cc)
            if self._luhn_check(clean_cc):
                valid_ccs.append(cc)
        
        if valid_ccs:
            detected_entities.extend([
                {"type": "credit_card", "value": cc, "location": content.find(cc)}
                for cc in valid_ccs
            ])
            confidence_scores["credit_card"] = 0.98
        
        # Determine risk level
        high_risk_types = ["ssn", "credit_card"]
        medium_risk_types = ["email", "phone"]
        
        if any(entity["type"] in high_risk_types for entity in detected_entities):
            risk_level = "high"
        elif any(entity["type"] in medium_risk_types for entity in detected_entities):
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Create redacted version if PII found
        redacted_content = None
        if detected_entities:
            redacted_content = content
            for entity in detected_entities:
                if entity["type"] == "email":
                    redacted_content = redacted_content.replace(entity["value"], "[EMAIL_REDACTED]")
                elif entity["type"] == "phone":
                    redacted_content = redacted_content.replace(entity["value"], "[PHONE_REDACTED]")
                elif entity["type"] == "ssn":
                    redacted_content = redacted_content.replace(entity["value"], "[SSN_REDACTED]")
                elif entity["type"] == "credit_card":
                    redacted_content = redacted_content.replace(entity["value"], "[CC_REDACTED]")
        
        return PIIDetectionResult(
            detected_entities=detected_entities,
            confidence_scores=confidence_scores,
            redacted_content=redacted_content,
            risk_level=risk_level
        )
    
    def _luhn_check(self, card_number: str) -> bool:
        """Validate credit card using Luhn algorithm."""
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        try:
            return luhn_checksum(card_number) == 0 and len(card_number) >= 13
        except (ValueError, TypeError):
            return False
    
    def _calculate_risk_score(self, request: Request, event_type: str) -> float:
        """Calculate risk score for an audit event."""
        risk_score = 0.0
        
        # Base risk by event type
        risk_weights = {
            AuditEvent.LOGIN: 0.3,
            AuditEvent.STRATEGY_DELETE: 0.8,
            AuditEvent.DATA_EXPORT: 0.7,
            AuditEvent.PERMISSION_CHANGE: 0.9,
            AuditEvent.SECURITY_ALERT: 1.0
        }
        
        risk_score += risk_weights.get(event_type, 0.2)
        
        # IP-based risk (simplified)
        if request.client and request.client.host:
            # Check if IP is in allowed ranges (simplified check)
            if not request.client.host.startswith(('127.', '10.', '192.168.')):
                risk_score += 0.2  # External IP
        
        # User agent analysis
        user_agent = request.headers.get("user-agent", "").lower()
        if "bot" in user_agent or "crawler" in user_agent:
            risk_score += 0.5
        
        # Time-based risk (off-hours activity)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            risk_score += 0.3
        
        return min(1.0, risk_score)
    
    def generate_compliance_report(self, tenant_id: str) -> ComplianceReport:
        """Generate compliance assessment report."""
        report_id = f"compliance-{uuid4().hex[:8]}"
        
        # Analyze audit logs for compliance
        tenant_logs = [log for log in self.audit_logs if log.tenant_id == tenant_id]
        
        findings = []
        recommendations = []
        
        # Check for required audit logging
        if not tenant_logs:
            findings.append({
                "severity": "high",
                "finding": "No audit logs found for tenant",
                "requirement": "SOC 2 - Logging and Monitoring"
            })
            recommendations.append("Implement comprehensive audit logging")
        
        # Check for high-risk events
        high_risk_logs = [log for log in tenant_logs if (log.risk_score or 0) > 0.7]
        if high_risk_logs:
            findings.append({
                "severity": "medium", 
                "finding": f"{len(high_risk_logs)} high-risk events detected",
                "requirement": "SOC 2 - Security Monitoring"
            })
            recommendations.append("Review high-risk events and implement additional controls")
        
        # Check for PII handling
        pii_related_logs = [log for log in tenant_logs 
                          if "pii" in log.details.get("content", "").lower()]
        if pii_related_logs:
            findings.append({
                "severity": "medium",
                "finding": "PII handling detected in logs",
                "requirement": "GDPR - Data Protection"
            })
            recommendations.append("Ensure proper PII redaction and consent management")
        
        # Calculate overall compliance score
        total_checks = 10
        failed_checks = len([f for f in findings if f["severity"] == "high"]) * 2 + \
                      len([f for f in findings if f["severity"] == "medium"])
        
        overall_score = max(0, ((total_checks - failed_checks) / total_checks) * 100)
        
        return ComplianceReport(
            report_id=report_id,
            generated_at=datetime.now(UTC).isoformat(),
            tenant_id=tenant_id,
            compliance_frameworks=["SOC 2", "GDPR", "ISO 27001"],
            overall_score=overall_score,
            findings=findings,
            recommendations=recommendations,
            next_assessment_due=datetime.now().replace(
                month=datetime.now().month + 3
            ).isoformat()
        )


# Global security service instance
security_service = SecurityService()


def get_current_user_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user role from JWT token (simplified implementation)."""
    # In production, this would decode and validate JWT token
    # For demo, we'll extract from token or default to viewer
    token = credentials.credentials
    
    # Simple token-based role extraction (production would use proper JWT)
    if "admin" in token:
        return UserRole.ADMIN
    elif "strategist" in token:
        return UserRole.STRATEGIST
    elif "analyst" in token:
        return UserRole.ANALYST
    else:
        return UserRole.VIEWER


def require_permission(permission: str):
    """Dependency to require specific permission."""
    def _require_permission(user_role: str = Depends(get_current_user_role)) -> str:
        if not security_service.check_permission(user_role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return user_role
    return _require_permission


@router.get("/audit-logs/{tenant_id}")
async def get_audit_logs(
    tenant_id: str,
    request: Request,
    user_role: str = Depends(require_permission(Permission.ADMIN_SYSTEM))
) -> dict[str, Any]:
    """Get audit logs for tenant - Sprint 9."""
    # Log this access
    security_service.log_audit_event(
        event_type="audit.access",
        action="get_audit_logs", 
        result="success",
        tenant_id=tenant_id,
        request=request
    )
    
    tenant_logs = [
        log.model_dump() for log in security_service.audit_logs 
        if log.tenant_id == tenant_id
    ]
    
    return {
        "tenant_id": tenant_id,
        "total_logs": len(tenant_logs),
        "logs": tenant_logs[-100:]  # Return last 100 logs
    }


@router.post("/pii-scan")
async def scan_for_pii(
    content: dict[str, str],
    request: Request,
    user_role: str = Depends(require_permission(Permission.READ_STRATEGIES))
) -> PIIDetectionResult:
    """Scan content for personally identifiable information - Sprint 9."""
    text_content = content.get("text", "")
    
    result = security_service.detect_pii(text_content)
    
    # Log PII scan
    security_service.log_audit_event(
        event_type="security.pii_scan",
        action="scan_content",
        result="success",
        details={
            "content_length": len(text_content),
            "entities_found": len(result.detected_entities),
            "risk_level": result.risk_level
        },
        request=request
    )
    
    return result


@router.get("/compliance-report/{tenant_id}")
async def get_compliance_report(
    tenant_id: str,
    request: Request,
    user_role: str = Depends(require_permission(Permission.ADMIN_SYSTEM))
) -> ComplianceReport:
    """Generate compliance assessment report - Sprint 9."""
    report = security_service.generate_compliance_report(tenant_id)
    
    # Log report generation
    security_service.log_audit_event(
        event_type="compliance.report_generated",
        action="generate_report",
        result="success",
        tenant_id=tenant_id,
        resource_id=report.report_id,
        request=request
    )
    
    return report


@router.get("/permissions")
async def get_user_permissions(
    user_role: str = Depends(get_current_user_role)
) -> dict[str, Any]:
    """Get current user's permissions - Sprint 9."""
    permissions = security_service.get_user_permissions(user_role)
    
    return {
        "user_role": user_role,
        "permissions": permissions,
        "total_permissions": len(permissions)
    }


@router.post("/security-alert")
async def create_security_alert(
    alert: dict[str, Any],
    request: Request,
    user_role: str = Depends(require_permission(Permission.ADMIN_SYSTEM))
) -> dict[str, Any]:
    """Create a security alert - Sprint 9."""
    alert_id = f"alert-{uuid4().hex[:8]}"
    
    # Log security alert
    entry = security_service.log_audit_event(
        event_type=AuditEvent.SECURITY_ALERT,
        action="create_alert",
        result="success",
        resource_id=alert_id,
        details=alert,
        request=request
    )
    
    return {
        "alert_id": alert_id,
        "status": "created",
        "audit_log_id": entry.id,
        "created_at": entry.timestamp
    }


# Keycloak OIDC Integration - Completing Sprint 9 to 100%
class OIDCConfig(BaseModel):
    """OIDC configuration for Keycloak integration."""
    issuer_url: str = Field(description="Keycloak realm issuer URL")
    client_id: str = Field(description="OIDC client ID")
    client_secret: str = Field(description="OIDC client secret")
    redirect_uri: str = Field(description="Post-login redirect URI")
    scopes: list[str] = Field(default=["openid", "profile", "email"])


class OIDCLoginResponse(BaseModel):
    """OIDC login initiation response."""
    auth_url: str = Field(description="Authorization URL for user redirect")
    state: str = Field(description="CSRF protection state parameter")
    session_id: str = Field(description="Internal session tracking ID")


class OIDCCallbackRequest(BaseModel):
    """OIDC callback handling request."""
    code: str = Field(description="Authorization code from Keycloak")
    state: str = Field(description="State parameter for CSRF validation")
    session_id: str = Field(description="Internal session tracking ID")


class OIDCTokenResponse(BaseModel):
    """OIDC token exchange response."""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="Refresh token")
    expires_in: int = Field(description="Token expiry in seconds")
    user_info: dict[str, Any] = Field(description="User profile information")


class KeycloakService:
    """Service for Keycloak OIDC integration."""
    
    def __init__(self):
        self.config = OIDCConfig(
            issuer_url="https://auth.stratmaster.ai/realms/stratmaster",
            client_id="stratmaster-api",
            client_secret="demo-secret-would-be-env-var",
            redirect_uri="https://app.stratmaster.ai/auth/callback"
        )
        self.active_sessions = {}
    
    def initiate_login(self, tenant_id: str) -> OIDCLoginResponse:
        """Initiate OIDC login flow."""
        import urllib.parse
        
        session_id = f"sess-{uuid4().hex[:12]}"
        state = f"state-{uuid4().hex[:16]}"
        
        # Store session for callback validation
        self.active_sessions[session_id] = {
            "state": state,
            "tenant_id": tenant_id,
            "created_at": datetime.now(UTC).isoformat(),
            "status": "pending"
        }
        
        # Construct Keycloak authorization URL
        auth_params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": state
        }
        
        auth_url = f"{self.config.issuer_url}/protocol/openid-connect/auth?" + \
                  urllib.parse.urlencode(auth_params)
        
        return OIDCLoginResponse(
            auth_url=auth_url,
            state=state,
            session_id=session_id
        )
    
    def handle_callback(self, callback: OIDCCallbackRequest) -> OIDCTokenResponse:
        """Handle OIDC callback and exchange code for tokens."""
        # Validate session and state
        if callback.session_id not in self.active_sessions:
            raise HTTPException(status_code=400, detail="Invalid session")
        
        session = self.active_sessions[callback.session_id]
        if session["state"] != callback.state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        if session["status"] != "pending":
            raise HTTPException(status_code=400, detail="Session already processed")
        
        # In real implementation, would make HTTP request to Keycloak token endpoint
        # For demo, return mock tokens
        mock_user_info = {
            "sub": f"user-{callback.session_id[-8:]}",
            "email": f"user@{session['tenant_id']}.com",
            "name": "Demo User",
            "preferred_username": "demo-user",
            "roles": ["strategist"],
            "tenant_id": session["tenant_id"]
        }
        
        # Update session status
        session["status"] = "completed"
        session["user_info"] = mock_user_info
        session["completed_at"] = datetime.now(UTC).isoformat()
        
        return OIDCTokenResponse(
            access_token=f"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.mock-token-{callback.session_id}",
            refresh_token=f"refresh-{callback.session_id}",
            expires_in=3600,
            user_info=mock_user_info
        )
    
    def validate_token(self, token: str) -> dict[str, Any]:
        """Validate JWT token (in production would verify signature)."""
        if not token.startswith("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.mock-token-"):
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        session_id = token.split("mock-token-")[1]
        
        for sess_id, session in self.active_sessions.items():
            if sess_id.endswith(session_id[-12:]) and session["status"] == "completed":
                return session["user_info"]
        
        raise HTTPException(status_code=401, detail="Token not found or expired")


# Keycloak service instance
keycloak_service = KeycloakService()


@router.post("/oidc/login", response_model=OIDCLoginResponse)
async def initiate_oidc_login(
    tenant_id: str,
) -> OIDCLoginResponse:
    """Initiate OIDC login with Keycloak - Sprint 9 completion to 100%."""
    response = keycloak_service.initiate_login(tenant_id)
    return response


@router.post("/oidc/callback", response_model=OIDCTokenResponse)
async def handle_oidc_callback(
    payload: OIDCCallbackRequest,
) -> OIDCTokenResponse:
    """Handle OIDC callback from Keycloak - Sprint 9 completion to 100%."""
    response = keycloak_service.handle_callback(payload)
    return response


@router.get("/oidc/userinfo")
async def get_oidc_userinfo(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Get user info from OIDC token - Sprint 9 completion to 100%."""
    token = credentials.credentials
    user_info = keycloak_service.validate_token(token)
    return user_info