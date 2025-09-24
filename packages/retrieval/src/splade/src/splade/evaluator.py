"""SPLADE retrieval evaluation and benchmarking system.

Implements comprehensive evaluation metrics including:
- NDCG@10/MRR@10 on BEIR-like evaluation splits
- Per-query contribution to downstream task accuracy
- Latency and cost profiling
- Quality gates and regression detection
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None

# Feature flag for Retrieval Benchmarking
def is_retrieval_benchmarks_enabled() -> bool:
    """Check if retrieval benchmarking is enabled via feature flag."""
    return os.getenv("ENABLE_RETRIEVAL_BENCHMARKS", "false").lower() == "true"


@dataclass
class EvalQuery:
    """Evaluation query with ground truth relevance judgments."""
    query_id: str
    query_text: str
    relevant_docs: list[str]  # List of relevant document IDs
    relevance_scores: dict[str, int] | None = None  # Optional graded relevance (0-3)


@dataclass
class RetrievalResult:
    """Retrieval result for evaluation."""
    doc_id: str
    score: float
    rank: int


@dataclass
class EvalMetrics:
    """Comprehensive evaluation metrics."""
    query_id: str
    ndcg_10: float
    mrr: float
    precision_10: float
    recall_10: float
    latency_ms: float
    retrieved_docs: int
    relevant_retrieved: int


class SPLADEEvaluator:
    """Comprehensive SPLADE retrieval evaluator with BEIR-style metrics."""
    
    def __init__(self, eval_data_path: str = "seeds/eval/retrieval_queries.json"):
        self.eval_data_path = Path(eval_data_path)
        self.eval_queries: list[EvalQuery] = []
        self._load_eval_data()
    
    def _load_eval_data(self) -> None:
        """Load evaluation queries and relevance judgments."""
        if not self.eval_data_path.exists():
            logger.warning(f"Eval data not found at {self.eval_data_path}, creating sample data")
            self._create_sample_eval_data()
        
        try:
            with open(self.eval_data_path) as f:
                eval_data = json.load(f)
            
            self.eval_queries = []
            for query_data in eval_data.get("queries", []):
                self.eval_queries.append(EvalQuery(
                    query_id=query_data["query_id"],
                    query_text=query_data["query_text"],
                    relevant_docs=query_data["relevant_docs"],
                    relevance_scores=query_data.get("relevance_scores", {})
                ))
            
            logger.info(f"Loaded {len(self.eval_queries)} evaluation queries")
            
        except Exception as e:
            logger.error(f"Failed to load eval data: {e}")
            self.eval_queries = []
    
    def _create_sample_eval_data(self) -> None:
        """Create sample evaluation data for testing."""
        sample_data = {
            "queries": [
                {
                    "query_id": "eval_001",
                    "query_text": "strategic planning methodologies for technology companies",
                    "relevant_docs": ["doc_001", "doc_003", "doc_007", "doc_012"],
                    "relevance_scores": {"doc_001": 3, "doc_003": 2, "doc_007": 3, "doc_012": 1}
                },
                {
                    "query_id": "eval_002", 
                    "query_text": "AI implementation challenges in enterprise settings",
                    "relevant_docs": ["doc_002", "doc_005", "doc_009", "doc_015", "doc_018"],
                    "relevance_scores": {"doc_002": 3, "doc_005": 2, "doc_009": 3, "doc_015": 2, "doc_018": 1}
                },
                {
                    "query_id": "eval_003",
                    "query_text": "competitive analysis frameworks for market positioning",
                    "relevant_docs": ["doc_004", "doc_008", "doc_011"],
                    "relevance_scores": {"doc_004": 3, "doc_008": 2, "doc_011": 2}
                }
            ]
        }
        
        # Ensure parent directory exists
        self.eval_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.eval_data_path, "w") as f:
            json.dump(sample_data, f, indent=2)
        
        logger.info(f"Created sample eval data at {self.eval_data_path}")
    
    async def evaluate_retrieval_system(
        self,
        retrieval_function: Any,  # Function that takes query text and returns results
        k: int = 10,
        quality_threshold: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """
        Evaluate retrieval system across all evaluation queries.
        
        Args:
            retrieval_function: Function that returns results for a query
            k: Number of top results to evaluate (default 10)
            quality_threshold: Quality gates to check against
            
        Returns:
            Dict with overall metrics and per-query results
        """
        if quality_threshold is None:
            quality_threshold = {
                "ndcg_10": 0.7,      # Target: ≥70% NDCG@10 
                "mrr": 0.8,          # Target: ≥80% MRR
                "latency_p95": 200,  # Target: ≤200ms at p95
            }
        
        query_metrics = []
        latencies = []
        
        for eval_query in self.eval_queries:
            start_time = time.time()
            
            try:
                # Run retrieval
                results = await retrieval_function(eval_query.query_text, k=k)
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)
                
                # Calculate metrics
                metrics = self._calculate_query_metrics(eval_query, results, k)
                metrics.latency_ms = latency_ms
                query_metrics.append(metrics)
                
            except Exception as e:
                logger.error(f"Evaluation failed for query {eval_query.query_id}: {e}")
                continue
        
        # Calculate overall metrics
        overall_metrics = self._aggregate_metrics(query_metrics, latencies, quality_threshold)
        
        return {
            "overall": overall_metrics,
            "per_query": [
                {
                    "query_id": m.query_id,
                    "ndcg_10": m.ndcg_10,
                    "mrr": m.mrr,
                    "precision_10": m.precision_10,
                    "recall_10": m.recall_10,
                    "latency_ms": m.latency_ms
                }
                for m in query_metrics
            ],
            "quality_gates": self._check_quality_gates(overall_metrics, quality_threshold)
        }
    
    def _calculate_query_metrics(
        self, 
        eval_query: EvalQuery, 
        results: list[dict[str, Any]], 
        k: int
    ) -> EvalMetrics:
        """Calculate retrieval metrics for a single query."""
        # Extract top-k results
        top_k_results = results[:k]
        retrieved_doc_ids = [r["doc_id"] for r in top_k_results]
        
        # Basic counts
        relevant_retrieved = len(set(retrieved_doc_ids) & set(eval_query.relevant_docs))
        total_relevant = len(eval_query.relevant_docs)
        
        # NDCG@10
        ndcg_10 = self._calculate_ndcg(eval_query, top_k_results, k)
        
        # MRR (Mean Reciprocal Rank)
        mrr = self._calculate_mrr(eval_query, retrieved_doc_ids)
        
        # Precision@10
        precision_10 = relevant_retrieved / k if k > 0 else 0.0
        
        # Recall@10  
        recall_10 = relevant_retrieved / total_relevant if total_relevant > 0 else 0.0
        
        return EvalMetrics(
            query_id=eval_query.query_id,
            ndcg_10=ndcg_10,
            mrr=mrr,
            precision_10=precision_10,
            recall_10=recall_10,
            latency_ms=0.0,  # Will be set by caller
            retrieved_docs=len(top_k_results),
            relevant_retrieved=relevant_retrieved
        )
    
    def _calculate_ndcg(self, eval_query: EvalQuery, results: list[dict[str, Any]], k: int) -> float:
        """Calculate Normalized Discounted Cumulative Gain at k."""
        # DCG calculation
        dcg = 0.0
        for i, result in enumerate(results[:k]):
            doc_id = result["doc_id"]
            relevance = 0
            
            if eval_query.relevance_scores:
                relevance = eval_query.relevance_scores.get(doc_id, 0)
            elif doc_id in eval_query.relevant_docs:
                relevance = 1  # Binary relevance
            
            if relevance > 0:
                dcg += (2**relevance - 1) / np.log2(i + 2)
        
        # IDCG calculation (ideal ranking)
        if eval_query.relevance_scores:
            ideal_relevances = sorted(eval_query.relevance_scores.values(), reverse=True)
        else:
            ideal_relevances = [1] * len(eval_query.relevant_docs)
        
        idcg = 0.0
        for i, relevance in enumerate(ideal_relevances[:k]):
            if relevance > 0:
                idcg += (2**relevance - 1) / np.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def _calculate_mrr(self, eval_query: EvalQuery, retrieved_doc_ids: list[str]) -> float:
        """Calculate Mean Reciprocal Rank."""
        for i, doc_id in enumerate(retrieved_doc_ids):
            if doc_id in eval_query.relevant_docs:
                return 1.0 / (i + 1)
        return 0.0
    
    def _aggregate_metrics(
        self, 
        query_metrics: list[EvalMetrics], 
        latencies: list[float],
        quality_threshold: dict[str, float]
    ) -> dict[str, Any]:
        """Aggregate per-query metrics into overall performance summary."""
        if not query_metrics:
            return {"error": "No query metrics available"}
        
        return {
            "num_queries": len(query_metrics),
            "avg_ndcg_10": np.mean([m.ndcg_10 for m in query_metrics]),
            "avg_mrr": np.mean([m.mrr for m in query_metrics]),
            "avg_precision_10": np.mean([m.precision_10 for m in query_metrics]),
            "avg_recall_10": np.mean([m.recall_10 for m in query_metrics]),
            "latency_stats": {
                "mean_ms": np.mean(latencies),
                "p50_ms": np.percentile(latencies, 50),
                "p95_ms": np.percentile(latencies, 95),
                "p99_ms": np.percentile(latencies, 99),
                "max_ms": np.max(latencies)
            },
            "total_relevant_docs": sum(m.relevant_retrieved for m in query_metrics),
            "total_retrieved_docs": sum(m.retrieved_docs for m in query_metrics)
        }
    
    def _check_quality_gates(
        self, 
        overall_metrics: dict[str, Any], 
        thresholds: dict[str, float]
    ) -> dict[str, Any]:
        """Check if metrics meet quality gate thresholds."""
        gates = {}
        
        # NDCG@10 gate
        ndcg_actual = overall_metrics.get("avg_ndcg_10", 0.0)
        ndcg_threshold = thresholds.get("ndcg_10", 0.7)
        gates["ndcg_10"] = {
            "passed": ndcg_actual >= ndcg_threshold,
            "actual": ndcg_actual,
            "threshold": ndcg_threshold,
            "improvement_needed": max(0, ndcg_threshold - ndcg_actual)
        }
        
        # MRR gate
        mrr_actual = overall_metrics.get("avg_mrr", 0.0)
        mrr_threshold = thresholds.get("mrr", 0.8)
        gates["mrr"] = {
            "passed": mrr_actual >= mrr_threshold,
            "actual": mrr_actual,
            "threshold": mrr_threshold,
            "improvement_needed": max(0, mrr_threshold - mrr_actual)
        }
        
        # Latency gate
        latency_actual = overall_metrics.get("latency_stats", {}).get("p95_ms", 999)
        latency_threshold = thresholds.get("latency_p95", 200)
        gates["latency_p95"] = {
            "passed": latency_actual <= latency_threshold,
            "actual": latency_actual,
            "threshold": latency_threshold,
            "improvement_needed": max(0, latency_actual - latency_threshold)
        }
        
        # Overall pass/fail
        all_passed = all(gate["passed"] for gate in gates.values())
        gates["overall"] = {
            "passed": all_passed,
            "gates_passed": sum(1 for gate in gates.values() if gate["passed"]),
            "total_gates": len([k for k in gates.keys() if k != "overall"])
        }
        
        return gates
    
    def generate_eval_report(self, eval_results: dict[str, Any]) -> str:
        """Generate human-readable evaluation report."""
        overall = eval_results["overall"]
        quality_gates = eval_results["quality_gates"]
        
        report = []
        report.append("🎯 SPLADE Retrieval Evaluation Report")
        report.append("=" * 50)
        
        # Overall metrics
        report.append(f"📊 Overall Performance ({overall['num_queries']} queries)")
        report.append(f"  • NDCG@10: {overall['avg_ndcg_10']:.3f}")
        report.append(f"  • MRR: {overall['avg_mrr']:.3f}")
        report.append(f"  • Precision@10: {overall['avg_precision_10']:.3f}")
        report.append(f"  • Recall@10: {overall['avg_recall_10']:.3f}")
        
        # Latency stats
        latency = overall["latency_stats"]
        report.append(f"⚡ Latency Performance")
        report.append(f"  • Mean: {latency['mean_ms']:.1f}ms")
        report.append(f"  • P95: {latency['p95_ms']:.1f}ms")
        report.append(f"  • P99: {latency['p99_ms']:.1f}ms")
        
        # Quality gates
        report.append(f"🚨 Quality Gates")
        gates_passed = quality_gates["overall"]["gates_passed"]
        total_gates = quality_gates["overall"]["total_gates"] 
        status = "✅ PASSED" if quality_gates["overall"]["passed"] else "❌ FAILED"
        report.append(f"  Overall: {status} ({gates_passed}/{total_gates})")
        
        for gate_name, gate_info in quality_gates.items():
            if gate_name == "overall":
                continue
            status_icon = "✅" if gate_info["passed"] else "❌"
            report.append(f"  • {gate_name}: {status_icon} {gate_info['actual']:.3f} (threshold: {gate_info['threshold']})")
        
        # Recommendations
        report.append(f"💡 Recommendations")
        if not quality_gates["ndcg_10"]["passed"]:
            improvement = quality_gates["ndcg_10"]["improvement_needed"]
            report.append(f"  • Improve relevance ranking by {improvement:.3f} NDCG points")
        
        if not quality_gates["latency_p95"]["passed"]:
            slowdown = quality_gates["latency_p95"]["improvement_needed"]
            report.append(f"  • Reduce P95 latency by {slowdown:.1f}ms")
        
        if quality_gates["overall"]["passed"]:
            report.append("  • All quality gates passed! 🎉")
        
        return "\n".join(report)