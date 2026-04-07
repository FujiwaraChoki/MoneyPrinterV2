# MoneyPrinter V2

MoneyPrinter V2 is a CLI-first YouTube Shorts automation repo. This fork has diverged substantially from the original upstream project and the documented product surface is now centered on one workflow: generate, review, schedule, and publish short-form video.

## Current Scope

- Generate Shorts scripts with OpenRouter.
- Generate vertical visuals with Gemini/Nano Banana 2 or OpenRouter-backed image models.
- Render voiceover, subtitles, and final video assets locally.
- Upload through a logged-in Firefox profile.
- Optionally publish or cross-post through Post Bridge.
- Revisit saved Shorts from cache and publish them later.
- Schedule recurring runs with custom weekday and time cron entries.

The top-level CLI currently exposes YouTube Shorts automation only.

## Quick Start

```bash
git clone https://github.com/btxbtwn/MoneyPrinterV2.git
cd MoneyPrinterV2
bash scripts/setup_local.sh
```

Then open `config.json` and set the values your workflow actually needs. For the standard Shorts flow, that usually means:

- `openrouter_api_key`
- `openrouter_model`
- `nanobanana2_api_key` or `GEMINI_API_KEY`
- `firefox_profile`
- `imagemagick_path`

After that, run:

```bash
money
```

If `money` is not on your `PATH`, the manual path still works:

```bash
source venv/bin/activate
python scripts/preflight_local.py
python src/main.py
```

## What `setup_local.sh` Does

`bash scripts/setup_local.sh` is the fastest way to get a local environment into a usable state. It will:

- create `config.json` from `config.example.json` if needed
- create `venv/` if needed
- install Python dependencies
- install the `money` launcher
- seed a few local defaults in `config.json` when they can be detected safely
- run `scripts/preflight_local.py`

It does not create API keys, log you into YouTube, or choose production models for you.

## Runtime Flow

The current interactive flow is:

1. Launch `money`.
2. Add or select a YouTube account profile.
3. Use the YouTube submenu to generate a Short, inspect saved Shorts, or manage cron schedules.

The YouTube submenu currently exposes:

- `Upload Short`
- `Show all Shorts`
- `Setup CRON Job`
- `View CRON Jobs`

Generated assets, cached metadata, and cron logs are written under `.mp/`.

## Required Services

- Python 3.12
- OpenRouter for text generation
- Gemini/Nano Banana 2 credentials for the default image path, or OpenRouter image models if you prefer that path
- A Firefox profile already signed into the YouTube account you want to automate
- ImageMagick for MoviePy text/subtitle rendering

`scripts/preflight_local.py` checks the current local setup for the pieces above and will also verify local Whisper imports when `stt_provider` is `local_whisper`.

## Configuration Notes

`config.example.json` still contains a few legacy or experimental keys that are not part of the current top-level documented workflow. The supported Shorts-focused configuration is documented in [docs/Configuration.md](docs/Configuration.md).

If you want Post Bridge to handle YouTube publishing directly instead of using the browser upload path, include `youtube` inside `post_bridge.platforms`. That behavior is documented in [docs/PostBridge.md](docs/PostBridge.md).

## Documentation

- [docs/Configuration.md](docs/Configuration.md)
- [docs/YouTube.md](docs/YouTube.md)
- [docs/PostBridge.md](docs/PostBridge.md)
- [docs/Roadmap.md](docs/Roadmap.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

## Contributing

Contributions that improve the current Shorts workflow are welcome. Before opening a PR, read [CONTRIBUTING.md](CONTRIBUTING.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

MoneyPrinter V2 is licensed under the GNU Affero General Public License v3. See [LICENSE](LICENSE).

## Disclaimer

This project is provided for educational purposes. You are responsible for complying with platform rules, copyright requirements, disclosure obligations, and any other legal or operational constraints that apply to your use case.
