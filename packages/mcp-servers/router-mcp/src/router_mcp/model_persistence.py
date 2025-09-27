"""SQLite persistence layer for Model Recommender V2.

Provides persistent storage for model performance metrics, external data cache,
and telemetry data from LiteLLM gateway calls.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator
import os

import aiosqlite

from .model_recommender import ModelPerformance

logger = logging.getLogger(__name__)


class ModelPerformanceStore:
    """SQLite-based storage for model performance data."""
    
    def __init__(self, db_path: str = "data/model_performance.db"):
        env_path = os.getenv("MODEL_PERFORMANCE_DB_PATH")
        resolved = Path(env_path) if env_path else Path(db_path)
        self.db_path = resolved
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize_schema(self) -> None:
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    model_name TEXT PRIMARY KEY,
                    arena_elo REAL,
                    mteb_score REAL,
                    internal_score REAL,
                    avg_latency_ms REAL,
                    cost_per_1k_tokens REAL,
                    success_rate REAL DEFAULT 1.0,
                    last_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS external_data_cache (
                    data_source TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    tenant_id TEXT,
                    latency_ms REAL,
                    success INTEGER,
                    cost_per_token REAL,
                    task_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_model_performance_updated ON model_performance(last_updated)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_model ON telemetry_events(model_name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_events(timestamp)")
            
            await db.commit()
            logger.info("Model performance database schema initialized")
    
    async def save_model_performance(self, performance: ModelPerformance) -> None:
        """Save or update model performance record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO model_performance (
                    model_name, arena_elo, mteb_score, internal_score,
                    avg_latency_ms, cost_per_1k_tokens, success_rate, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                performance.model_name,
                performance.arena_elo,
                performance.mteb_score,
                performance.internal_score,
                performance.avg_latency_ms,
                performance.cost_per_1k_tokens,
                performance.success_rate,
                performance.last_updated.isoformat() if performance.last_updated else None
            ))
            await db.commit()
    
    async def load_model_performance(self, model_name: str) -> ModelPerformance | None:
        """Load model performance record."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM model_performance WHERE model_name = ?", 
                (model_name,)
            ) as cursor:
                row = await cursor.fetchone()
                
            if row:
                return ModelPerformance(
                    model_name=row[0],
                    arena_elo=row[1],
                    mteb_score=row[2],
                    internal_score=row[3],
                    avg_latency_ms=row[4],
                    cost_per_1k_tokens=row[5],
                    success_rate=row[6],
                    last_updated=datetime.fromisoformat(row[7]) if row[7] else None
                )
            
        return None
    
    async def load_all_model_performance(self) -> dict[str, ModelPerformance]:
        """Load all model performance records."""
        performances = {}
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM model_performance") as cursor:
                async for row in cursor:
                    performances[row[0]] = ModelPerformance(
                        model_name=row[0],
                        arena_elo=row[1],
                        mteb_score=row[2],
                        internal_score=row[3],
                        avg_latency_ms=row[4],
                        cost_per_1k_tokens=row[5],
                        success_rate=row[6],
                        last_updated=datetime.fromisoformat(row[7]) if row[7] else None
                    )
        
        return performances
    
    async def save_external_data_cache(
        self, 
        data_source: str, 
        data: dict[str, Any],
        expires_at: datetime | None = None
    ) -> None:
        """Save external data cache (Arena, MTEB, etc.)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO external_data_cache (
                    data_source, data_json, fetched_at, expires_at
                ) VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                data_source,
                json.dumps(data),
                expires_at.isoformat() if expires_at else None
            ))
            await db.commit()
    
    async def load_external_data_cache(self, data_source: str) -> dict[str, Any] | None:
        """Load cached external data."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT data_json FROM external_data_cache 
                WHERE data_source = ? 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """, (data_source,)) as cursor:
                row = await cursor.fetchone()
                
            if row:
                return json.loads(row[0])
                
        return None
    
    async def record_telemetry_event(
        self,
        model_name: str,
        tenant_id: str | None,
        latency_ms: float,
        success: bool,
        cost_per_token: float | None = None,
        task_type: str | None = None
    ) -> None:
        """Record telemetry event from LiteLLM gateway."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO telemetry_events (
                    model_name, tenant_id, latency_ms, success, 
                    cost_per_token, task_type
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                model_name,
                tenant_id, 
                latency_ms,
                1 if success else 0,
                cost_per_token,
                task_type
            ))
            await db.commit()
    
    async def get_model_telemetry_stats(
        self, 
        model_name: str,
        hours_back: int = 24
    ) -> dict[str, float]:
        """Get aggregated telemetry stats for a model."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 
                    AVG(latency_ms) as avg_latency,
                    AVG(success) as success_rate,
                    AVG(cost_per_token) as avg_cost,
                    COUNT(*) as total_calls
                FROM telemetry_events 
                WHERE model_name = ?
                AND timestamp > datetime('now', '-{} hours')
            """.format(hours_back), (model_name,)) as cursor:
                row = await cursor.fetchone()
                
            if row and row[3] > 0:  # total_calls > 0
                return {
                    "avg_latency_ms": row[0] or 0.0,
                    "success_rate": row[1] or 0.0,
                    "avg_cost_per_token": row[2] or 0.0,
                    "total_calls": row[3] or 0
                }
        
        return {"avg_latency_ms": 0.0, "success_rate": 1.0, "avg_cost_per_token": 0.0, "total_calls": 0}
    
    async def cleanup_old_telemetry(self, days_to_keep: int = 30) -> int:
        """Clean up old telemetry events."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM telemetry_events 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            await db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old telemetry events")
            return deleted_count

    async def get_database_stats(self) -> dict[str, int]:
        """Get database statistics for monitoring."""
        stats = {}
        
        async with aiosqlite.connect(self.db_path) as db:
            # Count model performance records
            async with db.execute("SELECT COUNT(*) FROM model_performance") as cursor:
                row = await cursor.fetchone()
                stats["model_performance_records"] = row[0] if row else 0
            
            # Count cached data sources
            async with db.execute("SELECT COUNT(*) FROM external_data_cache") as cursor:
                row = await cursor.fetchone()
                stats["external_data_cache_records"] = row[0] if row else 0
            
            # Count telemetry events (last 7 days)
            async with db.execute("""
                SELECT COUNT(*) FROM telemetry_events 
                WHERE timestamp > datetime('now', '-7 days')
            """) as cursor:
                row = await cursor.fetchone()
                stats["recent_telemetry_events"] = row[0] if row else 0
        
        return stats