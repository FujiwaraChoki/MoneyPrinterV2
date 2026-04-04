# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MoneyPrinterV2 (MPV2) is a Python 3.12 CLI tool that automates four online workflows:
1. **YouTube Shorts** — generate video (LLM script → TTS → images → MoviePy composite) and upload via Selenium
2. **Twitter/X Bot** — generate and post tweets via Selenium
3. **Affiliate Marketing** — scrape Amazon product info, generate pitch, share on Twitter
4. **Local Business Outreach** — scrape Google Maps (Go binary), extract emails, send cold outreach via SMTP

There is no web UI and no REST API. The repo does include a `unittest` suite under `tests/`; there is no linting config or CI.

## Running the Application

```bash
# First-time setup
cp config.example.json config.json
python3.12 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt

# Optional macOS convenience setup (installs deps and seeds local defaults)
bash scripts/setup_local.sh

# Required before startup: configure openrouter_api_key and openrouter_model
# in config.json (or provide OPENROUTER_API_KEY / OPENROUTER_MODEL).
# Preflight also validates Nano Banana 2 credentials and local STT dependencies.
python scripts/preflight_local.py

# Run from the project root
python src/main.py
```

The app must be run from the project root. `python src/main.py` adds `src/` to `sys.path`, so all imports use bare module names (for example `from config import *`, not `from src.config import *`). Startup is config-driven: there is no interactive model picker.

## Architecture

### Entry Points
- `src/main.py` — interactive menu loop (primary); bootstraps the configured OpenRouter model once at startup
- `src/cron.py` — headless runner invoked by the scheduler as a subprocess using `sys.executable` and the repo-local script path, equivalent to `python src/cron.py <platform> <account_uuid> [model]`

### Provider Pattern
Two service categories use configuration-driven dispatch:

| Category | Config key | Options |
|---|---|---|
| LLM | `openrouter_model` | OpenRouter chat completions via `src/llm_provider.py`. `openrouter_api_key` is required, `openrouter_base_url` defaults to `https://openrouter.ai/api/v1`, and startup exits if no model is configured. |
| Image gen | — | `nanobanana2` (Gemini image API) |
| STT | `stt_provider` | `local_whisper`, `third_party_assemblyai` |

LLM text generation is OpenRouter-backed. There is no local model-server dependency or startup-time model selection flow.

### Key Modules
- **`src/llm_provider.py`** — unified `generate_text(prompt)` function using the OpenRouter chat completions API
- **`src/config.py`** — 30+ getter functions, each re-reads `config.json` on every call (no caching). `ROOT_DIR` = project root, computed as `os.path.dirname(sys.path[0])`
- **`src/cache.py`** — JSON file persistence in `.mp/` directory (accounts, videos, posts, products)
- **`src/constants.py`** — menu strings, Selenium selectors (YouTube Studio, X.com, Amazon)
- **`src/classes/YouTube.py`** — most complex class; full pipeline: topic → script → metadata → image prompts → images → TTS → subtitles → MoviePy combine → Selenium upload
- **`src/classes/Twitter.py`** — Selenium automation against x.com
- **`src/classes/AFM.py`** — Amazon scraping + LLM pitch generation
- **`src/classes/Outreach.py`** — Google Maps scraper (requires Go) + email sending via yagmail
- **`src/classes/Tts.py`** — KittenTTS wrapper

### Data Storage
All persistent state lives in `.mp/` at the project root as JSON files (`youtube.json`, `twitter.json`, `afm.json`). This directory also serves as scratch space for temporary WAV, PNG, SRT, and MP4 files — non-JSON files are cleaned on each run by `rem_temp_files()`.

### Browser Automation
Selenium uses pre-authenticated Firefox profiles (never handles login). The profile path is stored per-account in the cache JSON and also in `config.json` as a default.

### CRON Scheduling
Uses Python's `schedule` library (in-process, not OS cron). The scheduled job spawns `subprocess.run([sys.executable, ROOT_DIR/src/cron.py, platform, account_id, <optional model override>])`. If no override is passed, `src/cron.py` uses the configured `openrouter_model` by default.

## Configuration

All config lives in `config.json` at the project root. See `config.example.json` for the full template and `docs/Configuration.md` for reference. Key external dependencies to configure:
- **OpenRouter** — required for LLM text generation (`openrouter_api_key`, `openrouter_model`, optionally `openrouter_base_url`)
- **ImageMagick** — required for MoviePy subtitle rendering (`imagemagick_path`)
- **Firefox profile** — must be pre-logged-in to target platforms (`firefox_profile`)
- **Nano Banana 2** — for image generation (Gemini image API)
- **Go** — only needed for Outreach (Google Maps scraper)

## Contributing

PRs go against `main`. One feature/fix per PR. Open an issue first. Use `WIP` label for in-progress PRs.
