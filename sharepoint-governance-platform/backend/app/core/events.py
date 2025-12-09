import redis.asyncio as redis
import json
import logging
import os
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: redis.Redis = None
        self.channel_name = "spg_events"

    async def connect(self):
        """Connect to Redis"""
        logger.info(f"Connecting to Event Bus at {self.redis_url}")
        self.redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        try:
            await self.redis.ping()
            logger.info("Successfully connected to Event Bus")
        except Exception as e:
            logger.error(f"Failed to connect to Event Bus: {e}")

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Event Bus")

    async def publish(self, topic: str, payload: Dict[str, Any]):
        """Publish an event to a topic"""
        if not self.redis:
            logger.warning("Event Bus not connected. Cannot publish.")
            return

        message = {
            "topic": topic,
            "payload": payload
        }
        
        try:
            # Using basic Pub/Sub for now. 
            # In Phase 2, this will be upgraded to Redis Streams for persistence.
            await self.redis.publish(self.channel_name, json.dumps(message))
            logger.debug(f"Published event to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def subscribe(self, callback: Callable[[str, Dict[str, Any]], Awaitable[None]]):
        """Subscribe to all events"""
        if not self.redis:
            logger.warning("Event Bus not connected. Cannot subscribe.")
            return

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel_name)
        
        logger.info(f"Subscribed to {self.channel_name}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await callback(data.get("topic"), data.get("payload"))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

event_bus = EventBus()
