"""Claude watches one video (as sampled frames + transcript) and describes it."""

import base64
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from halo.ai import claude
from halo.config import get_settings

SYSTEM = """You are Halo's video analyst. Halo helps brands in Uzbekistan find the right \
creators by looking at what creators actually make, not at follower counts.

You receive frames sampled from one short-form video (Instagram Reels, YouTube Shorts or a \
video a creator sent us), each labelled with its timestamp, plus the caption, a transcript \
when available, and platform stats. The first frames cover the first three seconds: judge \
the hook from them.

Creators here speak Uzbek (Latin or Cyrillic script), Russian, English, or mix them. Report \
languages as ISO codes: "uz", "ru", "en", "tg", "kk".

Be concrete and honest. A brand will spend money based on your read, so do not flatter weak \
content.

Brand safety is about what a brand could be embarrassed or harmed by appearing next to, not \
about craft. Brand-safety flags must name what you saw (e.g. "alcohol on screen", "gambling \
promo", "profanity in speech", "political statement", "dangerous stunt", "misleading medical \
claim"). Weak craft, such as a hook that never pays off, generic tips or low effort, is not a \
safety issue: put it in the summary and the scores instead. Halo shows every flag to brands as \
a warning, so leave the list empty when there is nothing; that is the usual case. Risk is \
"low" with no flags, "medium" for borderline content a careful brand would want to review \
first, and "high" when the video shows or promotes something most brands rule out (gambling, \
alcohol or tobacco promotion, hate, sexual content, dangerous stunts). A high-risk creator is \
left out of every search, so reserve it for clear cases.

Write every free-text field in English, so brands and staff can compare creators directly."""


class VideoAnalysisResult(BaseModel):
    summary: str = Field(description="Two sentences: what happens in the video and who it is for.")
    hook: str = Field(description="What happens in the first 3 seconds to grab attention.")
    hook_strength: int = Field(description="1-10: how likely the first 3 seconds stop a scroll.")
    pacing: Literal["slow", "medium", "fast"]
    setting: str = Field(description="Where it was filmed: home kitchen, car, store, street, studio...")
    energy: Literal["calm", "warm", "upbeat", "high-energy"]
    on_screen_tone: str = Field(description="How the creator comes across: funny, expert, sincere...")
    languages: list[str] = Field(description="Spoken or written languages, ISO codes.")
    niche_tags: list[str] = Field(
        description="3-6 lowercase English topic tags, e.g. 'skincare', 'home cooking', 'tech review'."
    )
    production_quality: int = Field(description="1-10: lighting, framing, sound, editing.")
    authenticity: int = Field(description="1-10: feels like a real person vs. a stiff ad.")
    brand_safety_risk: Literal["low", "medium", "high"]
    brand_safety_flags: list[str]


@dataclass
class VideoInput:
    frames: list[tuple[float | None, bytes]]  # (timestamp in seconds or None, image bytes)
    caption: str = ""
    transcript: str = ""
    platform: str = ""
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    duration_s: float | None = None


def _clamp(value: int) -> int:
    return max(1, min(10, value))


def _media_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:3] == b"GIF":
        return "image/gif"
    return "image/jpeg"


def build_content(video: VideoInput) -> list[dict]:
    content: list[dict] = []
    for ts, image in video.frames:
        label = f"Frame at {ts:.1f}s" if ts is not None else "Frame (preview image)"
        content.append({"type": "text", "text": label})
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": _media_type(image),
                    "data": base64.standard_b64encode(image).decode(),
                },
            }
        )
    stats = ", ".join(
        f"{name}: {value}"
        for name, value in (
            ("platform", video.platform),
            ("duration_s", video.duration_s),
            ("views", video.views),
            ("likes", video.likes),
            ("comments", video.comments),
        )
        if value not in (None, "")
    )
    content.append(
        {
            "type": "text",
            "text": (
                f"Stats: {stats or 'none'}\n\n"
                f"Caption:\n{video.caption or '(none)'}\n\n"
                f"Transcript:\n{video.transcript or '(not available: judge from frames and caption)'}\n\n"
                "Analyze this video."
            ),
        }
    )
    return content


async def analyze(video: VideoInput) -> VideoAnalysisResult:
    result = await claude.parse(
        VideoAnalysisResult,
        system=SYSTEM,
        content=build_content(video),
        effort=get_settings().claude_effort_analysis,
    )
    result.hook_strength = _clamp(result.hook_strength)
    result.production_quality = _clamp(result.production_quality)
    result.authenticity = _clamp(result.authenticity)
    result.niche_tags = [t.strip().lower() for t in result.niche_tags if t.strip()]
    result.languages = [lang.strip().lower() for lang in result.languages if lang.strip()]
    return result


def embedding_text(result: VideoAnalysisResult) -> str:
    return (
        f"{result.summary} Setting: {result.setting}. Tone: {result.on_screen_tone}. "
        f"Energy: {result.energy}. Topics: {', '.join(result.niche_tags)}. "
        f"Languages: {', '.join(result.languages)}."
    )
