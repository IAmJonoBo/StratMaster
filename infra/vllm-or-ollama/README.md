# vLLM / Ollama Serving

This document describes the supported model catalog, resource expectations, and
fallback rules for running local LLM inference via vLLM or Ollama.

## Supported models

| Model name              | Provider | Context window | Recommended hardware  |
| ----------------------- | -------- | -------------- | --------------------- |
| `mixtral-8x7b-instruct` | vLLM     | 32k tokens     | 2×A100 40GB or 4×L40S |
| `qwen2.5-14b-instruct`  | vLLM     | 16k tokens     | 1×A100 80GB or 2×A40  |
| `mistral-nemo`          | vLLM     | 8k tokens      | 1×A100 40GB           |
| `llama3.1-8b-instruct`  | Ollama   | 8k tokens      | CPU ok, GPU optional  |
| `phi3-mini-4k`          | Ollama   | 4k tokens      | CPU ok                |

- vLLM runs behind `uvicorn` with tensor parallelism disabled by default (single
  GPU). Adjust via `--tensor-parallel-size` in `docker-compose.yml` when multiple
  GPUs are present.
- Ollama targets developer laptops; `docker-compose.dev.yml` exposes port 11434.

## Resource profiles

| Target     | CPU      | Memory | GPU                     | Notes                                           |
| ---------- | -------- | ------ | ----------------------- | ----------------------------------------------- |
| Dev (CPU)  | 8 cores  | 32 GB  | None                    | Ollama only.                                    |
| Dev (GPU)  | 16 cores | 64 GB  | 1×RTX 4090 / 24 GB VRAM | vLLM with `qwen2.5`.                            |
| Staging    | 32 cores | 128 GB | 2×L40S (48 GB)          | Mixtral for evaluation flows.                   |
| Production | 64 cores | 256 GB | 2×A100 80 GB            | Supports structured generation with guardrails. |

## Routing & fallback

- Router MCP consults `configs/router/models-policy.yaml` to map tasks to models.
- Default routing:
  - **Reasoning** → `mixtral-8x7b-instruct` (fallback to `llama3.1-8b-instruct`).
  - **Summarisation** → `qwen2.5-14b-instruct` (fallback to `phi3-mini-4k`).
  - **Embedding** requests bypass vLLM and use the embeddings MCP.
- Health checks hit `GET /healthz` on each runtime. If unhealthy for >5 minutes,
  the router demotes the model and switches to the fallback entry.

## Deployment

- Compose profile `vllm` builds `infra/vllm-or-ollama/docker-compose.vllm.yml` to
  start GPU-backed containers.
- Helm chart `helm/vllm-runtime` exposes config flags for model path, tensor
  parallelism, max batch size, and prompt caching.
- GPU scheduling uses Kubernetes `nvidia.com/gpu` resource requests; add tolerations
  for GPU nodes.

## Guided decoding

- Structured outputs rely on JSON schema or Outlines grammar; set
  `--guided-decoding json` in vLLM to enforce.
- Temperature defaults to 0.7; for safety-critical flows set to ≤0.3.
- Timeouts: 30s for interactive queries, 120s for long-form reports.

## Observability & maintenance

- Export Prometheus metrics using vLLM's `/metrics` endpoint; scrape via the
  `observability` Helm release.
- Enable tracing with OpenTelemetry by setting `LLM_TRACE_EXPORTER=otlp`.
- Nightly job warms prompt caches with high-traffic templates to reduce cold-start
  latency.
- Roll models forward using blue/green strategy: deploy new runtime with `-canary`
  suffix, run smoke tests, then update router policy once validated.

## Security

- Restrict Ollama to loopback interfaces in dev; never expose publicly.
- For cloud GPUs, attach IAM roles with least privilege for pulling models from
  object storage.
- Clear shared prompt caches during tenant teardown to avoid cross-tenant leakage.
