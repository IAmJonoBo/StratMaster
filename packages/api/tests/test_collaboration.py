"""Tests for Real-Time Collaboration Engine."""

import json
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from stratmaster_api.collaboration import (
    is_collaboration_enabled,
    YjsCollaborationServer,
    UserPresence,
    DocumentUpdate,
)
from stratmaster_api.app import create_app


class TestCollaborationFeatureFlag:
    """Test collaboration feature flag functionality."""
    
    def test_collaboration_disabled_by_default(self):
        """Test that collaboration is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert not is_collaboration_enabled()
    
    def test_collaboration_enabled_when_set(self):
        """Test that collaboration is enabled when flag is set."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "true"}):
            assert is_collaboration_enabled()
        
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "TRUE"}):
            assert is_collaboration_enabled()
    
    def test_collaboration_disabled_when_false(self):
        """Test that collaboration is disabled when explicitly set to false."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "false"}):
            assert not is_collaboration_enabled()
        
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "invalid"}):
            assert not is_collaboration_enabled()


class TestCollaborationStatusEndpoint:
    """Test collaboration status API endpoint."""
    
    def test_status_disabled_by_default(self):
        """Test status endpoint when collaboration is disabled."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "false"}):
            app = create_app()
            with TestClient(app) as client:
                response = client.get("/collaboration/status")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "disabled"
                assert data["feature_flag"] == "ENABLE_COLLAB_LIVE"
                assert data["current_value"] == "false"
    
    def test_status_enabled_when_flag_set(self):
        """Test status endpoint when collaboration is enabled."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "true"}):
            app = create_app()
            with TestClient(app) as client:
                response = client.get("/collaboration/status")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "enabled"
                assert data["version"] == "1.0"
                assert data["websocket_endpoint"] == "/ws/collaboration"
                assert "active_connections" in data
                assert "total_messages" in data


class TestCollaborationDataStructures:
    """Test collaboration data structures."""
    
    def test_user_presence_creation(self):
        """Test UserPresence dataclass creation."""
        presence = UserPresence(
            user_id="user123",
            username="TestUser",
            cursor_position=42,
            selection_start=10,
            selection_end=20,
            color="#ff0000"
        )
        
        assert presence.user_id == "user123"
        assert presence.username == "TestUser"
        assert presence.cursor_position == 42
        assert presence.selection_start == 10
        assert presence.selection_end == 20
        assert presence.color == "#ff0000"
    
    def test_user_presence_defaults(self):
        """Test UserPresence dataclass defaults."""
        presence = UserPresence(
            user_id="user123",
            username="TestUser"
        )
        
        assert presence.cursor_position is None
        assert presence.selection_start is None
        assert presence.selection_end is None
        assert presence.last_seen is None
        assert presence.color == "#3b82f6"  # Default blue
    
    def test_document_update_creation(self):
        """Test DocumentUpdate dataclass creation."""
        update = DocumentUpdate(
            doc_id="doc123",
            user_id="user123", 
            operations=[{"type": "insert", "position": 0, "text": "Hello"}],
            vector_clock={"user123": 1},
            timestamp=1234567890.0
        )
        
        assert update.doc_id == "doc123"
        assert update.user_id == "user123"
        assert len(update.operations) == 1
        assert update.operations[0]["type"] == "insert"
        assert update.vector_clock["user123"] == 1
        assert update.timestamp == 1234567890.0


@pytest.mark.asyncio
class TestYjsCollaborationServer:
    """Test YjsCollaborationServer functionality."""
    
    async def test_server_initialization(self):
        """Test collaboration server initialization."""
        server = YjsCollaborationServer(
            host="127.0.0.1",
            port=8765,
            redis_url="redis://localhost:6379"
        )
        
        assert server.host == "127.0.0.1"
        assert server.port == 8765
        assert server.redis_url == "redis://localhost:6379"
        assert server.message_count == 0
        assert server.connection_count == 0
        assert len(server.documents) == 0
        assert len(server.document_subscribers) == 0
        assert len(server.user_presence) == 0
    
    async def test_handle_subscribe_message(self):
        """Test handling subscribe messages."""
        server = YjsCollaborationServer()
        
        response = await server.handle_subscribe({
            "doc_id": "test-doc",
            "user_id": "test-user"
        })
        
        assert response["type"] == "document_state"
        assert response["doc_id"] == "test-doc"
        assert "state" in response
        assert "presence" in response
    
    async def test_handle_subscribe_missing_doc_id(self):
        """Test handling subscribe with missing doc_id."""
        server = YjsCollaborationServer()
        
        response = await server.handle_subscribe({
            "user_id": "test-user"
        })
        
        assert response["type"] == "error"
        assert "doc_id required" in response["message"]
    
    async def test_ping_pong_handling(self):
        """Test ping-pong message handling."""
        server = YjsCollaborationServer()
        mock_websocket = MagicMock()
        
        response = await server.handle_message(
            mock_websocket,
            {"type": "ping"},
            "connection123"
        )
        
        assert response["type"] == "pong"
        assert "timestamp" in response
    
    async def test_unknown_message_type(self):
        """Test handling unknown message types."""
        server = YjsCollaborationServer()
        mock_websocket = MagicMock()
        
        response = await server.handle_message(
            mock_websocket,
            {"type": "unknown_message"},
            "connection123"
        )
        
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]
    
    async def test_document_state_loading(self):
        """Test document state loading."""
        server = YjsCollaborationServer()
        
        # Test loading non-existent document
        state = await server.load_document_state("nonexistent-doc")
        assert state == {"content": "", "version": 0}
        
        # Add document and test loading
        server.documents["test-doc"] = {"content": "Hello World", "version": 5}
        state = await server.load_document_state("test-doc")
        assert state["content"] == "Hello World"
        assert state["version"] == 5
    
    async def test_document_state_persistence(self):
        """Test document state persistence."""
        server = YjsCollaborationServer()
        
        # Test saving document state
        await server.save_document_state("test-doc", {
            "content": "Test content",
            "version": 1
        })
        
        assert server.documents["test-doc"]["content"] == "Test content"
        assert server.documents["test-doc"]["version"] == 1
        
        # Test loading saved state
        state = await server.load_document_state("test-doc")
        assert state["content"] == "Test content"
        assert state["version"] == 1


class TestCollaborationIntegration:
    """Test integration between collaboration components."""
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_disabled(self):
        """Test WebSocket endpoint behavior when collaboration is disabled."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "false"}):
            app = create_app()
            
            # WebSocket endpoint should not be available or should close immediately
            with TestClient(app) as client:
                # Try to establish WebSocket connection
                with pytest.raises(Exception):
                    # WebSocket connection should fail or be rejected
                    with client.websocket_connect("/ws/collaboration/test-doc"):
                        pass  # Should not reach this point
    
    def test_app_creation_with_collaboration_enabled(self):
        """Test app creation when collaboration is enabled."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "true"}):
            # Should not raise any exceptions
            app = create_app()
            assert app is not None
            
            # Check that collaboration status endpoint is available
            with TestClient(app) as client:
                response = client.get("/collaboration/status")
                assert response.status_code == 200
    
    def test_app_creation_with_collaboration_disabled(self):
        """Test app creation when collaboration is disabled."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "false"}):
            # Should not raise any exceptions
            app = create_app()
            assert app is not None
    
    def test_collaboration_graceful_degradation(self):
        """Test that app works when WebSocket dependencies are missing."""
        with patch.dict(os.environ, {"ENABLE_COLLAB_LIVE": "true"}):
            with patch("stratmaster_api.routers.collaboration.setup_collaboration_websocket") as mock_setup:
                # Simulate missing WebSocket dependencies
                mock_setup.side_effect = ImportError("websockets not available")
                
                # App should still create successfully
                app = create_app()
                assert app is not None