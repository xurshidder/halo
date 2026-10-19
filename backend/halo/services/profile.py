"""Roll a creator's video analyses up into one profile used for search and matching."""

from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from halo.ai.embeddings import mean_vector
from halo.models import Creator, Video, VideoAnalysis

RECENT_VIDEOS = 12
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


async def recent_analyses(session: AsyncSession, creator_id: int, limit: int = RECENT_VIDEOS) -> list[VideoAnalysis]:
    rows = await session.execute(
        select(VideoAnalysis)
        .join(Video, Video.id == VideoAnalysis.video_id)
        .where(Video.creator_id == creator_id)
        .order_by(Video.posted_at.desc().nulls_last(), VideoAnalysis.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars())


async def refresh_creator_profile(session: AsyncSession, creator_id: int) -> Creator:
    creator = await session.get(Creator, creator_id)
    if creator is None:
        raise LookupError(f"Creator {creator_id} not found")
    analyses = await recent_analyses(session, creator_id)
    if not analyses:
        return creator

    n = len(analyses)
    lang_counts = Counter(lang for a in analyses for lang in dict.fromkeys(a.languages))
    creator.languages = [lang for lang, c in lang_counts.most_common() if c / n >= 0.25]
    creator.niche_tags = [tag for tag, _ in Counter(t for a in analyses for t in dict.fromkeys(a.niche_tags)).most_common(8)]
    creator.avg_quality = round(sum(a.production_quality for a in analyses) / n, 2)
    creator.avg_hook_strength = round(sum(a.hook_strength for a in analyses) / n, 2)
    creator.brand_safety_risk = max((a.brand_safety_risk for a in analyses), key=lambda r: RISK_ORDER.get(r, 0))
    creator.summary = " ".join(list(dict.fromkeys(a.summary for a in analyses))[:3])
    vectors = [a.embedding for a in analyses if a.embedding is not None]
    creator.embedding = mean_vector([list(v) for v in vectors]) if vectors else None
    creator.last_refreshed_at = datetime.now(UTC)
    return creator
