"""Tests for SPLADE hybrid search scoring."""

import pytest
from splade.hybrid_scorer import HybridScore, RetrievalBudget, SpladeHybridScorer


class TestSpladeHybridScorer:
    """Test hybrid scoring functionality."""

    def test_basic_scoring(self):
        """Test basic hybrid score calculation."""
        scorer = SpladeHybridScorer(sparse_weight=0.3, dense_weight=0.7)
        
        sparse_results = [
            {"doc_id": "doc1", "score": 0.8, "matched_fields": ["title"]},
            {"doc_id": "doc2", "score": 0.6, "matched_fields": ["content"]},
        ]
        dense_results = [
            {"doc_id": "doc1", "score": 0.5},
            {"doc_id": "doc2", "score": 0.9},
        ]
        
        scores = scorer.score(sparse_results, dense_results)
        
        assert len(scores) == 2
        assert scores[0].doc_id in ["doc1", "doc2"]
        assert all(0 <= score.hybrid_score <= 10 for score in scores)  # Allow for boosts
        
        # Check score components are preserved
        for score in scores:
            assert score.sparse_score >= 0
            assert score.dense_score >= 0

    def test_field_boosts(self):
        """Test field-specific boost application."""
        scorer = SpladeHybridScorer(
            sparse_weight=0.5, 
            dense_weight=0.5,
            title_boost=2.0,
            abstract_boost=1.5,
            content_boost=1.0
        )
        
        sparse_results = [
            {"doc_id": "title_doc", "score": 0.5, "matched_fields": ["title"]},
            {"doc_id": "summary_doc", "score": 0.5, "matched_fields": ["summary"]},
            {"doc_id": "content_doc", "score": 0.5, "matched_fields": ["content"]},
        ]
        dense_results = [
            {"doc_id": "title_doc", "score": 0.5},
            {"doc_id": "summary_doc", "score": 0.5},
            {"doc_id": "content_doc", "score": 0.5},
        ]
        
        scores = scorer.score(sparse_results, dense_results)
        score_dict = {s.doc_id: s for s in scores}
        
        # Title match should have highest score due to boost
        assert score_dict["title_doc"].hybrid_score > score_dict["summary_doc"].hybrid_score
        assert score_dict["summary_doc"].hybrid_score > score_dict["content_doc"].hybrid_score

    def test_missing_results(self):
        """Test handling of documents missing from one index."""
        scorer = SpladeHybridScorer()
        
        sparse_results = [{"doc_id": "doc1", "score": 0.8}]
        dense_results = [{"doc_id": "doc2", "score": 0.7}]
        
        scores = scorer.score(sparse_results, dense_results)
        
        assert len(scores) == 2
        score_dict = {s.doc_id: s for s in scores}
        
        # doc1 should have sparse score but zero dense score
        assert score_dict["doc1"].sparse_score == 0.8
        assert score_dict["doc1"].dense_score == 0.0
        
        # doc2 should have dense score but zero sparse score  
        assert score_dict["doc2"].sparse_score == 0.0
        assert score_dict["doc2"].dense_score == 0.7

    def test_normalization(self):
        """Test score normalization to [0,1] range."""
        scorer = SpladeHybridScorer()
        
        sparse_results = [
            {"doc_id": "doc1", "score": 10.0},
            {"doc_id": "doc2", "score": 5.0},
        ]
        dense_results = [
            {"doc_id": "doc1", "score": 8.0},
            {"doc_id": "doc2", "score": 2.0},
        ]
        
        scores = scorer.score(sparse_results, dense_results, normalize=True)
        
        # After normalization, highest score should be 1.0
        assert scores[0].hybrid_score == 1.0
        assert all(0 <= score.hybrid_score <= 1.0 for score in scores)

    def test_weight_updates(self):
        """Test dynamic weight updating."""
        scorer = SpladeHybridScorer(sparse_weight=0.5, dense_weight=0.5)
        
        scorer.update_weights(0.2, 0.8)
        
        assert scorer.sparse_weight == 0.2
        assert scorer.dense_weight == 0.8


class TestRetrievalBudget:
    """Test retrieval budget controls."""

    def test_passage_limit(self):
        """Test maximum passage limit enforcement."""
        budget = RetrievalBudget(max_passages=3, max_tokens=0)
        
        scores = [
            HybridScore(f"doc{i}", 0.5, 0.5, 1.0 - i*0.1) 
            for i in range(5)
        ]
        passage_texts = {f"doc{i}": "short text" for i in range(5)}
        
        filtered = budget.apply_budget(scores, passage_texts)
        
        assert len(filtered) == 3
        # Should keep highest scoring passages
        assert filtered[0].hybrid_score >= filtered[1].hybrid_score >= filtered[2].hybrid_score

    def test_token_budget(self):
        """Test token budget enforcement."""
        budget = RetrievalBudget(max_passages=10, max_tokens=100)
        
        scores = [
            HybridScore(f"doc{i}", 0.5, 0.5, 1.0 - i*0.1)
            for i in range(5)
        ]
        # Create passages with different lengths
        passage_texts = {
            "doc0": "short",  # ~1 token
            "doc1": "medium length passage" * 5,  # ~15 tokens  
            "doc2": "very long passage" * 20,  # ~60 tokens
            "doc3": "another long passage" * 20,  # ~60 tokens (would exceed budget)
            "doc4": "final passage"  # ~2 tokens
        }
        
        filtered = budget.apply_budget(scores, passage_texts)
        
        # Should stop before exceeding token budget
        total_estimated_tokens = sum(
            len(passage_texts[score.doc_id]) // 4 
            for score in filtered
        )
        assert total_estimated_tokens <= 100

    def test_disagreement_sampling(self):
        """Test disagreement sampling functionality.""" 
        budget = RetrievalBudget(
            max_passages=10, 
            enable_disagreement_sampling=True,
            disagreement_threshold=0.3
        )
        
        # Create scores with high disagreement between sparse/dense
        scores = [
            HybridScore("doc1", 0.9, 0.1, 0.5),  # High sparse, low dense
            HybridScore("doc2", 0.1, 0.9, 0.5),  # Low sparse, high dense  
            HybridScore("doc3", 0.5, 0.5, 0.5),  # Balanced
        ]
        passage_texts = {f"doc{i+1}": "text" for i in range(3)}
        
        filtered = budget.apply_budget(scores, passage_texts)
        
        # Should include disagreement samples
        assert len(filtered) >= 1
        assert any(
            abs(score.sparse_score - score.dense_score) >= 0.3 
            for score in filtered
        )

    def test_empty_input(self):
        """Test handling of empty input."""
        budget = RetrievalBudget()
        
        filtered = budget.apply_budget([], {})
        
        assert filtered == []


class TestHybridScore:
    """Test HybridScore dataclass."""

    def test_creation(self):
        """Test HybridScore creation."""
        score = HybridScore(
            doc_id="test_doc",
            sparse_score=0.7,
            dense_score=0.8,
            hybrid_score=0.75
        )
        
        assert score.doc_id == "test_doc"
        assert score.sparse_score == 0.7
        assert score.dense_score == 0.8
        assert score.hybrid_score == 0.75
        assert score.title_boost == 1.0  # default
        assert score.content_boost == 1.0  # default

    def test_with_boosts(self):
        """Test HybridScore with custom boosts."""
        score = HybridScore(
            doc_id="test_doc",
            sparse_score=0.7,
            dense_score=0.8, 
            hybrid_score=0.75,
            title_boost=2.0,
            content_boost=1.5
        )
        
        assert score.title_boost == 2.0
        assert score.content_boost == 1.5


@pytest.fixture
def sample_sparse_results():
    """Sample sparse search results."""
    return [
        {"doc_id": "doc1", "score": 0.8, "matched_fields": ["title"]},
        {"doc_id": "doc2", "score": 0.6, "matched_fields": ["content"]},
        {"doc_id": "doc3", "score": 0.4, "matched_fields": ["summary"]},
    ]


@pytest.fixture  
def sample_dense_results():
    """Sample dense search results."""
    return [
        {"doc_id": "doc1", "score": 0.3},
        {"doc_id": "doc2", "score": 0.9},
        {"doc_id": "doc4", "score": 0.7},
    ]


def test_integration_scenario(sample_sparse_results, sample_dense_results):
    """Test complete integration scenario."""
    scorer = SpladeHybridScorer(sparse_weight=0.4, dense_weight=0.6)
    
    # Score documents
    scores = scorer.score(sample_sparse_results, sample_dense_results)
    
    # Apply budget
    budget = RetrievalBudget(max_passages=3, max_tokens=200)
    passage_texts = {
        "doc1": "Title document with relevant content",
        "doc2": "Content document with detailed information",
        "doc3": "Summary document with overview",
        "doc4": "Dense-only document"
    }
    
    filtered_scores = budget.apply_budget(scores, passage_texts)
    
    # Verify results
    assert len(filtered_scores) <= 3
    assert all(score.hybrid_score >= 0 for score in filtered_scores)
    
    # Check that results are sorted by hybrid score
    for i in range(len(filtered_scores) - 1):
        assert filtered_scores[i].hybrid_score >= filtered_scores[i + 1].hybrid_score