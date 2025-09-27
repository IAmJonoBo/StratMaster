"""Comprehensive audit logging system for StratMaster."""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

import redis
try:  # structlog is optional; fall back to stdlib logging when unavailable
    import structlog  # type: ignore[import-untyped]
    STRUCTLOG_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    structlog = None  # type: ignore[assignment]
    STRUCTLOG_AVAILABLE = False
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

if STRUCTLOG_AVAILABLE:
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    audit_logger = structlog.get_logger("audit")
    _base_audit_logger = logging.getLogger("audit")
else:
    # Fallback to stdlib logging-only logger
    audit_logger = logging.getLogger("audit")
    _base_audit_logger = audit_logger


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGE = "role_change"

    # Data Access
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

    # Research & Analysis
    RESEARCH_QUERY = "research_query"
    ANALYSIS_RUN = "analysis_run"
    MODEL_INFERENCE = "model_inference"
    DOCUMENT_PROCESS = "document_process"

    # Privacy & Compliance
    PII_REDACTION = "pii_redaction"
    PRIVACY_SETTING_CHANGE = "privacy_setting_change"
    DATA_RETENTION_POLICY = "data_retention_policy"
    COMPLIANCE_CHECK = "compliance_check"

    # System Events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGE = "config_change"
    ERROR = "error"

    # Workspace & Tenant
    WORKSPACE_CREATE = "workspace_create"
    WORKSPACE_DELETE = "workspace_delete"
    TENANT_CREATE = "tenant_create"
    TENANT_DELETE = "tenant_delete"

    # Integration
    EXPORT_TO_NOTION = "export_to_notion"
    EXPORT_TO_TRELLO = "export_to_trello"
    EXPORT_TO_JIRA = "export_to_jira"
    API_CALL = "api_call"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Audit event model."""

    # Event identification
    event_id: str = Field(..., description="Unique event identifier")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: AuditSeverity = AuditSeverity.MEDIUM

    # User & Session
    user_id: str | None = None
    username: str | None = None
    session_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None

    # Request Context
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    method: str | None = None

    # Event Details
    action: str = Field(..., description="Action performed")
    resource_type: str | None = None
    resource_id: str | None = None
    description: str = Field(..., description="Human-readable description")

    # Results & Metadata
    success: bool = True
    error_message: str | None = None
    duration_ms: int | None = None
    data_size_bytes: int | None = None

    # Additional context
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    # Privacy & Compliance
    contains_pii: bool = False
    data_classification: str | None = None
    retention_policy: str | None = None


class AuditLogger:
    """Comprehensive audit logging system."""

    def __init__(
        self,
        redis_url: str | None = None,
        log_to_file: bool = True,
        log_file_path: str = "/var/log/stratmaster/audit.log",
        buffer_size: int = 100
    ):
        """Initialize audit logger.

        Args:
            redis_url: Redis URL for event streaming
            log_to_file: Whether to log to file
            log_file_path: Path to audit log file
            buffer_size: Buffer size for batch processing
        """
        self.redis_client: redis.Redis | None = None
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path
        self.buffer_size = buffer_size
        self.event_buffer: list[AuditEvent] = []

        # Initialize Redis if URL provided
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
                logger.info("Connected to Redis for audit event streaming")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None

        # Configure file logging
        if self.log_to_file:
            try:
                file_handler = logging.FileHandler(log_file_path)
                file_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
                # Attach handler to the underlying stdlib logger. When structlog is in use,
                # audit_logger is a BoundLogger that doesn't expose addHandler.
                _base_audit_logger.addHandler(file_handler)
                logger.info(f"Audit logging to file: {log_file_path}")
            except Exception as e:
                logger.error(f"Failed to setup file logging: {e}")

    def log_event(self, event: AuditEvent) -> None:
        """Log audit event."""
        try:
            # Generate event ID if not provided
            if not event.event_id:
                event.event_id = self._generate_event_id()

            # Convert to dict for logging
            event_dict = event.dict()

            # Log to structured logger
            audit_logger.info(
                "audit_event",
                **event_dict
            )

            # Stream to Redis if available
            if self.redis_client:
                self._stream_to_redis(event)

            # Add to buffer for batch processing
            self.event_buffer.append(event)

            # Flush buffer if full
            if len(self.event_buffer) >= self.buffer_size:
                self.flush_buffer()

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        return f"audit_{uuid.uuid4().hex[:12]}"

    def _stream_to_redis(self, event: AuditEvent) -> None:
        """Stream event to Redis."""
        if not self.redis_client:
            return

        try:
            # Stream to Redis with event type as stream key
            stream_key = f"audit:{event.event_type.value}"

            self.redis_client.xadd(
                stream_key,
                event.dict(),
                maxlen=10000  # Keep last 10k events per type
            )

            # Also add to general audit stream
            self.redis_client.xadd(
                "audit:all",
                event.dict(),
                maxlen=50000  # Keep last 50k events overall
            )

        except Exception as e:
            logger.error(f"Failed to stream event to Redis: {e}")

    def flush_buffer(self) -> None:
        """Flush event buffer for batch processing."""
        if not self.event_buffer:
            return

        try:
            # Batch process events (could send to external systems)
            self._process_event_batch(self.event_buffer)

            # Clear buffer
            self.event_buffer.clear()

        except Exception as e:
            logger.error(f"Failed to flush event buffer: {e}")

    def _process_event_batch(self, events: list[AuditEvent]) -> None:
        """Process batch of events (placeholder for external integrations)."""
        # This could send to SIEM, alerting systems, etc.
        logger.debug(f"Processed batch of {len(events)} audit events")

    # Convenience methods for common audit events

    def log_authentication(
        self,
        event_type: AuditEventType,
        user_id: str,
        username: str,
        success: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
        error_message: str | None = None,
        **kwargs
    ) -> None:
        """Log authentication event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            user_id=user_id,
            username=username,
            action=event_type.value,
            description=f"User {username} {event_type.value}",
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM,
            **kwargs
        )
        self.log_event(event)

    def log_data_access(
        self,
        event_type: AuditEventType,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
        workspace_id: str | None = None,
        data_size_bytes: int | None = None,
        contains_pii: bool = False,
        **kwargs
    ) -> None:
        """Log data access event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            workspace_id=workspace_id,
            description=f"User {user_id} {action} {resource_type} {resource_id}",
            success=success,
            data_size_bytes=data_size_bytes,
            contains_pii=contains_pii,
            severity=AuditSeverity.HIGH if contains_pii else AuditSeverity.MEDIUM,
            **kwargs
        )
        self.log_event(event)

    def log_privacy_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        workspace_id: str,
        action: str,
        description: str,
        pii_types: list[str] | None = None,
        **kwargs
    ) -> None:
        """Log privacy-related event."""
        metadata = kwargs.get('metadata', {})
        if pii_types:
            metadata['pii_types'] = pii_types

        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            user_id=user_id,
            workspace_id=workspace_id,
            action=action,
            description=description,
            contains_pii=True,
            severity=AuditSeverity.HIGH,
            metadata=metadata,
            tags=["privacy", "compliance"],
            **kwargs
        )
        self.log_event(event)

    def log_system_event(
        self,
        event_type: AuditEventType,
        action: str,
        description: str,
        success: bool = True,
        error_message: str | None = None,
        **kwargs
    ) -> None:
        """Log system event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            action=action,
            description=description,
            success=success,
            error_message=error_message,
            severity=AuditSeverity.CRITICAL if not success else AuditSeverity.LOW,
            **kwargs
        )
        self.log_event(event)

    def log_export_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        workspace_id: str,
        destination: str,
        resource_count: int,
        success: bool = True,
        **kwargs
    ) -> None:
        """Log export event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            user_id=user_id,
            workspace_id=workspace_id,
            action=f"export_to_{destination}",
            description=f"Exported {resource_count} resources to {destination}",
            success=success,
            metadata={"destination": destination, "resource_count": resource_count},
            severity=AuditSeverity.MEDIUM,
            **kwargs
        )
        self.log_event(event)

    # Query methods for audit events

    def get_events_by_user(
        self,
        user_id: str,
        limit: int = 100,
        event_types: list[AuditEventType] | None = None
    ) -> list[dict[str, Any]]:
        """Get audit events for specific user."""
        if not self.redis_client:
            logger.warning("Redis not available for event queries")
            return []

        try:
            # Query Redis streams for user events
            events = []

            # If specific event types requested, query those streams
            if event_types:
                streams = [f"audit:{event_type.value}" for event_type in event_types]
            else:
                streams = ["audit:all"]

            for stream in streams:
                stream_events = self.redis_client.xrevrange(stream, count=limit)
                for event_id, fields in stream_events:
                    if fields.get(b'user_id', b'').decode() == user_id:
                        event_data = {k.decode(): v.decode() for k, v in fields.items()}
                        events.append(event_data)

            return events[:limit]

        except Exception as e:
            logger.error(f"Failed to query events for user {user_id}: {e}")
            return []

    def get_events_by_workspace(
        self,
        workspace_id: str,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get audit events for specific workspace."""
        if not self.redis_client:
            logger.warning("Redis not available for event queries")
            return []

        try:
            events = []
            stream_events = self.redis_client.xrevrange("audit:all", count=limit * 2)

            for event_id, fields in stream_events:
                if fields.get(b'workspace_id', b'').decode() == workspace_id:
                    event_data = {k.decode(): v.decode() for k, v in fields.items()}
                    events.append(event_data)

                if len(events) >= limit:
                    break

            return events

        except Exception as e:
            logger.error(f"Failed to query events for workspace {workspace_id}: {e}")
            return []

    def get_security_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get security-related audit events."""
        security_event_types = [
            AuditEventType.LOGIN,
            AuditEventType.LOGOUT,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.ROLE_CHANGE,
            AuditEventType.PRIVACY_SETTING_CHANGE
        ]

        if not self.redis_client:
            return []

        try:
            events = []

            for event_type in security_event_types:
                stream = f"audit:{event_type.value}"
                stream_events = self.redis_client.xrevrange(stream, count=limit // len(security_event_types))

                for event_id, fields in stream_events:
                    event_data = {k.decode(): v.decode() for k, v in fields.items()}
                    events.append(event_data)

            # Sort by timestamp
            events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return events[:limit]

        except Exception as e:
            logger.error(f"Failed to query security events: {e}")
            return []

    def generate_audit_report(
        self,
        workspace_id: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Generate audit report."""
        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "filters": {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "summary": {},
            "events": []
        }

        try:
            # Get relevant events based on filters
            if user_id:
                events = self.get_events_by_user(user_id, limit=1000)
            elif workspace_id:
                events = self.get_events_by_workspace(workspace_id, limit=1000)
            else:
                events = self.get_security_events(limit=1000)

            # Filter by date range if specified
            if start_date or end_date:
                filtered_events = []
                for event in events:
                    try:
                        event_time = datetime.fromisoformat(event.get('timestamp', ''))
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue
                        filtered_events.append(event)
                    except ValueError:
                        continue
                events = filtered_events

            report["events"] = events

            # Generate summary statistics
            event_counts = {}
            success_count = 0
            failure_count = 0

            for event in events:
                event_type = event.get('event_type', 'unknown')
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

                if event.get('success', 'true').lower() == 'true':
                    success_count += 1
                else:
                    failure_count += 1

            report["summary"] = {
                "total_events": len(events),
                "success_count": success_count,
                "failure_count": failure_count,
                "event_type_counts": event_counts
            }

        except Exception as e:
            logger.error(f"Failed to generate audit report: {e}")
            report["error"] = str(e)

        return report


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def init_audit_logger(
    redis_url: str | None = None,
    log_to_file: bool = True,
    log_file_path: str = "/var/log/stratmaster/audit.log"
) -> AuditLogger:
    """Initialize global audit logger."""
    global _audit_logger

    _audit_logger = AuditLogger(
        redis_url=redis_url,
        log_to_file=log_to_file,
        log_file_path=log_file_path
    )

    logger.info("Initialized audit logging system")
    return _audit_logger


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    if _audit_logger is None:
        raise RuntimeError("Audit logger not initialized. Call init_audit_logger() first.")
    return _audit_logger


# Convenience functions for common audit events
def audit_login(user_id: str, username: str, success: bool, **kwargs):
    """Audit login event."""
    logger = get_audit_logger()
    logger.log_authentication(
        AuditEventType.LOGIN, user_id, username, success, **kwargs
    )


def audit_data_access(user_id: str, resource_type: str, resource_id: str, action: str, **kwargs):
    """Audit data access event."""
    logger = get_audit_logger()
    logger.log_data_access(
        AuditEventType.DATA_READ, user_id, resource_type, resource_id, action, **kwargs
    )


def audit_export(user_id: str, workspace_id: str, destination: str, resource_count: int, **kwargs):
    """Audit export event."""
    logger = get_audit_logger()
    logger.log_export_event(
        AuditEventType.DATA_EXPORT, user_id, workspace_id, destination, resource_count, **kwargs
    )
