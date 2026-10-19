import logging
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from halo.ai import claude
from halo.config import get_settings


class Answer(BaseModel):
    text: str


def response(stop_reason="end_turn", parsed=None, category=None):
    return SimpleNamespace(
        model="claude-opus-5-5",
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category=category) if category else None,
        parsed_output=parsed,
        usage=SimpleNamespace(
            input_tokens=100, cache_creation_input_tokens=None, cache_read_input_tokens=40, output_tokens=7
        ),
    )


class StubClient:
    """Stands in for the Anthropic client, so the real claude.parse runs without the network."""

    def __init__(self, resp):
        self.resp = resp
        self.kwargs = None
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self.parse))

    async def parse(self, **kwargs):
        self.kwargs = kwargs
        return self.resp


async def test_parse_returns_output_and_logs_usage(monkeypatch, caplog):
    stub = StubClient(response(parsed=Answer(text="ok")))
    monkeypatch.setattr(claude, "get_client", lambda: stub)

    with caplog.at_level(logging.INFO, logger="halo.ai.claude"):
        result = await claude.parse(Answer, system="s", content="c", effort="low")

    assert result.text == "ok"
    assert stub.kwargs["fallbacks"] == "default"
    assert stub.kwargs["output_config"] == {"effort": "low"}
    assert stub.kwargs["output_format"] is Answer
    assert "claude Answer model=claude-opus-5-5 stop=end_turn input=100 cache_write=0 cache_read=40 output=7" in caplog.text


async def test_parse_raises_on_refusal(monkeypatch):
    monkeypatch.setattr(claude, "get_client", lambda: StubClient(response(stop_reason="refusal", category="cyber")))
    with pytest.raises(claude.ClaudeError, match="cyber"):
        await claude.parse(Answer, system="s", content="c", effort="low")


@pytest.fixture
def fresh_client():
    get_settings.cache_clear()
    claude.get_client.cache_clear()
    yield
    get_settings.cache_clear()
    claude.get_client.cache_clear()


def test_client_prefers_halo_api_key(monkeypatch, fresh_client):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-sdk-env")
    monkeypatch.setenv("HALO_ANTHROPIC_API_KEY", "sk-ant-from-halo-env")
    assert claude.get_client().api_key == "sk-ant-from-halo-env"


def test_client_falls_back_to_sdk_env(monkeypatch, fresh_client):
    monkeypatch.delenv("HALO_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-sdk-env")
    assert claude.get_client().api_key == "sk-ant-from-sdk-env"
