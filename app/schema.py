from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


class ImageMotion(BaseModel):
    # Ken Burns motion
    pan_start: Optional[float] = Field(default=0.0, description="Horizontal pan start -1..1")
    pan_end: Optional[float] = Field(default=0.0, description="Horizontal pan end -1..1")
    zoom_start: Optional[float] = Field(default=1.0, description="Zoom multiplier at start")
    zoom_end: Optional[float] = Field(default=1.05, description="Zoom multiplier at end")


class Transition(BaseModel):
    type: Literal["crossfade", "fade", "none"] = "crossfade"
    duration_sec: float = 0.6


class VoiceSpec(BaseModel):
    provider: Literal["azure", "elevenlabs", "none"] = "azure"
    voice_name_or_id: str = ""
    style: Optional[str] = None
    rate: Optional[str] = None  # e.g. "+5%", "-10%"
    pitch: Optional[str] = None  # e.g. "+2st", "-1st"
    emotion: Optional[str] = None  # freeform tag we pass into prompts/ssml where supported


class Scene(BaseModel):
    scene_id: int
    paragraph_text: str
    image_path: Optional[str] = None
    image_prompt: Optional[str] = None
    voiceover_path: Optional[str] = None
    voice: Optional[VoiceSpec] = None
    duration_sec: Optional[float] = None
    motion: ImageMotion = ImageMotion()
    transition_in: Transition = Transition()
    transition_out: Transition = Transition()
    captions: Optional[List[str]] = None


class ProjectMeta(BaseModel):
    title: str
    slug: str
    style_prompt: Optional[str] = None
    reference_image: Optional[str] = None
    image_provider: Literal["stability", "placeholder"] = "stability"
    tts_provider: Literal["azure", "elevenlabs", "none"] = "azure"


class VideoProject(BaseModel):
    meta: ProjectMeta
    scenes: List[Scene]
    assets_dir: str
    output_video_path: Optional[str] = None
    fps: int = 30
    width: int = 1920
    height: int = 1080
    bg_music_path: Optional[str] = None
    sfx: Optional[Dict[str, str]] = None


def slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")