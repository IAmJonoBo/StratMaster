FROM python:3.13-slim

LABEL org.opencontainers.image.title="StratMaster Expertise MCP Server"
LABEL org.opencontainers.image.description="MCP server for expert discipline evaluation"
LABEL org.opencontainers.image.vendor="StratMaster"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY main.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose health check port (if needed for monitoring)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Default command runs the MCP server on stdio
CMD ["python", "main.py"]