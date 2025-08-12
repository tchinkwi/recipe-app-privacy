from __future__ import annotations

import argparse
import json
import os
from typing import List, Optional

from PIL import Image

from app.config import CONFIG
from app.schema import VideoProject, ProjectMeta, Scene, VoiceSpec, ImageMotion, slugify
from app.llm.gemini_client import GeminiClient
from app.images.stability_client import StabilityClient
from app.images.placeholder_client import PlaceholderImageClient
from app.tts.azure_tts_client import AzureTTSClient
from app.tts.elevenlabs_client import ElevenLabsClient
from app.renderer.video_renderer import render_video


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def parse_size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def generate_project(title: str, num_paragraphs: int, style_prompt: Optional[str], reference_image: Optional[str], image_provider: str, voice_provider: str, azure_voice: Optional[str], elevenlabs_voice_id: Optional[str], width: int, height: int, out_dir: str, source_url: Optional[str]) -> VideoProject:
    ensure_dir(out_dir)
    assets_dir = os.path.join(out_dir, "assets")
    ensure_dir(assets_dir)

    gemini = GeminiClient()
    story = gemini.generate_story_outline(title=title, num_paragraphs=num_paragraphs, style_prompt=style_prompt, source_url=source_url)

    meta = ProjectMeta(
        title=title,
        slug=slugify(title),
        style_prompt=style_prompt,
        reference_image=reference_image,
        image_provider=image_provider,  # type: ignore
        tts_provider=voice_provider,  # type: ignore
    )

    # Build scenes
    scenes: List[Scene] = []
    for idx, paragraph in enumerate(story.get("paragraphs", [])[:num_paragraphs]):
        image_prompt = gemini.image_prompt_for_paragraph(paragraph, style_prompt)
        voice_spec: Optional[VoiceSpec]
        if voice_provider == "none":
            voice_spec = VoiceSpec(provider="none")
        elif voice_provider == "azure":
            voice_spec = VoiceSpec(
                provider="azure",
                voice_name_or_id=(azure_voice or CONFIG.default_azure_voice),
                style=(CONFIG.default_voice_style),
            )
        else:
            voice_spec = VoiceSpec(
                provider="elevenlabs",
                voice_name_or_id=(elevenlabs_voice_id or CONFIG.elevenlabs_voice_id or ""),
            )
        duration = 6.0
        scenes.append(Scene(
            scene_id=idx + 1,
            paragraph_text=paragraph,
            image_prompt=image_prompt,
            duration_sec=duration,
            motion=ImageMotion(),
            voice=voice_spec,
        ))

    project = VideoProject(
        meta=meta,
        scenes=scenes,
        assets_dir=assets_dir,
        width=width,
        height=height,
        output_video_path=os.path.join(out_dir, f"{meta.slug}.mp4"),
    )

    # Providers
    placeholder = PlaceholderImageClient()
    stability = StabilityClient() if image_provider == "stability" else None
    tts_azure = AzureTTSClient() if voice_provider == "azure" else None
    tts_el = ElevenLabsClient() if voice_provider == "elevenlabs" else None

    ref_img = reference_image
    for scene in project.scenes:
        # Image
        if image_provider == "stability":
            if ref_img:
                img = stability.img2img(scene.image_prompt, ref_img, strength=0.35, width=project.width, height=project.height)
            else:
                img = stability.generate(scene.image_prompt, width=project.width, height=project.height)
        else:
            img = placeholder.generate(scene.image_prompt or scene.paragraph_text, width=project.width, height=project.height)
        img_path = os.path.join(project.assets_dir, f"scene_{scene.scene_id:02d}.jpg")
        img.save(img_path)
        scene.image_path = img_path

        # Voice
        if voice_provider == "azure":
            voice_out = os.path.join(project.assets_dir, f"scene_{scene.scene_id:02d}.mp3")
            assert scene.voice
            tts_azure.synthesize_to_file(text=scene.paragraph_text, output_path=voice_out, voice_name=scene.voice.voice_name_or_id, style=scene.voice.style)
            scene.voiceover_path = voice_out
        elif voice_provider == "elevenlabs":
            voice_out = os.path.join(project.assets_dir, f"scene_{scene.scene_id:02d}.mp3")
            assert scene.voice
            tts_el.synthesize_to_file(text=scene.paragraph_text, output_path=voice_out, voice_id=scene.voice.voice_name_or_id)
            scene.voiceover_path = voice_out
        else:
            scene.voiceover_path = None

    # Save JSON
    project_json = os.path.join(out_dir, "project.json")
    with open(project_json, "w", encoding="utf-8") as f:
        json.dump(json.loads(project.model_dump_json(indent=2)), f, indent=2)

    print(f"Project created: {project_json}")
    return project


def load_project(project_json_path: str) -> VideoProject:
    with open(project_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return VideoProject.model_validate(data)


def save_project(project: VideoProject, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(json.loads(project.model_dump_json(indent=2)), f, indent=2)


def regenerate(project: VideoProject, which: str, what: List[str], style_prompt: Optional[str], reference_image: Optional[str]) -> VideoProject:
    ensure_dir(project.assets_dir)
    regenerate_image = "image" in what or "both" in what
    regenerate_voice = "voice" in what or "both" in what

    gemini = GeminiClient()
    # Image providers
    img_provider = project.meta.image_provider
    stability = StabilityClient() if img_provider == "stability" else None
    placeholder = PlaceholderImageClient() if img_provider == "placeholder" else None

    parts = which.split(":")
    if parts[0] != "scene":
        raise ValueError("Use --regen scene:<id>")
    scene_id = int(parts[1])

    target_scene = next(s for s in project.scenes if s.scene_id == scene_id)
    if style_prompt is None:
        style_prompt = project.meta.style_prompt

    if regenerate_image:
        target_scene.image_prompt = gemini.image_prompt_for_paragraph(target_scene.paragraph_text, style_prompt)
        if img_provider == "stability":
            if reference_image or project.meta.reference_image:
                ref = reference_image or project.meta.reference_image
                img = stability.img2img(target_scene.image_prompt, ref, strength=0.35, width=project.width, height=project.height)
            else:
                img = stability.generate(target_scene.image_prompt, width=project.width, height=project.height)
        else:
            img = placeholder.generate(target_scene.image_prompt or target_scene.paragraph_text, width=project.width, height=project.height)
        img_path = os.path.join(project.assets_dir, f"scene_{target_scene.scene_id:02d}.jpg")
        img.save(img_path)
        target_scene.image_path = img_path

    if regenerate_voice and project.meta.tts_provider != "none":
        out = os.path.join(project.assets_dir, f"scene_{target_scene.scene_id:02d}.mp3")
        if project.meta.tts_provider == "azure":
            assert target_scene.voice
            AzureTTSClient().synthesize_to_file(
                text=target_scene.paragraph_text,
                output_path=out,
                voice_name=target_scene.voice.voice_name_or_id,
                style=target_scene.voice.style,
                rate=target_scene.voice.rate,
                pitch=target_scene.voice.pitch,
            )
        elif project.meta.tts_provider == "elevenlabs":
            assert target_scene.voice
            ElevenLabsClient().synthesize_to_file(
                text=target_scene.paragraph_text,
                output_path=out,
                voice_id=target_scene.voice.voice_name_or_id,
            )
        target_scene.voiceover_path = out

    return project


def main():
    ap = argparse.ArgumentParser("story-video-builder")
    ap.add_argument("--title", type=str, help="Story title")
    ap.add_argument("--num-paragraphs", type=int, default=6)
    ap.add_argument("--style-prompt", type=str, default=None)
    ap.add_argument("--reference-image", type=str, default=None)
    ap.add_argument("--output-dir", type=str, default=None)
    ap.add_argument("--image-size", type=str, default=CONFIG.default_image_size)
    ap.add_argument("--source-url", type=str, default=None)

    ap.add_argument("--image-provider", type=str, choices=["stability", "placeholder"], default=None)
    ap.add_argument("--voice-provider", type=str, choices=["azure", "elevenlabs", "none"], default=None)
    ap.add_argument("--azure-voice", type=str, default=CONFIG.default_azure_voice)
    ap.add_argument("--elevenlabs-voice-id", type=str, default=None)
    ap.add_argument("--voice-style", type=str, default=CONFIG.default_voice_style)
    ap.add_argument("--voice-rate", type=str, default=None)
    ap.add_argument("--voice-pitch", type=str, default=None)

    ap.add_argument("--project-json", type=str, default=None, help="Load existing project JSON")
    ap.add_argument("--regen", type=str, default=None, help="Regenerate target, e.g., scene:3")
    ap.add_argument("--regen-what", type=str, default="both", help="image,voice,both")
    ap.add_argument("--render", action="store_true")

    args = ap.parse_args()

    # Determine providers if not explicitly set
    img_provider = args.image_provider or ("stability" if CONFIG.stability_api_key else "placeholder")
    voice_provider = args.voice_provider or ("azure" if CONFIG.azure_speech_key and CONFIG.azure_speech_region else "none")

    if args.project_json:
        project = load_project(args.project_json)
        out_dir = os.path.dirname(args.project_json)
    else:
        if not args.title:
            raise SystemExit("--title is required when not using --project-json")
        width, height = parse_size(args.image_size)
        out_dir = args.output_dir or os.path.join("./outputs", slugify(args.title))
        project = generate_project(
            title=args.title,
            num_paragraphs=args.num_paragraphs,
            style_prompt=args.style_prompt,
            reference_image=args.reference_image,
            image_provider=img_provider,
            voice_provider=voice_provider,
            azure_voice=args.azure_voice,
            elevenlabs_voice_id=args.elevenlabs_voice_id,
            width=width,
            height=height,
            out_dir=out_dir,
            source_url=args.source_url,
        )

    # Apply regen if requested
    changed = False
    if args.regen:
        what = [w.strip() for w in args.regen_what.split(",")]
        project = regenerate(project, which=args.regen, what=what, style_prompt=args.style_prompt, reference_image=args.reference_image)
        changed = True

    # Save if modified
    project_json_path = os.path.join(out_dir, "project.json")
    if changed:
        save_project(project, project_json_path)
        print(f"Project updated: {project_json_path}")

    # Render if requested
    if args.render:
        render_video(project, project.output_video_path)
        print(f"Video written: {project.output_video_path}")


if __name__ == "__main__":
    main()