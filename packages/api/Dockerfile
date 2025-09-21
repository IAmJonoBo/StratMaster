# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY ./pyproject.toml /app/
RUN pip install --upgrade pip && pip install .

EXPOSE 8080
CMD ["uvicorn", "stratmaster_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
