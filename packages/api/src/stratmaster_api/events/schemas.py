"""
Event schemas for StratMaster event-driven architecture.
"""

import os
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, Optional, Union
import uuid

from pydantic import BaseModel, Field


# Feature flag for event streaming
ENABLE_EVENT_STREAMING = os.getenv("ENABLE_EVENT_STREAMING", "false").lower() == "true"


class EventType(str, Enum):
    """Types of events in the system."""
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_UPDATED = "strategy.updated"
    STRATEGY_DELETED = "strategy.deleted"
    STRATEGY_EXPORTED = "strategy.exported"
    
    DEBATE_STARTED = "debate.started"
    DEBATE_COMPLETED = "debate.completed"
    DEBATE_ARGUMENT_ADDED = "debate.argument.added"
    
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    USER_ACTION = "user.action"
    
    ANALYTICS_METRIC_RECORDED = "analytics.metric.recorded"
    FORECAST_GENERATED = "analytics.forecast.generated"
    
    MODEL_RECOMMENDATION_REQUESTED = "model.recommendation.requested"
    MODEL_SWITCHED = "model.switched"
    
    COLLABORATION_SESSION_STARTED = "collaboration.session.started"
    COLLABORATION_SESSION_ENDED = "collaboration.session.ended"
    COLLABORATION_DOCUMENT_CHANGED = "collaboration.document.changed"
    
    AUDIT_LOG_CREATED = "audit.log.created"
    SECURITY_ALERT = "security.alert"


class EventMetadata(BaseModel):
    """Standard metadata for all events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tenant_id: str
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    version: str = "1.0"
    source: str = "stratmaster-api"


class BaseEvent(BaseModel):
    """Base event structure."""
    metadata: EventMetadata
    payload: Dict[str, Any]


# Strategy Events
class StrategyCreatedEvent(BaseEvent):
    """Event emitted when a strategy is created."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        strategy_id: str,
        user_id: str,
        strategy_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> "StrategyCreatedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.STRATEGY_CREATED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "strategy_id": strategy_id,
                "title": strategy_data.get("title"),
                "category": strategy_data.get("category"),
                "complexity": strategy_data.get("complexity", "standard"),
                "created_at": datetime.now(UTC).isoformat()
            }
        )


class StrategyExportedEvent(BaseEvent):
    """Event emitted when a strategy is exported."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        strategy_id: str,
        user_id: str,
        export_format: str,
        destination: str,
        correlation_id: Optional[str] = None
    ) -> "StrategyExportedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.STRATEGY_EXPORTED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "strategy_id": strategy_id,
                "export_format": export_format,
                "destination": destination,
                "exported_at": datetime.now(UTC).isoformat()
            }
        )


# Debate Events
class DebateStartedEvent(BaseEvent):
    """Event emitted when a debate session starts."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        debate_id: str,
        strategy_id: str,
        user_id: str,
        topic: str,
        correlation_id: Optional[str] = None
    ) -> "DebateStartedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.DEBATE_STARTED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "debate_id": debate_id,
                "strategy_id": strategy_id,
                "topic": topic,
                "started_at": datetime.now(UTC).isoformat()
            }
        )


class DebateCompletedEvent(BaseEvent):
    """Event emitted when a debate session completes."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        debate_id: str,
        strategy_id: str,
        user_id: str,
        outcome: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> "DebateCompletedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.DEBATE_COMPLETED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "debate_id": debate_id,
                "strategy_id": strategy_id,
                "outcome": outcome,
                "duration_seconds": outcome.get("duration_seconds"),
                "completed_at": datetime.now(UTC).isoformat()
            }
        )


# User Events
class UserActionEvent(BaseEvent):
    """Event emitted for user actions."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        user_id: str,
        action_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> "UserActionEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.USER_ACTION,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


# Analytics Events
class ForecastGeneratedEvent(BaseEvent):
    """Event emitted when a forecast is generated."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        forecast_id: str,
        forecast_type: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> "ForecastGeneratedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.FORECAST_GENERATED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "forecast_id": forecast_id,
                "forecast_type": forecast_type,
                "generated_at": datetime.now(UTC).isoformat()
            }
        )


# Model Events
class ModelRecommendationRequestedEvent(BaseEvent):
    """Event emitted when model recommendation is requested."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        request_id: str,
        task_type: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> "ModelRecommendationRequestedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.MODEL_RECOMMENDATION_REQUESTED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "request_id": request_id,
                "task_type": task_type,
                "requested_at": datetime.now(UTC).isoformat()
            }
        )


# Audit Events
class AuditLogCreatedEvent(BaseEvent):
    """Event emitted when an audit log is created."""
    
    @classmethod
    def create(
        cls,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> "AuditLogCreatedEvent":
        return cls(
            metadata=EventMetadata(
                event_type=EventType.AUDIT_LOG_CREATED,
                tenant_id=tenant_id,
                user_id=user_id,
                correlation_id=correlation_id
            ),
            payload={
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "logged_at": datetime.now(UTC).isoformat()
            }
        )