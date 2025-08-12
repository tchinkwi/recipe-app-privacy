from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import hashlib
from textwrap import wrap


class PlaceholderImageClient:
    def __init__(self):
        pass

    def _measure_multiline(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, spacing: int) -> tuple[int, int]:
        try:
            bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            lines = text.split("\n")
            max_w = 0
            total_h = 0
            for idx, line in enumerate(lines):
                try:
                    lb = font.getbbox(line or " ")
                    lw, lh = lb[2] - lb[0], lb[3] - lb[1]
                except Exception:
                    lw = int(draw.textlength(line or " ", font=font)) if hasattr(draw, "textlength") else len(line) * max(8, font.size // 2)
                    lh = font.size
                max_w = max(max_w, lw)
                total_h += lh
                if idx < len(lines) - 1:
                    total_h += spacing
            return max_w, total_h

    def generate(self, prompt: str, width: int = 1024, height: int = 1024):
        seed = int(hashlib.md5(prompt.encode("utf-8")).hexdigest(), 16)
        bg_r = 160 + (seed % 80)
        bg_g = 160 + ((seed >> 8) % 80)
        bg_b = 160 + ((seed >> 16) % 80)
        img = Image.new("RGB", (width, height), (bg_r, bg_g, bg_b))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", size=max(18, width // 32))
        except Exception:
            font = ImageFont.load_default()
        text = " ".join(prompt.split()[:18]) + ("…" if len(prompt.split()) > 18 else "")
        wrapped = wrap(text, width=28)
        text_block = "\n".join(wrapped[:6])
        spacing = 6
        tw, th = self._measure_multiline(draw, text_block, font=font, spacing=spacing)
        x = max(10, (width - tw) // 2)
        y = max(10, (height - th) // 2)
        # Background panel
        pad = 20
        draw.rectangle([(x - pad, y - pad), (x + tw + pad, y + th + pad)], fill=(255, 255, 255))
        draw.multiline_text((x, y), text_block, fill=(20, 20, 20), font=font, align="center", spacing=spacing)
        return img