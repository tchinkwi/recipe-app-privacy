from __future__ import annotations

import os
from typing import List
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import numpy as np
from PIL import Image

# Pillow>=10 removed ANTIALIAS; alias to LANCZOS for MoviePy compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS  # type: ignore[attr-defined]

from app.schema import VideoProject, Scene


def _ken_burns_clip(image_path: str, duration: float, width: int, height: int, pan_start: float, pan_end: float, zoom_start: float, zoom_end: float):
    base_clip = ImageClip(image_path).resize(height=height)
    w, h = base_clip.size
    start_x = (w - width) * (pan_start + 1) / 2 if w > width else 0
    end_x = (w - width) * (pan_end + 1) / 2 if w > width else 0

    def make_frame(t):
        alpha = t / duration if duration > 0 else 1.0
        zoom = zoom_start + (zoom_end - zoom_start) * alpha
        x = int(start_x + (end_x - start_x) * alpha)
        frame = base_clip.get_frame(min(t, duration - 1e-3))
        H, W = frame.shape[0], frame.shape[1]
        crop_w = max(1, int(W / max(zoom, 1e-3)))
        crop_h = max(1, int(H / max(zoom, 1e-3)))
        x0 = max(0, min(W - crop_w, x))
        y0 = max(0, (H - crop_h) // 2)
        cropped = frame[y0:y0+crop_h, x0:x0+crop_w]
        img = Image.fromarray(cropped).resize((width, height), Image.LANCZOS)
        return np.array(img)

    animated = base_clip.set_duration(duration).set_make_frame(make_frame)
    return animated


def render_video(project: VideoProject, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    visual_clips = []

    for scene in project.scenes:
        duration = scene.duration_sec or 6.0
        motion = scene.motion
        img_clip = _ken_burns_clip(
            scene.image_path,
            duration,
            project.width,
            project.height,
            pan_start=motion.pan_start or 0.0,
            pan_end=motion.pan_end or 0.0,
            zoom_start=motion.zoom_start or 1.0,
            zoom_end=motion.zoom_end or 1.05,
        )
        if scene.voiceover_path:
            audio = AudioFileClip(scene.voiceover_path)
            img_clip = img_clip.set_audio(audio.set_duration(duration))
        visual_clips.append(
            img_clip.crossfadein(scene.transition_in.duration_sec).crossfadeout(scene.transition_out.duration_sec)
        )

    final = concatenate_videoclips(visual_clips, method="compose")
    final.write_videofile(output_path, fps=project.fps, audio_codec="aac")
    return output_path