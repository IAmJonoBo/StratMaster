"""
Sprint 0 - Tracing and observability utilities.

This module provides OTEL and Langfuse integration for the StratMaster API,
implementing the Sprint 0 requirement for visible traces.
"""

import logging
import os
import re
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any
from contextvars import ContextVar

# Module-level logger for optional diagnostics
logger = logging.getLogger(__name__)

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

# Optional OTLP tracing configuration pieces
try:  # pragma: no cover - optional instrumentation bits
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    OTEL_SDK_AVAILABLE = True
except Exception:  # noqa: BLE001 - keep optional
    OTEL_SDK_AVAILABLE = False
    OTLPSpanExporter = None  # type: ignore

# Optional Langfuse client - fallback gracefully if not available
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


try:  # pragma: no cover - optional dependency
    from .security.privacy_controls import DataSource
except Exception:  # noqa: BLE001 - privacy controls optional in some environments
    class DataSource:  # type: ignore[override]
        API_RESPONSES = "api_responses"


class TracingManager:
    """Central tracing manager for OTEL and Langfuse integration."""

    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.langfuse_client = self._init_langfuse() if LANGFUSE_AVAILABLE else None
        self._metadata_filter: Callable[[dict[str, Any]], dict[str, Any]] | None = None
        self._privacy_manager: Any | None = None
        self._privacy_default_workspace: str = "system"
        self._privacy_context: ContextVar[str | None] = ContextVar(
            "stratmaster_privacy_workspace", default=None
        )

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

    def set_metadata_filter(
        self,
        filter_fn: Callable[[dict[str, Any]], dict[str, Any]] | None,
    ) -> None:
        """Register a callable to scrub tracing metadata before export."""
        self._metadata_filter = filter_fn

    def _apply_metadata_filter(self, metadata: dict[str, Any]) -> dict[str, Any]:
        if not metadata or not self._metadata_filter:
            return metadata
        try:
            return self._metadata_filter(metadata)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Tracing metadata filter raised an exception")
            return metadata

    @contextmanager
    def trace_operation(self, operation_name: str, metadata: dict[str, Any] | None = None):
        """Create both OTEL and Langfuse spans for an operation."""
        metadata = metadata or {}
        metadata = self._apply_metadata_filter(metadata)
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


    # ------------------------------------------------------------------
    # Privacy-aware metadata helpers
    # ------------------------------------------------------------------
    def enable_privacy_sanitiser(
        self,
        privacy_manager: Any,
        default_workspace: str = "system",
    ) -> None:
        """Enable privacy-aware metadata filtering using the supplied manager."""

        self._privacy_manager = privacy_manager
        self._privacy_default_workspace = default_workspace

        if privacy_manager is None:
            self.set_metadata_filter(self._basic_metadata_scrub)
            return

        def _filter(payload: dict[str, Any]) -> dict[str, Any]:
            return self._sanitize_metadata(payload)

        self.set_metadata_filter(_filter)

    def push_privacy_context(self, workspace_id: str | None):
        """Bind workspace context for subsequent metadata sanitisation."""
        return self._privacy_context.set(workspace_id)

    def reset_privacy_context(self, token) -> None:
        """Reset workspace context token returned by push_privacy_context."""
        if token is not None:
            try:
                self._privacy_context.reset(token)
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to reset privacy context")

    # Internal ---------------------------------------------------------
    def _sanitize_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._privacy_manager:
            return self._basic_metadata_scrub(payload)

        workspace_id = self._privacy_context.get()
        workspace = workspace_id or self._privacy_default_workspace

        def _scrub(value: Any) -> Any:
            if isinstance(value, str):
                try:
                    result = self._privacy_manager.process_text_for_privacy(
                        workspace_id=workspace,
                        text=value,
                        data_source=DataSource.API_RESPONSES,
                        language="en",
                    )
                    return result.get("processed_text", value)
                except Exception:
                    logger.exception("Failed to sanitize tracing metadata value")
                    return value
            if isinstance(value, dict):
                return {k: _scrub(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_scrub(item) for item in value]
            return value

        sanitized = {}
        for key, value in payload.items():
            sanitized[key] = _scrub(value)

        return sanitized

    # ------------------------------------------------------------------
    # Basic scrubbing fallback (used when Presidio not available)
    # ------------------------------------------------------------------
    def _basic_metadata_scrub(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply lightweight regex-based scrubbing for common PII."""

        email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        phone_re = re.compile(r"(?:(?:\+?\d{1,3})?[-. (]*\d{3}[-. )]*\d{3}[-. ]*\d{4})")
        cc_re = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

        def _scrub(value: Any) -> Any:
            if isinstance(value, str):
                scrubbed = email_re.sub("[REDACTED_EMAIL]", value)
                scrubbed = phone_re.sub("[REDACTED_PHONE]", scrubbed)
                scrubbed = cc_re.sub("[REDACTED_CARD]", scrubbed)
                return scrubbed
            if isinstance(value, dict):
                return {k: _scrub(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_scrub(item) for item in value]
            return value

        return {key: _scrub(val) for key, val in (payload or {}).items()}


def configure_tracing(
    service_name: str,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
    sample_ratio: float = 1.0,
) -> bool:
    """Configure the global tracer provider with OTLP export if available."""
    if not (OTEL_AVAILABLE and OTEL_SDK_AVAILABLE):
        return False

    try:
        resource = Resource.create({SERVICE_NAME: service_name})
        sampler = TraceIdRatioBased(min(max(sample_ratio, 0.0), 1.0))
        provider = TracerProvider(resource=resource, sampler=sampler)

        if endpoint:
            exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers or {})
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        return True
    except Exception:  # pragma: no cover - configuration is best effort
        logger.exception("Failed to configure OpenTelemetry tracing")
        return False


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
