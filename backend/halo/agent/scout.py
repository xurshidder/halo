"""The scout agent: brief in, ranked shortlist with outreach drafts out.

load -> plan -> retrieve -> score -> rank -> draft -> save -> notify

Built as a LangGraph state graph (as in Kuli's stack). Every model call goes through
the Anthropic SDK (halo.ai.claude), and every step's output is structured.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import or_, select

from halo.agent import prompts
from halo.ai import claude, embeddings
from halo.config import get_settings
from halo.db import get_sessionmaker
from halo.models import Brand, Brief, BriefStatus, Creator, ShortlistEntry, ShortlistStatus
from halo.services.profile import recent_analyses

log = logging.getLogger(__name__)

MIN_SCORE = 50
BROWSE_LIMIT = 500


class ScoutState(TypedDict, total=False):
    brief_id: int
    brand_id: int
    brand_context: str
    brief_text: str
    criteria: dict
    candidate_ids: list[int]
    scores: list[dict]
    shortlist: list[dict]
    new_entry_ids: list[int]


def _topic_score(criteria: prompts.BriefCriteria, creator: Creator) -> float:
    topics = {t.lower() for t in criteria.topics}
    tags = set(creator.niche_tags)
    overlap = len(topics & tags)
    summary = creator.summary.lower()
    mentions = sum(1 for t in topics if t in summary)
    quality = (creator.avg_quality or 5) / 10
    return overlap * 2 + mentions + quality


async def load(state: ScoutState) -> ScoutState:
    async with get_sessionmaker()() as session:
        brief = await session.get(Brief, state["brief_id"])
        if brief is None:
            raise LookupError(f"Brief {state['brief_id']} not found")
        brand = await session.get(Brand, brief.brand_id)
        brief.status = BriefStatus.running
        brief.error = None
        await session.commit()
        return {
            "brand_id": brand.id,
            "brand_context": prompts.brand_context(brand),
            "brief_text": f"Title: {brief.title}\n\n{brief.text}",
        }


async def plan(state: ScoutState) -> ScoutState:
    criteria = await claude.parse(
        prompts.BriefCriteria,
        system=prompts.PLANNER_SYSTEM,
        content=f"{state['brand_context']}\n\n<brief>\n{state['brief_text']}\n</brief>",
        effort=get_settings().claude_effort_scoring,
    )
    return {"criteria": criteria.model_dump()}


async def retrieve(state: ScoutState) -> ScoutState:
    settings = get_settings()
    criteria = prompts.BriefCriteria(**state["criteria"])
    async with get_sessionmaker()() as session:
        rejected = select(ShortlistEntry.creator_id).where(
            ShortlistEntry.brief_id == state["brief_id"], ShortlistEntry.status == ShortlistStatus.rejected
        )
        query = select(Creator).where(
            Creator.summary != "",
            Creator.brand_safety_risk.in_(["low", "medium"]),
            Creator.id.not_in(rejected),
        )
        if criteria.languages:
            query = query.where(Creator.languages.overlap([lang.lower() for lang in criteria.languages]))
        if criteria.max_price_uzs:
            query = query.where(or_(Creator.price_uzs.is_(None), Creator.price_uzs <= criteria.max_price_uzs))

        vectors = await embeddings.embed([criteria.search_text], input_type="query")
        if vectors:
            distance = Creator.embedding.cosine_distance(vectors[0])
            query = query.where(Creator.embedding.is_not(None)).order_by(distance).limit(BROWSE_LIMIT)
            creators = list(await session.scalars(query))
        else:
            creators = list(await session.scalars(query.limit(BROWSE_LIMIT)))
            creators.sort(key=lambda c: _topic_score(criteria, c), reverse=True)

        if criteria.min_followers:
            creators = [
                c for c in creators
                if max((a.followers or 0 for a in c.accounts), default=0) >= criteria.min_followers
            ]
    return {"candidate_ids": [c.id for c in creators[: settings.candidate_pool_size]]}


def _has_candidates(state: ScoutState) -> str:
    return "score" if state.get("candidate_ids") else "save"


async def _candidate_dossier(session, creator_id: int) -> str:
    creator = await session.get(Creator, creator_id)
    analyses = await recent_analyses(session, creator_id, limit=6)
    accounts = [
        {
            "platform": a.platform,
            "handle": a.handle,
            "followers": a.followers,
            "avg_views": a.avg_views,
            "engagement_rate": a.engagement_rate,
        }
        for a in creator.accounts
    ]
    videos = [
        {
            "video_id": a.video_id,
            "summary": a.summary,
            "hook": a.hook,
            "hook_strength": a.hook_strength,
            "pacing": a.pacing,
            "setting": a.setting,
            "energy": a.energy,
            "tone": a.on_screen_tone,
            "languages": a.languages,
            "topics": a.niche_tags,
            "production_quality": a.production_quality,
            "authenticity": a.authenticity,
            "brand_safety_risk": a.brand_safety_risk,
            "brand_safety_flags": a.brand_safety_flags,
        }
        for a in analyses
    ]
    profile = {
        "creator_id": creator.id,
        "name": creator.display_name,
        "city": creator.city,
        "bio": creator.bio,
        "price_uzs": creator.price_uzs,
        "languages": creator.languages,
        "topics": creator.niche_tags,
        "accounts": accounts,
        "recent_videos": videos,
    }
    return json.dumps(profile, ensure_ascii=False, indent=1)


async def score(state: ScoutState) -> ScoutState:
    settings = get_settings()
    async with get_sessionmaker()() as session:
        dossiers = {cid: await _candidate_dossier(session, cid) for cid in state["candidate_ids"]}

    # Brand + criteria are identical for every candidate, so they sit in the cached system prompt.
    system = claude.cached_system(
        f"{prompts.SCORER_INSTRUCTIONS}\n\n{state['brand_context']}\n\n"
        f"<criteria>\n{json.dumps(state['criteria'], ensure_ascii=False, indent=1)}\n</criteria>"
    )
    limit = asyncio.Semaphore(settings.scoring_concurrency)

    async def score_one(creator_id: int) -> dict | None:
        async with limit:
            try:
                result = await claude.parse(
                    prompts.CandidateScore,
                    system=system,
                    content=f"<creator>\n{dossiers[creator_id]}\n</creator>\n\nScore this creator for the brief.",
                    effort=settings.claude_effort_scoring,
                )
            except claude.ClaudeError as e:
                log.warning("Scoring creator %s failed: %s", creator_id, e)
                return None
        return {"creator_id": creator_id, **result.model_dump(), "score": max(0, min(100, result.score))}

    results = await asyncio.gather(*(score_one(cid) for cid in state["candidate_ids"]))
    return {"scores": [r for r in results if r is not None]}


async def rank(state: ScoutState) -> ScoutState:
    good = [s for s in state.get("scores", []) if s["score"] >= MIN_SCORE]
    good.sort(key=lambda s: s["score"], reverse=True)
    return {"shortlist": good[: get_settings().shortlist_size]}


async def draft(state: ScoutState) -> ScoutState:
    settings = get_settings()
    criteria = prompts.BriefCriteria(**state["criteria"])
    system = claude.cached_system(f"{prompts.OUTREACH_INSTRUCTIONS}\n\n{state['brand_context']}")
    async with get_sessionmaker()() as session:
        dossiers = {s["creator_id"]: await _candidate_dossier(session, s["creator_id"]) for s in state["shortlist"]}
    limit = asyncio.Semaphore(settings.scoring_concurrency)

    async def draft_one(entry: dict) -> dict:
        async with limit:
            try:
                result = await claude.parse(
                    prompts.OutreachDraft,
                    system=system,
                    content=(
                        f"What the brand wants: {criteria.summary}\n"
                        f"Why this creator fits: {entry['fit_summary']}\n"
                        f"Write in: {entry['outreach_language']}\n\n"
                        f"<creator>\n{dossiers[entry['creator_id']]}\n</creator>"
                    ),
                    effort=settings.claude_effort_outreach,
                )
                return {**entry, "outreach_message": result.message}
            except claude.ClaudeError as e:
                log.warning("Outreach draft for creator %s failed: %s", entry["creator_id"], e)
                return {**entry, "outreach_message": None}

    return {"shortlist": list(await asyncio.gather(*(draft_one(e) for e in state.get("shortlist", []))))}


async def save(state: ScoutState) -> ScoutState:
    new_ids: list[int] = []
    async with get_sessionmaker()() as session:
        brief = await session.get(Brief, state["brief_id"])
        for item in state.get("shortlist", []):
            entry = await session.scalar(
                select(ShortlistEntry).where(
                    ShortlistEntry.brief_id == brief.id, ShortlistEntry.creator_id == item["creator_id"]
                )
            )
            fields = {
                "score": item["score"],
                "reasons": "\n".join(item["reasons"]),
                "risks": "\n".join(item["risks"]),
                "evidence_video_ids": item["evidence_video_ids"],
                "outreach_language": item["outreach_language"],
            }
            if entry is None:
                entry = ShortlistEntry(brief_id=brief.id, creator_id=item["creator_id"], **fields)
                entry.outreach_message = item.get("outreach_message")
                session.add(entry)
                await session.flush()
                new_ids.append(entry.id)
            else:
                # Re-runs refresh the scores but keep the team's decisions and edited messages.
                for key, value in fields.items():
                    setattr(entry, key, value)
                if not entry.outreach_message:
                    entry.outreach_message = item.get("outreach_message")
        brief.criteria = state.get("criteria")
        brief.status = BriefStatus.done
        brief.completed_at = datetime.now(UTC)
        await session.commit()
    return {"new_entry_ids": new_ids}


async def notify(state: ScoutState) -> ScoutState:
    from halo.bot.notify import notify_new_entries

    if state.get("new_entry_ids"):
        await notify_new_entries(state["brief_id"], state["new_entry_ids"])
    return {}


def build_graph():
    graph = StateGraph(ScoutState)
    for name, fn in [
        ("load", load), ("plan", plan), ("retrieve", retrieve), ("score", score),
        ("rank", rank), ("draft", draft), ("save", save), ("notify", notify),
    ]:
        graph.add_node(name, fn)
    graph.add_edge(START, "load")
    graph.add_edge("load", "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_conditional_edges("retrieve", _has_candidates, {"score": "score", "save": "save"})
    graph.add_edge("score", "rank")
    graph.add_edge("rank", "draft")
    graph.add_edge("draft", "save")
    graph.add_edge("save", "notify")
    graph.add_edge("notify", END)
    return graph.compile()


async def run_brief(brief_id: int) -> ScoutState:
    try:
        return await build_graph().ainvoke({"brief_id": brief_id})
    except Exception as e:
        log.exception("Scout run for brief %s failed", brief_id)
        async with get_sessionmaker()() as session:
            brief = await session.get(Brief, brief_id)
            if brief is not None:
                brief.status = BriefStatus.failed
                brief.error = str(e)[:1000]
                await session.commit()
        raise
