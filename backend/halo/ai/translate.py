"""Claude translates Halo's AI-written text into Uzbek or Russian for the people reading it.

Halo writes every analysis, reason and risk in English, so brands and staff can compare
creators directly. The web app shows them in the reader's language instead: each text is
translated once, the first time someone opens it in that language (services.translations).
"""

import asyncio
import json

from pydantic import BaseModel

from halo.ai import claude
from halo.config import get_settings

LANGUAGES = {"uz": "Uzbek, in the Latin alphabet (write oʻ and gʻ with ʻ)", "ru": "Russian"}
BATCH_SIZE = 40

SYSTEM = """You translate notes from Halo, an influencer marketing tool used by brands in \
Uzbekistan, for the marketers who read them. The notes describe creators and their videos: \
summaries, hooks, settings, fit reasons, risks, brand-safety flags and short topic tags.

Translate every item into {language}. Write it the way a local marketer would say it: plain, \
natural and about as short as the English, not word for word. Everyday industry words such as \
Reels, hook, bloger/блогер and kontent/контент are fine.

Keep these unchanged: people's and brand names, @handles, numbers and prices, and references \
like "video 12". A quote in Uzbek or Russian is the creator's own words, so keep it as it is. A \
quote in English is Halo's rendering of what the creator said or wrote, so translate it like \
the rest. A short lowercase topic tag stays a short lowercase tag.

Return one translation for every item, under the same id."""


class TranslatedItem(BaseModel):
    id: int
    text: str


class TranslatedBatch(BaseModel):
    items: list[TranslatedItem]


async def _translate_batch(texts: list[str], lang: str) -> dict[str, str]:
    items = [{"id": i, "text": text} for i, text in enumerate(texts)]
    result = await claude.parse(
        TranslatedBatch,
        system=SYSTEM.format(language=LANGUAGES[lang]),
        content=f"Translate these items:\n{json.dumps(items, ensure_ascii=False)}",
        effort=get_settings().claude_effort_translation,
    )
    by_id = {item.id: item.text.strip() for item in result.items}
    return {text: by_id[i] for i, text in enumerate(texts) if by_id.get(i)}


async def translate(texts: list[str], lang: str) -> dict[str, str]:
    """English text -> translation. Items Claude skipped are left out, so callers show the English."""
    batches = [texts[i : i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
    translated: dict[str, str] = {}
    for part in await asyncio.gather(*(_translate_batch(batch, lang) for batch in batches)):
        translated.update(part)
    return translated
