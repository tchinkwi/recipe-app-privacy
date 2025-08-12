from __future__ import annotations

import os
from typing import Optional
import requests

from app.config import CONFIG


class ElevenLabsClient:
    def __init__(self, api_key: Optional[str] = None, default_voice_id: Optional[str] = None):
        self.api_key = api_key or CONFIG.elevenlabs_api_key
        self.voice_id = default_voice_id or CONFIG.elevenlabs_voice_id
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not configured")
        self.base_url = "https://api.elevenlabs.io/v1"

    def synthesize_to_file(self, text: str, output_path: str, voice_id: Optional[str] = None, stability: float = 0.5, similarity_boost: float = 0.75, style: Optional[float] = None) -> str:
        vid = voice_id or self.voice_id
        if not vid:
            raise RuntimeError("No ElevenLabs voice id provided")
        url = f"{self.base_url}/text-to-speech/{vid}"
        headers = {
            "xi-api-key": self.api_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        }
        payload = {
            "text": text,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }
        if style is not None:
            payload["voice_settings"]["style"] = style
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path