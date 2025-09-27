"""Real-time collaboration system using Yjs CRDT for StratMaster.

Implements conflict-free collaborative editing with:
- Yjs WebSocket provider for real-time synchronization
- Presence awareness (cursors, user indicators)
- Operational Transformation (OT) and CRDT for conflict resolution
- PostgreSQL/Redis backend for document persistence
- TipTap/ProseMirror editor bindings ready
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Set
from uuid import uuid4

# Prefer new asyncio API; fallback to legacy for older installations
try:
    from websockets.asyncio.server import serve as ws_serve  # type: ignore
    from websockets.asyncio.client import connect as ws_connect  # type: ignore
    from websockets.exceptions import ConnectionClosed  # type: ignore
except Exception:
    try:
        # Legacy fallback (deprecated in websockets >=14)
        from websockets.server import serve as ws_serve  # type: ignore
        from websockets.client import connect as ws_connect  # type: ignore
        from websockets.exceptions import ConnectionClosed  # type: ignore
    except Exception:
        ws_serve = None  # type: ignore[assignment]
        ws_connect = None  # type: ignore[assignment]
        ConnectionClosed = Exception  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from y_py import YDoc, apply_update, encode_state_as_update
    YPY_AVAILABLE = True
except Exception:  # pragma: no cover - fall back when y-py not installed
    YDoc = None  # type: ignore
    apply_update = None  # type: ignore
    encode_state_as_update = None  # type: ignore
    YPY_AVAILABLE = False

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

# Feature flag for Real-Time Collaboration
def is_collaboration_enabled() -> bool:
    """Check if real-time collaboration is enabled via feature flag."""
    return os.getenv("ENABLE_COLLAB_LIVE", "false").lower() == "true"


@dataclass
class UserPresence:
    """User presence information for collaborative editing."""
    user_id: str
    username: str
    cursor_position: int | None = None
    selection_start: int | None = None
    selection_end: int | None = None
    last_seen: float | None = None
    color: str = "#3b82f6"  # Default blue


@dataclass
class DocumentUpdate:
    """Document update with CRDT operations."""
    doc_id: str
    user_id: str
    operations: list[dict[str, Any]]
    vector_clock: dict[str, int]
    timestamp: float


class YjsCollaborationServer:
    """WebSocket server for real-time collaborative editing using Yjs protocol."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        redis_url: str = "redis://localhost:6379"
    ):
        self.host = host
        self.port = port
        self.redis_url = redis_url
        # In-memory state (would be backed by Redis/PostgreSQL in production)
        self.documents: dict[str, dict[str, Any]] = {}
        self.document_subscribers: dict[str, set[Any]] = {}
        self.user_presence: dict[str, dict[str, UserPresence]] = {}  # doc_id -> user_id -> presence
        # Yjs document store (CRDT) per doc_id when y-py is available
        self.ydocs: dict[str, Any] = {}

        # Redis client for persistence
        self.redis_client = None

        # Performance metrics
        self.message_count = 0
        self.connection_count = 0

    async def start_server(self):
        """Start the collaborative editing WebSocket server."""
        if ws_serve is None:
            raise RuntimeError("websockets library not installed. Run: pip install websockets>=10")

        # Initialize Redis connection
        if redis is not None:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory storage only.")
                self.redis_client = None

        logger.info(f"Starting Yjs collaboration server on {self.host}:{self.port}")

        async with ws_serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=10,   # Timeout after 10 seconds
            compression=None   # Disable compression for low latency
        ):
            logger.info(f"✅ Collaboration server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    # ------------------------------------------------------------------
    # Yjs helpers
    # ------------------------------------------------------------------
    def _get_or_create_ydoc(self, doc_id: str) -> Any | None:
        """Return a YDoc for the document when y-py is available."""
        if not YPY_AVAILABLE:
            return None
        if doc_id not in self.ydocs:
            self.ydocs[doc_id] = YDoc()
        return self.ydocs[doc_id]

    def _sync_ydoc_from_text(self, doc_id: str, text: str) -> None:
        """Ensure the YDoc content matches the provided text."""
        if not YPY_AVAILABLE:
            return
        doc = self._get_or_create_ydoc(doc_id)
        if doc is None:
            return
        with doc.begin_transaction() as txn:
            ytext = doc.get_text("content")
            length = ytext.length(txn)
            if length:
                ytext.delete_range(txn, 0, length)
            if text:
                ytext.insert(txn, 0, text)

    def _extract_text_from_ydoc(self, doc_id: str) -> str:
        """Read the current document text from the YDoc."""
        if not YPY_AVAILABLE:
            return self.documents.get(doc_id, {}).get("content", "")
        doc = self._get_or_create_ydoc(doc_id)
        if doc is None:
            return self.documents.get(doc_id, {}).get("content", "")
        with doc.begin_transaction() as txn:
            ytext = doc.get_text("content")
            return ytext.to_string(txn)

    def _encode_full_update(self, doc_id: str) -> str | None:
        """Encode the current YDoc state as a base64 update for broadcasting."""
        if not YPY_AVAILABLE:
            return None
        doc = self._get_or_create_ydoc(doc_id)
        if doc is None:
            return None
        update_bytes = encode_state_as_update(doc, b"")
        return base64.b64encode(update_bytes).decode("ascii")

    def _apply_operation_to_ydoc(self, doc_id: str, operation: dict[str, Any]) -> None:
        """Apply a high-level operation (insert/delete) to the YDoc text."""
        if not YPY_AVAILABLE:
            return
        doc = self._get_or_create_ydoc(doc_id)
        if doc is None:
            return

        op_type = operation.get("type")
        if op_type not in {"insert", "delete"}:
            return

        position = int(operation.get("position", 0))
        if position < 0:
            position = 0

        with doc.begin_transaction() as txn:
            ytext = doc.get_text("content")
            text_length = ytext.length(txn)
            if position > text_length:
                position = text_length

            if op_type == "insert":
                text = operation.get("text", "")
                if text:
                    ytext.insert(txn, position, text)
            elif op_type == "delete":
                length = int(operation.get("length", 0))
                if length > 0:
                    length = min(length, text_length - position)
                    if length > 0:
                        ytext.delete_range(txn, position, length)

    async def _apply_y_update(
        self,
        doc_id: str,
        update_base64: str,
        user_id: str,
        timestamp: float,
    ) -> None:
        """Apply a base64-encoded Yjs update to the stored document."""
        if not YPY_AVAILABLE:
            return
        try:
            update_bytes = base64.b64decode(update_base64)
        except Exception:
            logger.warning("Invalid Yjs update payload; falling back to no-op")
            return

        doc = self._get_or_create_ydoc(doc_id)
        if doc is None:
            return

        apply_update(doc, update_bytes)

        # Update in-memory metadata for compatibility with existing API/tests
        state = self.documents.get(doc_id)
        if not state:
            state = {
                "content": "",
                "vector_clock": {},
                "operations": [],
                "version": 0,
            }
            self.documents[doc_id] = state

        state["vector_clock"][user_id] = state["vector_clock"].get(user_id, 0) + 1
        state["version"] = state.get("version", 0) + 1
        state["content"] = self._extract_text_from_ydoc(doc_id)
        state.setdefault("operations", []).append({
            "type": "y_update",
            "user_id": user_id,
            "timestamp": timestamp,
        })

        await self.save_document_state(doc_id, state)

    async def handle_connection(self, websocket: Any, path: str):
        """Handle new WebSocket connection for collaborative editing."""
        self.connection_count += 1
        connection_id = str(uuid4())
        doc_id = None
        user_id = None

        logger.info(f"New connection: {connection_id} (total: {self.connection_count})")

        try:
            async for message in websocket:
                start_time = time.time()

                try:
                    data = json.loads(message)
                    response = await self.handle_message(websocket, data, connection_id)

                    # Track document subscription
                    if data.get("type") == "subscribe" and "doc_id" in data:
                        doc_id = data["doc_id"]
                        user_id = data.get("user_id")
                        await self.subscribe_to_document(websocket, doc_id, user_id)

                    # Send response if needed
                    if response:
                        await websocket.send(json.dumps(response))

                    # Track performance
                    processing_time = (time.time() - start_time) * 1000
                    self.message_count += 1

                    if processing_time > 150:  # Warn if >150ms (quality gate)
                        logger.warning(f"Slow message processing: {processing_time:.1f}ms")

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }))

        except ConnectionClosed:
            logger.info(f"Connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            # Cleanup
            await self.cleanup_connection(websocket, doc_id, user_id, connection_id)

    async def handle_message(
        self,
        websocket: Any,
        data: dict[str, Any],
        connection_id: str
    ) -> dict[str, Any] | None:
        """Handle incoming WebSocket message."""
        message_type = data.get("type")

        if message_type == "subscribe":
            return await self.handle_subscribe(data)

        elif message_type == "document_update":
            return await self.handle_document_update(websocket, data)

        elif message_type == "presence_update":
            return await self.handle_presence_update(websocket, data)

        elif message_type == "ping":
            return {"type": "pong", "timestamp": time.time()}

        else:
            logger.warning(f"Unknown message type: {message_type}")
            return {"type": "error", "message": f"Unknown message type: {message_type}"}

    async def handle_subscribe(self, data: dict[str, Any]) -> dict[str, Any]:
        """Handle document subscription request."""
        doc_id = data.get("doc_id")
        user_id = data.get("user_id", "anonymous")

        if not doc_id:
            return {"type": "error", "message": "doc_id required"}

        # Load document state
        doc_state = await self.load_document_state(doc_id)
        y_update_base64 = self._encode_full_update(doc_id)

        return {
            "type": "document_state",
            "doc_id": doc_id,
            "state": doc_state,
            "presence": list(self.user_presence.get(doc_id, {}).values()),
            "y_update_base64": y_update_base64,
        }

    async def handle_document_update(
        self,
        websocket: Any,
        data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Handle document update with CRDT operations."""
        doc_id = data.get("doc_id")
        user_id = data.get("user_id", "anonymous")
        operations = data.get("operations", [])
        y_update_base64 = data.get("y_update_base64")

        if not doc_id:
            return {"type": "error", "message": "doc_id and operations required"}

        if not operations and not y_update_base64:
            return {"type": "error", "message": "operations or y_update_base64 required"}

        # Create update object
        update = DocumentUpdate(
            doc_id=doc_id,
            user_id=user_id,
            operations=operations,
            vector_clock=data.get("vector_clock", {}),
            timestamp=time.time()
        )

        # Apply operations via Yjs when possible, otherwise fall back to legacy handler
        if y_update_base64 and YPY_AVAILABLE:
            await self._apply_y_update(doc_id, y_update_base64, user_id, update.timestamp)
        else:
            await self.apply_document_update(update)

        # Broadcast to all subscribers except sender
        await self.broadcast_update(websocket, doc_id, {
            "type": "document_update",
            "doc_id": doc_id,
            "user_id": user_id,
            "operations": operations,
            "timestamp": update.timestamp,
            "y_update_base64": y_update_base64 or self._encode_full_update(doc_id),
        })

        return None  # No direct response needed

    async def handle_presence_update(
        self,
        websocket: Any,
        data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Handle user presence update (cursor position, selection, etc.)."""
        doc_id = data.get("doc_id")
        user_id = data.get("user_id", "anonymous")

        if not doc_id:
            return {"type": "error", "message": "doc_id required"}

        # Update presence
        if doc_id not in self.user_presence:
            self.user_presence[doc_id] = {}

        self.user_presence[doc_id][user_id] = UserPresence(
            user_id=user_id,
            username=data.get("username", user_id),
            cursor_position=data.get("cursor_position"),
            selection_start=data.get("selection_start"),
            selection_end=data.get("selection_end"),
            last_seen=time.time(),
            color=data.get("color", "#3b82f6")
        )

        # Broadcast presence to all subscribers except sender
        await self.broadcast_update(websocket, doc_id, {
            "type": "presence_update",
            "doc_id": doc_id,
            "user_id": user_id,
            "presence": {
                "cursor_position": data.get("cursor_position"),
                "selection_start": data.get("selection_start"),
                "selection_end": data.get("selection_end"),
                "username": data.get("username", user_id),
                "color": data.get("color", "#3b82f6")
            }
        })

        return None

    async def subscribe_to_document(
        self,
        websocket: Any,
        doc_id: str,
        user_id: str | None
    ):
        """Subscribe websocket to document updates."""
        if doc_id not in self.document_subscribers:
            self.document_subscribers[doc_id] = set()

        self.document_subscribers[doc_id].add(websocket)
        logger.info(f"User {user_id} subscribed to document {doc_id}")

    async def apply_document_update(self, update: DocumentUpdate):
        """Apply CRDT operations to document state."""
        doc_id = update.doc_id
        state = self.documents.setdefault(
            doc_id,
            {"content": "", "vector_clock": {}, "operations": [], "version": 0},
        )

        # Apply high-level operations to Yjs document when available
        for op in update.operations:
            self._apply_operation_to_ydoc(doc_id, op)

        # Update vector clock metadata
        for user_id, clock in update.vector_clock.items():
            state["vector_clock"][user_id] = max(
                state["vector_clock"].get(user_id, 0),
                clock,
            )
        state["vector_clock"][update.user_id] = (
            state["vector_clock"].get(update.user_id, 0) + 1
        )

        # Persist recent operations for audit/debug (trim to avoid unbounded growth)
        operation_record = {
            "user_id": update.user_id,
            "operation": update.operations,
            "timestamp": update.timestamp,
        }
        state.setdefault("operations", []).append(operation_record)
        if len(state["operations"]) > 100:
            state["operations"] = state["operations"][-100:]

        # Refresh materialised content + version counter
        if YPY_AVAILABLE:
            state["content"] = self._extract_text_from_ydoc(doc_id)
        else:
            # Fallback to naive application if Yjs unavailable
            for op in update.operations:
                if op.get("type") == "insert":
                    text = op.get("text", "")
                    position = max(int(op.get("position", 0)), 0)
                    content = state.get("content", "")
                    state["content"] = (
                        content[:position] + text + content[position:]
                    )
                elif op.get("type") == "delete":
                    length = int(op.get("length", 0))
                    position = max(int(op.get("position", 0)), 0)
                    content = state.get("content", "")
                    state["content"] = (
                        content[:position] + content[position + length :]
                    )

        state["version"] = state.get("version", 0) + 1

        await self.save_document_state(doc_id, state)

    async def broadcast_update(
        self,
        sender: Any,
        doc_id: str,
        message: dict[str, Any]
    ):
        """Broadcast update to all document subscribers except sender."""
        if doc_id not in self.document_subscribers:
            return

        subscribers = self.document_subscribers[doc_id].copy()
        message_json = json.dumps(message)

        for websocket in subscribers:
            if websocket != sender:  # Don't send to sender
                try:
                    await websocket.send(message_json)
                except ConnectionClosed:
                    # Remove closed connection
                    self.document_subscribers[doc_id].discard(websocket)
                except Exception as e:
                    logger.error(f"Failed to send message to subscriber: {e}")

    async def load_document_state(self, doc_id: str) -> dict[str, Any]:
        """Load document state from Redis or create new."""
        # Try Redis first
        if self.redis_client:
            try:
                doc_json = await self.redis_client.get(f"doc:{doc_id}")
                if doc_json:
                    state = json.loads(doc_json)
                    if not isinstance(state, dict):
                        state = {"content": "", "version": 0}
                    state.setdefault("content", "")
                    state.setdefault("vector_clock", {})
                    state.setdefault("operations", [])
                    state.setdefault("version", 0)
                    self.documents[doc_id] = state
                    self._sync_ydoc_from_text(doc_id, state["content"])
                    return {"content": state["content"], "version": state["version"]}
            except Exception as e:
                logger.warning(f"Failed to load document from Redis: {e}")

        # Try in-memory storage
        if doc_id in self.documents:
            state = self.documents[doc_id]
            if YPY_AVAILABLE:
                self._sync_ydoc_from_text(doc_id, state.get("content", ""))
            return {"content": state.get("content", ""), "version": state.get("version", 0)}

        # Create new document (store full state, return minimal view for compatibility)
        new_doc_full = {
            "content": "",
            "vector_clock": {},
            "operations": [],
            "version": 0,
        }
        self.documents[doc_id] = new_doc_full
        if YPY_AVAILABLE:
            self._sync_ydoc_from_text(doc_id, "")
        # For initial load of a brand-new document, return a compact state expected by clients/tests
        return {"content": "", "version": 0}

    async def save_document_state(self, doc_id: str, state: dict[str, Any]):
        """Save document state to storage."""
        # Ensure required keys exist for compatibility
        state.setdefault("content", "")
        state.setdefault("vector_clock", {})
        state.setdefault("operations", [])
        state.setdefault("version", 0)

        # Keep Yjs document in sync with materialised content
        if YPY_AVAILABLE:
            self._sync_ydoc_from_text(doc_id, state["content"])

        # Update in-memory storage (store a shallow copy to avoid external mutation)
        self.documents[doc_id] = {
            "content": state["content"],
            "vector_clock": dict(state.get("vector_clock", {})),
            "operations": list(state.get("operations", [])),
            "version": state.get("version", 0),
        }

        # Persist to Redis if available
        if self.redis_client:
            try:
                await self.redis_client.set(
                    f"doc:{doc_id}",
                    json.dumps(self.documents[doc_id]),
                    ex=3600 * 24  # Expire after 24 hours
                )
            except Exception as e:
                logger.warning(f"Failed to persist document to Redis: {e}")

    async def cleanup_connection(
        self,
        websocket: Any,
        doc_id: str | None,
        user_id: str | None,
        connection_id: str
    ):
        """Clean up connection state."""
        self.connection_count -= 1

        # Remove from document subscribers
        if doc_id and doc_id in self.document_subscribers:
            self.document_subscribers[doc_id].discard(websocket)

            # Clean up empty subscriber sets
            if not self.document_subscribers[doc_id]:
                del self.document_subscribers[doc_id]

        # Remove presence
        if doc_id and user_id and doc_id in self.user_presence:
            self.user_presence[doc_id].pop(user_id, None)

            # Broadcast user left
            await self.broadcast_update(websocket, doc_id, {
                "type": "presence_removed",
                "doc_id": doc_id,
                "user_id": user_id
            })

        logger.info(f"Cleaned up connection: {connection_id} (remaining: {self.connection_count})")

    def get_metrics(self) -> dict[str, Any]:
        """Get server performance metrics."""
        return {
            "connections": self.connection_count,
            "documents": len(self.documents),
            "total_messages": self.message_count,
            "avg_messages_per_connection": self.message_count / max(1, self.connection_count),
            "redis_connected": self.redis_client is not None
        }


# Client-side helper for testing
class YjsCollaborationClient:
    """Simple client for testing collaboration server."""

    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.doc_id = None
        self.user_id = str(uuid4())

    async def connect(self, doc_id: str):
        """Connect to collaboration server and subscribe to document."""
        if ws_connect is None:
            raise RuntimeError("websockets library not installed. Run: pip install websockets>=10")

        self.doc_id = doc_id
        self.websocket = await ws_connect(self.server_url)

        # Subscribe to document
        await self.send_message({
            "type": "subscribe",
            "doc_id": doc_id,
            "user_id": self.user_id
        })

        logger.info(f"Connected to {self.server_url} for document {doc_id}")

    async def send_message(self, message: dict[str, Any]):
        """Send message to server."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    async def send_document_update(self, operations: list[dict[str, Any]]):
        """Send document update operations."""
        await self.send_message({
            "type": "document_update",
            "doc_id": self.doc_id,
            "user_id": self.user_id,
            "operations": operations,
            "vector_clock": {self.user_id: int(time.time())}
        })

    async def send_presence_update(
        self,
        cursor_position: int | None = None,
        selection_start: int | None = None,
        selection_end: int | None = None
    ):
        """Send presence update."""
        await self.send_message({
            "type": "presence_update",
            "doc_id": self.doc_id,
            "user_id": self.user_id,
            "cursor_position": cursor_position,
            "selection_start": selection_start,
            "selection_end": selection_end,
            "username": f"User {self.user_id[:8]}"
        })

    async def listen_for_updates(self):
        """Listen for updates from server."""
        if not self.websocket:
            return

        async for message in self.websocket:
            data = json.loads(message)
            logger.info(f"Received: {data['type']}")

    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        """Run collaboration server."""
        server = YjsCollaborationServer()
        await server.start_server()

    asyncio.run(main())
