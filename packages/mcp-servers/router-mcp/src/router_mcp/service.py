"""Service layer for router MCP with policy enforcement."""

from __future__ import annotations

import json
import os
from typing import Any, Iterable

from fastapi import HTTPException

from .config import AppConfig, ProviderConfig, TaskPolicy, TaskRoute, TenantPolicy
from .models import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingVector,
    RerankRequest,
    RerankResponse,
    RerankResult,
)
from .providers import ProviderAdapter


class RouterService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.policy = config.policy
        self.decoding_cfg = config.structured_decoding
        self._provider_cache: dict[tuple[str, str, str, str], ProviderAdapter] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def complete(self, payload: CompletionRequest) -> CompletionResponse:
        tenant_policy, task_policy, route = self._select_route(
            payload.tenant_id,
            payload.task,
            default_model=self.config.default_provider.completion_model,
        )
        self._validate_completion(tenant_policy, task_policy, payload)
        adapter = self._adapter_for(
            route.provider,
            completion_model=route.model,
        )
        result = adapter.complete(
            payload.prompt,
            payload.max_tokens,
            model=route.model,
            temperature=payload.temperature,
        )
        text = self._ensure_structured(result["text"])
        return CompletionResponse(
            text=text,
            tokens=int(result["tokens"]),
            provider=result.get("provider", route.provider),
            model=result.get("model", route.model),
        )

    def embed(self, payload: EmbeddingRequest) -> EmbeddingResponse:
        tenant_policy, task_policy, route = self._select_route(
            payload.tenant_id,
            payload.task,
            default_model=payload.model or self.config.default_provider.embedding_model,
        )
        self._validate_embedding(tenant_policy, task_policy, payload)
        model_name = (
            payload.model or route.model or self.config.default_provider.embedding_model
        )
        adapter = self._adapter_for(route.provider, embedding_model=model_name)
        result = adapter.embed(payload.input, model=model_name)
        vectors = [
            EmbeddingVector(index=idx, vector=vec)
            for idx, vec in enumerate(result["embeddings"])
        ]
        return EmbeddingResponse(
            embeddings=vectors,
            provider=result.get("provider", route.provider),
            model=result.get("model", model_name),
        )

    def rerank(self, payload: RerankRequest) -> RerankResponse:
        tenant_policy, task_policy, route = self._select_route(
            payload.tenant_id,
            payload.task,
            default_model=self.config.default_provider.rerank_model,
        )
        self._validate_rerank(task_policy, payload)
        docs = [{"id": item.id, "text": item.text} for item in payload.documents]
        adapter = self._adapter_for(route.provider, rerank_model=route.model)
        result = adapter.rerank(payload.query, docs, payload.top_k, model=route.model)
        ranked = [
            RerankResult(id=item["id"], score=float(item["score"]), text=item["text"])
            for item in result["results"]
        ]
        return RerankResponse(
            results=ranked[: payload.top_k],
            provider=result.get("provider", route.provider),
            model=result.get("model", route.model),
        )

    # ------------------------------------------------------------------
    # Policy helpers
    # ------------------------------------------------------------------
    def _tenant_policy(self, tenant_id: str) -> TenantPolicy:
        if tenant_id in self.policy.tenants:
            return self.policy.tenants[tenant_id]
        if "default" in self.policy.tenants:
            return self.policy.tenants["default"]
        return TenantPolicy()

    def _select_route(
        self, tenant_id: str, task: str, default_model: str
    ) -> tuple[TenantPolicy, TaskPolicy, TaskRoute]:
        tenant_policy = self._tenant_policy(tenant_id)
        task_policy = tenant_policy.tasks.get(task)
        if task_policy is None:
            if tenant_policy.validation.reject_unknown_tasks:
                raise HTTPException(
                    status_code=400, detail=f"Task '{task}' is not allowed"
                )
            task_policy = TaskPolicy(
                name=task,
                primary=TaskRoute(
                    provider=self.config.default_provider.name,
                    model=default_model,
                ),
            )
        for candidate in [task_policy.primary, *task_policy.fallbacks]:
            if self._provider_enabled(tenant_policy, candidate.provider):
                return tenant_policy, task_policy, candidate
        raise HTTPException(
            status_code=503,
            detail=f"No providers available for task '{task}'",
        )

    def _provider_enabled(
        self, tenant_policy: TenantPolicy, provider_name: str
    ) -> bool:
        settings = tenant_policy.providers.get(provider_name)
        if settings is None:
            return provider_name == self.config.default_provider.name
        return settings.enabled

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _validate_completion(
        self,
        tenant_policy: TenantPolicy,
        task_policy: TaskPolicy,
        payload: CompletionRequest,
    ) -> None:
        params = task_policy.parameters
        guardrails = tenant_policy.validation.guardrails
        max_tokens = self._int_param(params.get("max_output_tokens"))
        if max_tokens is not None and payload.max_tokens > max_tokens:
            raise HTTPException(
                status_code=400, detail="max_tokens exceeds policy limit"
            )
        param_temp = self._float_param(params.get("temperature_max"))
        if param_temp is not None and payload.temperature > param_temp:
            raise HTTPException(
                status_code=400, detail="temperature exceeds task policy"
            )
        global_temp = self._float_param(guardrails.get("temperature_max_global"))
        if global_temp is not None and payload.temperature > global_temp:
            raise HTTPException(
                status_code=400, detail="temperature exceeds global guardrail"
            )
        max_context = self._int_param(guardrails.get("max_context_tokens"))
        if max_context is not None and payload.max_tokens > max_context:
            raise HTTPException(
                status_code=400, detail="context length exceeds guardrail"
            )

    def _validate_embedding(
        self,
        tenant_policy: TenantPolicy,
        task_policy: TaskPolicy,
        payload: EmbeddingRequest,
    ) -> None:
        params = task_policy.parameters
        max_batch = self._int_param(params.get("max_batch"))
        if max_batch is not None and len(payload.input) > max_batch:
            raise HTTPException(
                status_code=400, detail="embedding batch exceeds policy"
            )
        allow_raw = params.get("allow_raw_documents", True)
        if allow_raw is False:
            for item in payload.input:
                if len(item) > 512:
                    raise HTTPException(
                        status_code=400,
                        detail="raw documents not permitted for embedding",
                    )

    def _validate_rerank(self, task_policy: TaskPolicy, payload: RerankRequest) -> None:
        params = task_policy.parameters
        max_candidates = self._int_param(params.get("max_candidates"))
        if max_candidates is not None and payload.top_k > max_candidates:
            raise HTTPException(status_code=400, detail="top_k exceeds rerank policy")

    @staticmethod
    def _int_param(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float_param(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Provider helpers
    # ------------------------------------------------------------------
    def _adapter_for(
        self,
        provider_name: str,
        completion_model: str | None = None,
        embedding_model: str | None = None,
        rerank_model: str | None = None,
    ) -> ProviderAdapter:
        key = (
            provider_name,
            completion_model or "",
            embedding_model or "",
            rerank_model or "",
        )
        if key in self._provider_cache:
            return self._provider_cache[key]
        provider_cfg = self._build_provider_config(
            provider_name,
            completion_model=completion_model,
            embedding_model=embedding_model,
            rerank_model=rerank_model,
        )
        adapter = ProviderAdapter(provider_cfg)
        self._provider_cache[key] = adapter
        return adapter

    def _build_provider_config(
        self,
        provider_name: str,
        completion_model: str | None = None,
        embedding_model: str | None = None,
        rerank_model: str | None = None,
    ) -> ProviderConfig:
        prefix = f"ROUTER_PROVIDER_{provider_name.upper()}"
        default = self.config.default_provider
        return ProviderConfig(
            name=provider_name,
            completion_model=completion_model
            or os.getenv(f"{prefix}_COMPLETION_MODEL", default.completion_model),
            embedding_model=embedding_model
            or os.getenv(f"{prefix}_EMBEDDING_MODEL", default.embedding_model),
            rerank_model=rerank_model
            or os.getenv(f"{prefix}_RERANK_MODEL", default.rerank_model),
            temperature=self._float_param(
                os.getenv(f"{prefix}_TEMPERATURE", str(default.temperature))
            )
            or default.temperature,
            base_url=os.getenv(f"{prefix}_BASE_URL", default.base_url),
            api_key=os.getenv(f"{prefix}_API_KEY", default.api_key),
        )

    # ------------------------------------------------------------------
    # Structured decoding helpers
    # ------------------------------------------------------------------
    def _ensure_structured(self, text: str) -> str:
        cfg = self.decoding_cfg.get("llm", {})
        if not cfg.get("json_mode"):
            return text
        try:
            json.loads(text)
            return text
        except Exception:
            strict = self.decoding_cfg.get("schema_validation", {}).get("strict", False)
            fallback_obj = {
                "summary": text,
                "provider": self.config.default_provider.name,
            }
            fallback = json.dumps(fallback_obj)
            try:
                json.loads(fallback)
            except Exception as exc:  # pragma: no cover
                if strict:
                    raise HTTPException(
                        status_code=500, detail="structured decoding failed"
                    ) from exc
                return text
            if strict:
                return fallback
            return fallback
