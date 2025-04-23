# backend/app/core/redis.py
import redis.asyncio as aioredis

# Aquí se guardará el pool
redis_pool: aioredis.Redis | None = None