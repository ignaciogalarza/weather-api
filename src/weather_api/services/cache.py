"""Redis caching service with graceful degradation."""

import json
from typing import Any

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from weather_api.config import settings

logger = structlog.get_logger()

# Global Redis client
_redis_client: Redis | None = None


async def init_cache() -> None:
    """Initialize Redis connection if configured."""
    global _redis_client

    if not settings.cache_enabled or not settings.redis_url:
        logger.info("cache_disabled", reason="not configured")
        return

    try:
        _redis_client = Redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True,
        )
        # Test connection
        await _redis_client.ping()  # type: ignore[misc]
        logger.info("cache_connected", url=settings.redis_url)
    except RedisError as e:
        logger.warning("cache_connection_failed", error=str(e))
        _redis_client = None


async def close_cache() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("cache_closed")


async def cache_get(key: str) -> Any | None:
    """Get value from cache. Returns None on miss or error."""
    if _redis_client is None:
        return None

    try:
        value = await _redis_client.get(key)
        if value is not None:
            logger.debug("cache_hit", key=key)
            return json.loads(str(value))
        logger.debug("cache_miss", key=key)
        return None
    except RedisError as e:
        logger.warning("cache_get_error", key=key, error=str(e))
        return None
    except json.JSONDecodeError as e:
        logger.warning("cache_decode_error", key=key, error=str(e))
        return None


async def cache_set(key: str, value: Any, ttl: int) -> bool:
    """Set value in cache with TTL. Returns True on success."""
    if _redis_client is None:
        return False

    try:
        await _redis_client.set(key, json.dumps(value), ex=ttl)
        logger.debug("cache_set", key=key, ttl=ttl)
        return True
    except (RedisError, TypeError) as e:
        logger.warning("cache_set_error", key=key, error=str(e))
        return False


def get_coordinates_cache_key(city: str) -> str:
    """Generate cache key for coordinates lookup."""
    return f"coords:{city.lower().strip()}"


def get_weather_cache_key(lat: float, lon: float) -> str:
    """Generate cache key for weather lookup."""
    # Round to 2 decimal places for reasonable precision
    return f"weather:{lat:.2f}:{lon:.2f}"
