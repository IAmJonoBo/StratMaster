"""Enhanced BEIR dataset integration for retrieval benchmarking.

Provides integration with BEIR (Benchmarking Information Retrieval) datasets
including LoTTE, Natural Questions, and other standard IR evaluation datasets.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from .evaluator import EvalQuery, SPLADEEvaluator

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None


@dataclass
class BEIRDataset:
    """BEIR dataset metadata."""
    name: str
    description: str
    task_type: str
    num_queries: int
    num_documents: int
    download_url: str
    local_path: Path | None = None


class BEIRDatasetManager:
    """Manages BEIR dataset downloads and integration."""
    
    def __init__(self, data_dir: str = "seeds/eval/beir"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Available BEIR datasets (subset for StratMaster use cases)
        self.available_datasets = {
            "natural-questions": BEIRDataset(
                name="natural-questions",
                description="Natural Questions (NQ) test set",
                task_type="question-answering",
                num_queries=3452,
                num_documents=2681468,
                download_url="https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nq.zip"
            ),
            "lotte": BEIRDataset(
                name="lotte", 
                description="LoTTE (Long Tail Topic-stratified Evaluation)",
                task_type="long-tail-search",
                num_queries=2000,
                num_documents=1000000,
                download_url="https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/lotte.zip"
            ),
            "scidocs": BEIRDataset(
                name="scidocs",
                description="Scientific document retrieval",
                task_type="scientific-search", 
                num_queries=1000,
                num_documents=25657,
                download_url="https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scidocs.zip"
            )
        }
    
    async def download_dataset(self, dataset_name: str) -> Path | None:
        """Download and extract BEIR dataset."""
        if dataset_name not in self.available_datasets:
            raise ValueError(f"Dataset {dataset_name} not available")
        
        dataset = self.available_datasets[dataset_name]
        dataset_dir = self.data_dir / dataset_name
        
        # Check if already downloaded
        if dataset_dir.exists() and (dataset_dir / "queries.jsonl").exists():
            logger.info(f"Dataset {dataset_name} already exists")
            return dataset_dir
        
        dataset_dir.mkdir(exist_ok=True)
        
        try:
            logger.info(f"Downloading BEIR dataset: {dataset_name}")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(dataset.download_url)
                response.raise_for_status()
                
                zip_path = dataset_dir / f"{dataset_name}.zip"
                with open(zip_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded {len(response.content)} bytes to {zip_path}")
                
                # Extract zip file
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(dataset_dir)
                
                # Remove zip file
                zip_path.unlink()
                
                # Update dataset with local path
                dataset.local_path = dataset_dir
                
                logger.info(f"✅ Dataset {dataset_name} downloaded and extracted")
                return dataset_dir
                
        except Exception as e:
            logger.error(f"Failed to download dataset {dataset_name}: {e}")
            return None
    
    async def load_dataset_queries(self, dataset_name: str, limit: int = 100) -> list[EvalQuery]:
        """Load evaluation queries from BEIR dataset."""
        if dataset_name not in self.available_datasets:
            raise ValueError(f"Dataset {dataset_name} not available")
        
        dataset_dir = self.data_dir / dataset_name
        
        # Download if not exists
        if not dataset_dir.exists():
            download_result = await self.download_dataset(dataset_name)
            if not download_result:
                return []
        
        queries_file = dataset_dir / "queries.jsonl"
        qrels_file = dataset_dir / "qrels" / "test.tsv"
        
        if not queries_file.exists():
            logger.warning(f"Queries file not found for {dataset_name}")
            return []
        
        eval_queries = []
        
        try:
            # Load queries
            queries_data = {}
            with open(queries_file) as f:
                for line in f:
                    if line.strip():
                        query_data = json.loads(line)
                        queries_data[query_data["_id"]] = query_data["text"]
            
            # Load relevance judgments if available
            qrels_data = {}
            if qrels_file.exists():
                if pd is not None:
                    qrels_df = pd.read_csv(qrels_file, sep="\t", names=["query-id", "corpus-id", "score"])
                    for _, row in qrels_df.iterrows():
                        query_id = row["query-id"]
                        if query_id not in qrels_data:
                            qrels_data[query_id] = []
                        if row["score"] > 0:  # Only relevant documents
                            qrels_data[query_id].append(row["corpus-id"])
            
            # Create EvalQuery objects
            count = 0
            for query_id, query_text in queries_data.items():
                if count >= limit:
                    break
                
                relevant_docs = qrels_data.get(query_id, [])
                if relevant_docs:  # Only include queries with relevance judgments
                    eval_queries.append(EvalQuery(
                        query_id=query_id,
                        query_text=query_text,
                        relevant_docs=relevant_docs
                    ))
                    count += 1
            
            logger.info(f"Loaded {len(eval_queries)} queries from {dataset_name}")
            return eval_queries
            
        except Exception as e:
            logger.error(f"Failed to load queries from {dataset_name}: {e}")
            return []
    
    def get_dataset_info(self, dataset_name: str) -> dict[str, Any]:
        """Get information about a BEIR dataset."""
        if dataset_name not in self.available_datasets:
            return {"error": f"Dataset {dataset_name} not available"}
        
        dataset = self.available_datasets[dataset_name]
        dataset_dir = self.data_dir / dataset_name
        
        return {
            "name": dataset.name,
            "description": dataset.description,
            "task_type": dataset.task_type,
            "num_queries": dataset.num_queries,
            "num_documents": dataset.num_documents,
            "local_path": str(dataset_dir) if dataset_dir.exists() else None,
            "downloaded": dataset_dir.exists(),
            "available_files": list(dataset_dir.glob("*")) if dataset_dir.exists() else []
        }
    
    def list_available_datasets(self) -> list[dict[str, Any]]:
        """List all available BEIR datasets."""
        return [
            {
                "name": dataset.name,
                "description": dataset.description,
                "task_type": dataset.task_type,
                "num_queries": dataset.num_queries,
                "downloaded": (self.data_dir / dataset.name).exists()
            }
            for dataset in self.available_datasets.values()
        ]


class BEIREnhancedEvaluator(SPLADEEvaluator):
    """Enhanced SPLADE evaluator with BEIR dataset integration."""
    
    def __init__(self, eval_data_path: str = "seeds/eval/retrieval_queries.json"):
        super().__init__(eval_data_path)
        self.beir_manager = BEIRDatasetManager()
        self.benchmark_cache: dict[str, Any] = {}
    
    async def run_beir_benchmark(
        self,
        dataset_name: str,
        retrieval_function: Any,
        limit_queries: int = 50,
        k: int = 10
    ) -> dict[str, Any]:
        """Run benchmark evaluation on BEIR dataset."""
        logger.info(f"Running BEIR benchmark: {dataset_name}")
        
        # Load dataset queries
        beir_queries = await self.beir_manager.load_dataset_queries(
            dataset_name, limit=limit_queries
        )
        
        if not beir_queries:
            return {
                "error": f"No queries loaded from dataset {dataset_name}",
                "dataset_name": dataset_name
            }
        
        # Replace current eval queries with BEIR queries
        original_queries = self.eval_queries
        self.eval_queries = beir_queries
        
        try:
            # Run evaluation
            results = await self.evaluate_retrieval_system(
                retrieval_function, k=k
            )
            
            # Add dataset metadata to results
            dataset_info = self.beir_manager.get_dataset_info(dataset_name)
            results["dataset_info"] = dataset_info
            results["benchmark_type"] = "BEIR"
            results["timestamp"] = datetime.now().isoformat()
            
            # Cache results
            self.benchmark_cache[dataset_name] = results
            
            logger.info(
                f"✅ BEIR benchmark completed for {dataset_name}: "
                f"NDCG@10={results['overall']['ndcg_10']:.3f}, "
                f"MRR={results['overall']['mrr']:.3f}"
            )
            
            return results
            
        finally:
            # Restore original queries
            self.eval_queries = original_queries
    
    async def run_multi_dataset_benchmark(
        self,
        datasets: list[str],
        retrieval_function: Any,
        limit_queries: int = 30,
        k: int = 10
    ) -> dict[str, Any]:
        """Run benchmarks across multiple BEIR datasets."""
        results = {}
        overall_metrics = []
        
        for dataset_name in datasets:
            try:
                result = await self.run_beir_benchmark(
                    dataset_name, retrieval_function, limit_queries, k
                )
                results[dataset_name] = result
                
                if "overall" in result:
                    overall_metrics.append(result["overall"])
                    
            except Exception as e:
                logger.error(f"Benchmark failed for {dataset_name}: {e}")
                results[dataset_name] = {"error": str(e)}
        
        # Calculate aggregate metrics across datasets
        aggregate = self._calculate_aggregate_metrics(overall_metrics)
        
        return {
            "datasets": results,
            "aggregate": aggregate,
            "benchmark_type": "Multi-Dataset BEIR",
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_aggregate_metrics(self, metrics_list: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate aggregate metrics across multiple datasets."""
        if not metrics_list:
            return {}
        
        # Calculate means across datasets
        aggregate = {}
        for key in ["ndcg_10", "mrr", "precision_10", "recall_10", "latency_p95"]:
            values = [m.get(key, 0) for m in metrics_list if key in m]
            if values:
                aggregate[f"mean_{key}"] = sum(values) / len(values)
                aggregate[f"min_{key}"] = min(values)
                aggregate[f"max_{key}"] = max(values)
        
        aggregate["num_datasets"] = len(metrics_list)
        return aggregate
    
    async def get_cached_benchmark_results(self, dataset_name: str) -> dict[str, Any] | None:
        """Get cached benchmark results for a dataset."""
        return self.benchmark_cache.get(dataset_name)
    
    def clear_benchmark_cache(self) -> None:
        """Clear cached benchmark results."""
        self.benchmark_cache.clear()
        logger.info("Benchmark cache cleared")
    
    async def validate_retrieval_quality_gates(
        self,
        dataset_name: str,
        retrieval_function: Any,
        quality_gates: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Validate retrieval system against quality gates using BEIR data."""
        if quality_gates is None:
            quality_gates = {
                "ndcg_10": 0.65,      # BEIR baseline for most datasets
                "mrr": 0.70,          # Reasonable MRR target
                "latency_p95": 300,   # 300ms p95 latency target
            }
        
        # Run benchmark
        results = await self.run_beir_benchmark(
            dataset_name, retrieval_function, limit_queries=100
        )
        
        if "error" in results:
            return results
        
        # Check quality gates
        overall = results["overall"]
        quality_check = {
            "passed": True,
            "gates": {},
            "overall_score": 0.0
        }
        
        scores = []
        for gate_name, threshold in quality_gates.items():
            actual_value = overall.get(gate_name, 0)
            
            if gate_name == "latency_p95":
                # Lower is better for latency
                passed = actual_value <= threshold
            else:
                # Higher is better for quality metrics
                passed = actual_value >= threshold
            
            quality_check["gates"][gate_name] = {
                "threshold": threshold,
                "actual": actual_value,
                "passed": passed,
                "margin": actual_value - threshold if gate_name != "latency_p95" else threshold - actual_value
            }
            
            if not passed:
                quality_check["passed"] = False
            
            # Calculate normalized score (0-1)
            if gate_name != "latency_p95":
                scores.append(min(1.0, actual_value))
            else:
                scores.append(max(0.0, 1.0 - (actual_value / 1000)))  # Normalize latency
        
        quality_check["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "quality_gates": quality_check,
            "benchmark_results": results,
            "dataset_name": dataset_name
        }