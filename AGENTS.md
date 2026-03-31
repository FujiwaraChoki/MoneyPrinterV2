# Repository Guidelines

## Current Product Direction
- This fork is Frank's custom `MoneyPrinter`, not a generic client-acquisition helper.
- Prioritize business layers in this order:
  - `Asset Printer`: reusable content assets, checklists, SOPs, templates, comparison pages.
  - `Lead Printer`: owned audience, subscribers, repeat traffic, search/social entry points.
  - `Cash Printer`: selective service revenue only as bootstrap support.
- Strategy test for new work:
  - Prefer features and content that create reusable assets, strengthen owned audience, or improve low-touch monetization.
  - Avoid changes that mainly optimize for selling more hours or turning the repo into a generic agency machine.
- Current first asset path:
  - free asset first: `开源 AI 项目部署前检查清单`
  - then paid asset: launch / hardening SOPs, templates, or other low-touch digital products
- Site positioning:
  - `fzhang.dev` should remain content-first.
  - Homepage CTA should bias toward owned-asset capture, not hard service selling.
- Canonical strategy docs:
  - `docs/FrankMoneyPrinter.md`
  - `docs/Roadmap.md`
  - `docs/FirstAssetSpec.md`
  - `docs/FinancialFreedomPath.md`
  - `docs/FzhangHomepageCopy.md`

## Project Structure & Module Organization
- `src/` contains the application code. Use `src/main.py` as the interactive entrypoint.
- `src/classes/` holds provider-specific components (for example `YouTube.py`, `Twitter.py`, `Tts.py`, `AFM.py`, `Outreach.py`).
- Shared utilities and configuration live in modules like `src/config.py`, `src/utils.py`, `src/cache.py`, and `src/constants.py`.
- `scripts/` contains helper workflows such as setup, preflight checks, and upload helpers.
- `docs/` contains feature documentation; `assets/` and `fonts/` contain static resources.

## Build, Test, and Development Commands
- `bash scripts/setup_local.sh`: bootstrap local development (creates `venv`, installs deps, seeds `config.json`, runs preflight).
- `source venv/bin/activate && pip install -r requirements.txt`: manual dependency install/update.
- `python3 scripts/preflight_local.py`: validate local provider/config readiness before running tasks.
- `python3 src/main.py`: start the CLI app.
- `bash scripts/upload_video.sh`: run direct script-based upload flow from repo root.

## Coding Style & Naming Conventions
- Target Python 3.12 (project requirement in `README.md`).
- Use 4-space indentation and follow existing Python conventions:
  - `snake_case` for functions/variables
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants
- Keep new business logic in focused modules under `src/`; keep provider/integration code in `src/classes/`.
- Prefer small, explicit functions and preserve existing CLI-first behavior.

## Testing Guidelines
- There is currently no enforced automated test suite or coverage threshold.
- Minimum validation for changes:
  - Run `python3 scripts/preflight_local.py`
  - Smoke-test impacted flows via `python3 src/main.py`
- When adding tests, place them in a top-level `tests/` directory with names like `test_<module>.py`.

## Commit & Pull Request Guidelines
- Follow the existing commit style: imperative summaries like `Fix ...`, `Update ...`, optionally with issue refs (for example `(#128)`).
- Open PRs against `main`.
- Link each PR to an issue, keep scope to one feature/fix, and use a clear title + description.
- Mark not-ready PRs with `WIP` and remove it when ready for review.

## Security & Configuration Tips
- Treat `config.json` as environment-specific; do not commit real API keys or private profile paths.
- Start from `config.example.json` and prefer environment variables where supported (for example `GEMINI_API_KEY`).
