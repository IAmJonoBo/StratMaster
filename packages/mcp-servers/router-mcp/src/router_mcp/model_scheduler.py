"""APScheduler-based model data refresh scheduler.

Handles nightly updates of model performance data from external sources
and periodic telemetry aggregation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    AsyncIOScheduler = None
    CronTrigger = None
    IntervalTrigger = None

from .model_persistence import ModelPerformanceStore
from .model_recommender import ModelRecommender, is_model_recommender_v2_enabled

logger = logging.getLogger(__name__)


class ModelDataScheduler:
    """Scheduler for model data refresh jobs."""
    
    def __init__(
        self,
        recommender: ModelRecommender,
        store: ModelPerformanceStore,
        config_path: str = "configs/router/models-policy.yaml"
    ):
        if AsyncIOScheduler is None:
            raise RuntimeError(
                "APScheduler not installed. Run: pip install apscheduler"
            )
            
        self.recommender = recommender
        self.store = store
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # Performance metrics
        self.last_refresh_time: datetime | None = None
        self.total_refresh_jobs = 0
        self.failed_refresh_jobs = 0
    
    async def start(self) -> None:
        """Start the scheduler with job definitions."""
        if not is_model_recommender_v2_enabled():
            logger.info("Model Recommender V2 disabled, scheduler not started")
            return
            
        logger.info("Starting Model Data Scheduler...")
        
        # Initialize database schema
        await self.store.initialize_schema()
        
        # Schedule nightly data refresh at 2 AM UTC
        self.scheduler.add_job(
            self._refresh_external_data,
            trigger=CronTrigger(hour=2, minute=0),
            id="nightly_data_refresh",
            name="Nightly External Data Refresh",
            max_instances=1,
            replace_existing=True
        )
        
        # Schedule telemetry aggregation every 15 minutes
        self.scheduler.add_job(
            self._aggregate_telemetry,
            trigger=IntervalTrigger(minutes=15),
            id="telemetry_aggregation", 
            name="Telemetry Data Aggregation",
            max_instances=1,
            replace_existing=True
        )
        
        # Schedule weekly cleanup at 3 AM on Sundays
        self.scheduler.add_job(
            self._cleanup_old_data,
            trigger=CronTrigger(day_of_week=6, hour=3, minute=0),  # Sunday 3 AM
            id="weekly_cleanup",
            name="Weekly Data Cleanup",
            max_instances=1,
            replace_existing=True
        )
        
        # Schedule immediate refresh if no data exists
        self.scheduler.add_job(
            self._initial_data_check,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=30),
            id="initial_data_check",
            name="Initial Data Check"
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("✅ Model Data Scheduler started with 4 jobs")
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Model Data Scheduler stopped")
    
    async def _initial_data_check(self) -> None:
        """Check if initial data exists and refresh if needed."""
        try:
            logger.info("Performing initial data check...")
            
            # Check if we have recent data
            stats = await self.store.get_database_stats()
            if stats["model_performance_records"] == 0:
                logger.info("No model performance data found, triggering initial refresh")
                await self._refresh_external_data()
            else:
                logger.info(f"Found {stats['model_performance_records']} existing model records")
                
        except Exception as e:
            logger.error(f"Initial data check failed: {e}")
    
    async def _refresh_external_data(self) -> None:
        """Refresh external data sources (Arena, MTEB, internal evals)."""
        job_start = datetime.now()
        self.total_refresh_jobs += 1
        
        try:
            logger.info("🔄 Starting nightly external data refresh...")
            
            # Force cache refresh by clearing timestamp
            self.recommender.last_cache_update = None
            
            # This will trigger fresh fetches from Arena, MTEB, and internal sources
            await self.recommender._refresh_performance_cache()
            
            # Save all updated performance data to persistent storage
            performance_count = 0
            for model_name, performance in self.recommender.performance_cache.items():
                await self.store.save_model_performance(performance)
                performance_count += 1
            
            # Cache external data for faster subsequent loads
            await self._cache_external_sources()
            
            self.last_refresh_time = datetime.now()
            refresh_duration = (self.last_refresh_time - job_start).total_seconds()
            
            logger.info(
                f"✅ External data refresh completed in {refresh_duration:.1f}s. "
                f"Updated {performance_count} model records"
            )
            
        except Exception as e:
            self.failed_refresh_jobs += 1
            logger.error(f"❌ External data refresh failed: {e}")
            raise
    
    async def _cache_external_sources(self) -> None:
        """Cache external data sources with expiration."""
        try:
            # Fetch and cache Arena data
            arena_data = await self.recommender._fetch_arena_leaderboard()
            if arena_data:
                expires_at = datetime.now() + timedelta(hours=6)
                await self.store.save_external_data_cache(
                    "arena_leaderboard", arena_data, expires_at
                )
            
            # Fetch and cache MTEB data  
            mteb_data = await self.recommender._fetch_mteb_scores()
            if mteb_data:
                expires_at = datetime.now() + timedelta(hours=12)
                await self.store.save_external_data_cache(
                    "mteb_scores", mteb_data, expires_at
                )
            
            # Cache internal evaluations
            internal_data = await self.recommender._fetch_internal_evaluations()
            if internal_data:
                expires_at = datetime.now() + timedelta(hours=1)
                await self.store.save_external_data_cache(
                    "internal_evaluations", internal_data, expires_at
                )
            
            logger.debug("External data sources cached successfully")
            
        except Exception as e:
            logger.warning(f"Failed to cache external sources: {e}")
    
    async def _aggregate_telemetry(self) -> None:
        """Aggregate recent telemetry data into model performance records."""
        try:
            logger.debug("Aggregating telemetry data...")
            
            # Load existing performance data
            performance_data = await self.store.load_all_model_performance()
            
            updated_count = 0
            for model_name, performance in performance_data.items():
                # Get recent telemetry stats
                stats = await self.store.get_model_telemetry_stats(model_name, hours_back=1)
                
                if stats["total_calls"] > 0:
                    # Update performance with telemetry data
                    alpha = 0.1  # Smoothing factor
                    
                    if performance.avg_latency_ms is None:
                        performance.avg_latency_ms = stats["avg_latency_ms"]
                    else:
                        performance.avg_latency_ms = (
                            (1 - alpha) * performance.avg_latency_ms + 
                            alpha * stats["avg_latency_ms"]
                        )
                    
                    performance.success_rate = (
                        (1 - alpha) * performance.success_rate +
                        alpha * stats["success_rate"]
                    )
                    
                    if stats["avg_cost_per_token"] > 0:
                        performance.cost_per_1k_tokens = stats["avg_cost_per_token"] * 1000
                    
                    performance.last_updated = datetime.now()
                    
                    # Save updated performance
                    await self.store.save_model_performance(performance)
                    updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Updated {updated_count} models with telemetry data")
                
        except Exception as e:
            logger.error(f"Telemetry aggregation failed: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old telemetry data and expired cache entries."""
        try:
            logger.info("🧹 Starting weekly data cleanup...")
            
            # Clean up telemetry events older than 30 days
            deleted_count = await self.store.cleanup_old_telemetry(days_to_keep=30)
            
            # Log database stats
            stats = await self.store.get_database_stats()
            
            logger.info(
                f"✅ Weekly cleanup completed. Deleted {deleted_count} old telemetry events. "
                f"Current stats: {stats}"
            )
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    async def trigger_manual_refresh(self) -> dict[str, Any]:
        """Manually trigger a data refresh (for admin endpoints)."""
        if not is_model_recommender_v2_enabled():
            return {
                "status": "disabled",
                "message": "Model Recommender V2 is not enabled"
            }
        
        start_time = datetime.now()
        
        try:
            await self._refresh_external_data()
            
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "status": "success",
                "duration_seconds": duration,
                "models_updated": len(self.recommender.performance_cache),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def get_scheduler_status(self) -> dict[str, Any]:
        """Get scheduler status and metrics."""
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            "is_running": self.is_running,
            "total_refresh_jobs": self.total_refresh_jobs,
            "failed_refresh_jobs": self.failed_refresh_jobs,
            "success_rate": (
                (self.total_refresh_jobs - self.failed_refresh_jobs) / 
                max(1, self.total_refresh_jobs)
            ),
            "last_refresh_time": self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            "jobs": jobs,
            "model_recommender_v2_enabled": is_model_recommender_v2_enabled()
        }