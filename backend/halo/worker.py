"""arq worker: video analysis, creator refreshes, scout runs, and the scheduled routines.

Run with:  arq halo.worker.WorkerSettings
"""

import logging
from datetime import UTC, datetime, timedelta

from arq import cron
from sqlalchemy import or_, select

from halo.agent.scout import run_brief
from halo.config import get_settings
from halo.db import get_sessionmaker
from halo.logs import show_halo_logs
from halo.models import Brief, BriefStatus, CreatorAccount, Platform
from halo.queue import redis_settings
from halo.services.analyze import analyze_video
from halo.services.ingest import refresh_creator

log = logging.getLogger(__name__)


async def analyze_video_task(ctx, video_id: int) -> None:
    async with get_sessionmaker()() as session:
        await analyze_video(session, video_id)


async def refresh_creator_task(ctx, creator_id: int) -> None:
    async with get_sessionmaker()() as session:
        new_ids = await refresh_creator(session, creator_id)
    for video_id in new_ids:
        await ctx["redis"].enqueue_job("analyze_video_task", video_id)
    log.info("Creator %s: %d new videos queued for analysis", creator_id, len(new_ids))


async def run_brief_task(ctx, brief_id: int) -> None:
    await run_brief(brief_id)


async def refresh_stale_creators(ctx) -> None:
    """Hourly: re-sync creators whose connected accounts were not synced recently."""
    cutoff = datetime.now(UTC) - timedelta(hours=get_settings().creator_refresh_hours)
    async with get_sessionmaker()() as session:
        creator_ids = set(
            await session.scalars(
                select(CreatorAccount.creator_id).where(
                    CreatorAccount.platform.in_([Platform.instagram, Platform.youtube]),
                    or_(CreatorAccount.last_synced_at.is_(None), CreatorAccount.last_synced_at < cutoff),
                )
            )
        )
    for creator_id in creator_ids:
        await ctx["redis"].enqueue_job("refresh_creator_task", creator_id)


async def rerun_standing_briefs(ctx) -> None:
    """Daily: standing briefs search again and push only new matches to Telegram."""
    async with get_sessionmaker()() as session:
        brief_ids = list(
            await session.scalars(
                select(Brief.id).where(Brief.standing.is_(True), Brief.status != BriefStatus.running)
            )
        )
    for brief_id in brief_ids:
        await ctx["redis"].enqueue_job("run_brief_task", brief_id)


async def startup(ctx) -> None:
    show_halo_logs()


class WorkerSettings:
    functions = [analyze_video_task, refresh_creator_task, run_brief_task]
    on_startup = startup
    cron_jobs = [
        cron(refresh_stale_creators, minute=5),
        cron(rerun_standing_briefs, hour=4, minute=0),  # 09:00 in Tashkent (UTC+5)
    ]
    redis_settings = redis_settings()
    max_jobs = 10
    job_timeout = 900
