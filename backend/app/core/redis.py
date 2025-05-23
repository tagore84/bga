# backend/app/core/redis.py
import redis.asyncio as aioredis
import json

# Aquí se guardará el pool
redis_pool: aioredis.Redis | None = None

async def publish_stream_event(stream_key: str, data: dict):
    if redis_pool is None:
        raise RuntimeError("Redis pool not initialized")
    await redis_pool.xadd(stream_key, {
        k: (json.dumps(v) if not isinstance(v, str) else v)
        for k, v in data.items()
    })