"""Provider adapters for router MCP."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .config import ProviderConfig
from .model_recommender import ModelRecommender, TaskContext
from .telemetry import RoutingTelemetry, default_telemetry

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import litellm
except ImportError:  # pragma: no cover
    litellm = None

try:  # pragma: no cover - optional dependency
    from bge_reranker import BGEReranker, RerankDocument
except ImportError:  # pragma: no cover
    BGEReranker = None
    RerankDocument = None


@dataclass
class ProviderAdapter:
    config: ProviderConfig
    recommender: ModelRecommender | None = None
    telemetry: RoutingTelemetry = default_telemetry

    def __post_init__(self):
        """Initialize model recommender if not provided."""
        if self.recommender is None:
            self.recommender = ModelRecommender()

    async def complete(
        self,
        prompt: str,
        max_tokens: int,
        model: str | None = None,
        temperature: float | None = None,
        tenant_id: str = "default",
        task_type: str = "chat",
        complexity: str = "medium"
    ) -> dict[str, Any]:
        """Complete with intelligent model selection and fallback handling."""
        start_time = time.time()
        
        # Use intelligent model selection if no specific model requested
        if not model and self.recommender:
            context = TaskContext(
                task_type=task_type,
                tenant_id=tenant_id,
                complexity=complexity,
                latency_critical=False,
                cost_sensitive=True
            )
            
            try:
                primary_model, fallback_models = await self.recommender.recommend_model(context)
                models_to_try = [primary_model] + fallback_models
            except Exception as e:
                logger.warning(f"Model recommendation failed: {e}")
                models_to_try = [self.config.completion_model]
        else:
            models_to_try = [model or self.config.completion_model]
        
        # Try models in cascade order
        last_error = None
        for attempt_model in models_to_try:
            try:
                with self.telemetry.record_attempt(
                    model=attempt_model,
                    provider=self.config.name,
                    tenant=tenant_id,
                    task_type=task_type,
                    metadata={"cascade_index": models_to_try.index(attempt_model)},
                ) as metrics:
                    result = await self._attempt_completion(
                        prompt, max_tokens, attempt_model, temperature
                    )
                    metrics["tokens"] = result.get("tokens")
                    metrics["cost_usd"] = result.get("cost_usd", 0.0)
                result["latency_ms"] = metrics.get("latency_ms")

                # Update performance metrics
                latency_ms = (time.time() - start_time) * 1000
                if self.recommender:
                    await self.recommender.update_model_performance(
                        attempt_model, latency_ms, True
                    )
                
                result["model_used"] = attempt_model
                result["cascade_tried"] = models_to_try[:models_to_try.index(attempt_model) + 1]
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Model {attempt_model} failed: {e}")
                
                # Update failure metrics
                if self.recommender:
                    latency_ms = (time.time() - start_time) * 1000
                    await self.recommender.update_model_performance(
                        attempt_model, latency_ms, False
                    )
                continue
        
        # All models failed
        raise Exception(f"All models failed. Last error: {last_error}")

    async def _attempt_completion(
        self,
        prompt: str,
        max_tokens: int,
        model: str,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Attempt completion with a specific model."""
        temperature = self.config.temperature if temperature is None else temperature
        
        if self.config.name in {"openai", "litellm", "vllm"} and litellm is not None:
            try:  # pragma: no cover - network path
                response = litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    api_base=self.config.base_url,
                    api_key=self.config.api_key,
                )
                choice = response.choices[0]
                text = choice.message["content"]
                usage = response.usage or {}
                tokens = usage.get("total_tokens") or usage.get("completion_tokens") or max_tokens
                provider = response.model
                cost = float(getattr(response, "cost", 0.0))
                return {
                    "text": text,
                    "tokens": tokens,
                    "cost_usd": cost,
                    "provider": provider,
                    "model": model,
                }
            except Exception as exc:
                logger.warning("Provider completion failed; falling back", exc_info=exc)
                raise exc
        
        # Fallback response for non-LiteLLM providers
        return {
            "text": f"Mock completion for: {prompt[:50]}...",
            "tokens": max_tokens // 2,
            "provider": self.config.name,
            "model": model,
        }

    def embed(self, inputs: Iterable[str], model: str | None = None) -> dict[str, Any]:
        target_model = model or self.config.embedding_model
        payloads = list(inputs)
        vectors: list[list[float]] = []

        with self.telemetry.record_attempt(
            model=target_model,
            provider=self.config.name,
            tenant="-",
            task_type="embedding",
            metadata={"input_count": len(payloads)},
        ) as metrics:
            if self.config.name in {"openai", "litellm", "vllm"} and litellm is not None:
                try:  # pragma: no cover
                    response = litellm.embedding(
                        model=target_model,
                        input=payloads,
                        api_base=self.config.base_url,
                        api_key=self.config.api_key,
                    )
                    vectors = [item.embedding for item in response.data]
                    metrics["tokens"] = getattr(response, "usage", {}).get("total_tokens")
                    metrics["cost_usd"] = float(getattr(response, "cost", 0.0))
                except Exception as exc:
                    logger.warning("Provider embedding failed; falling back", exc_info=exc)
            if not vectors:
                for text in payloads:
                    vectors.append([float(ord(ch) % 17) / 16.0 for ch in text[:32]])

        return {
            "embeddings": vectors,
            "provider": self.config.name,
            "model": target_model,
        }

    def rerank(
        self,
        query: str,
        documents: list[dict[str, str]],
        top_k: int,
        model: str | None = None,
    ) -> dict[str, Any]:
        target_model = model or self.config.rerank_model
        with self.telemetry.record_attempt(
            model=target_model,
            provider=self.config.name,
            tenant="-",
            task_type="rerank",
            metadata={"document_count": len(documents)},
        ):
            if (
                self.config.name == "local"
                and BGEReranker is not None
                and RerankDocument is not None
            ):
                reranker = BGEReranker(model_name=target_model)
                request_docs = [
                    RerankDocument(id=doc["id"], text=doc["text"]) for doc in documents
                ]
                results = reranker.rerank(query=query, documents=request_docs, top_k=top_k)
                return {
                    "results": [
                        {"id": item.id, "score": float(item.score), "text": item.text}
                        for item in results
                    ],
                    "provider": self.config.name,
                    "model": target_model,
                }
            if self.config.name in {"openai", "litellm", "vllm"} and litellm is not None:
                try:  # pragma: no cover
                    response = litellm.rerank(
                        model=target_model,
                        query=query,
                        documents=[doc["text"] for doc in documents],
                        api_base=self.config.base_url,
                        api_key=self.config.api_key,
                    )
                    results = [
                        {
                            "id": documents[idx]["id"],
                            "score": item.score,
                            "text": documents[idx]["text"],
                        }
                        for idx, item in enumerate(response.data)
                    ]
                    return {
                        "results": results[:top_k],
                        "provider": self.config.name,
                        "model": target_model,
                    }
                except Exception as exc:
                    logger.warning("Provider rerank failed; falling back", exc_info=exc)
            scored = [
                {"id": doc["id"], "score": max(0.1, 1.0 - idx * 0.05), "text": doc["text"]}
                for idx, doc in enumerate(documents)
            ]
            return {
                "results": scored[:top_k],
                "provider": self.config.name,
                "model": target_model,
            }
