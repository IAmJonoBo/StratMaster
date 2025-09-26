"""
Sprint 0 - Tracing and observability utilities.

This module provides OTEL and Langfuse integration for the StratMaster API,
implementing the Sprint 0 requirement for visible traces.
"""

import os
import uuid
from contextlib import contextmanager
from typing import Any

# OTEL may be optional at runtime in some environments (e.g., minimal test envs)
try:  # pragma: no cover - import guard
    from opentelemetry import trace  # type: ignore
    OTEL_AVAILABLE = True
except Exception:  # noqa: BLE001 - broad to ensure safe fallback
    OTEL_AVAILABLE = False

    # Lightweight no-op tracer/shim that matches the minimal API surface we use
    class _NoopSpan:
        def set_attribute(self, *args, **kwargs):  # noqa: D401 - simple no-op
            """No-op set_attribute"""
            return None

    class _NoopSpanContext:
        def __enter__(self):
            return _NoopSpan()

        def __exit__(self, exc_type, exc, tb):
            return False

    class _NoopTracer:
        def start_as_current_span(self, _name: str):
            return _NoopSpanContext()

    class _NoopTraceModule:
        def get_tracer(self, _name: str):
            return _NoopTracer()

        def get_current_span(self):
            return _NoopSpan()

    # Expose a shim with the same symbol name used by the app
    trace = _NoopTraceModule()  # type: ignore

# Optional Langfuse client - fallback gracefully if not available
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class TracingManager:
    """Central tracing manager for OTEL and Langfuse integration."""

    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.langfuse_client = self._init_langfuse() if LANGFUSE_AVAILABLE else None

    def _init_langfuse(self) -> Any | None:
        """Initialize Langfuse client if configured."""
        if not LANGFUSE_AVAILABLE:
            return None

        # Check for Langfuse configuration
        server_url = os.getenv("LANGFUSE_SERVER_URL")
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")

        if server_url and public_key and secret_key:
            try:
                return Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=server_url
                )
            except Exception:
                # Gracefully handle Langfuse initialization failures
                return None
        return None

    @contextmanager
    def trace_operation(self, operation_name: str, metadata: dict[str, Any] | None = None):
        """Create both OTEL and Langfuse spans for an operation."""
        metadata = metadata or {}
        trace_id = str(uuid.uuid4())

        # Start OTEL span
        with self.tracer.start_as_current_span(operation_name) as otel_span:
            otel_span.set_attribute("trace_id", trace_id)
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    otel_span.set_attribute(key, value)

            # Start Langfuse trace if available
            langfuse_trace = None
            if self.langfuse_client:
                try:
                    langfuse_trace = self.langfuse_client.trace(
                        name=operation_name,
                        metadata=metadata,
                        id=trace_id
                    )
                except Exception:
                    # Gracefully handle Langfuse errors
                    pass

            try:
                yield {
                    "trace_id": trace_id,
                    "otel_span": otel_span,
                    "langfuse_trace": langfuse_trace
                }
            finally:
                if langfuse_trace:
                    try:
                        langfuse_trace.update(end_time=None)
                    except Exception:
                        pass

    def create_span(self, name: str, trace_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a named span within an existing trace context."""
        trace_context = trace_context or {}
        span_id = str(uuid.uuid4())

        # Create OTEL span
        with self.tracer.start_as_current_span(name) as otel_span:
            otel_span.set_attribute("span_id", span_id)

            # Create Langfuse span if available
            langfuse_span = None
            if self.langfuse_client and trace_context.get("langfuse_trace"):
                try:
                    langfuse_span = trace_context["langfuse_trace"].span(
                        name=name,
                        id=span_id
                    )
                except Exception:
                    pass

            return {
                "span_id": span_id,
                "otel_span": otel_span,
                "langfuse_span": langfuse_span
            }

    def log_agent_call(
        self, agent_name: str, input_data: dict[str, Any],
        trace_context: dict[str, Any] | None = None
    ):
        """Log an agent call with the standardized span name from Sprint 0."""
        with self.trace_operation(
            f"agent:call:{agent_name}", {"agent": agent_name, **input_data}
        ) as context:
            return context

    def log_debate_start(
        self, debate_id: str, participants: list,
        trace_context: dict[str, Any] | None = None
    ):
        """Log debate start with the standardized span name from Sprint 0."""
        with self.trace_operation("debate:start", {
            "debate_id": debate_id,
            "participants": participants
        }) as context:
            return context

    def log_retrieval_hybrid(
        self, query: str, sources: list, trace_context: dict[str, Any] | None = None
    ):
        """Log hybrid retrieval with the standardized span name from Sprint 0."""
        with self.trace_operation("retrieval:hybrid", {
            "query": query,
            "source_count": len(sources)
        }) as context:
            return context

    def log_guard_evidence(
        self, evidence_id: str, result: str,
        trace_context: dict[str, Any] | None = None
    ):
        """Log evidence guard check with the standardized span name from Sprint 0."""
        with self.trace_operation("guard:evidence", {
            "evidence_id": evidence_id,
            "result": result
        }) as context:
            return context


# Global tracing manager instance
tracing_manager = TracingManager()


# Convenience functions for common tracing operations
def trace_agent_call(agent_name: str, input_data: dict[str, Any]):
    """Convenience function for tracing agent calls."""
    return tracing_manager.log_agent_call(agent_name, input_data)


def trace_debate_start(debate_id: str, participants: list):
    """Convenience function for tracing debate start."""
    return tracing_manager.log_debate_start(debate_id, participants)


def trace_retrieval_hybrid(query: str, sources: list):
    """Convenience function for tracing hybrid retrieval."""
    return tracing_manager.log_retrieval_hybrid(query, sources)


def trace_guard_evidence(evidence_id: str, result: str):
    """Convenience function for tracing evidence guards."""
    return tracing_manager.log_guard_evidence(evidence_id, result)
