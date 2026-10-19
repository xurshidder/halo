from halo.ai.video_analysis import VideoAnalysisResult
from halo.models import Brand, Creator, CreatorAccount, Platform, Video, VideoAnalysis, VideoStatus
from halo.services.profile import refresh_creator_profile


def analysis_result(**overrides) -> VideoAnalysisResult:
    data = dict(
        summary="A creator shows her morning skincare routine in a home bathroom.",
        hook="Holds a cream jar to the camera and asks 'is this worth it?'",
        hook_strength=8,
        pacing="fast",
        setting="home bathroom",
        energy="upbeat",
        on_screen_tone="friendly and honest",
        languages=["uz"],
        niche_tags=["skincare", "beauty"],
        production_quality=7,
        authenticity=9,
        brand_safety_risk="low",
        brand_safety_flags=[],
    )
    data.update(overrides)
    return VideoAnalysisResult(**data)


async def make_brand(session, **overrides) -> Brand:
    brand = Brand(
        name=overrides.pop("name", "Nur Cosmetics"),
        description="Affordable Korean-style skincare sold on Uzum",
        pillars=["honest reviews", "simple routines"],
        no_go_topics=["alcohol", "gambling"],
        tone="warm, simple, a bit playful",
        languages=["uz", "ru"],
        **overrides,
    )
    session.add(brand)
    await session.commit()
    return brand


async def make_creator(session, name: str, tags: list[str], languages=("uz",), quality=7, risk="low",
                       followers=20000, embedding=None, videos=2) -> Creator:
    creator = Creator(display_name=name, city="Tashkent")
    creator.accounts = [CreatorAccount(platform=Platform.instagram, handle=name.lower(), followers=followers)]
    session.add(creator)
    await session.flush()
    for i in range(videos):
        video = Video(
            creator_id=creator.id,
            platform=Platform.manual,
            external_id=f"{name}-{i}",
            status=VideoStatus.analyzed,
        )
        session.add(video)
        await session.flush()
        result = analysis_result(
            summary=f"{name} video {i} about {', '.join(tags)}.",
            niche_tags=list(tags),
            languages=list(languages),
            production_quality=quality,
            brand_safety_risk=risk,
        )
        session.add(VideoAnalysis(video_id=video.id, model="test", embedding=embedding, **result.model_dump()))
    await session.flush()
    await refresh_creator_profile(session, creator.id)
    await session.commit()
    return creator
