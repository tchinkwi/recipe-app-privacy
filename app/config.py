from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return value


@dataclass
class AppConfig:
    google_api_key: Optional[str] = _env("GOOGLE_API_KEY")
    google_image_model: str = _env("GOOGLE_IMAGE_MODEL", "imagen-4.0-generate-preview-06-06") or "imagen-4.0-generate-preview-06-06"

    stability_api_key: Optional[str] = _env("STABILITY_API_KEY")
    stability_engine: str = _env("STABILITY_ENGINE", "stable-diffusion-xl-1024-v1-0") or "stable-diffusion-xl-1024-v1-0"

    azure_speech_key: Optional[str] = _env("AZURE_SPEECH_KEY")
    azure_speech_region: Optional[str] = _env("AZURE_SPEECH_REGION")

    elevenlabs_api_key: Optional[str] = _env("ELEVENLABS_API_KEY")
    elevenlabs_voice_id: Optional[str] = _env("ELEVENLABS_VOICE_ID")

    default_voice_provider: str = _env("DEFAULT_VOICE_PROVIDER", "azure") or "azure"
    default_azure_voice: str = _env("DEFAULT_AZURE_VOICE", "en-US-JennyNeural") or "en-US-JennyNeural"
    default_voice_style: str = _env("DEFAULT_VOICE_STYLE", "narration-professional") or "narration-professional"

    default_image_size: str = _env("DEFAULT_IMAGE_SIZE", "1024x1024") or "1024x1024"


CONFIG = AppConfig()