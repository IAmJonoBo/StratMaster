# Multi-stage build for Evals MCP Server
FROM python:3.13-slim as builder

RUN apt-get update && apt-get install -y build-essential curl git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
COPY packages/mcp-servers/evals-mcp/pyproject.toml packages/mcp-servers/evals-mcp/
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.13-slim
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && \
    groupadd -r mcp && useradd -r -g mcp mcp

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH PYTHONPATH=/app PYTHONNOUSERSITE=1

WORKDIR /app
COPY packages/mcp-servers/evals-mcp/ packages/mcp-servers/evals-mcp/
COPY configs/ configs/
RUN pip install --no-cache-dir -e packages/mcp-servers/evals-mcp

USER mcp
EXPOSE 8084

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8084/healthz || exit 1

CMD ["python", "-m", "evals_mcp.server"]