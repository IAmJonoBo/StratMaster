"""Tests for Retrieval Benchmarking & Latency Validation."""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from packages.retrieval.src.splade.src.splade.evaluator import (
    SPLADEEvaluator,
    EvalQuery,
    EvalMetrics,
    RetrievalResult,
    is_retrieval_benchmarks_enabled,
)


class TestRetrievalBenchmarkingFeatureFlag:
    """Test retrieval benchmarking feature flag functionality."""
    
    def test_benchmarking_disabled_by_default(self):
        """Test that benchmarking is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert not is_retrieval_benchmarks_enabled()
    
    def test_benchmarking_enabled_when_set(self):
        """Test that benchmarking is enabled when flag is set."""
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "true"}):
            assert is_retrieval_benchmarks_enabled()
        
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "TRUE"}):
            assert is_retrieval_benchmarks_enabled()
    
    def test_benchmarking_disabled_when_false(self):
        """Test that benchmarking is disabled when explicitly set to false."""
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "false"}):
            assert not is_retrieval_benchmarks_enabled()
        
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "invalid"}):
            assert not is_retrieval_benchmarks_enabled()


class TestRetrievalDataStructures:
    """Test retrieval benchmarking data structures."""
    
    def test_eval_query_creation(self):
        """Test EvalQuery dataclass creation."""
        query = EvalQuery(
            query_id="test_001",
            query_text="machine learning applications",
            relevant_docs=["doc1", "doc2", "doc3"],
            relevance_scores={"doc1": 3, "doc2": 2, "doc3": 1}
        )
        
        assert query.query_id == "test_001"
        assert query.query_text == "machine learning applications"
        assert len(query.relevant_docs) == 3
        assert query.relevance_scores["doc1"] == 3
        assert query.relevance_scores["doc2"] == 2
        assert query.relevance_scores["doc3"] == 1
    
    def test_eval_query_without_relevance_scores(self):
        """Test EvalQuery creation without relevance scores."""
        query = EvalQuery(
            query_id="test_002", 
            query_text="data analysis techniques",
            relevant_docs=["doc4", "doc5"]
        )
        
        assert query.query_id == "test_002"
        assert query.relevance_scores is None
        assert len(query.relevant_docs) == 2
    
    def test_retrieval_result_creation(self):
        """Test RetrievalResult dataclass creation."""
        result = RetrievalResult(
            doc_id="doc_123",
            score=0.85,
            rank=1
        )
        
        assert result.doc_id == "doc_123"
        assert result.score == 0.85
        assert result.rank == 1
    
    def test_eval_metrics_creation(self):
        """Test EvalMetrics dataclass creation."""
        metrics = EvalMetrics(
            query_id="test_query",
            ndcg_10=0.75,
            mrr=0.82,
            precision_10=0.7,
            recall_10=0.6,
            latency_ms=150.5,
            retrieved_docs=10,
            relevant_retrieved=7
        )
        
        assert metrics.query_id == "test_query"
        assert metrics.ndcg_10 == 0.75
        assert metrics.mrr == 0.82
        assert metrics.precision_10 == 0.7
        assert metrics.recall_10 == 0.6
        assert metrics.latency_ms == 150.5
        assert metrics.retrieved_docs == 10
        assert metrics.relevant_retrieved == 7


class TestSPLADEEvaluator:
    """Test SPLADEEvaluator functionality."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.eval_data_path = Path(self.temp_dir) / "test_queries.json"
        
        # Create test evaluation data
        test_data = {
            "queries": [
                {
                    "query_id": "test_001",
                    "query_text": "artificial intelligence applications",
                    "relevant_docs": ["doc_001", "doc_003", "doc_007"],
                    "relevance_scores": {"doc_001": 3, "doc_003": 2, "doc_007": 1}
                },
                {
                    "query_id": "test_002",
                    "query_text": "machine learning algorithms",
                    "relevant_docs": ["doc_002", "doc_005"],
                    "relevance_scores": {"doc_002": 3, "doc_005": 2}
                }
            ]
        }
        
        with open(self.eval_data_path, 'w') as f:
            json.dump(test_data, f)
    
    def test_evaluator_initialization(self):
        """Test evaluator initialization with custom eval data."""
        evaluator = SPLADEEvaluator(str(self.eval_data_path))
        
        assert len(evaluator.eval_queries) == 2
        assert evaluator.eval_queries[0].query_id == "test_001"
        assert evaluator.eval_queries[1].query_id == "test_002"
    
    def test_evaluator_loads_sample_data_when_missing(self):
        """Test that evaluator creates sample data when file doesn't exist."""
        missing_path = Path(self.temp_dir) / "missing_queries.json"
        evaluator = SPLADEEvaluator(str(missing_path))
        
        # Should have created sample data
        assert missing_path.exists()
        assert len(evaluator.eval_queries) > 0
        
        # Check sample data structure
        first_query = evaluator.eval_queries[0]
        assert first_query.query_id == "eval_001"
        assert len(first_query.relevant_docs) > 0
    
    def test_ndcg_calculation(self):
        """Test NDCG calculation with graded relevance."""
        evaluator = SPLADEEvaluator(str(self.eval_data_path))
        
        # Create test query with relevance scores
        eval_query = EvalQuery(
            query_id="test_ndcg",
            query_text="test query",
            relevant_docs=["doc1", "doc2", "doc3"],
            relevance_scores={"doc1": 3, "doc2": 2, "doc3": 1}
        )
        
        # Perfect ranking (should give NDCG = 1.0)
        perfect_results = [
            {"doc_id": "doc1", "score": 1.0},
            {"doc_id": "doc2", "score": 0.8},
            {"doc_id": "doc3", "score": 0.6},
            {"doc_id": "doc4", "score": 0.4},  # Irrelevant
            {"doc_id": "doc5", "score": 0.2}   # Irrelevant
        ]
        
        ndcg = evaluator._calculate_ndcg(eval_query, perfect_results, 5)
        assert ndcg == 1.0
        
        # Random ranking (should be < 1.0)
        random_results = [
            {"doc_id": "doc4", "score": 1.0},  # Irrelevant first
            {"doc_id": "doc1", "score": 0.8},  # Relevant second 
            {"doc_id": "doc5", "score": 0.6},  # Irrelevant third
            {"doc_id": "doc2", "score": 0.4},  # Relevant fourth
            {"doc_id": "doc3", "score": 0.2}   # Relevant fifth
        ]
        
        ndcg_random = evaluator._calculate_ndcg(eval_query, random_results, 5)
        assert 0.0 < ndcg_random < 1.0
    
    def test_mrr_calculation(self):
        """Test Mean Reciprocal Rank calculation."""
        evaluator = SPLADEEvaluator(str(self.eval_data_path))
        
        eval_query = EvalQuery(
            query_id="test_mrr",
            query_text="test query", 
            relevant_docs=["doc2", "doc5", "doc8"]
        )
        
        # First relevant doc at position 1 (0-indexed)
        retrieved_docs_1st = ["doc1", "doc2", "doc3", "doc4"]
        mrr_1st = evaluator._calculate_mrr(eval_query, retrieved_docs_1st)
        assert mrr_1st == 1.0 / 2  # 1 / (1+1)
        
        # First relevant doc at position 2 (0-indexed) 
        retrieved_docs_3rd = ["doc1", "doc3", "doc5", "doc4"]
        mrr_3rd = evaluator._calculate_mrr(eval_query, retrieved_docs_3rd)
        assert mrr_3rd == 1.0 / 3  # 1 / (2+1)
        
        # No relevant docs retrieved
        retrieved_docs_none = ["doc1", "doc3", "doc4", "doc6"]
        mrr_none = evaluator._calculate_mrr(eval_query, retrieved_docs_none)
        assert mrr_none == 0.0
    
    def test_query_metrics_calculation(self):
        """Test per-query metrics calculation."""
        evaluator = SPLADEEvaluator(str(self.eval_data_path))
        
        eval_query = EvalQuery(
            query_id="test_metrics",
            query_text="test query",
            relevant_docs=["doc1", "doc2", "doc3"],  # 3 relevant docs
            relevance_scores={"doc1": 3, "doc2": 2, "doc3": 1}
        )
        
        # Results with 2 relevant docs in top 5
        results = [
            {"doc_id": "doc1", "score": 1.0},  # Relevant
            {"doc_id": "doc4", "score": 0.8},  # Not relevant
            {"doc_id": "doc2", "score": 0.6},  # Relevant  
            {"doc_id": "doc5", "score": 0.4},  # Not relevant
            {"doc_id": "doc6", "score": 0.2}   # Not relevant
        ]
        
        metrics = evaluator._calculate_query_metrics(eval_query, results, k=5)
        
        assert metrics.query_id == "test_metrics"
        assert metrics.precision_10 == 2 / 5  # 2 relevant in top 5
        assert metrics.recall_10 == 2 / 3     # 2 of 3 relevant docs found
        assert metrics.retrieved_docs == 5
        assert metrics.relevant_retrieved == 2
        assert metrics.ndcg_10 > 0  # Should have some NDCG score
        assert metrics.mrr == 1.0   # First doc is relevant
    
    @pytest.mark.asyncio
    async def test_quality_gates_checking(self):
        """Test quality gates evaluation."""
        evaluator = SPLADEEvaluator(str(self.eval_data_path))
        
        # Mock overall metrics
        overall_metrics = {
            "avg_ndcg_10": 0.75,
            "avg_mrr": 0.85,
            "latency_stats": {"p95_ms": 150}
        }
        
        # Test gates with achievable thresholds
        thresholds = {
            "ndcg_10": 0.7,
            "mrr": 0.8,
            "latency_p95": 200
        }
        
        gates = evaluator._check_quality_gates(overall_metrics, thresholds)
        
        assert gates["ndcg_10"]["passed"] is True
        assert gates["mrr"]["passed"] is True
        assert gates["latency_p95"]["passed"] is True
        assert gates["overall"]["passed"] is True
        assert gates["overall"]["gates_passed"] == 3
    
    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self):
        """Test complete evaluation workflow."""
        evaluator = SPLADEEvaluator(str(self.eval_data_path))
        
        # Mock retrieval function that returns some results
        async def mock_retrieval(query_text: str, k: int = 10):
            return [
                {"doc_id": "doc_001", "score": 0.9, "rank": 0},  # Relevant for test_001
                {"doc_id": "doc_002", "score": 0.8, "rank": 1},  # Relevant for test_002
                {"doc_id": "doc_999", "score": 0.7, "rank": 2},  # Not relevant
                {"doc_id": "doc_003", "score": 0.6, "rank": 3},  # Relevant for test_001
                {"doc_id": "doc_005", "score": 0.5, "rank": 4},  # Relevant for test_002
            ]
        
        # Run evaluation
        results = await evaluator.evaluate_retrieval_system(
            mock_retrieval,
            k=10,
            quality_threshold={"ndcg_10": 0.5, "mrr": 0.5, "latency_p95": 500}
        )
        
        # Check results structure
        assert "overall_metrics" in results or "overall" in results
        assert "per_query" in results
        assert "quality_gates" in results
        
        # Should have results for both test queries
        per_query = results["per_query"]
        assert len(per_query) == 2
        
        query_ids = [q["query_id"] for q in per_query]
        assert "test_001" in query_ids
        assert "test_002" in query_ids


class TestRetrievalBenchmarkingIntegration:
    """Test integration between retrieval benchmarking components."""
    
    def test_performance_api_integration_disabled(self):
        """Test performance API behavior when benchmarking is disabled."""
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "false"}):
            # Import here to test with flag disabled
            from stratmaster_api.performance import PerformanceBenchmark
            
            benchmark = PerformanceBenchmark()
            # Should not raise exceptions even with benchmarking disabled
            assert benchmark is not None
    
    def test_performance_api_integration_enabled(self):
        """Test performance API behavior when benchmarking is enabled.""" 
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "true"}):
            # Should be able to import and create benchmark instance
            from stratmaster_api.performance import PerformanceBenchmark
            
            benchmark = PerformanceBenchmark()
            assert benchmark is not None
    
    def test_graceful_degradation_missing_dependencies(self):
        """Test graceful degradation when retrieval dependencies are missing."""
        with patch.dict(os.environ, {"ENABLE_RETRIEVAL_BENCHMARKS": "true"}):
            with patch("stratmaster_api.performance.SPLADEEvaluator", side_effect=ImportError("splade not available")):
                # Should not raise exceptions
                from stratmaster_api.performance import PerformanceBenchmark
                
                benchmark = PerformanceBenchmark()
                assert benchmark is not None