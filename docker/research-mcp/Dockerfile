# Multi-stage build for Research MCP Server
FROM python:3.13-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt ./
COPY packages/mcp-servers/research-mcp/pyproject.toml packages/mcp-servers/research-mcp/

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r mcp && useradd -r -g mcp mcp

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONNOUSERSITE=1

# Set working directory
WORKDIR /app

# Copy application code
COPY packages/mcp-servers/research-mcp/ packages/mcp-servers/research-mcp/
COPY configs/ configs/

# Install the MCP server package
RUN pip install --no-cache-dir -e packages/mcp-servers/research-mcp

# Create non-root user
USER mcp

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/healthz || exit 1

# Run the MCP server
CMD ["python", "-m", "research_mcp.server"]