# syntax=docker/dockerfile:1.19
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY ./pyproject.toml /app/
RUN pip install --upgrade pip && pip install .

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys,urllib.request;\n\
u=urllib.request.urlopen('http://127.0.0.1:8080/healthz');\n\
sys.exit(0 if u.getcode()==200 else 1)" || exit 1

# Create non-root user
RUN useradd -m -u 10001 appuser
USER appuser
CMD ["uvicorn", "stratmaster_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
