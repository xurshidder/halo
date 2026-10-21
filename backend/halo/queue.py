"""Background jobs go through Redis (arq). The API and bot only enqueue; the worker runs them.

With HALO_JOBS=inline (one-service hosts with no worker), the API process runs the same job
functions itself, in the background.
"""

import asyncio

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from halo.config import get_settings

_pool: ArqRedis | None = None
_inline: set[asyncio.Task] = set()  # keeps running inline jobs from being garbage-collected


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


def run_inline(function: str, *args) -> asyncio.Task:
    from halo.worker import run_job  # the job functions live with the worker

    task = asyncio.create_task(run_job(function, *args))
    _inline.add(task)
    task.add_done_callback(_inline.discard)
    return task


class JobQueue:
    async def enqueue(self, function: str, *args) -> None:
        if get_settings().jobs == "inline":
            run_inline(function, *args)
            return
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
