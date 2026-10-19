import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from halo.ai.claude import ClaudeError
from halo.db import get_session
from halo.schemas import TranslateIn, TranslateOut
from halo.services.translations import translated

router = APIRouter(tags=["translations"])


@router.post("/translate", response_model=TranslateOut)
async def translate(body: TranslateIn, session: AsyncSession = Depends(get_session)):
    """AI-written text in the reader's language. Each text is translated once per language, then kept."""
    try:
        return TranslateOut(texts=await translated(session, body.texts, body.lang))
    except (ClaudeError, anthropic.APIError) as e:
        raise HTTPException(502, f"Translation failed: {e}") from e
