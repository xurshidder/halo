from halo.bot.links import brand_start_payload, parse_brand_payload
from halo.bot.main import parse_handles
from halo.bot.notify import format_entries, notify_new_entries
from halo.models import Brief, ShortlistEntry
from tests.factories import make_brand, make_creator


def test_brand_link_roundtrip_and_tampering():
    payload = brand_start_payload(42)
    assert parse_brand_payload(payload) == 42
    assert parse_brand_payload(payload.replace("brand-42", "brand-43")) is None
    assert parse_brand_payload("garbage") is None


def test_parse_handles():
    text = "Instagram: @malika.uz\nyoutube: @malikavlog\ntiktok: @nope\nhello"
    assert parse_handles(text) == [("instagram", "malika.uz"), ("youtube", "@malikavlog")]


async def test_format_and_skip_without_token(session):
    brand = await make_brand(session, telegram_chat_id=123)
    creator = await make_creator(session, "Malika <3", ["skincare"])
    brief = Brief(brand_id=brand.id, title="Spring & serum", text="x")
    session.add(brief)
    await session.flush()
    entry = ShortlistEntry(brief_id=brief.id, creator_id=creator.id, score=91, reasons="video 1 fits\nvideo 2 too")
    session.add(entry)
    await session.commit()
    await session.refresh(entry, ["creator"])

    text = format_entries(brief, [entry])
    assert "Spring &amp; serum" in text
    assert "Malika &lt;3</b> — 91/100" in text
    assert "video 1 fits" in text and "video 2 too" not in text

    assert await notify_new_entries(brief.id, [entry.id]) is False  # no bot token in tests
