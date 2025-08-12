from __future__ import annotations

import asyncio
import os
from typing import Optional, Dict, Any

import edge_tts


class EdgeTTSClient:
    def __init__(self, default_voice: str = "en-US-JennyNeural"):
        self.default_voice = default_voice

    async def _synthesize_async(self, text: str, output_path: str, voice: Optional[str] = None, rate: Optional[str] = None, pitch: Optional[str] = None) -> str:
        kwargs: Dict[str, Any] = {}
        if isinstance(rate, str) and rate.strip():
            kwargs["rate"] = rate
        if isinstance(pitch, str) and pitch.strip():
            kwargs["pitch"] = pitch
        communicate = edge_tts.Communicate(text, voice or self.default_voice, **kwargs)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        await communicate.save(output_path)
        return output_path

    def synthesize_to_file(self, text: str, output_path: str, voice: Optional[str] = None, rate: Optional[str] = None, pitch: Optional[str] = None) -> str:
        asyncio.run(self._synthesize_async(text, output_path, voice=voice, rate=rate, pitch=pitch))
        return output_path