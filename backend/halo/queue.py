"""Background jobs go through Redis (arq). The API and bot only enqueue; the worker runs them."""

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from halo.config import get_settings

_pool: ArqRedis | None = None


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class JobQueue:
    async def enqueue(self, function: str, *args) -> None:
        global _pool
        if _pool is None:
            _pool = await create_pool(redis_settings())
        await _pool.enqueue_job(function, *args)


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def get_queue() -> JobQueue:
    return JobQueue()
