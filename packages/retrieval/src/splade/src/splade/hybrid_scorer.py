"""Hybrid search scorer combining dense (Qdrant) and sparse (SPLADE) scores."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class HybridScore:
    """Combined search score with component breakdown."""
    
    doc_id: str
    sparse_score: float
    dense_score: float
    hybrid_score: float
    title_boost: float = 1.0
    content_boost: float = 1.0


class SpladeHybridScorer:
    """Combines dense (Qdrant) and sparse (SPLADE) scores with configurable weights."""
    
    def __init__(
        self,
        sparse_weight: float = 0.3,
        dense_weight: float = 0.7,
        title_boost: float = 2.0,
        abstract_boost: float = 1.5,
        content_boost: float = 1.0,
    ) -> None:
        """Initialize hybrid scorer with fusion weights.
        
        Args:
            sparse_weight: Weight for SPLADE sparse scores (default 0.3)
            dense_weight: Weight for dense vector scores (default 0.7)  
            title_boost: Boost factor for title field matches (default 2.0)
            abstract_boost: Boost factor for abstract/summary matches (default 1.5)
            content_boost: Boost factor for content matches (default 1.0)
        """
        if abs(sparse_weight + dense_weight - 1.0) > 1e-6:
            logger.warning(
                f"Weights don't sum to 1.0: sparse={sparse_weight}, dense={dense_weight}"
            )
        
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight
        self.title_boost = title_boost
        self.abstract_boost = abstract_boost
        self.content_boost = content_boost
    
    def score(
        self,
        sparse_results: list[dict[str, Any]],
        dense_results: list[dict[str, Any]],
        normalize: bool = True,
    ) -> list[HybridScore]:
        """Combine sparse and dense retrieval results.
        
        Args:
            sparse_results: SPLADE/BM25 results with scores
            dense_results: Qdrant vector results with scores
            normalize: Whether to normalize scores to [0,1] range
            
        Returns:
            List of HybridScore objects sorted by hybrid_score descending
        """
        # Create lookup maps for efficient merging
        sparse_lookup = {result["doc_id"]: result for result in sparse_results}
        dense_lookup = {result["doc_id"]: result for result in dense_results}
        
        # Get all unique document IDs
        all_doc_ids = set(sparse_lookup.keys()) | set(dense_lookup.keys())
        
        hybrid_scores = []
        
        for doc_id in all_doc_ids:
            sparse_result = sparse_lookup.get(doc_id, {})
            dense_result = dense_lookup.get(doc_id, {})
            
            # Extract base scores (0 if document not found in that index)
            sparse_score = sparse_result.get("score", 0.0)
            dense_score = dense_result.get("score", 0.0)
            
            # Apply field-specific boosts based on match location
            field_boost = 1.0
            if sparse_result.get("matched_fields"):
                if "title" in sparse_result["matched_fields"]:
                    field_boost = max(field_boost, self.title_boost)
                elif "summary" in sparse_result["matched_fields"]:
                    field_boost = max(field_boost, self.abstract_boost)
                else:
                    field_boost = max(field_boost, self.content_boost)
            
            # Calculate weighted hybrid score
            hybrid_score = (
                self.sparse_weight * sparse_score + 
                self.dense_weight * dense_score
            ) * field_boost
            
            hybrid_scores.append(HybridScore(
                doc_id=doc_id,
                sparse_score=sparse_score,
                dense_score=dense_score,
                hybrid_score=hybrid_score,
                title_boost=field_boost if "title" in sparse_result.get("matched_fields", []) else 1.0,
                content_boost=field_boost if field_boost == self.content_boost else 1.0,
            ))
        
        # Sort by hybrid score descending
        hybrid_scores.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        # Optional normalization to [0,1] range
        if normalize and hybrid_scores:
            max_score = hybrid_scores[0].hybrid_score
            if max_score > 0:
                for score in hybrid_scores:
                    score.hybrid_score = score.hybrid_score / max_score
        
        return hybrid_scores
    
    def update_weights(self, sparse_weight: float, dense_weight: float) -> None:
        """Update fusion weights for A/B testing or policy tuning."""
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight
        logger.info(f"Updated weights: sparse={sparse_weight}, dense={dense_weight}")


class RetrievalBudget:
    """Controls retrieval resource usage with configurable limits."""
    
    def __init__(
        self,
        max_passages: int = 50,
        max_tokens: int = 8000,
        enable_disagreement_sampling: bool = False,
        disagreement_threshold: float = 0.3,
    ) -> None:
        """Initialize retrieval budget controls.
        
        Args:
            max_passages: Maximum number of passages to retrieve
            max_tokens: Maximum total tokens in retrieved passages
            enable_disagreement_sampling: Whether to use disagreement sampling
            disagreement_threshold: Score difference threshold for disagreement sampling
        """
        self.max_passages = max_passages
        self.max_tokens = max_tokens
        self.enable_disagreement_sampling = enable_disagreement_sampling
        self.disagreement_threshold = disagreement_threshold
    
    def apply_budget(
        self,
        hybrid_scores: list[HybridScore],
        passage_texts: dict[str, str],
    ) -> list[HybridScore]:
        """Apply budget constraints to retrieval results.
        
        Args:
            hybrid_scores: Scored retrieval results
            passage_texts: Map of doc_id to passage text
            
        Returns:
            Filtered results within budget constraints
        """
        # Start with passage count limit
        results = hybrid_scores[:self.max_passages]
        
        # Apply token budget
        if self.max_tokens > 0:
            filtered_results = []
            total_tokens = 0
            
            for score in results:
                passage_text = passage_texts.get(score.doc_id, "")
                # Rough token estimation: ~4 chars per token
                passage_tokens = len(passage_text) // 4
                
                if total_tokens + passage_tokens <= self.max_tokens:
                    filtered_results.append(score)
                    total_tokens += passage_tokens
                else:
                    break
            
            results = filtered_results
        
        # Apply disagreement sampling if enabled
        if self.enable_disagreement_sampling and len(results) > 2:
            results = self._apply_disagreement_sampling(results)
        
        logger.info(f"Applied budget: {len(results)} passages selected")
        return results
    
    def _apply_disagreement_sampling(
        self, 
        hybrid_scores: list[HybridScore]
    ) -> list[HybridScore]:
        """Sample passages where sparse and dense scoring disagree."""
        disagreement_scores = []
        
        for score in hybrid_scores:
            # Calculate disagreement as absolute difference in ranking preference
            sparse_rank = score.sparse_score
            dense_rank = score.dense_score
            
            # Normalize to [0,1] for comparison
            if sparse_rank > 0 and dense_rank > 0:
                disagreement = abs(sparse_rank - dense_rank) / max(sparse_rank, dense_rank)
                if disagreement >= self.disagreement_threshold:
                    disagreement_scores.append(score)
        
        # Include top results plus disagreement samples
        top_results = hybrid_scores[:len(hybrid_scores)//2]
        disagreement_sample = disagreement_scores[:len(hybrid_scores)//4]
        
        # Combine and re-sort
        combined = list(set(top_results + disagreement_sample))
        combined.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        return combined