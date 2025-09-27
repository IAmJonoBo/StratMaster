"""Telemetry helpers for router MCP."""

from __future__ import annotations

import logging
import time
import os
from contextlib import contextmanager
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)


class MetricSink:
    """Flexible sink abstraction for routing metrics."""

    def __init__(self, emitters: Iterable[Callable[[dict[str, Any]], None]] | None = None) -> None:
        self.emitters = list(emitters or [])

    def add_emitter(self, emitter: Callable[[dict[str, Any]], None]) -> None:
        self.emitters.append(emitter)

    def emit(self, payload: dict[str, Any]) -> None:
        for emitter in self.emitters:
            try:
                emitter(payload)
            except Exception:  # pragma: no cover - defensive guard
                logger.exception("Routing telemetry emitter failed")


class RoutingTelemetry:
    """Collects cost/latency metrics for routing decisions."""

    def __init__(self, sink: MetricSink | None = None) -> None:
        self.sink = sink or MetricSink()

    @contextmanager
    def record_attempt(
        self,
        *,
        model: str,
        provider: str,
        tenant: str,
        task_type: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Context manager to time model invocation and emit structured metrics."""
        start = time.perf_counter()
        metrics: dict[str, Any] = {
            "model": model,
            "provider": provider,
            "tenant": tenant,
            "task_type": task_type,
        }
        if metadata:
            metrics.update(metadata)

        try:
            yield metrics
            metrics["status"] = "success"
        except Exception as exc:  # pragma: no cover - propagated after logging
            metrics["status"] = "error"
            metrics["error_type"] = exc.__class__.__name__
            metrics["error_message"] = str(exc)
            raise
        finally:
            metrics["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
            self.sink.emit(metrics)

    def add_emitter(self, emitter: Callable[[dict[str, Any]], None]) -> None:
        self.sink.add_emitter(emitter)


def console_emitter(payload: dict[str, Any]) -> None:
    """Default emitter writing metrics to logger."""
    logger.info(
        "routing.telemetry", extra={"payload": payload}
    )


default_telemetry = RoutingTelemetry(MetricSink([console_emitter]))


def build_telemetry_from_env() -> RoutingTelemetry:
    """Construct telemetry pipeline using available env configuration."""
    telemetry = RoutingTelemetry(MetricSink([console_emitter]))

    # Optional Langfuse integration
    public_key = os.getenv("ROUTER_MCP_LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("ROUTER_MCP_LANGFUSE_SECRET_KEY")
    host = os.getenv("ROUTER_MCP_LANGFUSE_HOST")

    if public_key and secret_key and host:
        try:  # pragma: no cover - optional dependency
            from langfuse import Langfuse

            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )

            def _langfuse_emitter(payload: dict[str, Any]) -> None:
                try:
                    client.event(
                        name="router.telemetry",
                        input=payload,
                        metadata={
                            "model": payload.get("model"),
                            "provider": payload.get("provider"),
                            "tenant": payload.get("tenant"),
                            "task_type": payload.get("task_type"),
                        },
                    )
                except Exception:  # pragma: no cover - defensive
                    logger.exception("Failed to emit Langfuse routing event")

            telemetry.add_emitter(_langfuse_emitter)
        except Exception:  # pragma: no cover
            logger.exception("Failed to initialise Langfuse telemetry")

    # Optional OTLP metrics via OpenTelemetry
    otlp_endpoint = os.getenv("ROUTER_MCP_OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:  # pragma: no cover - optional dependency
            from opentelemetry import metrics
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": "router-mcp"})
            reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=otlp_endpoint)
            )
            provider = MeterProvider(resource=resource, metric_readers=[reader])
            metrics.set_meter_provider(provider)
            meter = metrics.get_meter(__name__)
            latency_hist = meter.create_histogram(
                name="router_mcp_latency_ms",
                unit="ms",
                description="Latency of routed model calls",
            )
            cost_hist = meter.create_histogram(
                name="router_mcp_cost_usd",
                unit="usd",
                description="Dollar cost per routed call",
            )

            def _otel_emitter(payload: dict[str, Any]) -> None:
                attrs = {
                    "model": payload.get("model"),
                    "provider": payload.get("provider"),
                    "tenant": payload.get("tenant"),
                    "task_type": payload.get("task_type"),
                    "status": payload.get("status"),
                }
                latency = payload.get("latency_ms")
                if latency is not None:
                    latency_hist.record(float(latency), attributes=attrs)
                cost = payload.get("cost_usd")
                if cost:
                    cost_hist.record(float(cost), attributes=attrs)

            telemetry.add_emitter(_otel_emitter)
        except Exception:  # pragma: no cover
            logger.exception("Failed to initialise OTLP metrics exporter")

    return telemetry
