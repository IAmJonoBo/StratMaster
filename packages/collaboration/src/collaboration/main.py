"""
FastAPI application for real-time collaboration service.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .service import CollaborationService
from .models import (
    CollaborationSession, 
    SessionJoinRequest,
    MessageType,
    WebSocketMessage
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instance
collaboration_service: CollaborationService = None


class CreateSessionRequest(BaseModel):
    """Request to create a new collaboration session."""
    document_id: str = Field(..., description="Document ID to collaborate on")
    max_participants: int = Field(10, description="Maximum number of participants", ge=1, le=50)


class SessionResponse(BaseModel):
    """Response containing session information."""
    session_id: str
    document_id: str
    owner_id: str
    participant_count: int
    max_participants: int
    created_at: str
    is_active: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "collaboration"
    active_sessions: int = 0
    connected_users: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global collaboration_service
    
    # Startup
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    collaboration_service = CollaborationService(redis_url=redis_url)
    
    try:
        await collaboration_service.start()
        logger.info("Collaboration service started successfully")
        yield
    finally:
        # Shutdown
        if collaboration_service:
            await collaboration_service.stop()
            logger.info("Collaboration service stopped")


# Create FastAPI app
app = FastAPI(
    title="StratMaster Collaboration Service",
    description="Real-time collaboration service for strategic debates and document editing",
    version="0.1.0",
    lifespan=lifespan
)


def get_collaboration_service() -> CollaborationService:
    """Dependency to get collaboration service instance."""
    if collaboration_service is None:
        raise HTTPException(status_code=503, detail="Collaboration service not available")
    return collaboration_service


@app.get("/health", response_model=HealthResponse)
async def health_check(service: CollaborationService = Depends(get_collaboration_service)):
    """Health check endpoint."""
    return HealthResponse(
        active_sessions=len(service.active_sessions),
        connected_users=len(service.websocket_connections)
    )


@app.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(service: CollaborationService = Depends(get_collaboration_service)):
    """List all active collaboration sessions."""
    sessions = []
    for session in service.active_sessions.values():
        sessions.append(SessionResponse(
            session_id=session.session_id,
            document_id=session.document_id,
            owner_id=session.owner_id,
            participant_count=len(session.participants),
            max_participants=session.max_participants,
            created_at=session.created_at.isoformat(),
            is_active=session.is_active
        ))
    return sessions


@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    user_id: str = "default-user",  # TODO: Get from authentication
    service: CollaborationService = Depends(get_collaboration_service)
):
    """Create a new collaboration session."""
    session = await service.create_session(
        document_id=request.document_id,
        owner_id=user_id,
        max_participants=request.max_participants
    )
    
    return SessionResponse(
        session_id=session.session_id,
        document_id=session.document_id,
        owner_id=session.owner_id,
        participant_count=len(session.participants),
        max_participants=session.max_participants,
        created_at=session.created_at.isoformat(),
        is_active=session.is_active
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    service: CollaborationService = Depends(get_collaboration_service)
):
    """Get details of a specific session."""
    if session_id not in service.active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = service.active_sessions[session_id]
    return SessionResponse(
        session_id=session.session_id,
        document_id=session.document_id,
        owner_id=session.owner_id,
        participant_count=len(session.participants),
        max_participants=session.max_participants,
        created_at=session.created_at.isoformat(),
        is_active=session.is_active
    )


@app.websocket("/ws/collaboration")
async def websocket_endpoint(
    websocket: WebSocket,
    service: CollaborationService = Depends(get_collaboration_service)
):
    """WebSocket endpoint for real-time collaboration."""
    await websocket.accept()
    
    user_id = None
    session_id = None
    
    try:
        # Wait for initial join message
        data = await websocket.receive_text()
        
        try:
            message = WebSocketMessage.model_validate_json(data)
        except Exception as e:
            await websocket.send_text(
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error_code": "invalid_message", "message": str(e)}
                ).model_dump_json()
            )
            await websocket.close()
            return
        
        if message.type != MessageType.JOIN_SESSION:
            await websocket.send_text(
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error_code": "invalid_initial_message", "message": "First message must be join_session"}
                ).model_dump_json()
            )
            await websocket.close()
            return
        
        # Extract join request data
        try:
            join_data = message.data
            session_id = join_data["session_id"]
            user_id = join_data["user_id"]
            username = join_data.get("username", user_id)
        except KeyError as e:
            await websocket.send_text(
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error_code": "missing_field", "message": f"Missing required field: {e}"}
                ).model_dump_json()
            )
            await websocket.close()
            return
        
        # Join the session
        success = await service.join_session(session_id, user_id, username, websocket)
        
        if not success:
            await websocket.send_text(
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error_code": "join_failed", "message": "Failed to join session"}
                ).model_dump_json()
            )
            await websocket.close()
            return
        
        logger.info(f"User {user_id} connected to session {session_id}")
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = WebSocketMessage.model_validate_json(data).model_dump()
                await service.handle_websocket_message(user_id, message_data)
            except Exception as e:
                logger.error(f"Error handling message from {user_id}: {e}")
                await websocket.send_text(
                    WebSocketMessage(
                        type=MessageType.ERROR,
                        data={"error_code": "message_error", "message": str(e)}
                    ).model_dump_json()
                )
    
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up user session
        if user_id:
            await service.leave_session(user_id)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "StratMaster Collaboration Service",
        "version": "0.1.0",
        "description": "Real-time collaboration for strategic debates and document editing",
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions",
            "websocket": "/ws/collaboration"
        },
        "websocket_protocol": {
            "url": "ws://localhost:8084/ws/collaboration",
            "initial_message": {
                "type": "join_session",
                "data": {
                    "session_id": "session-id",
                    "user_id": "user-id",
                    "username": "display-name"
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8084"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "collaboration.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )