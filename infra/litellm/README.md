# LiteLLM Router Shim

LiteLLM acts as the policy-enforcing facade between StratMaster services and
upstream LLM providers. This guide covers endpoint exposure, authentication, per-
tenant policies, and observability hooks.

## Deployment

- Service runs as a FastAPI app deployed via the `helm/litellm-router` chart.
- Default port: `8086`. Health endpoint: `/healthz`.
- Configure upstream providers through `configs/router/models-policy.yaml`.

## Endpoint exposure

| Endpoint               | Method | Description                         |
| ---------------------- | ------ | ----------------------------------- |
| `/v1/chat/completions` | POST   | OpenAI-compatible chat completions. |
| `/v1/completions`      | POST   | Legacy completion API.              |
| `/v1/embeddings`       | POST   | Embedding proxy (if enabled).       |
| `/v1/models`           | GET    | Lists allowed models per tenant.    |
| `/internal/metrics`    | GET    | Prometheus metrics.                 |

- Expose endpoints via the API gateway/ingress with mTLS enforced between the
  router and upstream providers when supported.
- For internal calls, services use service accounts with signed JWT assertions.

## Authentication & policy mapping

- Requests must include `X-Tenant-ID` header; router loads tenant config from
  `configs/router/models-policy.yaml`.
- API keys map 1:1 with tenants and are stored in Vault (synchronised via
  ExternalSecrets).
- Example policy snippet:
  ```yaml
  tenants:
    acme:
      providers:
        openai:
          enabled: true
          models:
            reasoning:
              default: gpt-4.1
              fallbacks: [gpt-4o-mini]
            summarisation:
              default: gpt-4o-mini
            embedding:
              default: text-embedding-3-large
          privacy:
            send_raw_docs: false
  ```
- The router enforces token-per-minute and budget caps defined in the policy. Exceeding
  limits returns HTTP 429 with contextual error JSON.

## Observability

- Enable LiteLLM tracing by setting `LITELLM_TRACE=true`; traces exported via OTLP
  to the observability stack.
- Metrics:
  - `litellm_requests_total{tenant,provider,model}`
  - `litellm_request_duration_seconds_bucket`
  - `litellm_throttled_total`
- Alert when throttled requests exceed 5% or when upstream latency > 2s P95.

## Failure handling

- Router wraps provider exceptions and returns structured errors with `code` and
  `retryable` flags.
- Automatic retries configurable per provider (default: 1 retry on 429/5xx with
  exponential backoff).
- If all providers for a task are unavailable, router surfaces `503` and instructs
  clients to fall back to cached recommendations.

## Local development

- `docker-compose.yml` runs LiteLLM with demo configuration (`default` tenant
  hitting mocked upstream providers).
- Use `scripts/mock_openai.py` to emulate OpenAI responses when offline.
- Run `pytest packages/router/tests/test_policy.py` to ensure config parsing
  matches the schema.

## Security

- Require TLS for all external traffic; certificates managed by ingress + cert-manager.
- Audit request logs for personally identifiable information and redact prompt
  snippets using the router's middleware.
- Rotate API keys quarterly; store hashed versions in the database when using
  self-service key management.
