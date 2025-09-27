"""Service layer for router MCP with policy enforcement."""

from __future__ import annotations

import asyncio
import json
import os
from json import JSONDecodeError
from typing import Any

from fastapi import HTTPException

from .config import AppConfig, ProviderConfig, TaskPolicy, TaskRoute, TenantPolicy
from .models import (
    AgentRouteRequest,
    AgentRouteResponse,
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
from .model_recommender import ModelRecommender, is_model_recommender_v2_enabled
from .telemetry import build_telemetry_from_env


class RouterService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.policy = config.policy
        self.decoding_cfg = config.structured_decoding
        self._provider_cache: dict[tuple[str, str, str, str], ProviderAdapter] = {}
        
        # Initialize model recommender if V2 is enabled
        self.model_recommender = None
        if is_model_recommender_v2_enabled():
            try:
                self.model_recommender = ModelRecommender()
            except Exception as e:
                # Log but don't fail startup if recommender fails to initialize
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to initialize model recommender: {e}")
    
    def get_model_recommender(self) -> ModelRecommender | None:
        """Get the model recommender instance."""
        return self.model_recommender

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def complete(self, payload: CompletionRequest) -> CompletionResponse:
        _tenant_policy, task_policy, route = self._select_route(
            payload.tenant_id,
            payload.task,
            default_model=self.config.default_provider.completion_model,
        )
        self._validate_completion(_tenant_policy, task_policy, payload)
        adapter = self._adapter_for(
            route.provider,
            completion_model=route.model,
        )
        complexity = "high" if len(payload.prompt) > 2000 else "medium"
        result = await adapter.complete(
            payload.prompt,
            payload.max_tokens,
            model=route.model,
            temperature=payload.temperature,
            tenant_id=payload.tenant_id,
            task_type=payload.task,
            complexity=complexity,
        )
        text = self._ensure_structured(result["text"])
        tokens = result.get("tokens") or payload.max_tokens
        response = CompletionResponse(
            text=text,
            tokens=int(tokens),
            provider=result.get("provider", route.provider),
            model=result.get("model", route.model),
        )
        if self.model_recommender:
            cost = float(result.get("cost_usd", 0.0))
            latency = float(result.get("latency_ms", 0.0)) if result.get("latency_ms") else 0.0
            await self.model_recommender.record_outcome(
                model_name=response.model,
                task_type=payload.task,
                success=True,
                latency_ms=latency,
                cost_usd=cost,
            )
        return response

    def embed(self, payload: EmbeddingRequest) -> EmbeddingResponse:
        _tenant_policy, task_policy, route = self._select_route(
            payload.tenant_id,
            payload.task,
            default_model=payload.model or self.config.default_provider.embedding_model,
        )
        self._validate_embedding(task_policy, payload)
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
        _tenant_policy, task_policy, route = self._select_route(
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
        adapter = ProviderAdapter(
            provider_cfg,
            recommender=self.model_recommender,
            telemetry=build_telemetry_from_env(),
        )
        self._provider_cache[key] = adapter
        return adapter

    def _build_provider_config(
        self,
        provider_name: str,
        completion_model: str | None = None,
        embedding_model: str | None = None,
        rerank_model: str | None = None,
    ) -> ProviderConfig:
        def _coerce_str(value: str | None, fallback: str) -> str:
            return value if value is not None and value != "" else fallback

        prefix = f"ROUTER_PROVIDER_{provider_name.upper()}"
        default = self.config.default_provider
        coerced_completion: str = _coerce_str(
            completion_model,
            os.getenv(f"{prefix}_COMPLETION_MODEL", default.completion_model)
            or default.completion_model,
        )
        coerced_embedding: str = _coerce_str(
            embedding_model,
            os.getenv(f"{prefix}_EMBEDDING_MODEL", default.embedding_model)
            or default.embedding_model,
        )
        coerced_rerank: str = _coerce_str(
            rerank_model,
            os.getenv(f"{prefix}_RERANK_MODEL", default.rerank_model)
            or default.rerank_model,
        )
        return ProviderConfig(
            name=provider_name,
            completion_model=coerced_completion,
            embedding_model=coerced_embedding,
            rerank_model=coerced_rerank,
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
        except JSONDecodeError:
            strict = self.decoding_cfg.get("schema_validation", {}).get("strict", False)
            fallback_obj = {
                "summary": text,
                "provider": self.config.default_provider.name,
            }
            fallback = json.dumps(fallback_obj)
            try:
                json.loads(fallback)
            except JSONDecodeError as exc:  # pragma: no cover
                if strict:
                    raise HTTPException(
                        status_code=500, detail="structured decoding failed"
                    ) from exc
                return text
            return fallback

    def route_agents(self, payload: AgentRouteRequest) -> AgentRouteResponse:
        """Route request to appropriate agents - Sprint 1 implementation."""
        # Import from the correct path - agents package is a sibling
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../../agents/src"))
        
        from router_graph import AgentRouter, RouterInput
        
        # Create router instance
        router = AgentRouter()
        
        # Build router input
        router_input = RouterInput(
            query=payload.query,
            tenant_id=payload.tenant_id,
            metadata=payload.metadata,
            policy_flags=payload.policy_flags
        )
        
        # Route to agents
        result = router.route(router_input)
        
        return AgentRouteResponse(
            selected_agents=[agent.value for agent in result.selected_agents],
            rationale=result.rationale,
            confidence=result.confidence,
            routing_metadata=result.routing_metadata,
            tenant_id=payload.tenant_id
        )
