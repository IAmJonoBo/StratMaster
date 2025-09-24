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
    """Combines dense (Qdrant), sparse (SPLADE), and BM25 scores with configurable fusion methods."""
    
    def __init__(
        self,
        sparse_weight: float = 0.2,
        dense_weight: float = 0.5,
        bm25_weight: float = 0.3,
        fusion_method: str = "weighted_sum",  # "weighted_sum" or "rrf"
        rrf_k: int = 60,  # RRF parameter
        title_boost: float = 2.0,
        abstract_boost: float = 1.5,
        content_boost: float = 1.0,
    ) -> None:
        """Initialize hybrid scorer with fusion weights.
        
        Args:
            sparse_weight: Weight for SPLADE sparse scores (default 0.2)
            dense_weight: Weight for dense vector scores (default 0.5)
            bm25_weight: Weight for BM25 lexical scores (default 0.3)
            fusion_method: Fusion method - "weighted_sum" or "rrf" (Reciprocal Rank Fusion)
            rrf_k: RRF parameter for rank normalization (default 60)
            title_boost: Boost factor for title field matches (default 2.0)
            abstract_boost: Boost factor for abstract/summary matches (default 1.5)
            content_boost: Boost factor for content matches (default 1.0)
        """
        if fusion_method == "weighted_sum" and abs(sparse_weight + dense_weight + bm25_weight - 1.0) > 1e-6:
            logger.warning(
                f"Weights don't sum to 1.0: sparse={sparse_weight}, dense={dense_weight}, bm25={bm25_weight}"
            )
        
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.fusion_method = fusion_method
        self.rrf_k = rrf_k
        self.title_boost = title_boost
        self.abstract_boost = abstract_boost
        self.content_boost = content_boost
    
    def score(
        self,
        sparse_results: list[dict[str, Any]],
        dense_results: list[dict[str, Any]],
        bm25_results: list[dict[str, Any]] | None = None,
        normalize: bool = True,
    ) -> list[HybridScore]:
        """Combine sparse, dense, and BM25 retrieval results.
        
        Args:
            sparse_results: SPLADE sparse results with scores
            dense_results: Qdrant vector results with scores
            bm25_results: BM25 lexical results with scores (optional)
            normalize: Whether to normalize scores to [0,1] range
            
        Returns:
            List of HybridScore objects sorted by hybrid_score descending
        """
        if self.fusion_method == "rrf":
            return self._score_with_rrf(sparse_results, dense_results, bm25_results, normalize)
        else:
            return self._score_with_weighted_sum(sparse_results, dense_results, bm25_results, normalize)
    
    def _score_with_weighted_sum(
        self,
        sparse_results: list[dict[str, Any]],
        dense_results: list[dict[str, Any]],
        bm25_results: list[dict[str, Any]] | None = None,
        normalize: bool = True,
    ) -> list[HybridScore]:
        """Score using weighted sum fusion (original implementation enhanced)."""
        # Create lookup maps for efficient merging
        sparse_lookup = {result["doc_id"]: result for result in sparse_results}
        dense_lookup = {result["doc_id"]: result for result in dense_results}
        bm25_lookup = {}
        if bm25_results:
            bm25_lookup = {result["doc_id"]: result for result in bm25_results}
        
        # Get all unique document IDs
        all_doc_ids = set(sparse_lookup.keys()) | set(dense_lookup.keys()) | set(bm25_lookup.keys())
        
        hybrid_scores = []
        
        for doc_id in all_doc_ids:
            sparse_result = sparse_lookup.get(doc_id, {})
            dense_result = dense_lookup.get(doc_id, {})
            bm25_result = bm25_lookup.get(doc_id, {})
            
            # Extract base scores (0 if document not found in that index)
            sparse_score = sparse_result.get("score", 0.0)
            dense_score = dense_result.get("score", 0.0)
            bm25_score = bm25_result.get("score", 0.0)
            
            # Apply field-specific boosts based on match location
            field_boost = self._calculate_field_boost(sparse_result, dense_result, bm25_result)
            
            # Calculate weighted hybrid score
            if bm25_results:
                hybrid_score = (
                    self.sparse_weight * sparse_score + 
                    self.dense_weight * dense_score +
                    self.bm25_weight * bm25_score
                ) * field_boost
            else:
                # Adjust weights when no BM25 results
                total_weight = self.sparse_weight + self.dense_weight
                adjusted_sparse = self.sparse_weight / total_weight
                adjusted_dense = self.dense_weight / total_weight
                hybrid_score = (
                    adjusted_sparse * sparse_score + 
                    adjusted_dense * dense_score
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
    
    def _score_with_rrf(
        self,
        sparse_results: list[dict[str, Any]],
        dense_results: list[dict[str, Any]],
        bm25_results: list[dict[str, Any]] | None = None,
        normalize: bool = True,
    ) -> list[HybridScore]:
        """Score using Reciprocal Rank Fusion (RRF) method."""
        # Create rank-ordered lists for each retrieval method
        sparse_ranks = {result["doc_id"]: idx + 1 for idx, result in enumerate(sparse_results)}
        dense_ranks = {result["doc_id"]: idx + 1 for idx, result in enumerate(dense_results)}
        bm25_ranks = {}
        if bm25_results:
            bm25_ranks = {result["doc_id"]: idx + 1 for idx, result in enumerate(bm25_results)}
        
        # Get all unique document IDs
        sparse_lookup = {result["doc_id"]: result for result in sparse_results}
        dense_lookup = {result["doc_id"]: result for result in dense_results}
        bm25_lookup = {}
        if bm25_results:
            bm25_lookup = {result["doc_id"]: result for result in bm25_results}
        
        all_doc_ids = set(sparse_ranks.keys()) | set(dense_ranks.keys()) | set(bm25_ranks.keys())
        
        hybrid_scores = []
        
        for doc_id in all_doc_ids:
            # Calculate RRF score: sum of 1/(k + rank) for each retrieval method
            rrf_score = 0.0
            
            if doc_id in sparse_ranks:
                rrf_score += 1.0 / (self.rrf_k + sparse_ranks[doc_id])
            
            if doc_id in dense_ranks:
                rrf_score += 1.0 / (self.rrf_k + dense_ranks[doc_id])
            
            if doc_id in bm25_ranks:
                rrf_score += 1.0 / (self.rrf_k + bm25_ranks[doc_id])
            
            # Apply field-specific boosts
            sparse_result = sparse_lookup.get(doc_id, {})
            dense_result = dense_lookup.get(doc_id, {})
            bm25_result = bm25_lookup.get(doc_id, {})
            
            field_boost = self._calculate_field_boost(sparse_result, dense_result, bm25_result)
            rrf_score *= field_boost
            
            # Extract original scores for tracking
            sparse_score = sparse_result.get("score", 0.0)
            dense_score = dense_result.get("score", 0.0)
            
            hybrid_scores.append(HybridScore(
                doc_id=doc_id,
                sparse_score=sparse_score,
                dense_score=dense_score,
                hybrid_score=rrf_score,
                title_boost=field_boost if "title" in sparse_result.get("matched_fields", []) else 1.0,
                content_boost=field_boost if field_boost == self.content_boost else 1.0,
            ))
        
        # Sort by RRF score descending
        hybrid_scores.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        # Optional normalization to [0,1] range
        if normalize and hybrid_scores:
            max_score = hybrid_scores[0].hybrid_score
            if max_score > 0:
                for score in hybrid_scores:
                    score.hybrid_score = score.hybrid_score / max_score
        
        return hybrid_scores
    
    def _calculate_field_boost(
        self, 
        sparse_result: dict[str, Any], 
        dense_result: dict[str, Any],
        bm25_result: dict[str, Any] | None = None
    ) -> float:
        """Calculate field-specific boost based on match locations across all retrieval methods."""
        field_boost = 1.0
        
        # Check for title matches in any retrieval method
        for result in [sparse_result, dense_result, bm25_result or {}]:
            matched_fields = result.get("matched_fields", [])
            if "title" in matched_fields:
                field_boost = max(field_boost, self.title_boost)
            elif "summary" in matched_fields:
                field_boost = max(field_boost, self.abstract_boost)
            else:
                field_boost = max(field_boost, self.content_boost)
        
        return field_boost
    
    def update_weights(
        self, 
        sparse_weight: float, 
        dense_weight: float, 
        bm25_weight: float | None = None
    ) -> None:
        """Update fusion weights for A/B testing or policy tuning."""
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight
        if bm25_weight is not None:
            self.bm25_weight = bm25_weight
        
        if self.fusion_method == "weighted_sum":
            total_weight = self.sparse_weight + self.dense_weight + self.bm25_weight
            logger.info(f"Updated weights: sparse={sparse_weight}, dense={dense_weight}, bm25={self.bm25_weight} (total={total_weight})")
        else:
            logger.info(f"Updated RRF weights: sparse={sparse_weight}, dense={dense_weight}, bm25={self.bm25_weight}")


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
        
        # Combine and re-sort by removing duplicates by doc_id
        seen_doc_ids = set()
        combined = []
        for result in top_results + disagreement_sample:
            if result.doc_id not in seen_doc_ids:
                seen_doc_ids.add(result.doc_id)
                combined.append(result)
        combined.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        return combined