"""Speech-to-text for creator videos (Uzbek, Russian, English).

Uzbek speech recognition quality varies a lot between providers, so this is a
small interface: test providers on real Uzbek/Russian audio and swap freely.
"""

from typing import Protocol

import httpx

from halo.config import get_settings


class Transcriber(Protocol):
    async def transcribe(self, audio_mp3: bytes) -> str: ...


class ElevenLabsTranscriber:
    url = "https://api.elevenlabs.io/v1/speech-to-text"

    def __init__(self, api_key: str, model_id: str = "scribe_v1"):
        self.api_key = api_key
        self.model_id = model_id

    async def transcribe(self, audio_mp3: bytes) -> str:
        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(
                self.url,
                headers={"xi-api-key": self.api_key},
                data={"model_id": self.model_id},
                files={"file": ("audio.mp3", audio_mp3, "audio/mpeg")},
            )
            resp.raise_for_status()
            return resp.json().get("text", "")


def get_transcriber() -> Transcriber | None:
    settings = get_settings()
    if settings.elevenlabs_api_key:
        return ElevenLabsTranscriber(settings.elevenlabs_api_key)
    return None
