from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from halo.api.routes.brands import get_brand_or_404
from halo.db import get_session
from halo.models import Brief, BriefStatus, ShortlistEntry
from halo.queue import JobQueue, get_queue
from halo.schemas import BriefDetail, BriefIn, BriefOut, EntryOut, EntryPatch, JobOut

router = APIRouter(tags=["briefs"])


@router.post("/brands/{brand_id}/briefs", response_model=BriefOut, status_code=201)
async def create_brief(brand_id: int, body: BriefIn, session: AsyncSession = Depends(get_session)):
    await get_brand_or_404(session, brand_id)
    brief = Brief(brand_id=brand_id, **body.model_dump())
    session.add(brief)
    await session.commit()
    await session.refresh(brief)
    return brief


@router.get("/brands/{brand_id}/briefs", response_model=list[BriefOut])
async def list_briefs(brand_id: int, session: AsyncSession = Depends(get_session)):
    return list(await session.scalars(select(Brief).where(Brief.brand_id == brand_id).order_by(Brief.id.desc())))


@router.get("/briefs/{brief_id}", response_model=BriefDetail)
async def get_brief(brief_id: int, session: AsyncSession = Depends(get_session)):
    brief = await session.scalar(
        select(Brief).where(Brief.id == brief_id).options(selectinload(Brief.entries))
    )
    if brief is None:
        raise HTTPException(404, "Brief not found")
    return brief


@router.post("/briefs/{brief_id}/run", response_model=JobOut, status_code=202)
async def run(brief_id: int, session: AsyncSession = Depends(get_session), jobs: JobQueue = Depends(get_queue)):
    brief = await session.get(Brief, brief_id)
    if brief is None:
        raise HTTPException(404, "Brief not found")
    if brief.status == BriefStatus.running:
        raise HTTPException(409, "This brief is already running")
    brief.status = BriefStatus.running
    brief.error = None
    await session.commit()
    await jobs.enqueue("run_brief_task", brief_id)
    return JobOut(queued="run_brief_task", id=brief_id)


@router.patch("/shortlist/{entry_id}", response_model=EntryOut)
async def update_entry(entry_id: int, body: EntryPatch, session: AsyncSession = Depends(get_session)):
    entry = await session.get(ShortlistEntry, entry_id)
    if entry is None:
        raise HTTPException(404, "Shortlist entry not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    await session.commit()
    return entry
