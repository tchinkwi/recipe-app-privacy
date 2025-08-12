from __future__ import annotations

from typing import Dict, List
import google.generativeai as genai

from app.config import CONFIG


class GeminiClient:
    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key or CONFIG.google_api_key
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY not configured")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def _extract_json(self, text: str) -> Dict | None:
        import json, re
        s = text.strip()
        # Remove common code fences
        if s.startswith("```"):
            # remove the first fence line and the last fence
            s = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", s)
            s = re.sub(r"\n```\s*$", "", s)
        # Try direct parse
        try:
            return json.loads(s)
        except Exception:
            pass
        # Heuristic: take between first { and last }
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except Exception:
                return None
        return None

    def generate_story_outline(
        self,
        title: str,
        num_paragraphs: int,
        audience: str = "sleepy story",
        style_prompt: str | None = None,
        source_url: str | None = None,
    ) -> Dict:
        instr = (
            "You are an expert YouTube scriptwriter focused on retention. "
            "Write a calm sleepy story with gentle hooks, micro-tension, and curiosity loops. "
            "Return ONLY valid JSON. No extra text. No markdown fences."
        )
        url_line = f"Source inspiration: {source_url}\n" if source_url else ""
        user = (
            f"Title: {title}\n"
            f"{url_line}"
            f"Audience: {audience}\n"
            f"Paragraphs: {num_paragraphs}\n"
            f"Style: {style_prompt or 'calm, minimalist'}\n\n"
            "JSON schema: {\n"
            "  \"hook\": string,\n"
            "  \"outline\": string[],\n"
            "  \"paragraphs\": string[],\n"
            "  \"retention_notes\": string[]\n"
            "}\n"
            "Output: JSON only."
        )
        prompt = instr + "\n\n" + user
        resp = self.model.generate_content(prompt)
        text = resp.text or ""
        data = self._extract_json(text)
        if data and isinstance(data, dict) and isinstance(data.get("paragraphs"), list):
            # Normalize paragraph count
            paragraphs: List[str] = [p.strip() for p in data.get("paragraphs", []) if isinstance(p, str) and p.strip()]
            if len(paragraphs) < num_paragraphs:
                # fallback: split text to get more
                extra_src = "\n\n".join(paragraphs) or text
                chunks = [c.strip() for c in extra_src.split("\n\n") if c.strip()]
                for c in chunks:
                    if len(paragraphs) >= num_paragraphs:
                        break
                    if c not in paragraphs:
                        paragraphs.append(c)
            data["paragraphs"] = paragraphs[:num_paragraphs]
            if "outline" in data and isinstance(data["outline"], list):
                data["outline"] = data["outline"][:num_paragraphs]
            return data
        # Fallback: build distinct paragraphs by splitting on blank lines
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not parts:
            parts = [text.strip()] * num_paragraphs
        elif len(parts) < num_paragraphs:
            # expand by sentence groups
            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
            while len(parts) < num_paragraphs and sentences:
                parts.append(". ".join(sentences[:3]) + ".")
                sentences = sentences[3:]
            while len(parts) < num_paragraphs:
                parts.append(parts[-1])
        return {
            "hook": parts[0][:180] if parts else title,
            "outline": [f"Part {i+1}" for i in range(num_paragraphs)],
            "paragraphs": parts[:num_paragraphs],
            "retention_notes": [],
        }

    def image_prompt_for_paragraph(self, paragraph: str, style_prompt: str | None) -> str:
        base = (
            "Create a concise, vivid visual prompt for an illustration that represents the paragraph content. "
            "No text in the image. Keep it calm and suitable for a sleepy story."
        )
        style = f" Style: {style_prompt}." if style_prompt else ""
        return f"{base}{style} Paragraph: {paragraph}"