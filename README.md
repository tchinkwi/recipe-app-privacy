# Story Video Builder

A modular Python toolchain to generate story-style YouTube videos with:

- Script ideation and retention-optimized outline via Gemini
- Per-paragraph images from text or image-to-image with reference style
- Expressive voice-overs (Azure Neural TTS with SSML, or ElevenLabs)
- Regeneration controls for script, images, or voice per scene
- JSON timeline output for effects and movement
- Offline rendering to video with Ken Burns motion and transitions

## Requirements
- Python 3.10+
- API keys (paid):
  - Google Generative AI (Gemini) `GOOGLE_API_KEY`
  - Stability API (SDXL) `STABILITY_API_KEY` (or swap provider later)
  - Azure Cognitive Services Speech (recommended for expressive SSML)
    - `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
  - Optional: ElevenLabs `ELEVENLABS_API_KEY`

## Setup
1. Copy `.env.template` to `.env` and fill in your keys.
2. Create a virtual environment and install deps:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Quickstart
Generate a short sleepy-story video from a title and a style reference image:
```bash
python -m app.orchestrator \
  --title "The Clockmaker of Silent Town" \
  --num-paragraphs 6 \
  --style-prompt "calm, minimalist, cozy night lighting, soft blue palette" \
  --reference-image /path/to/style_ref.jpg \
  --voice-provider azure \
  --azure-voice "en-US-JennyNeural" \
  --voice-style "narration-professional" \
  --voice-rate "-10%" \
  --output-dir ./outputs/clockmaker
```
Regenerate image and voice for scene 3 only:
```bash
python -m app.orchestrator \
  --project-json ./outputs/clockmaker/project.json \
  --regen scene:3 --regen-what image,voice
```
Render video from an existing JSON:
```bash
python -m app.orchestrator \
  --project-json ./outputs/clockmaker/project.json \
  --render
```

## JSON Timeline
The pipeline produces a `project.json` with scenes and assets, suitable for re-rendering and downstream editors.

## Notes
- Default image provider: Stability SDXL. Swap providers by extending `app/images/`.
- Voice: Azure SSML is best for nuanced styles (slow, surprised, whisper). ElevenLabs supported as an alternative.
- Keep outputs organized per project in `./outputs/<slug>/`.