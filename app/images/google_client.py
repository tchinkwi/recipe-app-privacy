from __future__ import annotations

from io import BytesIO
from typing import Optional
from PIL import Image

from google import genai
from google.genai import types

from app.config import CONFIG


class GoogleImageClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or CONFIG.google_api_key
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY not configured")
        self.model = model or CONFIG.google_image_model
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, width: int = 1024, height: int = 1024) -> Image.Image:
        resp = self.client.models.generate_images(
            model=self.model,
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
        if not resp.generated_images:
            raise RuntimeError("No images returned from Google image generation")
        img_bytes = resp.generated_images[0].image.image_bytes
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        return img