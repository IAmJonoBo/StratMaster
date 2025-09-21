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

CMD ["/app/.venv/bin/uvicorn", "research_mcp.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8081"]
