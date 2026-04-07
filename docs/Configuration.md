# Configuration

MoneyPrinter V2 reads runtime settings from `config.json` in the repository root. The easiest way to create it is still:

```bash
cp config.example.json config.json
```

This guide documents the supported YouTube Shorts workflow. `config.example.json` may still include a few legacy or experimental keys that are not part of the current top-level documented product surface.

## Recommended Baseline

```json
{
  "verbose": true,
  "firefox_profile": "/path/to/firefox/profile",
  "headless": false,
  "openrouter_api_key": "",
  "openrouter_base_url": "https://openrouter.ai/api/v1",
  "openrouter_model": "google/gemma-4-26b-a4b-it",
  "openrouter_fallback_models": [
    "google/gemma-4-31b-it",
    "qwen/qwen3.6-plus:free"
  ],
  "image_provider": "googleai_studio",
  "openrouter_image_models": [],
  "nanobanana2_api_base_url": "https://generativelanguage.googleapis.com/v1beta",
  "nanobanana2_api_key": "",
  "nanobanana2_model": "gemini-3.1-flash-image-preview",
  "nanobanana2_aspect_ratio": "9:16",
  "stt_provider": "local_whisper",
  "whisper_model": "base",
  "whisper_device": "auto",
  "whisper_compute_type": "int8",
  "assembly_ai_api_key": "",
  "tts_voice": "Jasper",
  "tts_speed": 1.0,
  "subtitle_max_chars": 45,
  "font": "BebasNeue-Regular.ttf",
  "imagemagick_path": "/usr/bin/convert",
  "script_sentence_length": 6,
  "video_motion_style": "static",
  "video_zoom_intensity": 1.12,
  "video_pan_enabled": true,
  "video_pan_intensity": 0.03,
  "threads": 2,
  "zip_url": "",
  "is_for_kids": false,
  "post_bridge": {
    "enabled": false,
    "api_key": "",
    "platforms": ["tiktok", "instagram"],
    "account_ids": [],
    "auto_crosspost": false
  }
}
```

## Required Keys

- `firefox_profile`: Absolute path to the Firefox profile already signed into the YouTube account you want to automate.
- `openrouter_api_key`: OpenRouter API key. Falls back to `OPENROUTER_API_KEY`.
- `openrouter_model`: Primary text model used for script and metadata generation. Falls back to `OPENROUTER_MODEL`.
- `imagemagick_path`: Path to `magick` or `convert`, depending on your platform.

For the default image path, you also need:

- `nanobanana2_api_key`: Gemini image API key. Falls back to `GEMINI_API_KEY`.

## Core Shorts Settings

- `verbose`: Enables extra CLI logging.
- `headless`: Runs browser automation without a visible window when `true`.
- `is_for_kids`: Controls the YouTube upload setting for made-for-kids content.
- `threads`: Worker count used by render-heavy steps.
- `zip_url`: Optional ZIP source for background songs.

## Text Generation

- `openrouter_base_url`: Defaults to `https://openrouter.ai/api/v1` when blank.
- `openrouter_fallback_models`: Ordered fallback list when the primary model fails or is rate-limited.
- `script_sentence_length`: Target number of sentences in the generated script.

## Image Generation

- `image_provider`: Current supported strategies are `googleai_studio`, `openrouter_only`, and `openrouter_then_googleai`.
- `openrouter_image_models`: Ordered list of OpenRouter image models to try when `image_provider` uses an OpenRouter path.
- `nanobanana2_api_base_url`: Gemini image endpoint base URL.
- `nanobanana2_model`: Image model identifier.
- `nanobanana2_aspect_ratio`: Should stay `9:16` for Shorts unless you are deliberately changing the render pipeline.

## Voiceover And Subtitles

- `stt_provider`: `local_whisper` or `third_party_assemblyai`.
- `whisper_model`: Local Whisper model name.
- `whisper_device`: `auto`, `cpu`, or `cuda`.
- `whisper_compute_type`: Precision / quantization mode for local Whisper.
- `assembly_ai_api_key`: Only needed when using AssemblyAI.
- `tts_voice`: KittenTTS voice.
- `tts_speed`: Playback speed multiplier for synthesized narration.
- `subtitle_max_chars`: Maximum subtitle segment width before rebalancing.
- `font`: Subtitle font file stored in `fonts/`.

## Motion And Render Tuning

- `video_motion_style`: `static` or `cinematic`.
- `video_zoom_intensity`: End zoom multiplier for cinematic mode.
- `video_pan_enabled`: Enables horizontal drift in cinematic mode.
- `video_pan_intensity`: Horizontal drift amount as a fraction of frame width.

## Post Bridge

`post_bridge` is optional. Use it when you want to publish through Post Bridge or cross-post a completed YouTube Short to other platforms.

- `enabled`: Turns the integration on.
- `api_key`: Falls back to `POST_BRIDGE_API_KEY` when blank.
- `platforms`: Ordered list of target platforms. The documented flow uses `youtube`, `tiktok`, and `instagram`.
- `account_ids`: Optional fixed Post Bridge account IDs. Keep these in the same order as `platforms`.
- `auto_crosspost`: Runs automatically after success instead of prompting in interactive mode.

See [PostBridge.md](./PostBridge.md) for behavior details.

## Environment Variable Fallbacks

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `GEMINI_API_KEY`
- `POST_BRIDGE_API_KEY`

Example:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export OPENROUTER_MODEL="google/gemma-4-26b-a4b-it"
export GEMINI_API_KEY="your-gemini-api-key"
export POST_BRIDGE_API_KEY="your-post-bridge-api-key"
```

## Validation

Run the local preflight after changing config:

```bash
python scripts/preflight_local.py
```

The preflight checks OpenRouter, Nano Banana 2, ImageMagick, Firefox profile availability, and local Whisper imports when applicable.
