# Multi-stage build for StratMaster API
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
COPY requirements.txt requirements-dev.txt ./
COPY packages/api/pyproject.toml packages/api/

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r stratmaster && useradd -r -g stratmaster stratmaster

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONNOUSERSITE=1

# Set working directory
WORKDIR /app

# Copy application code
COPY packages/api/ packages/api/
COPY configs/ configs/

# Install the API package
RUN pip install --no-cache-dir -e packages/api

# Create non-root user
USER stratmaster

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Run the application
CMD ["uvicorn", "stratmaster_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]