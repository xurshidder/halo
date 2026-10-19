"""Turn one stored video into a VideoAnalysis: get frames, transcribe, ask Claude."""

import logging
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from halo.ai import embeddings, video_analysis
from halo.config import get_settings
from halo.media import download, frames
from halo.media.transcribe import get_transcriber
from halo.models import Video, VideoAnalysis, VideoStatus
from halo.services.profile import refresh_creator_profile

log = logging.getLogger(__name__)


async def _video_input(video: Video) -> video_analysis.VideoInput:
    settings = get_settings()
    path: Path | None = None
    if video.local_path:
        path = Path(video.local_path)
    elif video.media_url:
        path = await download.download(video.media_url)

    sampled: list[tuple[float | None, bytes]] = []
    transcript = ""
    duration = video.duration_s
    if path is not None:
        duration = await frames.probe_duration(path)
        for frame in await frames.extract_frames(path, settings.frames_per_video, settings.frame_width):
            sampled.append((frame.timestamp_s, frame.jpeg))
        transcriber = get_transcriber()
        if transcriber is not None:
            audio = await frames.extract_audio(path, settings.max_video_seconds)
            if audio:
                try:
                    transcript = await transcriber.transcribe(audio)
                except Exception as e:  # a failed transcript should not block the visual analysis
                    log.warning("Transcription failed for video %s: %s", video.id, e)
    else:
        for url in video.frame_urls:
            try:
                sampled.append((None, await download.fetch_bytes(url)))
            except Exception as e:
                log.warning("Could not fetch preview %s for video %s: %s", url, video.id, e)
    if not sampled:
        raise frames.MediaError("Video has no file, media URL or preview images to analyze")

    return video_analysis.VideoInput(
        frames=sampled,
        caption=video.caption,
        transcript=transcript,
        platform=video.platform,
        views=video.views,
        likes=video.likes,
        comments=video.comments,
        duration_s=duration,
    )


async def analyze_video(session: AsyncSession, video_id: int) -> VideoAnalysis:
    video = await session.get(Video, video_id)
    if video is None:
        raise LookupError(f"Video {video_id} not found")
    video.status = VideoStatus.analyzing
    await session.commit()

    try:
        data = await _video_input(video)
        result = await video_analysis.analyze(data)
        vectors = await embeddings.embed([video_analysis.embedding_text(result)])
    except Exception as e:
        video.status = VideoStatus.failed
        video.error = str(e)[:1000]
        await session.commit()
        raise

    await session.execute(delete(VideoAnalysis).where(VideoAnalysis.video_id == video.id))
    analysis = VideoAnalysis(
        video_id=video.id,
        summary=result.summary,
        hook=result.hook,
        hook_strength=result.hook_strength,
        pacing=result.pacing,
        setting=result.setting,
        energy=result.energy,
        on_screen_tone=result.on_screen_tone,
        languages=result.languages,
        niche_tags=result.niche_tags,
        production_quality=result.production_quality,
        authenticity=result.authenticity,
        brand_safety_risk=result.brand_safety_risk,
        brand_safety_flags=result.brand_safety_flags,
        transcript=data.transcript,
        model=get_settings().claude_model,
        embedding=vectors[0] if vectors else None,
    )
    session.add(analysis)
    video.status = VideoStatus.analyzed
    video.error = None
    if data.duration_s:
        video.duration_s = data.duration_s
    await session.flush()
    await refresh_creator_profile(session, video.creator_id)
    await session.commit()
    return analysis
