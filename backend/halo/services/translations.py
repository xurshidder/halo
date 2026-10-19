"""AI-written text in the reader's language, translated once per language and kept."""

import hashlib

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from halo.ai import translate
from halo.models import Translation


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def translated(session: AsyncSession, texts: list[str], lang: str) -> list[str]:
    """The texts in `lang`, in the same order. English, blank and untranslated texts come back as they are."""
    if lang not in translate.LANGUAGES:
        return texts
    hashes = {text: _hash(text) for text in texts if text.strip()}
    rows = await session.execute(
        select(Translation.source_hash, Translation.text).where(
            Translation.lang == lang, Translation.source_hash.in_(set(hashes.values()))
        )
    )
    known = dict(rows.all())

    missing = [text for text, digest in hashes.items() if digest not in known]
    if missing:
        fresh = await translate.translate(missing, lang)
        if fresh:
            # Two readers can open the same page at once; the first translation stored wins.
            await session.execute(
                insert(Translation)
                .values([
                    {"lang": lang, "source_hash": hashes[text], "source": text, "text": result}
                    for text, result in fresh.items()
                ])
                .on_conflict_do_nothing(index_elements=["lang", "source_hash"])
            )
            await session.commit()
            known.update({hashes[text]: result for text, result in fresh.items()})
    return [known.get(hashes[text], text) if text in hashes else text for text in texts]
