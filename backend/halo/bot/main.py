"""Halo's Telegram bot.

- Brands open a signed link from the web app; the bot remembers their chat and posts
  new matches there.
- Creators run /join, give their name and Instagram/YouTube handles, and send 1-3 of
  their best videos. Halo analyzes them like any other video.

Run with:  python -m halo.bot.main
Telegram bots can download files up to 20 MB.
"""

import asyncio
import logging
import uuid

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from halo.bot.links import parse_brand_payload
from halo.config import get_settings
from halo.db import get_sessionmaker
from halo.media.download import media_dir
from halo.models import Brand, Creator, CreatorAccount, Platform
from halo.queue import get_queue
from halo.services.ingest import add_manual_video

log = logging.getLogger(__name__)
router = Router()
MAX_VIDEOS = 3


class Join(StatesGroup):
    name = State()
    handles = State()
    videos = State()


@router.message(CommandStart(deep_link=True))
async def start_with_payload(message: Message, command: CommandObject) -> None:
    brand_id = parse_brand_payload(command.args or "")
    if brand_id is None:
        await message.answer("This link is not valid. Open it again from the Halo web app.")
        return
    async with get_sessionmaker()() as session:
        brand = await session.get(Brand, brand_id)
        if brand is None:
            await message.answer("Brand not found.")
            return
        brand.telegram_chat_id = message.chat.id
        await session.commit()
        name = brand.name
    await message.answer(f"Connected. Halo will post new creator matches for <b>{name}</b> in this chat.")


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Assalomu alaykum! I'm Halo.\n\n"
        "Bloggers: send /join to get paid brand deals. Brands find you by your videos, "
        "not your follower count.\n\n"
        "Brands: connect this chat from the Halo web app."
    )


@router.message(Command("join"))
async def join(message: Message, state: FSMContext) -> None:
    await state.set_state(Join.name)
    await message.answer("What name should brands see? (Ism yoki blog nomi)")


@router.message(Join.name, F.text)
async def join_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip()[:200])
    await state.set_state(Join.handles)
    await message.answer(
        "Send your Instagram and/or YouTube handles, one per line, e.g.\n"
        "instagram: @yourname\nyoutube: @yourchannel\n\nOr send - to skip."
    )


def parse_handles(text: str) -> list[tuple[str, str]]:
    handles = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        platform, handle = (part.strip() for part in line.split(":", 1))
        platform = platform.lower()
        if platform in (Platform.instagram, Platform.youtube) and handle:
            handles.append((platform, handle.lstrip("@") if platform == Platform.instagram else handle))
    return handles


@router.message(Join.handles, F.text)
async def join_handles(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user = message.from_user
    async with get_sessionmaker()() as session:
        creator = await session.scalar(select(Creator).where(Creator.telegram_user_id == user.id))
        if creator is None:
            creator = Creator(display_name=data["name"], telegram_user_id=user.id)
            session.add(creator)
        creator.display_name = data["name"]
        creator.contact = f"@{user.username}" if user.username else f"tg:{user.id}"
        await session.flush()
        for platform, handle in parse_handles(message.text):
            exists = await session.scalar(
                select(CreatorAccount).where(CreatorAccount.platform == platform, CreatorAccount.handle == handle)
            )
            if exists is None:
                session.add(CreatorAccount(creator_id=creator.id, platform=platform, handle=handle))
        await session.commit()
        creator_id = creator.id
    await state.update_data(creator_id=creator_id, sent=0)
    await state.set_state(Join.videos)
    await message.answer(
        f"Now send up to {MAX_VIDEOS} of your best videos (as video files, under 20 MB each). "
        "Send /done when finished."
    )


@router.message(Join.videos, F.video | F.document)
async def join_video(message: Message, state: FSMContext, bot: Bot) -> None:
    file = message.video or message.document
    if message.document and not (message.document.mime_type or "").startswith("video/"):
        await message.answer("Please send a video file.")
        return
    if file.file_size and file.file_size > 20 * 1024 * 1024:
        await message.answer("That file is over 20 MB. Please send a shorter or compressed version.")
        return
    data = await state.get_data()
    path = media_dir() / f"tg-{uuid.uuid4().hex}.mp4"
    await bot.download(file, destination=path)
    async with get_sessionmaker()() as session:
        video = await add_manual_video(session, data["creator_id"], path, caption=message.caption or "")
    await get_queue().enqueue("analyze_video_task", video.id)

    sent = data.get("sent", 0) + 1
    await state.update_data(sent=sent)
    if sent >= MAX_VIDEOS:
        await finish(message, state)
    else:
        await message.answer(f"Got it ({sent}/{MAX_VIDEOS}). Send another, or /done.")


@router.message(Join.videos, Command("done"))
async def done(message: Message, state: FSMContext) -> None:
    await finish(message, state)


async def finish(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Rahmat! Halo is watching your videos. We'll message you here when a brand wants to work with you.")


async def main() -> None:
    token = get_settings().telegram_bot_token
    if not token:
        raise SystemExit("Set HALO_TELEGRAM_BOT_TOKEN to run the bot")
    bot = Bot(token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
