"""
Real-time collaboration service implementation.
"""

import asyncio
import json
import logging
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Set
from uuid import uuid4

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from .models import (
    CollaborationSession,
    DocumentUpdate,
    UserPresence,
    WebSocketMessage,
    MessageType,
    SessionState,
    ErrorResponse,
    SessionJoinRequest
)

logger = logging.getLogger(__name__)


class CollaborationService:
    """Real-time collaboration service with Redis pub/sub and WebSocket management."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", cleanup_interval: int = 300):
        self.redis_url = redis_url
        self.cleanup_interval = cleanup_interval
        
        # In-memory storage for active sessions and connections
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.session_participants: Dict[str, Dict[str, UserPresence]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        
        # Redis connection for pub/sub
        self._redis_pool: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._pubsub_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the collaboration service."""
        logger.info("Starting collaboration service")
        
        # Initialize Redis connection
        self._redis_pool = redis.from_url(self.redis_url)
        self._pubsub = self._redis_pool.pubsub()
        
        # Subscribe to collaboration events
        await self._pubsub.subscribe("collaboration:updates")
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        self._pubsub_task = asyncio.create_task(self._handle_pubsub_messages())
        
        logger.info("Collaboration service started successfully")
    
    async def stop(self) -> None:
        """Stop the collaboration service."""
        logger.info("Stopping collaboration service")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._pubsub_task:
            self._pubsub_task.cancel()
        
        # Close Redis connections
        if self._pubsub:
            await self._pubsub.close()
        if self._redis_pool:
            await self._redis_pool.close()
        
        logger.info("Collaboration service stopped")
    
    async def create_session(self, document_id: str, owner_id: str, 
                           max_participants: int = 10) -> CollaborationSession:
        """Create a new collaboration session."""
        session_id = str(uuid4())
        
        session = CollaborationSession(
            session_id=session_id,
            document_id=document_id,
            owner_id=owner_id,
            max_participants=max_participants,
            participants=[owner_id],
            permissions={owner_id: ["read", "write", "admin"]}
        )
        
        self.active_sessions[session_id] = session
        self.session_participants[session_id] = {}
        
        # Store in Redis for persistence
        await self._store_session(session)
        
        logger.info(f"Created collaboration session {session_id} for document {document_id}")
        return session
    
    async def join_session(self, session_id: str, user_id: str, username: str,
                          websocket: WebSocket) -> bool:
        """Join a collaboration session."""
        if session_id not in self.active_sessions:
            # Try to load from Redis
            session = await self._load_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False
            self.active_sessions[session_id] = session
            self.session_participants[session_id] = {}
        
        session = self.active_sessions[session_id]
        
        # Check if session has space
        if len(session.participants) >= session.max_participants:
            logger.warning(f"Session {session_id} is full")
            return False
        
        # Add user to session
        if user_id not in session.participants:
            session.participants.append(user_id)
            session.permissions[user_id] = ["read", "write"]
        
        # Create user presence
        presence = UserPresence(
            user_id=user_id,
            username=username,
            color=self._generate_user_color(user_id)
        )
        
        self.session_participants[session_id][user_id] = presence
        self.websocket_connections[user_id] = websocket
        self.user_sessions[user_id] = session_id
        
        # Update session activity
        session.last_activity = datetime.now(UTC)
        await self._store_session(session)
        
        # Notify other participants
        await self._broadcast_to_session(session_id, WebSocketMessage(
            type=MessageType.PRESENCE_UPDATE,
            session_id=session_id,
            user_id=user_id,
            data={"action": "joined", "presence": presence.model_dump()}
        ), exclude_user=user_id)
        
        # Send current session state to new participant
        session_state = await self._get_session_state(session_id)
        await self._send_to_user(user_id, WebSocketMessage(
            type=MessageType.SESSION_STATE,
            session_id=session_id,
            data=session_state.model_dump()
        ))
        
        logger.info(f"User {user_id} joined session {session_id}")
        return True
    
    async def leave_session(self, user_id: str) -> None:
        """Remove user from their current session."""
        if user_id not in self.user_sessions:
            return
        
        session_id = self.user_sessions[user_id]
        
        # Remove from session participants
        if session_id in self.session_participants:
            self.session_participants[session_id].pop(user_id, None)
        
        # Remove from active session
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if user_id in session.participants:
                session.participants.remove(user_id)
            session.permissions.pop(user_id, None)
            session.last_activity = datetime.now(UTC)
            await self._store_session(session)
        
        # Clean up connections
        self.websocket_connections.pop(user_id, None)
        self.user_sessions.pop(user_id, None)
        
        # Notify other participants
        await self._broadcast_to_session(session_id, WebSocketMessage(
            type=MessageType.PRESENCE_UPDATE,
            session_id=session_id,
            user_id=user_id,
            data={"action": "left"}
        ), exclude_user=user_id)
        
        logger.info(f"User {user_id} left session {session_id}")
    
    async def handle_websocket_message(self, user_id: str, message: dict) -> None:
        """Handle incoming WebSocket message from user."""
        try:
            ws_message = WebSocketMessage(**message)
        except ValidationError as e:
            await self._send_error_to_user(user_id, "invalid_message", str(e))
            return
        
        session_id = self.user_sessions.get(user_id)
        if not session_id:
            await self._send_error_to_user(user_id, "not_in_session", "User not in any session")
            return
        
        # Route message based on type
        if ws_message.type == MessageType.DOCUMENT_UPDATE:
            await self._handle_document_update(user_id, session_id, ws_message)
        elif ws_message.type == MessageType.CURSOR_UPDATE:
            await self._handle_cursor_update(user_id, session_id, ws_message)
        elif ws_message.type == MessageType.PRESENCE_UPDATE:
            await self._handle_presence_update(user_id, session_id, ws_message)
        else:
            logger.warning(f"Unknown message type: {ws_message.type}")
    
    async def _handle_document_update(self, user_id: str, session_id: str, 
                                    message: WebSocketMessage) -> None:
        """Handle document update from user."""
        try:
            update_data = message.data
            update = DocumentUpdate(
                update_id=str(uuid4()),
                user_id=user_id,
                session_id=session_id,
                **update_data
            )
        except ValidationError as e:
            await self._send_error_to_user(user_id, "invalid_update", str(e))
            return
        
        # Store update in Redis
        await self._store_document_update(update)
        
        # Broadcast to other participants
        await self._broadcast_to_session(session_id, WebSocketMessage(
            type=MessageType.DOCUMENT_UPDATE,
            session_id=session_id,
            user_id=user_id,
            data=update.model_dump()
        ), exclude_user=user_id)
        
        # Publish to Redis for other service instances
        await self._redis_pool.publish("collaboration:updates", json.dumps({
            "type": "document_update",
            "session_id": session_id,
            "update": update.model_dump()
        }))
    
    async def _handle_cursor_update(self, user_id: str, session_id: str,
                                  message: WebSocketMessage) -> None:
        """Handle cursor position update."""
        if session_id not in self.session_participants:
            return
        
        if user_id not in self.session_participants[session_id]:
            return
        
        presence = self.session_participants[session_id][user_id]
        cursor_data = message.data
        
        # Update cursor position
        presence.cursor_position = cursor_data.get("position")
        presence.selection_start = cursor_data.get("selection_start")
        presence.selection_end = cursor_data.get("selection_end")
        presence.last_seen = datetime.now(UTC)
        
        # Broadcast to other participants
        await self._broadcast_to_session(session_id, WebSocketMessage(
            type=MessageType.CURSOR_UPDATE,
            session_id=session_id,
            user_id=user_id,
            data=cursor_data
        ), exclude_user=user_id)
    
    async def _handle_presence_update(self, user_id: str, session_id: str,
                                    message: WebSocketMessage) -> None:
        """Handle user presence update."""
        if session_id not in self.session_participants:
            return
        
        if user_id not in self.session_participants[session_id]:
            return
        
        presence = self.session_participants[session_id][user_id]
        presence.is_active = message.data.get("is_active", True)
        presence.last_seen = datetime.now(UTC)
        
        # Broadcast to other participants
        await self._broadcast_to_session(session_id, message, exclude_user=user_id)
    
    async def _broadcast_to_session(self, session_id: str, message: WebSocketMessage,
                                  exclude_user: Optional[str] = None) -> None:
        """Broadcast message to all participants in a session."""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        failed_connections = []
        
        for participant_id in session.participants:
            if participant_id == exclude_user:
                continue
            
            if participant_id in self.websocket_connections:
                try:
                    await self._send_to_user(participant_id, message)
                except Exception as e:
                    logger.error(f"Failed to send message to {participant_id}: {e}")
                    failed_connections.append(participant_id)
        
        # Clean up failed connections
        for failed_user in failed_connections:
            await self.leave_session(failed_user)
    
    async def _send_to_user(self, user_id: str, message: WebSocketMessage) -> None:
        """Send message to a specific user."""
        if user_id not in self.websocket_connections:
            return
        
        websocket = self.websocket_connections[user_id]
        await websocket.send_text(message.model_dump_json())
    
    async def _send_error_to_user(self, user_id: str, error_code: str, message: str) -> None:
        """Send error message to user."""
        error_response = ErrorResponse(error_code=error_code, message=message)
        await self._send_to_user(user_id, WebSocketMessage(
            type=MessageType.ERROR,
            data=error_response.model_dump()
        ))
    
    async def _get_session_state(self, session_id: str) -> SessionState:
        """Get complete session state for synchronization."""
        session = self.active_sessions.get(session_id)
        if not session:
            return SessionState(session_id=session_id)
        
        participants = self.session_participants.get(session_id, {})
        
        # TODO: Load actual document content from storage
        document_content = ""
        
        return SessionState(
            session_id=session_id,
            document_content=document_content,
            participants=participants,
            last_updated=session.last_activity
        )
    
    async def _store_session(self, session: CollaborationSession) -> None:
        """Store session in Redis."""
        if not self._redis_pool:
            return
        
        key = f"session:{session.session_id}"
        await self._redis_pool.setex(
            key, 
            timedelta(hours=24), 
            session.model_dump_json()
        )
    
    async def _load_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Load session from Redis."""
        if not self._redis_pool:
            return None
        
        key = f"session:{session_id}"
        data = await self._redis_pool.get(key)
        if not data:
            return None
        
        try:
            return CollaborationSession.model_validate_json(data)
        except ValidationError:
            logger.error(f"Failed to parse session data for {session_id}")
            return None
    
    async def _store_document_update(self, update: DocumentUpdate) -> None:
        """Store document update in Redis."""
        if not self._redis_pool:
            return
        
        key = f"updates:{update.session_id}"
        await self._redis_pool.lpush(key, update.model_dump_json())
        await self._redis_pool.expire(key, timedelta(hours=24))
    
    def _generate_user_color(self, user_id: str) -> str:
        """Generate consistent color for user based on their ID."""
        colors = [
            "#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1",
            "#fd7e14", "#20c997", "#e83e8c", "#6c757d", "#17a2b8"
        ]
        return colors[hash(user_id) % len(colors)]
    
    async def _cleanup_inactive_sessions(self) -> None:
        """Background task to clean up inactive sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                now = datetime.now(UTC)
                inactive_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    # Remove sessions inactive for more than 1 hour
                    if (now - session.last_activity).total_seconds() > 3600:
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    logger.info(f"Cleaning up inactive session {session_id}")
                    self.active_sessions.pop(session_id, None)
                    self.session_participants.pop(session_id, None)
                    
                    # Clean up user connections in this session
                    users_to_remove = [
                        user_id for user_id, user_session_id in self.user_sessions.items()
                        if user_session_id == session_id
                    ]
                    
                    for user_id in users_to_remove:
                        self.websocket_connections.pop(user_id, None)
                        self.user_sessions.pop(user_id, None)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _handle_pubsub_messages(self) -> None:
        """Handle Redis pub/sub messages from other service instances."""
        if not self._pubsub:
            return
        
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                
                try:
                    data = json.loads(message["data"])
                    if data["type"] == "document_update":
                        # Handle document updates from other instances
                        session_id = data["session_id"]
                        update = DocumentUpdate(**data["update"])
                        
                        # Broadcast to local participants
                        await self._broadcast_to_session(session_id, WebSocketMessage(
                            type=MessageType.DOCUMENT_UPDATE,
                            session_id=session_id,
                            user_id=update.user_id,
                            data=update.model_dump()
                        ))
                        
                except Exception as e:
                    logger.error(f"Error handling pubsub message: {e}")
        
        except Exception as e:
            logger.error(f"Error in pubsub listener: {e}")