"""Find creators similar to one a brand liked ("more like this")."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from halo.models import Creator


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def tag_similarity(seed: Creator, other: Creator) -> float:
    """Fallback when there are no embeddings: topics, languages and quality."""
    topics = _jaccard(seed.niche_tags, other.niche_tags)
    langs = _jaccard(seed.languages, other.languages)
    quality = 0.0
    if seed.avg_quality is not None and other.avg_quality is not None:
        quality = 1 - abs(seed.avg_quality - other.avg_quality) / 9
    return round(0.7 * topics + 0.2 * langs + 0.1 * quality, 4)


async def find_lookalikes(session: AsyncSession, creator_id: int, limit: int = 10) -> list[tuple[Creator, float]]:
    seed = await session.get(Creator, creator_id)
    if seed is None:
        raise LookupError(f"Creator {creator_id} not found")

    if seed.embedding is not None:
        distance = Creator.embedding.cosine_distance(seed.embedding)
        rows = await session.execute(
            select(Creator, distance)
            .where(Creator.id != seed.id, Creator.embedding.is_not(None), Creator.brand_safety_risk != "high")
            .order_by(distance)
            .limit(limit)
        )
        return [(creator, round(1 - float(dist), 4)) for creator, dist in rows]

    if not seed.niche_tags:
        return []
    candidates = await session.scalars(
        select(Creator).where(
            Creator.id != seed.id,
            Creator.niche_tags.overlap(seed.niche_tags),
            Creator.brand_safety_risk != "high",
        )
    )
    scored = sorted(((c, tag_similarity(seed, c)) for c in candidates), key=lambda x: x[1], reverse=True)
    return scored[:limit]
