from __future__ import annotations

from typing import List, Dict
import google.generativeai as genai

from app.config import CONFIG


class GeminiClient:
    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key or CONFIG.google_api_key
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY not configured")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_story_outline(self, title: str, num_paragraphs: int, audience: str = "sleepy story", style_prompt: str | None = None) -> Dict:
        sys = (
            "You are an expert YouTube scriptwriter focused on retention. "
            "Craft hooks, micro-tension, and curiosity loops suitable for calm, sleepy storytelling that still keeps attention."
        )
        user = (
            f"Title: {title}\n"
            f"Audience: {audience}\n"
            f"Paragraphs: {num_paragraphs}\n"
            f"Style: {style_prompt or 'calm, minimalist'}\n\n"
            "Return JSON with keys: hook, outline (array of paragraph summaries), "+
            "paragraphs (array of full paragraphs, 3-5 sentences each), and retention_notes (bulleted strategies used)."
        )
        resp = self.model.generate_content([
            {"role": "system", "parts": [sys]},
            {"role": "user", "parts": [user]},
        ])
        text = resp.text
        # The model returns Markdown sometimes; attempt to extract JSON
        import json, re
        match = re.search(r"\{[\s\S]*\}$", text.strip())
        if not match:
            # fallback: simple heuristic to build structure
            return {
                "hook": text.strip().split("\n")[0][:180],
                "outline": [f"Part {i+1}" for i in range(num_paragraphs)],
                "paragraphs": [text.strip() for _ in range(num_paragraphs)],
                "retention_notes": [],
            }
        return json.loads(match.group(0))

    def image_prompt_for_paragraph(self, paragraph: str, style_prompt: str | None) -> str:
        base = (
            "Create a concise, vivid visual prompt for an illustration that represents the paragraph content. "
            "No text in the image. Keep it calm and suitable for a sleepy story."
        )
        style = f" Style: {style_prompt}." if style_prompt else ""
        return f"{base}{style} Paragraph: {paragraph}"