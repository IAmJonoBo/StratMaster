#!/usr/bin/env python3
"""
Retrieval Benchmarking & Latency Validation Test
Implements BEIR-style evaluation as specified in Issue 003
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import statistics
import random


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockRetrievalSystem:
    """Mock retrieval system for benchmark testing."""
    
    def __init__(self, system_name: str, base_latency_ms: float = 50.0):
        self.system_name = system_name
        self.base_latency_ms = base_latency_ms
        self.query_count = 0
        
    async def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Perform mock retrieval with simulated latency."""
        start_time = time.time()
        
        # Simulate processing latency with some variance
        latency_variance = random.uniform(0.8, 1.5)
        await asyncio.sleep(self.base_latency_ms / 1000 * latency_variance)
        
        self.query_count += 1
        
        # Generate mock results with realistic score distribution
        results = []
        for i in range(k):
            # Simulate relevance scores with some randomness
            base_relevance = max(0, 0.9 - (i * 0.08))
            relevance_noise = random.uniform(-0.1, 0.1)
            score = max(0, min(1, base_relevance + relevance_noise))
            
            results.append({
                "doc_id": f"{self.system_name}_doc_{i:03d}_{hash(query) % 10000:04d}",
                "text": f"Mock document {i} for query: {query[:50]}...",
                "score": score,
                "rank": i
            })
        
        actual_latency = (time.time() - start_time) * 1000
        
        return results, actual_latency


class BEIRDatasetSimulator:
    """Simulate BEIR-style evaluation datasets."""
    
    def __init__(self):
        # Mock dataset with query-relevance pairs
        self.mock_queries = {
            "nfcorpus": [
                {
                    "query_id": "PLAIN-1",
                    "query": "What are the causes of type 2 diabetes?",
                    "relevant_docs": ["doc_001", "doc_003", "doc_007"],
                    "domain": "medical"
                },
                {
                    "query_id": "PLAIN-2", 
                    "query": "How does photosynthesis work in plants?",
                    "relevant_docs": ["doc_002", "doc_009"],
                    "domain": "biology"
                },
                {
                    "query_id": "PLAIN-3",
                    "query": "What is the capital of France?",
                    "relevant_docs": ["doc_004"],
                    "domain": "geography"
                },
                {
                    "query_id": "PLAIN-4",
                    "query": "Explain quantum computing principles",
                    "relevant_docs": ["doc_005", "doc_008"],
                    "domain": "technology"  
                },
                {
                    "query_id": "PLAIN-5",
                    "query": "Benefits of renewable energy sources",
                    "relevant_docs": ["doc_006", "doc_010", "doc_011"],
                    "domain": "environment"
                }
            ],
            "msmarco": [
                {
                    "query_id": "MS-1",
                    "query": "how to install python packages",
                    "relevant_docs": ["doc_101", "doc_105"],
                    "domain": "programming"
                },
                {
                    "query_id": "MS-2",
                    "query": "best restaurants in New York",
                    "relevant_docs": ["doc_102", "doc_107", "doc_109"],
                    "domain": "local"
                },
                {
                    "query_id": "MS-3", 
                    "query": "symptoms of common cold",
                    "relevant_docs": ["doc_103"],
                    "domain": "health"
                }
            ]
        }
    
    def get_dataset_queries(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Get queries for a specific dataset."""
        return self.mock_queries.get(dataset_name, [])
    
    def get_all_datasets(self) -> List[str]:
        """Get list of available datasets."""
        return list(self.mock_queries.keys())


class RetrievalBenchmarkEvaluator:
    """BEIR-style retrieval benchmark evaluator."""
    
    def __init__(self):
        self.dataset_simulator = BEIRDatasetSimulator()
        self.results_dir = Path("data/benchmark_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def calculate_ndcg_at_k(self, retrieved_docs: List[str], relevant_docs: List[str], k: int = 10) -> float:
        """Calculate NDCG@k metric."""
        if not relevant_docs:
            return 0.0
            
        # Calculate DCG@k
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_docs[:k]):
            if doc_id in relevant_docs:
                # Use binary relevance (1 if relevant, 0 otherwise)
                relevance = 1.0
                # DCG formula: rel_i / log2(i + 2)
                dcg += relevance / (1.0 + i)  # Simplified version
        
        # Calculate IDCG@k (ideal DCG)
        ideal_relevance_count = min(len(relevant_docs), k)
        idcg = sum(1.0 / (1.0 + i) for i in range(ideal_relevance_count))
        
        # NDCG = DCG / IDCG
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def calculate_mrr(self, retrieved_docs: List[str], relevant_docs: List[str]) -> float:
        """Calculate Mean Reciprocal Rank (MRR)."""
        if not relevant_docs:
            return 0.0
            
        for i, doc_id in enumerate(retrieved_docs):
            if doc_id in relevant_docs:
                return 1.0 / (i + 1)
        
        return 0.0
    
    def calculate_recall_at_k(self, retrieved_docs: List[str], relevant_docs: List[str], k: int = 10) -> float:
        """Calculate Recall@k metric."""
        if not relevant_docs:
            return 0.0
            
        retrieved_relevant = set(retrieved_docs[:k]) & set(relevant_docs)
        return len(retrieved_relevant) / len(relevant_docs)
    
    async def evaluate_system(
        self, 
        retrieval_system: MockRetrievalSystem,
        dataset_name: str = "nfcorpus",
        k: int = 10
    ) -> Dict[str, Any]:
        """Evaluate a retrieval system on a BEIR dataset."""
        logger.info(f"🔍 Evaluating {retrieval_system.system_name} on {dataset_name}")
        
        queries = self.dataset_simulator.get_dataset_queries(dataset_name)
        if not queries:
            raise ValueError(f"Dataset {dataset_name} not found")
        
        # Metrics storage
        ndcg_scores = []
        mrr_scores = []
        recall_scores = []
        latencies = []
        
        start_time = time.time()
        
        for i, query_data in enumerate(queries):
            query = query_data["query"]
            relevant_docs = query_data["relevant_docs"]
            
            logger.info(f"  Query {i+1}/{len(queries)}: {query[:50]}...")
            
            # Perform retrieval
            try:
                results, latency_ms = await retrieval_system.search(query, k)
                latencies.append(latency_ms)
                
                retrieved_doc_ids = [result["doc_id"] for result in results]
                
                # Calculate metrics
                ndcg = self.calculate_ndcg_at_k(retrieved_doc_ids, relevant_docs, k)
                mrr = self.calculate_mrr(retrieved_doc_ids, relevant_docs)
                recall = self.calculate_recall_at_k(retrieved_doc_ids, relevant_docs, k)
                
                ndcg_scores.append(ndcg)
                mrr_scores.append(mrr)
                recall_scores.append(recall)
                
                logger.debug(f"    NDCG@{k}: {ndcg:.3f}, MRR: {mrr:.3f}, Latency: {latency_ms:.1f}ms")
                
            except Exception as e:
                logger.error(f"    Error processing query: {e}")
                continue
        
        total_time = time.time() - start_time
        
        # Calculate aggregate metrics
        results = {
            "system_name": retrieval_system.system_name,
            "dataset": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "k": k,
            "total_queries": len(queries),
            "metrics": {
                "ndcg_at_k": {
                    "mean": statistics.mean(ndcg_scores) if ndcg_scores else 0.0,
                    "std": statistics.stdev(ndcg_scores) if len(ndcg_scores) > 1 else 0.0,
                    "scores": ndcg_scores
                },
                "mrr": {
                    "mean": statistics.mean(mrr_scores) if mrr_scores else 0.0,
                    "std": statistics.stdev(mrr_scores) if len(mrr_scores) > 1 else 0.0,
                    "scores": mrr_scores
                },
                "recall_at_k": {
                    "mean": statistics.mean(recall_scores) if recall_scores else 0.0,
                    "std": statistics.stdev(recall_scores) if len(recall_scores) > 1 else 0.0,
                    "scores": recall_scores
                }
            },
            "latency": {
                "p50_ms": statistics.median(latencies) if latencies else 0.0,
                "p95_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0),
                "p99_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else (max(latencies) if latencies else 0.0),
                "mean_ms": statistics.mean(latencies) if latencies else 0.0,
                "all_latencies": latencies
            },
            "evaluation_time_s": total_time,
            "queries_per_second": len(queries) / total_time if total_time > 0 else 0.0
        }
        
        logger.info(f"✅ Evaluation completed:")
        logger.info(f"   NDCG@{k}: {results['metrics']['ndcg_at_k']['mean']:.3f} ± {results['metrics']['ndcg_at_k']['std']:.3f}")
        logger.info(f"   MRR: {results['metrics']['mrr']['mean']:.3f} ± {results['metrics']['mrr']['std']:.3f}")
        logger.info(f"   Recall@{k}: {results['metrics']['recall_at_k']['mean']:.3f} ± {results['metrics']['recall_at_k']['std']:.3f}")
        logger.info(f"   P95 Latency: {results['latency']['p95_ms']:.1f}ms")
        
        return results
    
    def check_quality_gates(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check if results meet quality gate thresholds."""
        gates = {
            "ndcg_threshold": 0.3,      # Minimum NDCG@10
            "mrr_threshold": 0.4,       # Minimum MRR
            "recall_threshold": 0.2,    # Minimum Recall@10
            "latency_p95_threshold": 200.0,  # Maximum P95 latency in ms
        }
        
        gate_results = {}
        
        # Check NDCG gate
        ndcg_mean = results["metrics"]["ndcg_at_k"]["mean"]
        gate_results["ndcg_gate"] = {
            "passed": ndcg_mean >= gates["ndcg_threshold"],
            "value": ndcg_mean,
            "threshold": gates["ndcg_threshold"]
        }
        
        # Check MRR gate
        mrr_mean = results["metrics"]["mrr"]["mean"]
        gate_results["mrr_gate"] = {
            "passed": mrr_mean >= gates["mrr_threshold"],
            "value": mrr_mean,
            "threshold": gates["mrr_threshold"]
        }
        
        # Check Recall gate
        recall_mean = results["metrics"]["recall_at_k"]["mean"]
        gate_results["recall_gate"] = {
            "passed": recall_mean >= gates["recall_threshold"],
            "value": recall_mean,
            "threshold": gates["recall_threshold"]
        }
        
        # Check Latency gate
        p95_latency = results["latency"]["p95_ms"]
        gate_results["latency_gate"] = {
            "passed": p95_latency <= gates["latency_p95_threshold"],
            "value": p95_latency,
            "threshold": gates["latency_p95_threshold"]
        }
        
        # Overall gate status
        all_passed = all(gate["passed"] for gate in gate_results.values())
        gate_results["overall"] = {
            "passed": all_passed,
            "passed_gates": sum(1 for gate in gate_results.values() if gate["passed"]),
            "total_gates": len(gate_results)
        }
        
        return gate_results
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark across multiple systems and datasets."""
        logger.info("🚀 Starting Comprehensive Retrieval Benchmark")
        logger.info("=" * 60)
        
        # Define retrieval systems to test
        systems = [
            MockRetrievalSystem("baseline", base_latency_ms=30.0),
            MockRetrievalSystem("splade", base_latency_ms=80.0),
            MockRetrievalSystem("colbert", base_latency_ms=120.0)
        ]
        
        # Run benchmarks
        all_results = {}
        
        for system in systems:
            system_results = {}
            
            for dataset_name in self.dataset_simulator.get_all_datasets():
                try:
                    results = await self.evaluate_system(system, dataset_name, k=10)
                    quality_gates = self.check_quality_gates(results)
                    
                    system_results[dataset_name] = {
                        "evaluation_results": results,
                        "quality_gates": quality_gates
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to evaluate {system.system_name} on {dataset_name}: {e}")
                    continue
            
            all_results[system.system_name] = system_results
        
        # Generate summary report
        summary = self.generate_benchmark_summary(all_results)
        
        # Save results
        results_file = self.results_dir / f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": summary,
                "detailed_results": all_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"📁 Results saved to: {results_file}")
        
        return {"summary": summary, "results_file": str(results_file)}
    
    def generate_benchmark_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report from benchmark results."""
        logger.info("\n📊 Benchmark Summary Report")
        logger.info("-" * 40)
        
        summary = {
            "systems_tested": len(all_results),
            "datasets_per_system": 0,
            "overall_best_system": None,
            "quality_gate_summary": {},
            "performance_summary": {}
        }
        
        # Calculate averages and find best system
        system_averages = {}
        
        for system_name, system_results in all_results.items():
            summary["datasets_per_system"] = len(system_results)
            
            # Aggregate metrics across datasets
            all_ndcg = []
            all_mrr = []
            all_latency_p95 = []
            passed_gates = 0
            total_gates = 0
            
            for dataset_name, result_data in system_results.items():
                eval_results = result_data["evaluation_results"]
                quality_gates = result_data["quality_gates"]
                
                all_ndcg.append(eval_results["metrics"]["ndcg_at_k"]["mean"])
                all_mrr.append(eval_results["metrics"]["mrr"]["mean"])
                all_latency_p95.append(eval_results["latency"]["p95_ms"])
                
                passed_gates += quality_gates["overall"]["passed_gates"]
                total_gates += quality_gates["overall"]["total_gates"]
            
            avg_ndcg = statistics.mean(all_ndcg) if all_ndcg else 0
            avg_mrr = statistics.mean(all_mrr) if all_mrr else 0
            avg_p95_latency = statistics.mean(all_latency_p95) if all_latency_p95 else 0
            gate_pass_rate = passed_gates / total_gates if total_gates > 0 else 0
            
            system_averages[system_name] = {
                "avg_ndcg": avg_ndcg,
                "avg_mrr": avg_mrr,
                "avg_p95_latency": avg_p95_latency,
                "gate_pass_rate": gate_pass_rate
            }
            
            logger.info(f"\n🔧 {system_name}:")
            logger.info(f"   Avg NDCG@10: {avg_ndcg:.3f}")
            logger.info(f"   Avg MRR: {avg_mrr:.3f}")
            logger.info(f"   Avg P95 Latency: {avg_p95_latency:.1f}ms")
            logger.info(f"   Quality Gates: {passed_gates}/{total_gates} ({gate_pass_rate:.1%})")
        
        # Find best system (highest combined score)
        best_system = None
        best_score = -1
        
        for system_name, averages in system_averages.items():
            # Combined score: emphasize quality metrics, penalize latency
            score = (averages["avg_ndcg"] * 0.4 + 
                    averages["avg_mrr"] * 0.3 + 
                    averages["gate_pass_rate"] * 0.2 -
                    (averages["avg_p95_latency"] / 1000) * 0.1)  # Latency penalty
            
            if score > best_score:
                best_score = score
                best_system = system_name
        
        summary["overall_best_system"] = best_system
        summary["performance_summary"] = system_averages
        
        logger.info(f"\n🏆 Best Overall System: {best_system}")
        
        return summary


async def main():
    """Main benchmark runner."""
    evaluator = RetrievalBenchmarkEvaluator()
    
    try:
        results = await evaluator.run_comprehensive_benchmark()
        
        logger.info("\n✅ Comprehensive benchmark completed successfully!")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))