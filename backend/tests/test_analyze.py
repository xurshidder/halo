import pytest

from halo.ai.video_analysis import VideoAnalysisResult
from halo.media.frames import MediaError
from halo.models import Creator, Platform, Video, VideoStatus
from halo.services.analyze import analyze_video
from halo.services.ingest import add_manual_video
from tests.factories import analysis_result


async def test_analyze_manual_video(session, fake_claude, sample_video):
    fake_claude.on(VideoAnalysisResult, analysis_result(hook_strength=14, niche_tags=["Skincare ", "beauty"]))
    creator = Creator(display_name="Malika")
    session.add(creator)
    await session.commit()
    video = await add_manual_video(session, creator.id, sample_video, caption="Ertalabki parvarish")

    analysis = await analyze_video(session, video.id)

    assert analysis.hook_strength == 10  # clamped to 1-10
    assert analysis.niche_tags == ["skincare", "beauty"]
    call = fake_claude.calls[0]
    images = [b for b in call["content"] if b["type"] == "image"]
    assert len(images) == 8
    assert call["content"][0]["text"] == "Frame at 0.3s"
    assert "Ertalabki parvarish" in call["content"][-1]["text"]

    await session.refresh(video)
    assert video.status == VideoStatus.analyzed
    await session.refresh(creator)
    assert creator.niche_tags == ["skincare", "beauty"]
    assert creator.languages == ["uz"]
    assert creator.avg_quality == 7
    assert creator.brand_safety_risk == "low"


async def test_same_file_is_not_added_twice(session, sample_video):
    creator = Creator(display_name="Malika")
    session.add(creator)
    await session.commit()
    first = await add_manual_video(session, creator.id, sample_video)
    second = await add_manual_video(session, creator.id, sample_video)
    assert first.id == second.id


async def test_video_without_media_is_marked_failed(session, fake_claude):
    creator = Creator(display_name="Jasur")
    session.add(creator)
    await session.flush()
    video = Video(creator_id=creator.id, platform=Platform.youtube, external_id="abc", frame_urls=[])
    session.add(video)
    await session.commit()

    with pytest.raises(MediaError):
        await analyze_video(session, video.id)
    await session.refresh(video)
    assert video.status == VideoStatus.failed
    assert "no file" in video.error
    assert fake_claude.calls == []
