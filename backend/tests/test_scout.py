import json

from sqlalchemy import select

from halo.agent import prompts
from halo.agent.scout import run_brief
from halo.models import Brief, BriefStatus, ShortlistEntry, ShortlistStatus
from tests.factories import make_brand, make_creator

CRITERIA = prompts.BriefCriteria(
    summary="Uzbek-speaking skincare creators with honest, simple routines.",
    languages=["uz"],
    topics=["skincare", "beauty"],
    content_style="natural light, at home",
    audience="women 18-35 in Tashkent",
    deal_breakers=["alcohol"],
    search_text="Home skincare routines filmed in natural light, in Uzbek.",
)
SCORES = {"Malika": 91, "Dilnoza": 72, "Sevara": 35}


def score_for(content: str) -> prompts.CandidateScore:
    creator = json.loads(content.split("<creator>\n")[1].split("\n</creator>")[0])
    first_video = creator["recent_videos"][0]["video_id"]
    return prompts.CandidateScore(
        score=SCORES[creator["name"]],
        fit_summary=f"{creator['name']} films honest routines.",
        reasons=[f"video {first_video} shows a real routine"],
        risks=[],
        evidence_video_ids=[first_video],
        outreach_language="uz",
    )


def setup_claude(fake_claude):
    fake_claude.on(prompts.BriefCriteria, CRITERIA)
    fake_claude.on(prompts.CandidateScore, score_for)
    fake_claude.on(prompts.OutreachDraft, prompts.OutreachDraft(message="Assalomu alaykum! Videongiz juda yoqdi."))


async def seed(session):
    brand = await make_brand(session)
    await make_creator(session, "Malika", ["skincare", "beauty"])
    await make_creator(session, "Dilnoza", ["skincare", "lifestyle"])
    await make_creator(session, "Sevara", ["beauty"], quality=4)
    await make_creator(session, "Bobur", ["cars"], languages=("ru",))  # wrong language: never scored
    await make_creator(session, "Risky", ["skincare"], risk="high")  # brand-safety risk: never scored
    brief = Brief(brand_id=brand.id, title="Spring serum launch", text="Find Uzbek skincare creators.")
    session.add(brief)
    await session.commit()
    return brief


async def test_scout_builds_ranked_shortlist(session, fake_claude):
    setup_claude(fake_claude)
    brief = await seed(session)

    state = await run_brief(brief.id)

    scored = {json.loads(c["content"].split("<creator>\n")[1].split("\n</creator>")[0])["name"]
              for c in fake_claude.calls if c["type"] is prompts.CandidateScore}
    assert scored == {"Malika", "Dilnoza", "Sevara"}
    entries = list(await session.scalars(select(ShortlistEntry).order_by(ShortlistEntry.score.desc())))
    assert [(e.creator.display_name, e.score) for e in entries] == [("Malika", 91), ("Dilnoza", 72)]
    assert entries[0].outreach_message.startswith("Assalomu alaykum")
    assert entries[0].outreach_language == "uz"
    assert len(state["new_entry_ids"]) == 2

    await session.refresh(brief)
    assert brief.status == BriefStatus.done
    assert brief.criteria["topics"] == ["skincare", "beauty"]

    # Brand context is in the cached system prompt for scoring
    scoring_call = next(c for c in fake_claude.calls if c["type"] is prompts.CandidateScore)
    assert scoring_call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Nur Cosmetics" in scoring_call["system"][0]["text"]


async def test_rerun_keeps_decisions_and_skips_rejected(session, fake_claude):
    setup_claude(fake_claude)
    brief = await seed(session)
    await run_brief(brief.id)

    malika, dilnoza = list(await session.scalars(select(ShortlistEntry).order_by(ShortlistEntry.score.desc())))
    malika.status = ShortlistStatus.starred
    malika.outreach_message = "Edited by the team"
    dilnoza.status = ShortlistStatus.rejected
    await session.commit()
    fake_claude.calls.clear()

    state = await run_brief(brief.id)

    assert state["new_entry_ids"] == []
    scored = [c for c in fake_claude.calls if c["type"] is prompts.CandidateScore]
    assert all('"name": "Dilnoza"' not in c["content"] for c in scored)
    await session.refresh(malika)
    assert malika.status == ShortlistStatus.starred
    assert malika.outreach_message == "Edited by the team"


async def test_failed_run_marks_brief_failed(session, fake_claude):
    brief = await seed(session)  # no responders registered: the planner call raises

    try:
        await run_brief(brief.id)
    except KeyError:
        pass
    await session.refresh(brief)
    assert brief.status == BriefStatus.failed
    assert brief.error
