from __future__ import annotations

import os
import uuid
from typing import Optional
import requests

from app.config import CONFIG


class AzureTTSClient:
    def __init__(self, key: Optional[str] = None, region: Optional[str] = None):
        self.key = key or CONFIG.azure_speech_key
        self.region = region or CONFIG.azure_speech_region
        if not self.key or not self.region:
            raise RuntimeError("Azure Speech not configured")
        self.endpoint = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1"

    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice_name: str,
        style: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
    ) -> str:
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
            "User-Agent": "story-video-builder",
        }
        prosody_attrs = []
        if rate:
            prosody_attrs.append(f'rate="{rate}"')
        if pitch:
            prosody_attrs.append(f'pitch="{pitch}"')
        prosody_attr_str = (" " + " ".join(prosody_attrs)) if prosody_attrs else ""

        if style:
            express_open = f"<mstts:express-as style=\"{style}\">"
            express_close = "</mstts:express-as>"
        else:
            express_open = ""
            express_close = ""

        ssml = f"""
<speak version='1.0' xml:lang='en-US' xmlns:mstts='http://www.w3.org/2001/mstts' xmlns='http://www.w3.org/2001/10/synthesis'>
  <voice name='{voice_name}'>
    <prosody{prosody_attr_str}>{express_open}{text}{express_close}</prosody>
  </voice>
</speak>
""".strip()
        resp = requests.post(self.endpoint, headers=headers, data=ssml.encode("utf-8"), timeout=120)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path