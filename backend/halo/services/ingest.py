"""Pull creators' recent videos from their platforms and store new ones for analysis."""

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from halo.models import Creator, Platform, Video, VideoStatus
from halo.sources import get_source
from halo.sources.base import SourceError

log = logging.getLogger(__name__)


async def refresh_creator(session: AsyncSession, creator_id: int, limit: int = 12) -> list[int]:
    """Sync every connected account of a creator. Returns ids of newly found videos."""
    creator = await session.get(Creator, creator_id)
    if creator is None:
        raise LookupError(f"Creator {creator_id} not found")

    new_ids: list[int] = []
    for account in creator.accounts:
        source = get_source(account.platform)
        if source is None:
            continue
        try:
            snapshot = await source.fetch(account, limit=limit)
        except SourceError as e:
            log.warning("Skipping %s account %s: %s", account.platform, account.handle, e)
            continue

        account.external_id = snapshot.external_id or account.external_id
        account.followers = snapshot.followers
        account.avg_views = snapshot.avg_views
        account.engagement_rate = snapshot.engagement_rate
        account.last_synced_at = datetime.now(UTC)

        for item in snapshot.videos:
            existing = await session.scalar(
                select(Video).where(Video.platform == account.platform, Video.external_id == item.external_id)
            )
            if existing:
                existing.views, existing.likes, existing.comments = item.views, item.likes, item.comments
                existing.media_url = item.media_url or existing.media_url
                continue
            video = Video(
                creator_id=creator.id,
                account_id=account.id,
                platform=account.platform,
                external_id=item.external_id,
                url=item.url,
                media_url=item.media_url,
                frame_urls=item.frame_urls,
                caption=item.caption,
                posted_at=item.posted_at,
                views=item.views,
                likes=item.likes,
                comments=item.comments,
                duration_s=item.duration_s,
                status=VideoStatus.pending,
            )
            session.add(video)
            await session.flush()
            new_ids.append(video.id)

    await session.commit()
    return new_ids


async def add_manual_video(session: AsyncSession, creator_id: int, path: Path, caption: str = "") -> Video:
    """A video a creator uploaded or sent to the Telegram bot."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    existing = await session.scalar(
        select(Video).where(Video.platform == Platform.manual, Video.external_id == digest)
    )
    if existing:
        return existing
    video = Video(
        creator_id=creator_id,
        platform=Platform.manual,
        external_id=digest,
        local_path=str(path),
        caption=caption,
        posted_at=datetime.now(UTC),
        status=VideoStatus.pending,
    )
    session.add(video)
    await session.commit()
    return video
