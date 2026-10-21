"""Load demo data so the web app can be explored without API keys.

Everything here is made up for demonstration: one brand, six creators with
analyzed videos, and one finished brief with a shortlist.

    uv run python -m scripts.seed_demo
    uv run python -m scripts.seed_demo --if-empty   # skip when the database already has a brand
"""

import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from halo.db import get_sessionmaker
from halo.models import (
    Brand,
    Brief,
    BriefStatus,
    Creator,
    CreatorAccount,
    ShortlistEntry,
    Video,
    VideoAnalysis,
    VideoStatus,
)
from halo.services.profile import refresh_creator_profile

CREATORS = [
    # name, city, handle, followers, price, tags, languages, quality, hook, risk, summary, hook text, setting
    ("Malika (demo)", "Tashkent", "malika.demo", 18400, 900_000, ["skincare", "beauty", "routines"], ["uz"], 8, 8, "low",
     "Shows a simple morning skincare routine with affordable products, talking straight to camera in Uzbek.",
     "Holds up a cream and asks 'is this worth 90,000 soum?'", "home bathroom, natural light"),
    ("Dilnoza (demo)", "Samarkand", "dilnoza.demo", 9200, 600_000, ["skincare", "lifestyle"], ["uz", "ru"], 7, 7, "low",
     "Honest product reviews mixing Uzbek and Russian, filmed at a vanity table.",
     "Splits the screen: before and after a week of use", "bedroom vanity"),
    ("Aziza (demo)", "Tashkent", "aziza.demo", 54000, 2_500_000, ["beauty", "makeup", "fashion"], ["ru"], 9, 6, "medium",
     "Polished makeup tutorials in Russian with studio lighting and fast cuts.",
     "Starts mid-transformation with half her face done", "home studio with ring light"),
    ("Jasur (demo)", "Fergana", "jasur.demo", 31000, 1_200_000, ["tech review", "gadgets"], ["uz"], 7, 8, "low",
     "Unboxes budget phones and earbuds sold on Uzum, comparing them to the price.",
     "Drops the phone on the floor in the first second", "desk setup"),
    ("Kamola (demo)", "Bukhara", "kamola.demo", 7600, 400_000, ["home cooking", "family"], ["uz"], 6, 7, "low",
     "Quick plov and salad recipes in a family kitchen, warm and chatty in Uzbek.",
     "Pours oil into a sizzling kazan", "family kitchen"),
    ("Sardor (demo)", "Tashkent", "sardor.demo", 120000, 5_000_000, ["comedy", "skits"], ["uz", "ru"], 7, 9, "high",
     "Comedy skits about city life; some videos joke about betting apps.",
     "Shouts at a taxi driver in a fake argument", "street and car"),
]


async def main(if_empty: bool = False) -> None:
    async with get_sessionmaker()() as session:
        if if_empty and await session.scalar(select(Brand.id).limit(1)) is not None:
            print("Database already has data; demo data not loaded.")
            return
        brand = Brand(
            name="Nur Cosmetics (demo)",
            description="Affordable Korean-style skincare sold on Uzum, for women 18-35.",
            pillars=["honest reviews", "simple routines", "real skin"],
            no_go_topics=["alcohol", "gambling", "politics"],
            tone="warm, simple, a bit playful",
            languages=["uz", "ru"],
            past_campaigns="Paid one big blogger in 2025: lots of views, few sales. Small honest reviewers sold better.",
        )
        session.add(brand)
        await session.flush()

        ids = {}
        for i, (name, city, handle, followers, price, tags, langs, quality, hook, risk, summary, hook_text, setting) in enumerate(CREATORS):
            creator = Creator(display_name=name, city=city, price_uzs=price, contact=f"@{handle}")
            creator.accounts = [CreatorAccount(platform="instagram", handle=handle, followers=followers,
                                               avg_views=followers // 2, engagement_rate=0.05)]
            session.add(creator)
            await session.flush()
            for n in range(3):
                video = Video(creator_id=creator.id, platform="instagram", external_id=f"demo-{i}-{n}",
                              url=f"https://instagram.com/{handle}", caption=f"Demo video {n + 1}",
                              posted_at=datetime(2026, 10, 1 + n, tzinfo=UTC), views=followers // 2,
                              status=VideoStatus.analyzed)
                session.add(video)
                await session.flush()
                session.add(VideoAnalysis(
                    video_id=video.id, summary=summary, hook=hook_text, hook_strength=hook, pacing="fast",
                    setting=setting, energy="upbeat", on_screen_tone="friendly", languages=langs, niche_tags=tags,
                    production_quality=quality, authenticity=8, brand_safety_risk=risk,
                    brand_safety_flags=["gambling promo"] if risk == "high" else [], model="demo",
                ))
            await session.flush()
            await refresh_creator_profile(session, creator.id)
            ids[name] = creator.id

        brief = Brief(
            brand_id=brand.id, title="Spring serum launch (demo)", standing=True,
            text="Uzbek-speaking creators who film honest skincare routines at home. Budget up to 1,000,000 UZS per video.",
            criteria={"summary": "Uzbek-speaking skincare creators with honest, simple at-home routines.",
                      "topics": ["skincare", "beauty", "routines"], "languages": ["uz"]},
            status=BriefStatus.done, completed_at=datetime.now(UTC),
        )
        session.add(brief)
        await session.flush()
        session.add_all([
            ShortlistEntry(
                brief_id=brief.id, creator_id=ids["Malika (demo)"], score=91,
                reasons="Her routines already look like the brand: home bathroom, natural light, honest tone\nSpeaks Uzbek to camera; hook strength 8/10\nPrice fits the budget",
                risks="", outreach_language="uz",
                outreach_message="Assalomu alaykum, Malika! 90 ming so'mlik krem haqidagi videongiz juda samimiy chiqqan. Biz Nur Cosmetics — Uzumdagi koreyscha parvarish brendimiz. Yangi serumimiz uchun ertalabki rutina videosi qilishni xohlaysizmi?",
            ),
            ShortlistEntry(
                brief_id=brief.id, creator_id=ids["Dilnoza (demo)"], score=78,
                reasons="Before/after review format suits a serum launch\nSmaller audience, but steady engagement",
                risks="Mixes Russian into most videos", outreach_language="uz",
                outreach_message="Assalomu alaykum, Dilnoza! Bir haftalik oldin-keyin videongiz juda ishonarli. Biz Nur Cosmetics — yangi serumimizni sinab ko'rib, halol fikringizni aytishga tayyormisiz?",
            ),
        ])
        await session.commit()
    print("Demo data loaded.")


if __name__ == "__main__":
    asyncio.run(main(if_empty="--if-empty" in sys.argv))
