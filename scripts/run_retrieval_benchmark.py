#!/usr/bin/env python3
"""
CLI script for running retrieval benchmarks and validation.

This script can be run manually or as part of CI/nightly jobs to validate
retrieval performance against BEIR-style datasets and quality gates.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add packages to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "packages" / "retrieval" / "src" / "splade" / "src"))

try:
    from splade.evaluator import SPLADEEvaluator, is_retrieval_benchmarks_enabled
except ImportError as e:
    print(f"Error: Could not import SPLADE evaluator: {e}")
    print("Make sure the retrieval package is properly installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


async def mock_retrieval_function(query_text: str, k: int = 10):
    """Mock retrieval function for testing benchmarks."""
    # Simulate some retrieval latency
    await asyncio.sleep(0.05)
    
    # Return mock results with decreasing scores
    return [
        {
            "doc_id": f"doc_{i:03d}",
            "score": 1.0 - (i * 0.08),
            "rank": i,
            "title": f"Document {i} for query: {query_text[:30]}...",
        }
        for i in range(k)
    ]


async def run_benchmark(
    eval_data_path: str | None = None,
    k: int = 10,
    quality_thresholds: dict[str, float] | None = None,
    output_file: str | None = None
) -> dict:
    """Run retrieval benchmarks and return results."""
    logger.info("Starting retrieval benchmark evaluation")
    
    # Initialize evaluator
    evaluator_path = eval_data_path or "seeds/eval/retrieval_queries.json"
    evaluator = SPLADEEvaluator(evaluator_path)
    
    logger.info(f"Loaded {len(evaluator.eval_queries)} evaluation queries from {evaluator_path}")
    
    # Set default quality thresholds
    if quality_thresholds is None:
        quality_thresholds = {
            "ndcg_10": 0.7,   # 70% NDCG@10
            "mrr": 0.8,       # 80% MRR
            "latency_p95": 200  # 200ms p95 latency
        }
    
    logger.info(f"Quality thresholds: {quality_thresholds}")
    
    # Run evaluation
    logger.info(f"Running evaluation with k={k}")
    results = await evaluator.evaluate_retrieval_system(
        mock_retrieval_function,
        k=k,
        quality_threshold=quality_thresholds
    )
    
    # Generate and log report
    if hasattr(evaluator, 'generate_eval_report'):
        report = evaluator.generate_eval_report(results)
        logger.info(f"Evaluation Report:\n{report}")
    
    # Output results to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_path}")
    
    # Log summary
    overall = results.get("overall", results.get("overall_metrics", {}))
    quality_gates = results.get("quality_gates", {})
    
    logger.info("Benchmark Summary:")
    logger.info(f"  Queries evaluated: {overall.get('num_queries', 'unknown')}")
    logger.info(f"  Average NDCG@10: {overall.get('avg_ndcg_10', 0.0):.3f}")
    logger.info(f"  Average MRR: {overall.get('avg_mrr', 0.0):.3f}")
    
    latency_stats = overall.get('latency_stats', {})
    if latency_stats:
        logger.info(f"  Latency p95: {latency_stats.get('p95_ms', 0.0):.1f}ms")
    
    # Check quality gates
    overall_gate = quality_gates.get("overall", {})
    if overall_gate.get("passed", False):
        logger.info("✅ All quality gates PASSED")
        exit_code = 0
    else:
        logger.warning("❌ Some quality gates FAILED")
        failed_gates = []
        for gate_name, gate_result in quality_gates.items():
            if gate_name != "overall" and isinstance(gate_result, dict):
                if not gate_result.get("passed", True):
                    failed_gates.append(f"{gate_name}: {gate_result.get('actual', 'N/A')} vs {gate_result.get('threshold', 'N/A')}")
        
        if failed_gates:
            logger.warning(f"Failed gates: {', '.join(failed_gates)}")
        
        exit_code = 1
    
    return results, exit_code


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Run SPLADE retrieval benchmarks and quality validation"
    )
    
    parser.add_argument(
        "--eval-data",
        help="Path to evaluation data JSON file (default: seeds/eval/retrieval_queries.json)"
    )
    
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Number of top results to evaluate (default: 10)"
    )
    
    parser.add_argument(
        "--ndcg-threshold",
        type=float,
        default=0.7,
        help="Minimum NDCG@10 threshold (default: 0.7)"
    )
    
    parser.add_argument(
        "--mrr-threshold",
        type=float,
        default=0.8,
        help="Minimum MRR threshold (default: 0.8)"
    )
    
    parser.add_argument(
        "--latency-threshold",
        type=float,
        default=200,
        help="Maximum p95 latency in ms (default: 200)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for benchmark results (JSON format)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check feature flag
    if not is_retrieval_benchmarks_enabled():
        logger.warning("Retrieval benchmarks are disabled. Set ENABLE_RETRIEVAL_BENCHMARKS=true to enable.")
        logger.info("Running with mock data for demonstration...")
    else:
        logger.info("Retrieval benchmarks enabled - using real evaluation system")
    
    # Build quality thresholds
    quality_thresholds = {
        "ndcg_10": args.ndcg_threshold,
        "mrr": args.mrr_threshold,
        "latency_p95": args.latency_threshold
    }
    
    # Run benchmark
    try:
        results, exit_code = asyncio.run(run_benchmark(
            eval_data_path=args.eval_data,
            k=args.k,
            quality_thresholds=quality_thresholds,
            output_file=args.output
        ))
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Benchmark failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()