from typing import Literal

from pydantic import BaseModel, Field

from halo.models import Brand

MARKET = """Market: Uzbekistan. Creators post on Instagram, YouTube and Telegram (TikTok is \
blocked). They speak Uzbek (Latin or Cyrillic script), Russian, or mix both. Prices are in \
Uzbek soum (UZS). Most brands are small and mid-size: Uzum marketplace sellers, local D2C \
brands, cafes, clinics, education centers."""


def brand_context(brand: Brand) -> str:
    def lines(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items) or "- (none given)"

    return f"""<brand>
Name: {brand.name}
About: {brand.description or "(not given)"}
Pillars:
{lines(brand.pillars)}
No-go topics (never match creators who touch these):
{lines(brand.no_go_topics)}
Tone of voice: {brand.tone or "(not given)"}
Languages the brand speaks to customers in: {", ".join(brand.languages) or "(not given)"}
Past campaigns: {brand.past_campaigns or "(none)"}
</brand>"""


PLANNER_SYSTEM = f"""You are Halo, an AI coworker for influencer marketing teams. \
Turn a brand's brief into concrete search criteria for finding creators.

{MARKET}

Only set min_followers or max_price_uzs when the brief states them. Topics are lowercase \
English tags like "skincare", "home cooking", "kids", "tech review". The search_text is a \
short description of the videos the ideal creator makes, written to be matched against \
descriptions of real videos."""


class BriefCriteria(BaseModel):
    summary: str = Field(description="One sentence: what kind of creator the brand needs and why.")
    languages: list[str] = Field(description="Languages the creator must speak (ISO codes). Empty = any.")
    topics: list[str] = Field(description="3-8 lowercase English topic tags to search for.")
    content_style: str = Field(description="The look and feel the brand wants in videos.")
    audience: str = Field(description="Who the brand wants to reach.")
    deal_breakers: list[str] = Field(description="Things that rule a creator out.")
    min_followers: int | None = None
    max_price_uzs: int | None = None
    search_text: str = Field(description="2-3 sentences describing the ideal creator's videos.")


SCORER_INSTRUCTIONS = f"""You are Halo, an AI coworker for influencer marketing teams. \
You judge whether one creator fits one brand's brief, based on what Halo saw in their \
recent videos (each analysis below came from watching the video's frames and reading its \
transcript and caption).

{MARKET}

Scoring, 0-100:
- 85-100: clearly right; their videos already look like what the brand needs.
- 65-84: good fit with a gap the brand should know about.
- 40-64: partial fit.
- 0-39: wrong fit, or any no-go topic or deal-breaker present.

Reasons must point to specific videos by their id. Name real risks (brand-safety flags, \
inconsistent quality, audience mismatch, wrong language). Pick outreach_language as the \
language the creator mostly speaks in their videos. Write reasons and risks in English."""


class CandidateScore(BaseModel):
    score: int = Field(description="0-100 fit score.")
    fit_summary: str = Field(description="One line a busy marketer can read.")
    reasons: list[str] = Field(description="2-4 reasons, each citing video ids like 'video 12'.")
    risks: list[str] = Field(
        description=(
            "0-3 risks specific to this creator and brief, most important first. Each one is shown "
            "to the marketer, so leave out unknowns that apply to every creator (audience "
            "demographics, filters, share of sponsored posts) unless their videos point to a problem."
        )
    )
    evidence_video_ids: list[int]
    outreach_language: Literal["uz", "ru", "en"]


OUTREACH_INSTRUCTIONS = f"""You are Halo, writing a first message from a brand to a \
creator, to send as a Telegram or Instagram DM.

{MARKET}

Rules:
- Write in the requested language. For Uzbek use Latin script.
- First line is about the creator: mention something specific from one of their videos.
- Then one or two sentences: who the brand is and what collaboration it proposes.
- End with one easy question they can answer in a few words.
- Under 600 characters. Warm and respectful, no hype, no emoji walls, at most one emoji.
- Never promise money, dates or terms the brief does not state.
- Match the brand's tone of voice."""


class OutreachDraft(BaseModel):
    message: str
