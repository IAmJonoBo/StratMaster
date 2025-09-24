"""MCP server for expertise evaluation using stdio transport."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

# Note: Using a simplified MCP server implementation since the full MCP SDK may not be available
# This would normally import from mcp.server import Server

from .schemas import MEMO_SCHEMA
from .tools import evaluate as _eval, vote as _vote

logger = logging.getLogger(__name__)


class SimpleMCPServer:
    """Simplified MCP server implementation for expertise evaluation."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
    
    def tool(self, name: str, description: str, schema: dict[str, Any]):
        """Decorator to register a tool."""
        def decorator(func):
            self.tools[name] = {
                "function": func,
                "description": description,
                "schema": schema
            }
            return func
        return decorator
    
    def run_stdio(self):
        """Run the server using stdio transport."""
        logger.info(f"Starting {self.name} MCP server")
        
        # In a real implementation, this would handle the MCP protocol
        # For now, we'll create a simple JSON-RPC like interface
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = self._handle_request(request)
                
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                error_response = {
                    "error": {"code": -32000, "message": str(e)}
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
    
    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "tools/list":
            return {
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": name,
                            "description": info["description"],
                            "inputSchema": info["schema"]
                        }
                        for name, info in self.tools.items()
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return {
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                }
            
            try:
                result = self.tools[tool_name]["function"](**arguments)
                return {
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
                }
            except Exception as e:
                return {
                    "id": request_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        
        else:
            return {
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }


# Create the server instance
server = SimpleMCPServer(name="expertise-mcp")


@server.tool(
    name="expert.evaluate",
    description="Run discipline checks and produce memos",
    schema={
        "type": "object",
        "properties": {
            "strategy": {"type": "object"},
            "disciplines": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["strategy", "disciplines"]
    }
)
def evaluate(strategy: dict[str, Any], disciplines: list[str]) -> list[dict[str, Any]]:
    """Evaluate strategy across disciplines and return memos."""
    memos = _eval(strategy, disciplines)
    return [memo.model_dump() for memo in memos]


@server.tool(
    name="expert.vote", 
    description="Aggregate memos into a weighted council vote",
    schema={
        "type": "object",
        "properties": {
            "strategy_id": {"type": "string"},
            "weights": {"type": "object"},
            "memos": {"type": "array", "items": MEMO_SCHEMA}
        },
        "required": ["strategy_id", "weights", "memos"]
    }
)
def vote(strategy_id: str, weights: dict[str, float], memos: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate memos into weighted council vote."""
    # Convert dict memos back to DisciplineMemo objects for internal processing
    from packages.api.src.stratmaster_api.models.experts.memo import DisciplineMemo
    
    memo_objects = []
    for memo_data in memos:
        try:
            memo_obj = DisciplineMemo(**memo_data)
            memo_objects.append(memo_obj)
        except Exception as e:
            logger.warning(f"Failed to parse memo: {e}")
            continue
    
    council_vote = _vote(strategy_id, weights, memo_objects)
    return council_vote.model_dump()


def main():
    """Main entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)
    server.run_stdio()


if __name__ == "__main__":
    main()


__all__ = ["server", "main"]