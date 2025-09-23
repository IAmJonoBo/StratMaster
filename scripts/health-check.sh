#!/usr/bin/env bash

# Health check script for Docker containers
# Returns 0 if healthy, 1 if unhealthy

set -euo pipefail

SERVICE_NAME="${1:-api}"
HEALTH_ENDPOINT="${2:-/healthz}"
PORT="${3:-8080}"

# Check if service is responding
if curl -f "http://localhost:${PORT}${HEALTH_ENDPOINT}" >/dev/null 2>&1; then
    echo "✅ ${SERVICE_NAME} is healthy"
    exit 0
else
    echo "❌ ${SERVICE_NAME} is unhealthy"
    exit 1
fi