"""
Advanced Analytics for StratMaster

This module provides advanced analytics capabilities including:
- Custom business metrics collection
- Real-time dashboard updates
- Business intelligence reporting
- User behavior analysis
- Revenue impact tracking
- Performance monitoring
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import asyncpg
import redis.asyncio as aioredis
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics we can collect."""
    COUNTER = "counter"
    GAUGE = "gauge" 
    HISTOGRAM = "histogram"


@dataclass
class MetricDefinition:
    """Definition of a custom metric."""
    name: str
    metric_type: MetricType
    description: str
    labels: list[str] = None
    buckets: list[float] = None  # For histograms
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


@dataclass
class MetricEvent:
    """Represents a metric event to be recorded."""
    metric_name: str
    value: int | float
    labels: dict[str, str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AnalyticsCollector:
    """Collects and manages custom analytics metrics."""
    
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or CollectorRegistry()
        self.metrics = {}
        self.metric_definitions = {}
        self.event_queue = asyncio.Queue()
        self.redis_client = None
        self.db_pool = None
        
    async def initialize(self, redis_url: str = None, db_url: str = None):
        """Initialize connections to Redis and database."""
        if redis_url:
            self.redis_client = await aioredis.from_url(redis_url)
        
        if db_url:
            self.db_pool = await asyncpg.create_pool(db_url)
    
    def register_metric(self, definition: MetricDefinition):
        """Register a custom metric definition."""
        self.metric_definitions[definition.name] = definition
        
        if definition.metric_type == MetricType.COUNTER:
            metric = Counter(
                definition.name,
                definition.description,
                definition.labels,
                registry=self.registry
            )
        elif definition.metric_type == MetricType.GAUGE:
            metric = Gauge(
                definition.name,
                definition.description,
                definition.labels,
                registry=self.registry
            )
        elif definition.metric_type == MetricType.HISTOGRAM:
            metric = Histogram(
                definition.name,
                definition.description,
                definition.labels,
                buckets=definition.buckets,
                registry=self.registry
            )
        else:
            raise ValueError(f"Unsupported metric type: {definition.metric_type}")
        
        self.metrics[definition.name] = metric
        logger.info(f"Registered metric: {definition.name}")
    
    async def record_metric(self, event: MetricEvent):
        """Record a metric event."""
        if event.metric_name not in self.metrics:
            logger.warning(f"Metric not registered: {event.metric_name}")
            return
        
        metric = self.metrics[event.metric_name]
        definition = self.metric_definitions[event.metric_name]
        
        try:
            if definition.metric_type == MetricType.COUNTER:
                if event.labels:
                    metric.labels(**event.labels).inc(event.value)
                else:
                    metric.inc(event.value)
            elif definition.metric_type == MetricType.GAUGE:
                if event.labels:
                    metric.labels(**event.labels).set(event.value)
                else:
                    metric.set(event.value)
            elif definition.metric_type == MetricType.HISTOGRAM:
                if event.labels:
                    metric.labels(**event.labels).observe(event.value)
                else:
                    metric.observe(event.value)
            
            # Store in Redis for real-time analytics
            if self.redis_client:
                await self._store_in_redis(event)
            
            # Store in database for historical analysis
            if self.db_pool:
                await self._store_in_database(event)
                
        except Exception as e:
            logger.error(f"Failed to record metric {event.metric_name}: {e}")
    
    async def _store_in_redis(self, event: MetricEvent):
        """Store metric event in Redis for real-time access."""
        key = f"metrics:{event.metric_name}"
        
        # Store latest value
        await self.redis_client.hset(
            key,
            mapping={
                "value": str(event.value),
                "timestamp": event.timestamp.isoformat(),
                "labels": json.dumps(event.labels)
            }
        )
        
        # Add to time series
        ts_key = f"metrics:ts:{event.metric_name}"
        await self.redis_client.zadd(
            ts_key,
            {json.dumps({
                "value": event.value,
                "labels": event.labels
            }): event.timestamp.timestamp()}
        )
        
        # Keep only last 24 hours
        cutoff = (datetime.utcnow() - timedelta(hours=24)).timestamp()
        await self.redis_client.zremrangebyscore(ts_key, 0, cutoff)
    
    async def _store_in_database(self, event: MetricEvent):
        """Store metric event in database for historical analysis."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO analytics_metrics 
                (metric_name, value, labels, timestamp)
                VALUES ($1, $2, $3, $4)
            """, 
            event.metric_name,
            event.value, 
            json.dumps(event.labels),
            event.timestamp
            )
    
    async def get_metric_data(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None,
        labels_filter: dict[str, str] = None
    ) -> list[dict[str, Any]]:
        """Get metric data for analysis."""
        if not self.db_pool:
            logger.warning("Database not configured for metric retrieval")
            return []
        
        query = "SELECT * FROM analytics_metrics WHERE metric_name = $1"
        params = [metric_name]
        
        if start_time:
            query += " AND timestamp >= $2"
            params.append(start_time)
            
        if end_time:
            query += f" AND timestamp <= ${len(params) + 1}"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT 10000"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                data = {
                    "metric_name": row["metric_name"],
                    "value": row["value"],
                    "labels": json.loads(row["labels"] or "{}"),
                    "timestamp": row["timestamp"]
                }
                
                # Apply label filtering
                if labels_filter:
                    if all(data["labels"].get(k) == v for k, v in labels_filter.items()):
                        results.append(data)
                else:
                    results.append(data)
            
            return results


class StrategyCoreAnalytics:
    """Core analytics for strategy-related metrics."""
    
    def __init__(self, collector: AnalyticsCollector):
        self.collector = collector
        
    async def record_strategy_success(
        self,
        tenant_id: str,
        category: str,
        user_id: str,
        success: bool = True
    ):
        """Record strategy success/failure."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_strategy_success_total",
            value=1 if success else 0,
            labels={
                "tenant_id": tenant_id,
                "category": category,
                "user_id": user_id,
                "outcome": "success" if success else "failure"
            }
        ))
    
    async def record_strategy_generation_time(
        self,
        tenant_id: str,
        complexity: str,
        duration_seconds: float
    ):
        """Record time taken to generate strategy."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_strategy_generation_duration",
            value=duration_seconds,
            labels={
                "tenant_id": tenant_id,
                "complexity": complexity
            }
        ))
    
    async def record_constitutional_violation(
        self,
        violation_type: str,
        severity: str,
        tenant_id: str
    ):
        """Record constitutional violation."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_constitutional_violations_total",
            value=1,
            labels={
                "violation_type": violation_type,
                "severity": severity,
                "tenant_id": tenant_id
            }
        ))
    
    async def update_compliance_score(
        self,
        tenant_id: str,
        category: str,
        score: float
    ):
        """Update constitutional compliance score."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_constitutional_compliance_score",
            value=score,
            labels={
                "tenant_id": tenant_id,
                "category": category
            }
        ))


class UserAnalytics:
    """User behavior and engagement analytics."""
    
    def __init__(self, collector: AnalyticsCollector):
        self.collector = collector
    
    async def record_user_action(
        self,
        user_id: str,
        role: str,
        action_type: str,
        tenant_id: str
    ):
        """Record user action."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_user_actions_total",
            value=1,
            labels={
                "user_id": user_id,
                "role": role,
                "action_type": action_type,
                "tenant_id": tenant_id
            }
        ))
    
    async def record_session_duration(
        self,
        role: str,
        tenant_id: str,
        duration_seconds: float
    ):
        """Record user session duration."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_user_session_duration",
            value=duration_seconds,
            labels={
                "role": role,
                "tenant_id": tenant_id
            }
        ))
    
    async def record_user_satisfaction(
        self,
        tenant_id: str,
        feature: str,
        score: float
    ):
        """Record user satisfaction rating."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_user_satisfaction_score",
            value=score,
            labels={
                "tenant_id": tenant_id,
                "feature": feature
            }
        ))


class BusinessAnalytics:
    """Business impact and ROI analytics."""
    
    def __init__(self, collector: AnalyticsCollector):
        self.collector = collector
    
    async def record_revenue_impact(
        self,
        tenant_id: str,
        impact_type: str,
        amount: float
    ):
        """Record revenue impact."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_revenue_impact_total",
            value=amount,
            labels={
                "tenant_id": tenant_id,
                "impact_type": impact_type
            }
        ))
    
    async def record_cost_savings(
        self,
        tenant_id: str,
        savings_type: str,
        amount: float
    ):
        """Record cost savings."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_cost_savings_total",
            value=amount,
            labels={
                "tenant_id": tenant_id,
                "savings_type": savings_type
            }
        ))
    
    async def update_roi_score(
        self,
        tenant_id: str,
        time_period: str,
        roi_score: float
    ):
        """Update ROI score."""
        await self.collector.record_metric(MetricEvent(
            metric_name="stratmaster_roi_score",
            value=roi_score,
            labels={
                "tenant_id": tenant_id,
                "time_period": time_period
            }
        ))


class RealtimeDashboard:
    """Real-time dashboard data provider."""
    
    def __init__(self, collector: AnalyticsCollector):
        self.collector = collector
        
    async def get_executive_summary(self, tenant_id: str = None) -> dict[str, Any]:
        """Get executive summary metrics."""
        filter_labels = {"tenant_id": tenant_id} if tenant_id else None
        
        # Get recent data for key metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        success_data = await self.collector.get_metric_data(
            "stratmaster_strategy_success_total",
            start_time,
            end_time,
            filter_labels
        )
        
        violations_data = await self.collector.get_metric_data(
            "stratmaster_constitutional_violations_total", 
            start_time,
            end_time,
            filter_labels
        )
        
        user_actions_data = await self.collector.get_metric_data(
            "stratmaster_user_actions_total",
            start_time, 
            end_time,
            filter_labels
        )
        
        # Calculate summary statistics
        total_strategies = len(success_data)
        successful_strategies = sum(1 for d in success_data if d["value"] > 0)
        success_rate = (successful_strategies / total_strategies * 100) if total_strategies > 0 else 0
        
        total_violations = sum(d["value"] for d in violations_data)
        compliance_rate = max(0, 100 - (total_violations / max(total_strategies, 1) * 100))
        
        active_users = len(set(d["labels"].get("user_id", "") for d in user_actions_data))
        
        return {
            "success_rate": round(success_rate, 2),
            "compliance_rate": round(compliance_rate, 2),
            "total_strategies": total_strategies,
            "active_users": active_users,
            "total_violations": total_violations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_user_engagement_metrics(self, tenant_id: str = None) -> dict[str, Any]:
        """Get user engagement metrics."""
        filter_labels = {"tenant_id": tenant_id} if tenant_id else None
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        actions_data = await self.collector.get_metric_data(
            "stratmaster_user_actions_total",
            start_time,
            end_time,
            filter_labels
        )
        
        satisfaction_data = await self.collector.get_metric_data(
            "stratmaster_user_satisfaction_score",
            start_time,
            end_time,
            filter_labels
        )
        
        # Analyze engagement by role
        role_engagement = {}
        for data in actions_data:
            role = data["labels"].get("role", "unknown")
            role_engagement[role] = role_engagement.get(role, 0) + data["value"]
        
        # Calculate average satisfaction
        avg_satisfaction = (
            sum(d["value"] for d in satisfaction_data) / len(satisfaction_data)
            if satisfaction_data else 0
        )
        
        return {
            "role_engagement": role_engagement,
            "average_satisfaction": round(avg_satisfaction, 2),
            "total_actions": sum(d["value"] for d in actions_data),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global analytics instances
analytics_collector = AnalyticsCollector()
strategy_analytics = StrategyCoreAnalytics(analytics_collector)
user_analytics = UserAnalytics(analytics_collector)
business_analytics = BusinessAnalytics(analytics_collector)
dashboard = RealtimeDashboard(analytics_collector)


async def initialize_analytics(config_path: str = None):
    """Initialize analytics system."""
    if config_path is None:
        config_path = os.getenv("ANALYTICS_CONFIG_PATH", "configs/analytics/analytics-config.yaml")
    
    import yaml
    
    try:
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        
        # Register custom metrics
        metrics_config = config_data.get("custom_metrics", [])
        for metric_config in metrics_config:
            definition = MetricDefinition(
                name=metric_config["name"],
                metric_type=MetricType(metric_config["type"]),
                description=metric_config["description"],
                labels=metric_config.get("labels", []),
                buckets=metric_config.get("buckets")
            )
            analytics_collector.register_metric(definition)
        
        # Initialize connections
        redis_url = os.getenv("REDIS_URL")
        db_url = os.getenv("DATABASE_URL")
        
        await analytics_collector.initialize(redis_url, db_url)
        
        logger.info(f"Initialized analytics with {len(metrics_config)} custom metrics")
        
    except FileNotFoundError:
        logger.warning(f"Analytics config file not found: {config_path}")
    except Exception as e:
        logger.error(f"Failed to initialize analytics: {e}")
        raise


# Convenience functions for FastAPI integration
async def track_strategy_outcome(
    tenant_id: str,
    category: str, 
    user_id: str,
    success: bool,
    duration_seconds: float = None
):
    """Track strategy outcome with timing."""
    await strategy_analytics.record_strategy_success(
        tenant_id, category, user_id, success
    )
    
    if duration_seconds:
        await strategy_analytics.record_strategy_generation_time(
            tenant_id, "standard", duration_seconds
        )


async def track_user_activity(
    user_id: str,
    role: str,
    action_type: str,
    tenant_id: str
):
    """Track user activity."""
    await user_analytics.record_user_action(
        user_id, role, action_type, tenant_id
    )


async def get_dashboard_data(tenant_id: str = None) -> dict[str, Any]:
    """Get comprehensive dashboard data."""
    executive_summary = await dashboard.get_executive_summary(tenant_id)
    engagement_metrics = await dashboard.get_user_engagement_metrics(tenant_id)
    
    return {
        "executive_summary": executive_summary,
        "user_engagement": engagement_metrics
    }


# Initialize analytics on module import
try:
    asyncio.create_task(initialize_analytics())
except Exception as e:
    logger.warning(f"Could not initialize analytics: {e}")