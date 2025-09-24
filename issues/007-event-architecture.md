# Issue 007: Event-Driven Microservices Architecture

## Summary
Adopt the event-driven architecture described in [Implementation Plan §Event-Driven Microservices Architecture](../IMPLEMENTATION_PLAN.md#event-driven-microservices-architecture) to meet scalability roadmap goals.

## Current State
- All services communicate synchronously; no Kafka/Redis Streams producers or consumers exist.【F:Upgrade.md†L413-L418】
- There is no outbox pattern or schema registry for domain events.

## Proposed Solution
1. Introduce outbox table and dispatcher to emit events via Redis Streams (initially) or Kafka.
2. Define event schemas and implement producers in API services after transactional commits.
3. Build consumer workers for analytics, notifications, and audit logging.

## Feature Flag
- `ENABLE_EVENT_STREAMING` (default `false`).

## Acceptance Criteria
- Event schemas published and validated; producers emit events for key domain changes when flag enabled.
- Consumers process events idempotently with monitoring for lag and failures.
- Documentation outlines event catalog and deployment steps.
- With flag disabled, system behaves as today with no side effects.

## Dependencies
- Message broker (Redis Streams or Kafka) and infrastructure support.
- Observability stack for lag and error metrics.

## Testing Plan
- Unit tests for schema validation and producer logic.
- Integration tests running docker-compose with broker, verifying end-to-end event flow.
- Contract tests for event payloads using jsonschema/protobuf tooling.

## Rollout & Monitoring
- Enable per-event-type, starting with low-risk events (export audit).
- Monitor consumer lag, error rates, and throughput; configure alerts.
