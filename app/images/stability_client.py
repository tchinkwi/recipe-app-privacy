from __future__ import annotations

import base64
import os
from typing import Optional
import requests
from PIL import Image
from io import BytesIO

from app.config import CONFIG


class StabilityClient:
    def __init__(self, api_key: Optional[str] = None, engine: Optional[str] = None):
        self.api_key = api_key or CONFIG.stability_api_key
        self.engine = engine or CONFIG.stability_engine
        if not self.api_key:
            raise RuntimeError("STABILITY_API_KEY not configured")
        self.base_url = "https://api.stability.ai"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
        }

    def generate(self, prompt: str, width: int = 1024, height: int = 1024, seed: Optional[int] = None) -> Image.Image:
        url = f"{self.base_url}/v1/generation/{self.engine}/text-to-image"
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "width": width,
            "height": height,
            "cfg_scale": 7,
            "samples": 1,
        }
        if seed is not None:
            payload["seed"] = seed
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("artifacts"):
            raise RuntimeError("No artifacts returned from Stability")
        b64 = data["artifacts"][0]["base64"]
        return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")

    def img2img(self, prompt: str, reference_path: str, strength: float = 0.35, width: int = 1024, height: int = 1024) -> Image.Image:
        url = f"{self.base_url}/v1/generation/{self.engine}/image-to-image"
        with open(reference_path, "rb") as f:
            files = {
                "init_image": (os.path.basename(reference_path), f, "image/jpeg"),
            }
            data = {
                "text_prompts[0][text]": prompt,
                "image_strength": str(strength),
                "cfg_scale": "7",
                "width": str(width),
                "height": str(height),
                "samples": "1",
            }
            resp = requests.post(url, headers=self._headers(), files=files, data=data, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            if not result.get("artifacts"):
                raise RuntimeError("No artifacts from Stability img2img")
            b64 = result["artifacts"][0]["base64"]
            return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")