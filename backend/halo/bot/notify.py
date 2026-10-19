"""Push new shortlist matches to the brand's Telegram chat (Kuli does this in Slack)."""

import html
import logging
from datetime import UTC, datetime

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select

from halo.config import get_settings
from halo.db import get_sessionmaker
from halo.models import Brand, Brief, ShortlistEntry

log = logging.getLogger(__name__)


def format_entries(brief: Brief, entries: list[ShortlistEntry]) -> str:
    lines = [f"<b>Halo found {len(entries)} new creator(s) for “{html.escape(brief.title)}”</b>", ""]
    for i, entry in enumerate(entries, 1):
        creator = entry.creator
        handles = ", ".join(f"{a.platform}: {a.handle}" for a in creator.accounts) or creator.contact
        top_reason = entry.reasons.split("\n")[0] if entry.reasons else ""
        lines.append(f"{i}. <b>{html.escape(creator.display_name)}</b> — {entry.score}/100")
        if handles:
            lines.append(f"   {html.escape(handles)}")
        if top_reason:
            lines.append(f"   {html.escape(top_reason)}")
    lines += ["", "Outreach drafts are ready in Halo."]
    return "\n".join(lines)


async def notify_new_entries(brief_id: int, entry_ids: list[int]) -> bool:
    token = get_settings().telegram_bot_token
    if not token:
        log.info("Telegram bot token not set; skipping notification for brief %s", brief_id)
        return False
    async with get_sessionmaker()() as session:
        brief = await session.get(Brief, brief_id)
        brand = await session.get(Brand, brief.brand_id)
        if not brand.telegram_chat_id:
            return False
        entries = list(
            await session.scalars(
                select(ShortlistEntry)
                .where(ShortlistEntry.id.in_(entry_ids))
                .order_by(ShortlistEntry.score.desc())
            )
        )
        text = format_entries(brief, entries)
        bot = Bot(token, default=DefaultBotProperties(parse_mode="HTML"))
        try:
            await bot.send_message(brand.telegram_chat_id, text)
        finally:
            await bot.session.close()
        now = datetime.now(UTC)
        for entry in entries:
            entry.notified_at = now
        await session.commit()
    return True
