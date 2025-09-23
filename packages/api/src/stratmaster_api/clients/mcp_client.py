"""MCP client for communication with expertise-mcp server."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


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

        self.request_id += 1
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


# Global client instance for dependency injection
_mcp_client: MCPClient | None = None


async def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


async def close_mcp_client() -> None:
    """Close the global MCP client instance."""
    global _mcp_client
    if _mcp_client is not None:
        await _mcp_client.stop()
        _mcp_client = None