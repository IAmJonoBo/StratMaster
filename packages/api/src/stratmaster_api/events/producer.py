"""
Event producer for emitting events to Redis Streams or Kafka.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional
import uuid

from .schemas import BaseEvent, ENABLE_EVENT_STREAMING

logger = logging.getLogger(__name__)


class EventProducer:
    """Produces events to Redis Streams or Kafka."""
    
    def __init__(self):
        self.redis_client = None
        self.kafka_producer = None
        self.enabled = ENABLE_EVENT_STREAMING
        self.stream_name = "stratmaster-events"
        
    async def initialize(self, redis_url: str = None, kafka_config: Dict[str, Any] = None):
        """Initialize event producer connections."""
        if not self.enabled:
            logger.info("Event streaming disabled, producer will no-op")
            return
            
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self.redis_client = await aioredis.from_url(redis_url)
                logger.info("Redis event producer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis producer: {e}")
        
        if kafka_config:
            try:
                # Import Kafka client lazily to avoid hard dependency
                from aiokafka import AIOKafkaProducer
                self.kafka_producer = AIOKafkaProducer(**kafka_config)
                await self.kafka_producer.start()
                logger.info("Kafka event producer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Kafka producer: {e}")
    
    async def emit_event(self, event: BaseEvent, correlation_id: Optional[str] = None) -> bool:
        """Emit an event to the configured stream."""
        if not self.enabled:
            logger.debug(f"Event streaming disabled, skipping event: {event.metadata.event_type}")
            return False
        
        try:
            # Serialize event
            event_data = event.model_dump()
            
            # Add correlation ID if provided
            if correlation_id:
                event_data["metadata"]["correlation_id"] = correlation_id
            
            # Emit to Redis Streams first (primary)
            if self.redis_client:
                success = await self._emit_to_redis(event_data)
                if success:
                    return True
            
            # Fallback to Kafka
            if self.kafka_producer:
                success = await self._emit_to_kafka(event_data)
                if success:
                    return True
            
            # No transport available
            logger.warning(f"No event transport available for event: {event.metadata.event_type}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to emit event {event.metadata.event_type}: {e}")
            return False
    
    async def _emit_to_redis(self, event_data: Dict[str, Any]) -> bool:
        """Emit event to Redis Streams."""
        try:
            # Use XADD to add to stream
            stream_id = await self.redis_client.xadd(
                self.stream_name,
                {
                    "event_type": event_data["metadata"]["event_type"],
                    "event_data": json.dumps(event_data),
                    "tenant_id": event_data["metadata"]["tenant_id"],
                    "timestamp": event_data["metadata"]["timestamp"]
                }
            )
            
            logger.debug(f"Event emitted to Redis stream {self.stream_name}: {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to emit to Redis: {e}")
            return False
    
    async def _emit_to_kafka(self, event_data: Dict[str, Any]) -> bool:
        """Emit event to Kafka."""
        try:
            event_type = event_data["metadata"]["event_type"]
            tenant_id = event_data["metadata"]["tenant_id"]
            
            # Use event type as topic
            topic = f"stratmaster.{event_type.replace('.', '-')}"
            
            # Serialize event data
            value = json.dumps(event_data).encode('utf-8')
            
            # Use tenant_id as key for partitioning
            key = tenant_id.encode('utf-8') if tenant_id else None
            
            # Send to Kafka
            await self.kafka_producer.send_and_wait(
                topic,
                value=value,
                key=key,
                headers={"event_type": event_type.encode('utf-8')}
            )
            
            logger.debug(f"Event emitted to Kafka topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to emit to Kafka: {e}")
            return False
    
    async def close(self):
        """Close producer connections."""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.kafka_producer:
            await self.kafka_producer.stop()


# Global event producer instance
event_producer = EventProducer()


async def emit_event(event: BaseEvent, correlation_id: Optional[str] = None) -> bool:
    """Convenience function to emit an event."""
    return await event_producer.emit_event(event, correlation_id)


async def initialize_event_producer(
    redis_url: str = None,
    kafka_config: Dict[str, Any] = None
):
    """Initialize the global event producer."""
    if redis_url is None:
        redis_url = os.getenv("REDIS_URL")
    
    await event_producer.initialize(redis_url, kafka_config)