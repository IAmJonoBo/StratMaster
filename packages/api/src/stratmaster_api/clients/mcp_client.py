"""MCP client for communication with expertise-mcp server."""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import subprocess
import sys
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MCPConnectionPool:
    """Connection pool for MCP clients to improve performance."""
    
    def __init__(self, server_path: str | Path, pool_size: int = 3):
        self.server_path = Path(server_path)
        self.pool_size = pool_size
        self.available_clients: queue.Queue = queue.Queue()
        self.all_clients: list[MCPClient] = []
        self.lock = threading.Lock()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self.initialized:
            return
            
        with self.lock:
            if self.initialized:
                return
                
            for _ in range(self.pool_size):
                client = MCPClient(self.server_path)
                await client.start()
                self.all_clients.append(client)
                self.available_clients.put(client)
            
            self.initialized = True
            logger.info(f"Initialized MCP connection pool with {self.pool_size} clients")
    
    async def get_client(self) -> MCPClient:
        """Get a client from the pool."""
        if not self.initialized:
            await self.initialize()
        
        # Try to get an available client with timeout
        try:
            client = self.available_clients.get(timeout=5.0)
            return client
        except queue.Empty:
            # If no clients available, create a temporary one
            logger.warning("No available MCP clients in pool, creating temporary client")
            temp_client = MCPClient(self.server_path)
            await temp_client.start()
            return temp_client
    
    def return_client(self, client: MCPClient):
        """Return a client to the pool."""
        if client in self.all_clients:
            self.available_clients.put(client)
        else:
            # This is a temporary client, clean it up
            asyncio.create_task(client.stop())
    
    async def close(self):
        """Close all clients in the pool."""
        with self.lock:
            for client in self.all_clients:
                await client.stop()
            self.all_clients.clear()
            
            # Clear any remaining clients in queue
            while not self.available_clients.empty():
                try:
                    self.available_clients.get_nowait()
                except queue.Empty:
                    break
            
            self.initialized = False
            logger.info("Closed MCP connection pool")


class MCPClient:
    """MCP client for stdio communication with expertise-mcp server."""

    def __init__(self, server_path: str | Path | None = None):
        """Initialize MCP client.
        
        Args:
            server_path: Path to the MCP server executable or main.py
        """
        if server_path is None:
            # Default to expertise-mcp server in the monorepo
            base_path = Path(__file__).parent.parent.parent.parent.parent
            server_path = base_path / "mcp-servers" / "expertise-mcp" / "main.py"
        
        self.server_path = Path(server_path)
        self.process: subprocess.Popen | None = None
        self.request_id = 0
        self.last_used = time.time()

    async def start(self) -> None:
        """Start the MCP server process."""
        if self.process is not None:
            logger.warning("MCP server process already running")
            return

        try:
            # Start the expertise-mcp server as subprocess
            self.process = subprocess.Popen(
                [sys.executable, str(self.server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered for real-time communication
            )
            self.last_used = time.time()
            logger.info(f"Started MCP server process: {self.process.pid}")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self.process is None:
            return

        try:
            self.process.terminate()
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("MCP server did not terminate gracefully, killing")
                self.process.kill()
                self.process.wait()
        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")
        finally:
            self.process = None
            logger.info("MCP server process stopped")

    def is_healthy(self) -> bool:
        """Check if the client process is healthy."""
        if self.process is None:
            return False
        
        # Check if process is still running
        if self.process.poll() is not None:
            return False
        
        # Check if client hasn't been used for too long (10 minutes)
        if time.time() - self.last_used > 600:
            return False
        
        return True

    async def call(self, method: str, params: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.
        
        Args:
            method: The tool name (e.g., "expert.evaluate")
            params: Parameters to pass to the tool
            
        Returns:
            The result from the MCP server
        """
        if self.process is None:
            await self.start()

        if self.process is None:
            raise RuntimeError("Failed to start MCP server process")

        # Check if process is still healthy
        if not self.is_healthy():
            logger.warning("MCP client unhealthy, restarting")
            await self.stop()
            await self.start()

        self.request_id += 1
        self.last_used = time.time()
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": params
            }
        }

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            logger.debug(f"Sending MCP request: {request_json.strip()}")
            
            if self.process.stdin is None:
                raise RuntimeError("Process stdin is None")
            
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response
            if self.process.stdout is None:
                raise RuntimeError("Process stdout is None")
                
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("No response from MCP server")

            logger.debug(f"Received MCP response: {response_line.strip()}")
            response = json.loads(response_line.strip())

            # Check for errors
            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"MCP server error: {error.get('message', 'Unknown error')}")

            # Return the result
            result = response.get("result")
            if result is None:
                raise RuntimeError("No result in MCP response")

            return result.get("content", [{}])[0].get("text", {})

        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            # Try to restart the server on failure
            await self.stop()
            raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[MCPClient]:
        """Context manager for MCP client session."""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()


# Global connection pool instance
_connection_pool: MCPConnectionPool | None = None


async def get_mcp_client() -> MCPClient:
    """Get an MCP client from the connection pool."""
    global _connection_pool
    if _connection_pool is None:
        # Default to expertise-mcp server in the monorepo
        base_path = Path(__file__).parent.parent.parent.parent.parent
        server_path = base_path / "mcp-servers" / "expertise-mcp" / "main.py"
        _connection_pool = MCPConnectionPool(server_path, pool_size=3)
    
    return await _connection_pool.get_client()


def return_mcp_client(client: MCPClient):
    """Return an MCP client to the connection pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.return_client(client)


async def close_mcp_clients():
    """Close the MCP connection pool."""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None