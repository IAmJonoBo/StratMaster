"""Configuration loader for router MCP with per-tenant policies."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass
class ProviderConfig:
    name: str
    completion_model: str
    embedding_model: str
    rerank_model: str
    temperature: float
    base_url: str | None
    api_key: str | None


@dataclass
class TaskRoute:
    provider: str
    model: str


@dataclass
class TaskPolicy:
    name: str
    primary: TaskRoute
    fallbacks: list[TaskRoute] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderSettings:
    name: str
    enabled: bool = True
    default: bool = False
    models: list[str] = field(default_factory=list)
    limits: dict[str, Any] = field(default_factory=dict)
    privacy: dict[str, Any] = field(default_factory=dict)
    egress: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationSettings:
    reject_unknown_tasks: bool = False
    enforce_privacy_constraints: bool = False
    guardrails: dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantPolicy:
    tasks: dict[str, TaskPolicy] = field(default_factory=dict)
    providers: dict[str, ProviderSettings] = field(default_factory=dict)
    validation: ValidationSettings = field(default_factory=ValidationSettings)


@dataclass
class ModelsPolicy:
    tenants: dict[str, TenantPolicy] = field(default_factory=dict)
    structured_outputs: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    default_provider: ProviderConfig
    structured_decoding: dict[str, Any]
    policy: ModelsPolicy


def load_config() -> AppConfig:
    provider = ProviderConfig(
        name=_env("ROUTER_MCP_PROVIDER", "local"),
        completion_model=_env("ROUTER_MCP_COMPLETION_MODEL", "mixtral-8x7b"),
        embedding_model=_env("ROUTER_MCP_EMBEDDING_MODEL", "bge-small"),
        rerank_model=_env("ROUTER_MCP_RERANK_MODEL", "bge-reranker-large"),
        temperature=_float_env("ROUTER_MCP_TEMPERATURE", 0.2),
        base_url=os.getenv("ROUTER_MCP_PROVIDER_BASE_URL"),
        api_key=os.getenv("ROUTER_MCP_PROVIDER_API_KEY"),
    )
    structured = _load_structured_decoding()
    policy = _load_models_policy()
    return AppConfig(default_provider=provider, structured_decoding=structured, policy=policy)


def _load_structured_decoding() -> dict[str, Any]:
    cfg_path = (
        Path(__file__).resolve().parents[5]
        / "configs"
        / "router"
        / "structured_decoding.yaml"
    )
    if not cfg_path.is_file():
        return {}
    try:
        with cfg_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}


def _load_models_policy() -> ModelsPolicy:
    cfg_path = (
        Path(__file__).resolve().parents[5]
        / "configs"
        / "router"
        / "models-policy.yaml"
    )
    if not cfg_path.is_file():
        return ModelsPolicy()
    try:
        with cfg_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    except Exception:
        return ModelsPolicy()

    tenants_cfg = raw.get("tenants", {}) or {}
    tenants: dict[str, TenantPolicy] = {}
    for tenant_id, tenant_cfg in tenants_cfg.items():
        tasks_cfg = tenant_cfg.get("tasks", {}) or {}
        tasks: dict[str, TaskPolicy] = {}
        for task_name, task_cfg in tasks_cfg.items():
            primary_cfg = task_cfg.get("primary", {}) or {}
            if not primary_cfg:
                continue
            primary = TaskRoute(
                provider=str(primary_cfg.get("provider", "")),
                model=str(primary_cfg.get("model", "")),
            )
            fallbacks = [
                TaskRoute(provider=str(item.get("provider")), model=str(item.get("model")))
                for item in task_cfg.get("fallbacks", []) or []
                if item.get("provider") and item.get("model")
            ]
            parameters = task_cfg.get("parameters", {}) or {}
            tasks[task_name] = TaskPolicy(
                name=task_name,
                primary=primary,
                fallbacks=fallbacks,
                parameters=parameters,
            )

        providers_cfg = tenant_cfg.get("providers", {}) or {}
        providers: dict[str, ProviderSettings] = {}
        for provider_name, provider_cfg in providers_cfg.items():
            providers[provider_name] = ProviderSettings(
                name=provider_name,
                enabled=bool(provider_cfg.get("enabled", True)),
                default=bool(provider_cfg.get("default", False)),
                models=list(provider_cfg.get("models", []) or []),
                limits=provider_cfg.get("limits", {}) or {},
                privacy=provider_cfg.get("privacy", {}) or {},
                egress=provider_cfg.get("egress", {}) or {},
            )

        validation_cfg = tenant_cfg.get("validation", {}) or {}
        validation = ValidationSettings(
            reject_unknown_tasks=bool(validation_cfg.get("reject_unknown_tasks", False)),
            enforce_privacy_constraints=bool(
                validation_cfg.get("enforce_privacy_constraints", False)
            ),
            guardrails=validation_cfg.get("guardrails", {}) or {},
        )
        tenants[tenant_id] = TenantPolicy(tasks=tasks, providers=providers, validation=validation)

    structured_outputs = raw.get("structured_outputs", {}) or {}
    return ModelsPolicy(tenants=tenants, structured_outputs=structured_outputs)

