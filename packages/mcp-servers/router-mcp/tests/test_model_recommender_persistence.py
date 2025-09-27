"""Persistence-focused tests for Model Recommender V2."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from router_mcp.model_persistence import ModelPerformanceStore
from router_mcp.model_recommender import ModelRecommender


def test_bootstrap_initialises_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The recommender should create the persistence schema on bootstrap."""

    async def _run() -> None:
        db_path = tmp_path / "model-metrics.db"
        monkeypatch.setenv("MODEL_PERFORMANCE_DB_PATH", str(db_path))

        recommender = ModelRecommender(persistence_store=ModelPerformanceStore(str(db_path)))
        try:
            await recommender.bootstrap_persistence()
            stats = await recommender.store.get_database_stats()  # type: ignore[union-attr]
            assert stats["model_performance_records"] == 0
            assert stats["external_data_cache_records"] == 0
            assert stats["recent_telemetry_events"] == 0
        finally:
            await recommender.aclose()

    asyncio.run(_run())


def test_record_outcome_persists_telemetry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Recording an outcome should persist a telemetry event when V2 is enabled."""

    async def _run() -> None:
        db_path = tmp_path / "model-metrics.db"
        monkeypatch.setenv("MODEL_PERFORMANCE_DB_PATH", str(db_path))
        monkeypatch.setenv("ENABLE_MODEL_RECOMMENDER_V2", "true")

        recommender = ModelRecommender(persistence_store=ModelPerformanceStore(str(db_path)))
        try:
            await recommender.bootstrap_persistence()
            await recommender.record_outcome(
                model_name="gpt-4o",
                task_type="reasoning",
                success=True,
                latency_ms=150.0,
                cost_usd=0.002,
                tenant_id="tenant-a",
                tokens_used=200,
            )

            telemetry = await recommender.store.get_model_telemetry_stats("gpt-4o")  # type: ignore[union-attr]
            assert telemetry["total_calls"] == 1
            assert telemetry["avg_latency_ms"] > 0
        finally:
            await recommender.aclose()

    asyncio.run(_run())
