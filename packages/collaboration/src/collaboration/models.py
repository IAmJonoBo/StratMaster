"""
Data models for real-time collaboration system.
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""
    JOIN_SESSION = "join_session"
    LEAVE_SESSION = "leave_session"
    DOCUMENT_UPDATE = "document_update"
    CURSOR_UPDATE = "cursor_update"
    PRESENCE_UPDATE = "presence_update"
    SESSION_STATE = "session_state"
    ERROR = "error"


class UserPresence(BaseModel):
    """User presence information."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Display name")
    cursor_position: Optional[int] = Field(None, description="Current cursor position in document")
    selection_start: Optional[int] = Field(None, description="Selection start position")
    selection_end: Optional[int] = Field(None, description="Selection end position")
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(True, description="Whether user is actively editing")
    color: str = Field("#007bff", description="User's cursor/selection color")


class DocumentUpdate(BaseModel):
    """CRDT document update operation."""
    update_id: str = Field(..., description="Unique update identifier")
    user_id: str = Field(..., description="User who made the update")
    session_id: str = Field(..., description="Collaboration session ID")
    operation_type: str = Field(..., description="Type of operation (insert, delete, retain)")
    position: int = Field(..., description="Position in document")
    content: Optional[str] = Field(None, description="Content for insert operations")
    length: Optional[int] = Field(None, description="Length for delete operations")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    vector_clock: Dict[str, int] = Field(default_factory=dict, description="Vector clock for ordering")


class CollaborationSession(BaseModel):
    """Collaborative session metadata."""
    session_id: str = Field(..., description="Unique session identifier")
    document_id: str = Field(..., description="Document being collaborated on")
    owner_id: str = Field(..., description="Session owner")
    participants: List[str] = Field(default_factory=list, description="List of participant user IDs")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = Field(True, description="Whether session is still active")
    max_participants: int = Field(10, description="Maximum allowed participants")
    permissions: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="User permissions (read, write, admin)"
    )


class WebSocketMessage(BaseModel):
    """WebSocket message wrapper."""
    type: MessageType = Field(..., description="Message type")
    session_id: Optional[str] = Field(None, description="Target session ID")
    user_id: Optional[str] = Field(None, description="Sender user ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SessionJoinRequest(BaseModel):
    """Request to join a collaboration session."""
    session_id: str = Field(..., description="Session to join")
    user_id: str = Field(..., description="User joining")
    username: str = Field(..., description="Display name")
    token: Optional[str] = Field(None, description="Authentication token")


class SessionState(BaseModel):
    """Complete session state for synchronization."""
    session_id: str
    document_content: str = Field("", description="Current document content")
    participants: Dict[str, UserPresence] = Field(
        default_factory=dict, 
        description="Current participants and their presence"
    )
    version: int = Field(1, description="Document version number")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorResponse(BaseModel):
    """Error response for WebSocket messages."""
    error_code: str = Field(..., description="Error identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")