"""Schemas for evals MCP."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class EvalRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    suite: Literal["rag", "truthfulqa", "factscore", "custom"]
    thresholds: dict[str, float] | None = None


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    passed: bool
    metrics: dict[str, float]


class InfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    suites: list[str]
