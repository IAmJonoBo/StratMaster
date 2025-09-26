"""Evidence-guided model recommendation engine for StratMaster.

Implements intelligent model selection based on:
- LMSYS Arena leaderboard data for general chat performance  
- MTEB scores for embedding tasks
- Internal evaluations via Langfuse + RAGAS
- Cost and latency telemetry from gateway
- Cascade routing (FrugalGPT/RouteLLM inspired)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

try:  # pragma: no cover
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler
except ImportError:
    pd = None
    np = None

# Feature flag for Model Recommender V2
def is_model_recommender_v2_enabled() -> bool:
    """Check if Model Recommender V2 is enabled via feature flag."""
    return os.getenv("ENABLE_MODEL_RECOMMENDER_V2", "false").lower() == "true"


@dataclass 
class ModelPerformance:
    """Model performance metrics from various sources."""
    model_name: str
    arena_elo: float | None = None
    mteb_score: float | None = None
    internal_score: float | None = None
    avg_latency_ms: float | None = None
    cost_per_1k_tokens: float | None = None
    success_rate: float = 1.0
    last_updated: datetime | None = None


@dataclass
class TaskContext:
    """Context information for model selection."""
    task_type: str = "reasoning"  # reasoning, summarization, tool-use
    prompt_length: int = 0
    context_size: int = 0
    requires_tools: bool = False
    gpu_available: bool = True
    tenant_id: str = "default"
    user_preferences: dict[str, Any] | None = None


@dataclass
class BanditArm:
    """Bandit arm representing a model choice."""
    model_name: str
    provider: str
    estimated_reward: float = 0.0
    confidence_bound: float = 0.0
    selection_count: int = 0
    total_reward: float = 0.0
    last_updated: datetime | None = None


class UCBBanditSelector:
    """Upper Confidence Bound (UCB1) bandit for model selection."""
    
    def __init__(self, exploration_factor: float = 1.4):
        self.exploration_factor = exploration_factor
        self.arms: dict[str, BanditArm] = {}
        self.total_selections = 0
        
    def add_model(self, model_name: str, provider: str) -> None:
        """Add a model as a bandit arm."""
        if model_name not in self.arms:
            self.arms[model_name] = BanditArm(model_name=model_name, provider=provider)
    
    def select_model(self, context: TaskContext) -> str:
        """Select model using UCB1 algorithm."""
        if not self.arms:
            raise ValueError("No models available for selection")
        
        # If any arm hasn't been tried, select it first
        unselected = [arm for arm in self.arms.values() if arm.selection_count == 0]
        if unselected:
            return unselected[0].model_name
        
        # Calculate UCB1 scores for all arms
        best_model = None
        best_score = float('-inf')
        
        for arm in self.arms.values():
            if arm.selection_count == 0:
                # Infinite confidence bound for unselected arms
                confidence_bound = float('inf')
            else:
                # UCB1 formula: mean_reward + exploration_factor * sqrt(ln(total_selections) / arm_selections)
                if np is not None:
                    confidence_bound = (
                        arm.estimated_reward + 
                        self.exploration_factor * np.sqrt(np.log(self.total_selections) / arm.selection_count)
                    )
                else:
                    # Fallback without numpy
                    import math
                    confidence_bound = (
                        arm.estimated_reward + 
                        self.exploration_factor * math.sqrt(math.log(self.total_selections) / arm.selection_count)
                    )
            
            if confidence_bound > best_score:
                best_score = confidence_bound
                best_model = arm.model_name
                
        return best_model or list(self.arms.keys())[0]
    
    def update_reward(self, model_name: str, reward: float) -> None:
        """Update reward for selected model."""
        if model_name not in self.arms:
            logger.warning(f"Model {model_name} not found in bandit arms")
            return
            
        arm = self.arms[model_name]
        arm.selection_count += 1
        arm.total_reward += reward
        arm.estimated_reward = arm.total_reward / arm.selection_count
        arm.last_updated = datetime.utcnow()
        
        self.total_selections += 1
        
        logger.debug(f"Updated {model_name}: reward={reward:.3f}, avg_reward={arm.estimated_reward:.3f}")


@dataclass
class TaskContext:
    """Context for model selection decision."""
    task_type: str  # "chat", "embed", "reasoning", "summarization" 
    tenant_id: str
    complexity: str = "medium"  # "low", "medium", "high"
    latency_critical: bool = False
    cost_sensitive: bool = False
    quality_threshold: float = 0.7


class ModelRecommender:
    """Evidence-guided model recommendation engine with UCB1 bandit selection."""
    
    def __init__(
        self, 
        config_path: str = "configs/router/models-policy.yaml",
        persistence_store: "ModelPerformanceStore | None" = None
    ):
        self.config_path = Path(config_path)
        self.performance_cache: dict[str, ModelPerformance] = {}
        self.last_cache_update: datetime | None = None
        self.client = httpx.AsyncClient()
        
        # Bandit selection per task type
        self.bandits: dict[str, UCBBanditSelector] = {}
        
        # Persistence layer for Model Recommender V2
        self.store = persistence_store
        if persistence_store and is_model_recommender_v2_enabled():
            logger.info("Model Recommender V2 enabled with persistent storage")
            
    def _get_or_create_bandit(self, task_type: str) -> UCBBanditSelector:
        """Get or create bandit selector for task type."""
        if task_type not in self.bandits:
            self.bandits[task_type] = UCBBanditSelector()
            
            # Initialize with available models for this task
            available_models = self._get_available_models_for_task(task_type)
            for model in available_models:
                self.bandits[task_type].add_model(model, "local")  # Provider determined by config
                
        return self.bandits[task_type]
    
    def _get_available_models_for_task(self, task_type: str) -> list[str]:
        """Get available models for a specific task type."""
        # Default models per task type from SCRATCH.md
        model_mapping = {
            "reasoning": ["together/llama-3.1-70b-instruct", "vllm/gemma-2-27b", "tgi/llama-3.1-8b"],
            "summarization": ["tgi/llama-3.1-8b", "vllm/gemma-2-27b"],
            "embedding": ["local/bge-large-en", "local/e5-large"],
            "reranking": ["local/bge-reranker-v2", "local/mxbai-rerank-large"]
        }
        return model_mapping.get(task_type, ["together/llama-3.1-70b-instruct"])
    
    async def recommend_model_with_bandit(
        self, 
        context: TaskContext, 
        available_models: list[str] | None = None
    ) -> tuple[str, list[str]]:
        """
        Recommend model using bandit selection with quality gates.
        
        Returns:
            Tuple of (primary_model, fallback_models)
        """
        # Get bandit for task type
        bandit = self._get_or_create_bandit(context.task_type)
        
        # Select primary model using UCB1
        primary_model = bandit.select_model(context)
        
        # Create fallback chain based on performance scores
        candidates = available_models or self._get_available_models_for_task(context.task_type)
        fallbacks = [model for model in candidates if model != primary_model][:2]  # Top 2 fallbacks
        
        logger.info(
            f"Bandit selected {primary_model} for {context.task_type} "
            f"(tenant: {context.tenant_id}), fallbacks: {fallbacks}"
        )
        
        return primary_model, fallbacks
    
    async def record_outcome(
        self, 
        model_name: str, 
        task_type: str,
        success: bool, 
        latency_ms: float, 
        cost_usd: float,
        quality_score: float = 0.0
    ) -> None:
        """Record outcome for bandit learning (multi-objective reward)."""
        # Multi-objective reward calculation as per SCRATCH.md
        # Objectives: [accept_label, -latency_ms, -cost_usd]
        
        # Normalize and weight objectives
        accept_reward = 1.0 if success else 0.0
        latency_penalty = max(0, (latency_ms - 100) / 1000)  # Penalty above 100ms
        cost_penalty = cost_usd * 100  # Scale cost to meaningful range
        
        # Combined reward (higher is better)
        reward = accept_reward - 0.5 * latency_penalty - 0.3 * cost_penalty
        
        # Add quality score if available
        if quality_score > 0:
            reward += 0.2 * quality_score
            
        # Update bandit
        if task_type in self.bandits:
            self.bandits[task_type].update_reward(model_name, reward)
            
        # Log for observability
        logger.info(
            f"Recorded outcome for {model_name}/{task_type}: "
            f"success={success}, latency={latency_ms}ms, cost=${cost_usd:.4f}, "
            f"quality={quality_score:.3f}, reward={reward:.3f}"
        )
        
    async def recommend_model(
        self, 
        context: TaskContext, 
        available_models: list[str] | None = None
    ) -> tuple[str, list[str]]:
        """
        Recommend primary model and fallback chain for given context.
        
        Returns:
            Tuple of (primary_model, fallback_models)
        """
        # Update performance cache if stale
        await self._refresh_performance_cache()
        
        # Get candidate models
        candidates = available_models or self._get_available_models(context)
        
        # Score candidates based on multiple criteria
        scored_models = []
        for model in candidates:
            score = await self._score_model(model, context)
            scored_models.append((model, score))
        
        # Sort by composite score (quality, cost, latency)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        if not scored_models:
            raise ValueError(f"No suitable models found for task: {context.task_type}")
        
        # Implement cascade routing: try cheap/fast first, escalate if needed
        primary, fallbacks = self._apply_cascade_strategy(scored_models, context)
        
        logger.info(
            f"Recommended {primary} with fallbacks {fallbacks} for "
            f"{context.task_type} (tenant: {context.tenant_id})"
        )
        
        return primary, fallbacks
    
    async def _refresh_performance_cache(self) -> None:
        """Refresh model performance data from external sources."""
        # If using persistent storage, try loading from DB first
        if self.store and is_model_recommender_v2_enabled():
            await self._load_from_persistent_storage()
        
        if (self.last_cache_update and 
            datetime.now() - self.last_cache_update < timedelta(hours=1)):
            return
        
        logger.info("Refreshing model performance cache...")
        
        # Try loading cached external data first
        arena_data = await self._get_cached_or_fresh_arena_data()
        mteb_data = await self._get_cached_or_fresh_mteb_data()
        internal_data = await self._fetch_internal_evaluations()
        
        # Merge all data sources
        self._update_performance_cache(arena_data, mteb_data, internal_data)
        
        # Save to persistent storage if available
        if self.store and is_model_recommender_v2_enabled():
            await self._save_to_persistent_storage()
        
        self.last_cache_update = datetime.now()
        logger.info(f"Updated performance data for {len(self.performance_cache)} models")
    
    async def _fetch_arena_leaderboard(self) -> dict[str, float]:
        """Fetch current LMSYS Arena Elo ratings from multiple sources."""
        # If V2 is not enabled, return cached representative data
        if not is_model_recommender_v2_enabled():
            logger.debug("Model Recommender V2 disabled, using cached data")
            return {
                "gpt-4o": 1287,
                "claude-3-5-sonnet": 1269,
                "gpt-4o-mini": 1206,
                "llama-3.1-70b": 1213,
                "llama-3.1-8b": 1156,
            }
        
        # Try multiple data sources for robustness
        data_sources = [
            {
                "name": "Hugging Face Leaderboards",
                "url": "https://api.huggingface.co/api/models?search=arena&filter=leaderboard",
                "parser": self._parse_hf_arena_data
            },
            {
                "name": "LMSYS GitHub",
                "url": "https://raw.githubusercontent.com/lm-sys/FastChat/main/fastchat/serve/monitor/elo_results_20241201.json",
                "parser": self._parse_lmsys_github_data
            },
            {
                "name": "LMSYS GitHub (fallback)",
                "url": "https://raw.githubusercontent.com/lm-sys/FastChat/main/fastchat/serve/monitor/elo_results_20240101.json", 
                "parser": self._parse_lmsys_github_data
            }
        ]
        
        for source in data_sources:
            try:
                logger.info(f"Fetching Arena data from {source['name']}")
                response = await self.client.get(source["url"], timeout=30.0)
                
                if response.status_code == 200:
                    arena_data = response.json()
                    elo_ratings = source["parser"](arena_data)
                    
                    if elo_ratings and len(elo_ratings) >= 5:  # Minimum threshold
                        logger.info(f"Successfully fetched Arena data from {source['name']} for {len(elo_ratings)} models")
                        return elo_ratings
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source['name']}: {e}")
                continue
        
        logger.warning("All Arena data sources failed, using fallback data")
        return self._get_fallback_arena_data()
    
    def _parse_hf_arena_data(self, data: dict) -> dict[str, float]:
        """Parse Arena data from Hugging Face API."""
        elo_ratings = {}
        # This is a placeholder parser - actual HF API structure may differ
        if isinstance(data, list):
            for model in data:
                if "arena_elo" in model and "modelId" in model:
                    model_name = model["modelId"].lower()
                    elo_score = model["arena_elo"]
                    normalized_name = self._normalize_model_name(model_name)
                    if normalized_name and elo_score > 0:
                        elo_ratings[normalized_name] = float(elo_score)
        return elo_ratings
    
    def _parse_lmsys_github_data(self, data: dict) -> dict[str, float]:
        """Parse Arena data from LMSYS GitHub repository."""
        elo_ratings = {}
        
        if "leaderboard_table_df" in data:
            for entry in data["leaderboard_table_df"]:
                model_name = entry.get("key", "").lower()
                elo_score = entry.get("rating", 0)
                
                normalized_name = self._normalize_model_name(model_name)
                if normalized_name and elo_score > 0:
                    elo_ratings[normalized_name] = float(elo_score)
        
        # Try alternative format
        elif "models" in data:
            for model_name, model_data in data["models"].items():
                if "elo" in model_data:
                    elo_score = model_data["elo"]
                    normalized_name = self._normalize_model_name(model_name.lower())
                    if normalized_name and elo_score > 0:
                        elo_ratings[normalized_name] = float(elo_score)
        
        return elo_ratings
    
    def _normalize_model_name(self, model_name: str) -> str | None:
        """Normalize model names from external sources to internal format."""
        name_mappings = {
            "gpt-4o": "gpt-4o",
            "gpt-4-turbo": "gpt-4-turbo",
            "gpt-4": "gpt-4",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "claude-3-5-sonnet": "claude-3-5-sonnet",
            "claude-3-opus": "claude-3-opus",
            "claude-3-haiku": "claude-3-haiku",
            "llama-3.1-405b": "llama-3.1-405b",
            "llama-3.1-70b": "llama-3.1-70b",
            "llama-3.1-8b": "llama-3.1-8b",
            "mixtral-8x7b": "mixtral-8x7b-instruct",
            "gemini-1.5-pro": "gemini-1.5-pro",
        }
        
        # Try exact match first
        if model_name in name_mappings:
            return name_mappings[model_name]
        
        # Try partial matches for variations
        for external_name, internal_name in name_mappings.items():
            if external_name in model_name.lower():
                return internal_name
        
        return None
    
    def _get_fallback_arena_data(self) -> dict[str, float]:
        """Get fallback Arena data when real data is unavailable."""
        return {
            "gpt-4o": 1287,
            "claude-3-5-sonnet": 1269,
            "gpt-4o-mini": 1206,
            "llama-3.1-70b": 1213,
            "llama-3.1-8b": 1156,
            "mixtral-8x7b-instruct": 1149,
            "phi3-medium-instruct": 1098,
        }
    
    async def _fetch_mteb_scores(self) -> dict[str, float]:
        """Fetch MTEB embedding benchmarks from multiple sources."""
        # If V2 is not enabled, return cached representative data
        if not is_model_recommender_v2_enabled():
            logger.debug("Model Recommender V2 disabled, using cached MTEB data")
            return {
                "text-embedding-3-large": 64.6,
                "text-embedding-3-small": 62.3,
                "all-mpnet-base-v2": 57.8,
                "bge-large-en-v1.5": 63.5,
            }
        
        # Try multiple MTEB data sources
        data_sources = [
            {
                "name": "MTEB Hugging Face Leaderboard API",
                "url": "https://huggingface.co/api/datasets/mteb/leaderboard/data",
                "parser": self._parse_mteb_api_data
            },
            {
                "name": "MTEB GitHub Repository",
                "url": "https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/results/en/SentenceTransformersEval.json",
                "parser": self._parse_mteb_github_data
            },
            {
                "name": "MTEB Parquet Data",
                "url": "https://huggingface.co/api/datasets/mteb/results/parquet/default/train/0.parquet",
                "parser": self._parse_mteb_parquet_data
            }
        ]
        
        for source in data_sources:
            try:
                logger.info(f"Fetching MTEB data from {source['name']}")
                response = await self.client.get(source["url"], timeout=45.0)
                
                if response.status_code == 200:
                    if source["name"] == "MTEB Parquet Data":
                        # Handle binary parquet data
                        mteb_scores = source["parser"](response.content)
                    else:
                        # Handle JSON data
                        mteb_data = response.json()
                        mteb_scores = source["parser"](mteb_data)
                    
                    if mteb_scores and len(mteb_scores) >= 3:  # Minimum threshold
                        logger.info(f"Successfully fetched MTEB data from {source['name']} for {len(mteb_scores)} models")
                        return mteb_scores
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source['name']}: {e}")
                continue
        
        logger.warning("All MTEB data sources failed, using fallback data")
        return self._get_fallback_mteb_data()
    
    def _parse_mteb_api_data(self, data: dict) -> dict[str, float]:
        """Parse MTEB data from HuggingFace API."""
        mteb_scores = {}
        
        # Handle different API response formats
        if "data" in data:
            for entry in data["data"]:
                if "model" in entry and "score" in entry:
                    model_name = entry["model"]
                    score = entry["score"]
                    normalized_name = self._normalize_embedding_model_name(model_name)
                    if normalized_name and score > 0:
                        mteb_scores[normalized_name] = float(score)
                        
        return mteb_scores
    
    def _parse_mteb_github_data(self, data: dict) -> dict[str, float]:
        """Parse MTEB data from GitHub repository."""
        mteb_scores = {}
        
        if isinstance(data, dict):
            for model_name, model_data in data.items():
                if isinstance(model_data, dict) and "average_score" in model_data:
                    score = model_data["average_score"]
                    normalized_name = self._normalize_embedding_model_name(model_name)
                    if normalized_name and score > 0:
                        mteb_scores[normalized_name] = float(score)
                        
        return mteb_scores
    
    def _parse_mteb_parquet_data(self, content: bytes) -> dict[str, float]:
        """Parse MTEB data from parquet file."""
        mteb_scores = {}
        
        if pd is None:
            logger.warning("Pandas not available, cannot parse parquet data")
            return mteb_scores
        
        try:
            import io
            df = pd.read_parquet(io.BytesIO(content))
            
            # Extract average scores per model
            if 'model_name' in df.columns and 'score' in df.columns:
                model_scores = df.groupby('model_name')['score'].mean()
                
                for model_name, avg_score in model_scores.items():
                    normalized_name = self._normalize_embedding_model_name(model_name)
                    if normalized_name:
                        mteb_scores[normalized_name] = float(avg_score)
                        
        except Exception as e:
            logger.error(f"Error parsing parquet data: {e}")
            
        return mteb_scores
    
    def _normalize_embedding_model_name(self, model_name: str) -> str | None:
        """Normalize embedding model names from MTEB to internal format."""
        name_mappings = {
            "text-embedding-3-large": "text-embedding-3-large",
            "text-embedding-3-small": "text-embedding-3-small", 
            "text-embedding-ada-002": "text-embedding-ada-002",
            "all-mpnet-base-v2": "all-mpnet-base-v2",
            "all-MiniLM-L6-v2": "all-minilm-l6-v2",
            "bge-large-en-v1.5": "bge-large-en-v1.5",
            "e5-large-v2": "e5-large-v2",
            "instructor-xl": "instructor-xl",
            "phi3-medium-embedding": "phi3-medium-embedding",
            "nous-hermes2-embed": "nous-hermes2-embed",
        }
        
        # Try exact match first
        if model_name in name_mappings:
            return name_mappings[model_name]
        
        # Try partial matches
        for external_name, internal_name in name_mappings.items():
            if external_name.lower() in model_name.lower():
                return internal_name
        
        return None
    
    def _get_fallback_mteb_data(self) -> dict[str, float]:
        """Get fallback MTEB data when real data is unavailable."""
        return {
            "text-embedding-3-large": 64.6,
            "text-embedding-3-small": 62.3,
            "all-mpnet-base-v2": 57.8,
            "bge-large-en-v1.5": 63.5,
            "phi3-medium-embedding": 58.2,
            "nous-hermes2-embed": 56.1,
        }
    
    async def _fetch_internal_evaluations(self) -> dict[str, dict[str, float]]:
        """Fetch internal evaluation scores from Langfuse."""
        try:
            # This would integrate with actual Langfuse API
            # Return mock data showing internal StratMaster-specific scores
            return {
                "gpt-4o": {"faithfulness": 0.85, "answer_relevancy": 0.82},
                "claude-3-5-sonnet": {"faithfulness": 0.83, "answer_relevancy": 0.84},
                "llama-3.1-70b": {"faithfulness": 0.78, "answer_relevancy": 0.76},
            }
        except Exception as e:
            logger.warning(f"Failed to fetch internal evaluations: {e}")
            return {}
    
    def _update_performance_cache(
        self, 
        arena_data: dict[str, float],
        mteb_data: dict[str, float], 
        internal_data: dict[str, dict[str, float]]
    ) -> None:
        """Update performance cache with fresh data."""
        all_models = set(arena_data.keys()) | set(mteb_data.keys()) | set(internal_data.keys())
        
        for model in all_models:
            # Calculate internal score as average of RAGAS metrics
            internal_metrics = internal_data.get(model, {})
            internal_score = None
            if internal_metrics:
                internal_score = sum(internal_metrics.values()) / len(internal_metrics)
            
            # Update or create performance record
            self.performance_cache[model] = ModelPerformance(
                model_name=model,
                arena_elo=arena_data.get(model),
                mteb_score=mteb_data.get(model),
                internal_score=internal_score,
                last_updated=datetime.now()
            )
    
    async def _score_model(self, model: str, context: TaskContext) -> float:
        """Score a model for given context using multi-criteria evaluation."""
        perf = self.performance_cache.get(model)
        if not perf:
            return 0.0
        
        scores = []
        weights = []
        
        # Quality score based on task type
        if context.task_type == "embed" and perf.mteb_score:
            scores.append(perf.mteb_score / 100.0)  # Normalize to 0-1
            weights.append(0.4)
        elif context.task_type in ["chat", "reasoning"] and perf.arena_elo:
            # Normalize Arena Elo (typical range 1000-1300)
            normalized_elo = (perf.arena_elo - 1000) / 300.0
            scores.append(min(1.0, max(0.0, normalized_elo)))
            weights.append(0.4)
        
        # Internal evaluation score (StratMaster-specific)
        if perf.internal_score:
            scores.append(perf.internal_score)
            weights.append(0.3)
        
        # Cost efficiency (inverse cost)
        if perf.cost_per_1k_tokens and context.cost_sensitive:
            # Lower cost = higher score
            cost_score = 1.0 / (1.0 + perf.cost_per_1k_tokens)
            scores.append(cost_score)
            weights.append(0.2)
        
        # Latency score (inverse latency)
        if perf.avg_latency_ms and context.latency_critical:
            # Lower latency = higher score
            latency_score = 1.0 / (1.0 + perf.avg_latency_ms / 1000.0)
            scores.append(latency_score)
            weights.append(0.1)
        
        # Reliability score
        scores.append(perf.success_rate)
        weights.append(0.1)
        
        # Weighted average
        if not scores:
            return 0.0
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
            
        return sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    def _apply_cascade_strategy(
        self, 
        scored_models: list[tuple[str, float]], 
        context: TaskContext
    ) -> tuple[str, list[str]]:
        """
        Apply cascade routing strategy inspired by FrugalGPT/RouteLLM.
        
        Strategy:
        1. For high complexity tasks, use best model directly
        2. For medium/low complexity, try efficient model first
        3. Provide escalation fallbacks based on performance
        """
        if not scored_models:
            raise ValueError("No models available for cascade")
        
        # Sort models by score (highest first)
        models_by_score = [model for model, score in scored_models]
        
        if context.complexity == "high":
            # High complexity: start with best model
            primary = models_by_score[0]
            fallbacks = models_by_score[1:3]  # Top 2 alternatives
        else:
            # Medium/low complexity: try efficient model first
            # Find models with good cost/latency profile
            efficient_models = []
            premium_models = []
            
            for model, score in scored_models:
                perf = self.performance_cache.get(model)
                if (perf and perf.cost_per_1k_tokens and 
                    perf.cost_per_1k_tokens < 0.01):  # Cheap models
                    efficient_models.append(model)
                else:
                    premium_models.append(model)
            
            # Start with efficient model, fall back to premium
            if efficient_models:
                primary = efficient_models[0]
                fallbacks = efficient_models[1:2] + premium_models[:2]
            else:
                primary = models_by_score[0] 
                fallbacks = models_by_score[1:3]
        
        return primary, fallbacks[:2]  # Limit to 2 fallbacks
    
    def _get_available_models(self, context: TaskContext) -> list[str]:
        """Get available models for tenant and task type."""
        # This would read from actual tenant configuration
        # For now, return representative models
        if context.task_type == "embed":
            return ["text-embedding-3-large", "text-embedding-3-small", "bge-large-en-v1.5"]
        else:
            return ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "llama-3.1-70b", "llama-3.1-8b"]
    
    async def update_model_performance(
        self, 
        model: str, 
        latency_ms: float, 
        success: bool,
        cost_per_token: float | None = None
    ) -> None:
        """Update model performance based on actual usage."""
        perf = self.performance_cache.get(model)
        if not perf:
            perf = ModelPerformance(model_name=model)
            self.performance_cache[model] = perf
        
        # Update moving averages
        alpha = 0.1  # Smoothing factor
        
        if perf.avg_latency_ms is None:
            perf.avg_latency_ms = latency_ms
        else:
            perf.avg_latency_ms = (1 - alpha) * perf.avg_latency_ms + alpha * latency_ms
        
        if cost_per_token:
            perf.cost_per_1k_tokens = cost_per_token * 1000
        
        # Update success rate
        perf.success_rate = (1 - alpha) * perf.success_rate + alpha * (1.0 if success else 0.0)
        
        perf.last_updated = datetime.now()
        
        logger.debug(f"Updated performance for {model}: latency={latency_ms}ms, success={success}")
        
        # Record to persistent storage and telemetry if available
        if self.store and is_model_recommender_v2_enabled():
            await self.store.record_telemetry_event(
                model_name=model,
                tenant_id=None,  # Would come from context in real usage
                latency_ms=latency_ms,
                success=success,
                cost_per_token=cost_per_token
            )
    
    async def _load_from_persistent_storage(self) -> None:
        """Load performance data from persistent storage."""
        if not self.store:
            return
            
        try:
            stored_performance = await self.store.load_all_model_performance()
            if stored_performance:
                self.performance_cache = stored_performance
                logger.info(f"Loaded {len(stored_performance)} models from persistent storage")
        except Exception as e:
            logger.warning(f"Failed to load from persistent storage: {e}")
    
    async def _save_to_persistent_storage(self) -> None:
        """Save current performance cache to persistent storage."""
        if not self.store:
            return
            
        try:
            for performance in self.performance_cache.values():
                await self.store.save_model_performance(performance)
        except Exception as e:
            logger.warning(f"Failed to save to persistent storage: {e}")
    
    async def _get_cached_or_fresh_arena_data(self) -> dict[str, float]:
        """Get Arena data from cache or fetch fresh."""
        if self.store and is_model_recommender_v2_enabled():
            cached_data = await self.store.load_external_data_cache("arena_leaderboard")
            if cached_data:
                logger.debug("Using cached Arena data")
                return cached_data
        
        return await self._fetch_arena_leaderboard()
    
    async def _get_cached_or_fresh_mteb_data(self) -> dict[str, float]:
        """Get MTEB data from cache or fetch fresh."""
        if self.store and is_model_recommender_v2_enabled():
            cached_data = await self.store.load_external_data_cache("mteb_scores")
            if cached_data:
                logger.debug("Using cached MTEB data")
                return cached_data
        
        return await self._fetch_mteb_scores()
    
    def get_debug_info(self) -> dict[str, Any]:
        """Get debugging information about model recommendations."""
        cache_age = None
        if self.last_cache_update:
            cache_age = (datetime.now() - self.last_cache_update).total_seconds()
        
        return {
            "cache_size": len(self.performance_cache),
            "cache_age_seconds": cache_age,
            "last_updated": self.last_cache_update.isoformat() if self.last_cache_update else None,
            "model_recommender_v2_enabled": is_model_recommender_v2_enabled(),
            "has_persistence": self.store is not None,
            "models": [
                {
                    "name": perf.model_name,
                    "arena_elo": perf.arena_elo,
                    "mteb_score": perf.mteb_score,
                    "internal_score": perf.internal_score,
                    "avg_latency_ms": perf.avg_latency_ms,
                    "cost_per_1k_tokens": perf.cost_per_1k_tokens,
                    "success_rate": perf.success_rate,
                    "last_updated": perf.last_updated.isoformat() if perf.last_updated else None
                }
                for perf in self.performance_cache.values()
            ]
        }
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()