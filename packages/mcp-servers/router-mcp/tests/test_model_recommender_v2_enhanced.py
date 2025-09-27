"""Tests for Model Recommender V2 enhancements."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("aiosqlite")

from aiosqlite import connect as aiosqlite_connect

from router_mcp.model_persistence import ModelPerformanceStore
from router_mcp.model_recommender import (
    ModelRecommender, 
    ModelPerformance, 
    TaskContext, 
    is_model_recommender_v2_enabled
)
from router_mcp.model_scheduler import ModelDataScheduler


class TestModelRecommenderV2:
    """Test enhanced Model Recommender V2 functionality."""
    
    def test_feature_flag_enabled_by_default(self):
        """Test that Model Recommender V2 is enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_model_recommender_v2_enabled()
    
    def test_feature_flag_enabled_when_set(self):
        """Test that Model Recommender V2 is enabled when flag is set."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "true"}):
            assert is_model_recommender_v2_enabled()
        
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "TRUE"}):
            assert is_model_recommender_v2_enabled()
    
    @pytest.mark.asyncio
    async def test_recommender_without_persistence(self):
        """Test basic recommender functionality without persistence."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "false"}):
            recommender = ModelRecommender()
            assert recommender.store is None
            
            context = TaskContext(
                task_type="chat",
                tenant_id="test-tenant",
                complexity="medium"
            )
            
            # Mock external data fetching
            with patch.object(recommender, '_fetch_arena_leaderboard') as mock_arena, \
                 patch.object(recommender, '_fetch_mteb_scores') as mock_mteb, \
                 patch.object(recommender, '_fetch_internal_evaluations') as mock_internal:
                
                mock_arena.return_value = {"gpt-4o": 1287, "claude-3-5-sonnet": 1269}
                mock_mteb.return_value = {}
                mock_internal.return_value = {}
                
                primary, fallbacks = await recommender.recommend_model(context)
                assert primary in ["gpt-4o", "claude-3-5-sonnet", "gpt-4o-mini"]
                assert len(fallbacks) <= 2


class TestModelPerformanceStore:
    """Test SQLite persistence layer."""
    
    @pytest.mark.asyncio
    async def test_schema_initialization(self):
        """Test database schema creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_schema.db"
            store = ModelPerformanceStore(str(db_path))
            
            await store.initialize_schema()
            
            # Verify tables exist
            async with aiosqlite_connect(db_path) as db:
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in await cursor.fetchall()]
                
                assert "model_performance" in tables
                assert "external_data_cache" in tables
                assert "telemetry_events" in tables


class TestModelScoringLogic:
    """Test model scoring and cascade routing logic."""
    
    @pytest.mark.asyncio
    async def test_embedding_task_scoring(self):
        """Test scoring logic for embedding tasks."""
        recommender = ModelRecommender()
        
        # Set up test performance data
        recommender.performance_cache = {
            "text-embedding-3-large": ModelPerformance(
                model_name="text-embedding-3-large",
                mteb_score=64.6,
                avg_latency_ms=100.0,
                cost_per_1k_tokens=0.00013,
                success_rate=0.98
            ),
        }
        
        context = TaskContext(
            task_type="embed",
            tenant_id="test",
            cost_sensitive=True
        )
        
        # Score model
        score = await recommender._score_model("text-embedding-3-large", context)
        
        # Should have non-zero score
        assert score > 0
