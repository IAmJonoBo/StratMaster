FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONNOUSERSITE=1

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src

RUN python -m venv .venv \
    && . .venv/bin/activate \
    && pip install --no-cache-dir -e . \
    && pip install --no-cache-dir uvicorn[standard]

EXPOSE 8081

# Add a simple HTTP health probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys,urllib.request;\n\
import json;\n\
u=urllib.request.urlopen('http://127.0.0.1:8081/healthz');\n\
sys.exit(0 if u.getcode()==200 else 1)" || exit 1

# Create non-root user and drop privileges
RUN useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["/app/.venv/bin/uvicorn", "research_mcp.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8081"]
