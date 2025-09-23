"""
Sprint 0 - MCP Server Tracing utilities.

Lightweight tracing for MCP servers to support Sprint 0 observability requirements.
"""

import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import trace


class MCPTracingManager:
    """Lightweight tracing manager for MCP servers."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(f"mcp-{service_name}")
    
    @contextmanager
    def trace_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Create an OTEL span for an MCP operation."""
        metadata = metadata or {}
        trace_id = str(uuid.uuid4())
        
        # Start OTEL span with MCP-specific naming
        span_name = f"mcp:{self.service_name}:{operation_name}"
        with self.tracer.start_as_current_span(span_name) as otel_span:
            otel_span.set_attribute("mcp.service", self.service_name)
            otel_span.set_attribute("mcp.operation", operation_name)
            otel_span.set_attribute("trace_id", trace_id)
            
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    otel_span.set_attribute(f"mcp.{key}", value)
            
            yield {
                "trace_id": trace_id,
                "otel_span": otel_span,
                "service": self.service_name
            }
    
    def trace_tool_call(self, tool_name: str, input_data: Dict[str, Any]):
        """Trace an MCP tool call."""
        return self.trace_operation(f"tool:{tool_name}", {
            "tool": tool_name,
            **{k: v for k, v in input_data.items() if isinstance(v, (str, int, float, bool))}
        })
    
    def trace_resource_access(self, resource_uri: str, operation: str = "read"):
        """Trace MCP resource access."""
        return self.trace_operation(f"resource:{operation}", {
            "resource_uri": resource_uri,
            "operation": operation
        })