import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import any_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from halo.db import get_session
from halo.media.download import media_dir
from halo.models import Creator, CreatorAccount, Platform, Video, VideoStatus
from halo.queue import JobQueue, get_queue
from halo.schemas import (
    AccountIn,
    CreatorDetail,
    CreatorIn,
    CreatorOut,
    JobOut,
    LookalikeOut,
    VideoOut,
    VideoUrlIn,
)
from halo.services.ingest import add_manual_video
from halo.services.lookalike import find_lookalikes

router = APIRouter(tags=["creators"])
MAX_UPLOAD_BYTES = 200 * 1024 * 1024


async def get_creator_or_404(session: AsyncSession, creator_id: int) -> Creator:
    creator = await session.get(Creator, creator_id)
    if creator is None:
        raise HTTPException(404, "Creator not found")
    return creator


@router.post("/creators", response_model=CreatorOut, status_code=201)
async def create_creator(body: CreatorIn, session: AsyncSession = Depends(get_session)):
    creator = Creator(**body.model_dump(exclude={"accounts"}))
    creator.accounts = [CreatorAccount(**a.model_dump()) for a in body.accounts]
    session.add(creator)
    await session.commit()
    await session.refresh(creator, ["accounts"])
    return creator


@router.get("/creators", response_model=list[CreatorOut])
async def list_creators(
    q: str | None = None,
    language: str | None = None,
    tag: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    query = select(Creator).order_by(Creator.avg_quality.desc().nulls_last(), Creator.id)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Creator.display_name.ilike(like), Creator.summary.ilike(like)))
    if language:
        query = query.where(language == any_(Creator.languages))
    if tag:
        query = query.where(tag.lower() == any_(Creator.niche_tags))
    return list(await session.scalars(query.limit(200)))


@router.get("/creators/{creator_id}", response_model=CreatorDetail)
async def get_creator(creator_id: int, session: AsyncSession = Depends(get_session)):
    creator = await session.scalar(
        select(Creator).where(Creator.id == creator_id).options(selectinload(Creator.videos))
    )
    if creator is None:
        raise HTTPException(404, "Creator not found")
    creator.videos.sort(key=lambda v: (v.posted_at is not None, v.posted_at), reverse=True)
    return creator


@router.post("/creators/{creator_id}/accounts", response_model=CreatorOut)
async def add_account(creator_id: int, body: AccountIn, session: AsyncSession = Depends(get_session)):
    creator = await get_creator_or_404(session, creator_id)
    creator.accounts.append(CreatorAccount(**body.model_dump()))
    await session.commit()
    await session.refresh(creator, ["accounts"])
    return creator


@router.post("/creators/{creator_id}/refresh", response_model=JobOut, status_code=202)
async def refresh(creator_id: int, session: AsyncSession = Depends(get_session), jobs: JobQueue = Depends(get_queue)):
    await get_creator_or_404(session, creator_id)
    await jobs.enqueue("refresh_creator_task", creator_id)
    return JobOut(queued="refresh_creator_task", id=creator_id)


@router.post("/creators/{creator_id}/videos", response_model=VideoOut, status_code=201)
async def upload_video(
    creator_id: int,
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_session),
    jobs: JobQueue = Depends(get_queue),
):
    await get_creator_or_404(session, creator_id)
    path = media_dir() / f"upload-{uuid.uuid4().hex}.mp4"
    size = 0
    with path.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                f.close()
                path.unlink(missing_ok=True)
                raise HTTPException(413, "Video is larger than 200 MB")
            f.write(chunk)
    video = await add_manual_video(session, creator_id, path, caption)
    await jobs.enqueue("analyze_video_task", video.id)
    await session.refresh(video, ["analysis"])
    return video


@router.post("/creators/{creator_id}/videos/url", response_model=VideoOut, status_code=201)
async def add_video_url(
    creator_id: int,
    body: VideoUrlIn,
    session: AsyncSession = Depends(get_session),
    jobs: JobQueue = Depends(get_queue),
):
    await get_creator_or_404(session, creator_id)
    existing = await session.scalar(
        select(Video).where(Video.platform == Platform.manual, Video.external_id == body.url)
    )
    if existing:
        await session.refresh(existing, ["analysis"])
        return existing
    video = Video(
        creator_id=creator_id,
        platform=Platform.manual,
        external_id=body.url,
        url=body.url,
        media_url=body.url,
        caption=body.caption,
        status=VideoStatus.pending,
    )
    session.add(video)
    await session.commit()
    await jobs.enqueue("analyze_video_task", video.id)
    await session.refresh(video, ["analysis"])
    return video


@router.post("/videos/{video_id}/analyze", response_model=JobOut, status_code=202)
async def analyze(video_id: int, session: AsyncSession = Depends(get_session), jobs: JobQueue = Depends(get_queue)):
    if await session.get(Video, video_id) is None:
        raise HTTPException(404, "Video not found")
    await jobs.enqueue("analyze_video_task", video_id)
    return JobOut(queued="analyze_video_task", id=video_id)


@router.get("/creators/{creator_id}/lookalikes", response_model=list[LookalikeOut])
async def lookalikes(creator_id: int, limit: int = 10, session: AsyncSession = Depends(get_session)):
    await get_creator_or_404(session, creator_id)
    return [
        LookalikeOut(creator=CreatorOut.model_validate(c), similarity=s)
        for c, s in await find_lookalikes(session, creator_id, limit)
    ]
