import json

from halo.ai import translate
from halo.ai.claude import ClaudeError
from halo.ai.translate import TranslatedBatch, TranslatedItem


def sent_items(content: str) -> list[dict]:
    return json.loads(content[content.index("[") :])


def to_uzbek(content: str) -> TranslatedBatch:
    return TranslatedBatch(items=[TranslatedItem(id=i["id"], text=f"UZ {i['text']}") for i in sent_items(content)])


async def test_translates_once_then_serves_from_cache(api, fake_claude):
    fake_claude.on(TranslatedBatch, to_uzbek)
    body = {"lang": "uz", "texts": ["skincare", "", "Films at home.", "skincare"]}

    first = await api.post("/translate", json=body)

    assert first.json()["texts"] == ["UZ skincare", "", "UZ Films at home.", "UZ skincare"]
    assert [i["text"] for i in sent_items(fake_claude.calls[0]["content"])] == ["skincare", "Films at home."]
    assert "Uzbek" in fake_claude.calls[0]["system"]

    second = await api.post("/translate", json=body)
    assert second.json() == first.json()
    assert len(fake_claude.calls) == 1  # served from the translations table


async def test_english_needs_no_translation(api, fake_claude):
    resp = await api.post("/translate", json={"lang": "en", "texts": ["skincare"]})
    assert resp.json()["texts"] == ["skincare"]
    assert fake_claude.calls == []


async def test_skipped_items_stay_english_and_are_asked_for_again(api, fake_claude):
    fake_claude.on(TranslatedBatch, TranslatedBatch(items=[TranslatedItem(id=0, text="teri parvarishi")]))
    body = {"lang": "uz", "texts": ["skincare", "makeup"]}

    resp = await api.post("/translate", json=body)
    assert resp.json()["texts"] == ["teri parvarishi", "makeup"]

    fake_claude.on(TranslatedBatch, to_uzbek)
    resp = await api.post("/translate", json=body)
    assert resp.json()["texts"] == ["teri parvarishi", "UZ makeup"]
    assert [i["text"] for i in sent_items(fake_claude.calls[-1]["content"])] == ["makeup"]


async def test_large_requests_are_split_into_batches(api, fake_claude, monkeypatch):
    monkeypatch.setattr(translate, "BATCH_SIZE", 2)
    fake_claude.on(TranslatedBatch, to_uzbek)

    resp = await api.post("/translate", json={"lang": "ru", "texts": ["a", "b", "c"]})

    assert resp.json()["texts"] == ["UZ a", "UZ b", "UZ c"]
    assert len(fake_claude.calls) == 2
    assert "Russian" in fake_claude.calls[0]["system"]


async def test_failed_translation_is_a_502(api, fake_claude):
    def decline(content):
        raise ClaudeError("Claude declined the request")

    fake_claude.on(TranslatedBatch, decline)
    resp = await api.post("/translate", json={"lang": "uz", "texts": ["skincare"]})
    assert resp.status_code == 502


async def test_request_size_is_limited(api, fake_claude):
    resp = await api.post("/translate", json={"lang": "uz", "texts": ["x"] * 301})
    assert resp.status_code == 422
    assert fake_claude.calls == []
