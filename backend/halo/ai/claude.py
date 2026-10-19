"""Thin wrapper around the Anthropic SDK used by every Halo AI step.

Every call asks for a structured (Pydantic) result, so callers never parse free text.
Server-side refusal fallbacks are enabled: if the model declines on a policy
category, the API re-runs the request on a fallback model inside the same call.
"""

import logging
from functools import lru_cache
from typing import Any

import anthropic
from pydantic import BaseModel

from halo.config import get_settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"

log = logging.getLogger(__name__)


class ClaudeError(RuntimeError):
    pass


@lru_cache
def get_client() -> anthropic.AsyncAnthropic:
    # HALO_ANTHROPIC_API_KEY if set; otherwise the SDK reads ANTHROPIC_API_KEY (or an
    # `ant auth login` profile) from the environment.
    api_key = get_settings().anthropic_api_key
    if api_key:
        return anthropic.AsyncAnthropic(api_key=api_key, max_retries=4)
    return anthropic.AsyncAnthropic(max_retries=4)


def cached_system(text: str) -> list[dict[str, Any]]:
    """A system prompt marked for prompt caching (brand context is reused across many calls)."""
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


async def parse[T: BaseModel](
    output_type: type[T],
    *,
    system: str | list[dict[str, Any]],
    content: str | list[dict[str, Any]],
    effort: str,
    max_tokens: int = 16000,
) -> T:
    settings = get_settings()
    response = await get_client().beta.messages.parse(
        model=settings.claude_model,
        max_tokens=max_tokens,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        system=system,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort},
        output_format=output_type,
    )
    usage = response.usage
    # One line per call, so real token spend can be read from the logs.
    log.info(
        "claude %s model=%s stop=%s input=%d cache_write=%d cache_read=%d output=%d",
        output_type.__name__,
        response.model,
        response.stop_reason,
        usage.input_tokens,
        usage.cache_creation_input_tokens or 0,
        usage.cache_read_input_tokens or 0,
        usage.output_tokens,
    )
    if response.stop_reason == "refusal":
        details = response.stop_details
        category = getattr(details, "category", None) if details else None
        raise ClaudeError(f"Claude declined the request (category: {category})")
    if response.stop_reason == "max_tokens":
        raise ClaudeError("Claude hit max_tokens before finishing the structured output")
    if response.parsed_output is None:
        raise ClaudeError(f"No structured output returned (stop_reason={response.stop_reason})")
    return response.parsed_output
