"""Tests for Model Recommender V2 functionality."""

import os
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from router_mcp.model_recommender import (
    ModelRecommender,
    ModelPerformance,
    TaskContext,
    is_model_recommender_v2_enabled,
)


class TestModelRecommenderV2:
    """Test Model Recommender V2 features."""
    
    def test_feature_flag_enabled_by_default(self):
        """Test that V2 is enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_model_recommender_v2_enabled()
    
    def test_feature_flag_enabled_when_set(self):
        """Test that V2 is enabled when flag is set."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "true"}):
            assert is_model_recommender_v2_enabled()
        
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "TRUE"}):
            assert is_model_recommender_v2_enabled()
    
    def test_feature_flag_disabled_when_false(self):
        """Test that V2 is disabled when explicitly set to false."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "false"}):
            assert not is_model_recommender_v2_enabled()
        
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "invalid"}):
            assert not is_model_recommender_v2_enabled()
    
    @pytest.mark.asyncio
    async def test_fallback_data_when_v2_disabled(self):
        """Test that fallback data is returned when V2 is disabled."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "false"}):
            recommender = ModelRecommender()
            
            arena_data = await recommender._fetch_arena_leaderboard()
            assert "gpt-4o" in arena_data
            assert arena_data["gpt-4o"] == 1287
            
            mteb_data = await recommender._fetch_mteb_scores()
            assert "text-embedding-3-large" in mteb_data
            assert mteb_data["text-embedding-3-large"] == 64.6
    
    @pytest.mark.asyncio
    async def test_external_data_fetching_when_v2_enabled(self):
        """Test external data fetching when V2 is enabled."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "true"}):
            recommender = ModelRecommender()
            
            # Mock successful Arena API response
            mock_arena_response = {
                "leaderboard_table_df": [
                    {"key": "gpt-4o", "rating": 1300},
                    {"key": "claude-3-5-sonnet", "rating": 1280},
                ]
            }
            
            with patch.object(recommender.client, 'get') as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_arena_response
                
                arena_data = await recommender._fetch_arena_leaderboard()
                assert "gpt-4o" in arena_data
                assert arena_data["gpt-4o"] == 1300.0
                assert "claude-3-5-sonnet" in arena_data
                assert arena_data["claude-3-5-sonnet"] == 1280.0
    
    @pytest.mark.asyncio 
    async def test_arena_api_failure_fallback(self):
        """Test fallback when Arena API fails."""
        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "true"}):
            recommender = ModelRecommender()
            
            with patch.object(recommender.client, 'get') as mock_get:
                mock_get.return_value.status_code = 500
                
                arena_data = await recommender._fetch_arena_leaderboard()
                # Should return fallback data
                assert "gpt-4o" in arena_data
                assert arena_data["gpt-4o"] == 1287  # Fallback value
    
    def test_model_name_normalization(self):
        """Test model name normalization functionality."""
        recommender = ModelRecommender()
        
        # Test exact matches
        assert recommender._normalize_model_name("gpt-4o") == "gpt-4o"
        assert recommender._normalize_model_name("claude-3-5-sonnet") == "claude-3-5-sonnet"
        
        # Test partial matches
        assert recommender._normalize_model_name("mixtral-8x7b-something") == "mixtral-8x7b-instruct"
        
        # Test no match
        assert recommender._normalize_model_name("unknown-model") is None
    
    def test_embedding_model_name_normalization(self):
        """Test embedding model name normalization."""
        recommender = ModelRecommender()
        
        # Test exact matches  
        assert recommender._normalize_embedding_model_name("text-embedding-3-large") == "text-embedding-3-large"
        assert recommender._normalize_embedding_model_name("bge-large-en-v1.5") == "bge-large-en-v1.5"
        
        # Test case insensitive partial matches
        assert recommender._normalize_embedding_model_name("ALL-MPNET-BASE-V2") == "all-mpnet-base-v2"
        
        # Test no match
        assert recommender._normalize_embedding_model_name("unknown-embedding") is None

    @pytest.mark.asyncio
    async def test_record_outcome_emits_telemetry(self):
        """Ensure telemetry emit is called with outcome payload."""
        fake_telemetry = MagicMock()
        fake_telemetry.emit = MagicMock()

        with patch.dict(os.environ, {"ENABLE_MODEL_RECOMMENDER_V2": "true"}):
            with patch("router_mcp.model_recommender.build_telemetry_from_env", return_value=fake_telemetry):
                recommender = ModelRecommender()
                # ensure bandit entry exists
                bandit = recommender._get_or_create_bandit("reasoning")
                # register model if not present
                if "together/llama-3.1-70b-instruct" not in bandit.arms:
                    bandit.add_model("together/llama-3.1-70b-instruct", "local")

                await recommender.record_outcome(
                    model_name="together/llama-3.1-70b-instruct",
                    task_type="reasoning",
                    success=True,
                    latency_ms=120.5,
                    cost_usd=0.0003,
                    quality_score=0.8,
                )

                fake_telemetry.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_cache_update(self):
        """Test performance cache updates with multiple data sources."""
        recommender = ModelRecommender()
        
        arena_data = {"gpt-4o": 1300.0, "claude-3-5-sonnet": 1280.0}
        mteb_data = {"text-embedding-3-large": 65.0}
        internal_data = {
            "gpt-4o": {"faithfulness": 0.85, "answer_relevancy": 0.82}
        }
        
        recommender._update_performance_cache(arena_data, mteb_data, internal_data)
        
        # Check gpt-4o has arena and internal data
        gpt4o_perf = recommender.performance_cache["gpt-4o"]
        assert gpt4o_perf.arena_elo == 1300.0
        assert gpt4o_perf.internal_score == 0.835  # (0.85 + 0.82) / 2
        assert gpt4o_perf.mteb_score is None
        
        # Check embedding model has MTEB data
        embed_perf = recommender.performance_cache["text-embedding-3-large"]
        assert embed_perf.mteb_score == 65.0
        assert embed_perf.arena_elo is None
        
        # Check claude has only arena data
        claude_perf = recommender.performance_cache["claude-3-5-sonnet"]
        assert claude_perf.arena_elo == 1280.0
        assert claude_perf.internal_score is None
    
    def test_task_context_creation(self):
        """Test TaskContext creation and defaults."""
        context = TaskContext(
            task_type="chat",
            tenant_id="test-tenant"
        )
        
        assert context.task_type == "chat"
        assert context.tenant_id == "test-tenant"
        assert context.complexity == "medium"  # default
        assert context.latency_critical is False  # default
        assert context.cost_sensitive is False  # default
        assert context.quality_threshold == 0.7  # default
    
    def test_model_performance_creation(self):
        """Test ModelPerformance dataclass creation."""
        now = datetime.now()
        perf = ModelPerformance(
            model_name="gpt-4o",
            arena_elo=1300.0,
            mteb_score=None,
            internal_score=0.85,
            avg_latency_ms=150.0,
            cost_per_1k_tokens=0.03,
            success_rate=0.98,
            last_updated=now
        )
        
        assert perf.model_name == "gpt-4o"
        assert perf.arena_elo == 1300.0
        assert perf.mteb_score is None
        assert perf.internal_score == 0.85
        assert perf.avg_latency_ms == 150.0
        assert perf.cost_per_1k_tokens == 0.03
        assert perf.success_rate == 0.98
        assert perf.last_updated == now
