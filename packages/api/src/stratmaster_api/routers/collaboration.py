"""Collaboration WebSocket router for StratMaster API."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ..collaboration import is_collaboration_enabled, YjsCollaborationServer
from ..middleware.auth import get_optional_user_from_middleware

logger = logging.getLogger(__name__)

# Global collaboration server instance
collaboration_server: YjsCollaborationServer | None = None


def setup_collaboration_websocket(app: FastAPI) -> None:
    """Setup collaboration WebSocket endpoints in the FastAPI app."""
    global collaboration_server
    
    if not is_collaboration_enabled():
        logger.info("Collaboration WebSocket endpoints disabled (ENABLE_COLLAB_LIVE=false)")
        return
    
    logger.info("Setting up collaboration WebSocket endpoints")
    
    # Initialize the collaboration server
    collaboration_server = YjsCollaborationServer()
    
    @app.get("/collaboration/status")
    async def collaboration_status():
        """Get collaboration feature status."""
        if not is_collaboration_enabled():
            return JSONResponse(
                content={
                    "status": "disabled",
                    "message": "Real-time collaboration is disabled. Set ENABLE_COLLAB_LIVE=true to enable.",
                    "feature_flag": "ENABLE_COLLAB_LIVE",
                    "current_value": "false"
                }
            )
        
        return JSONResponse(
            content={
                "status": "enabled",
                "version": "1.0",
                "websocket_endpoint": "/ws/collaboration",
                "active_connections": collaboration_server.connection_count if collaboration_server else 0,
                "total_messages": collaboration_server.message_count if collaboration_server else 0,
                "feature_flags": {
                    "ENABLE_COLLAB_LIVE": "true"
                }
            }
        )
    
    @app.websocket("/ws/collaboration/{doc_id}")
    async def websocket_collaboration_endpoint(websocket: WebSocket, doc_id: str):
        """WebSocket endpoint for real-time collaborative editing.
        
        Args:
            doc_id: Document ID to collaborate on
        """
        if not is_collaboration_enabled() or not collaboration_server:
            await websocket.close(code=1001, reason="Collaboration disabled")
            return
            
        await websocket.accept()
        
        user_id = None
        connection_id = None
        
        try:
            # Extract user info from headers if available
            user_info = await get_user_from_websocket_headers(websocket)
            user_id = user_info.get("user_id", "anonymous") if user_info else "anonymous"
            
            logger.info(f"WebSocket connection for doc {doc_id}, user {user_id}")
            
            # Subscribe to document
            await collaboration_server.subscribe_to_document(websocket, doc_id, user_id)
            
            # Send initial document state
            doc_state = await collaboration_server.load_document_state(doc_id)
            await websocket.send_json({
                "type": "document_state",
                "doc_id": doc_id,
                "state": doc_state,
                "presence": list(collaboration_server.user_presence.get(doc_id, {}).values())
            })
            
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                
                # Process message through collaboration server
                response = await collaboration_server.handle_message(
                    websocket, 
                    {**data, "doc_id": doc_id, "user_id": user_id},
                    connection_id or "websocket"
                )
                
                # Send response if any
                if response:
                    await websocket.send_json(response)
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for doc {doc_id}, user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for doc {doc_id}: {e}")
            await websocket.close(code=1011, reason="Internal error")
        finally:
            # Cleanup connection
            if collaboration_server:
                await collaboration_server.cleanup_connection(websocket, doc_id, user_id, connection_id)


async def get_user_from_websocket_headers(websocket: WebSocket) -> dict[str, Any] | None:
    """Extract user information from WebSocket headers.
    
    This would integrate with the authentication middleware to validate
    user tokens from WebSocket headers.
    """
    try:
        # Get authorization header if present
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, this would validate the JWT token
            # and extract user information
            # For now, return mock user info
            return {
                "user_id": "user_from_token",
                "username": "User",
                "authenticated": True
            }
        
        # Get user ID from query params as fallback
        user_id = websocket.query_params.get("user_id")
        if user_id:
            return {
                "user_id": user_id,
                "username": f"User {user_id}",
                "authenticated": False
            }
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to extract user from WebSocket headers: {e}")
        return None