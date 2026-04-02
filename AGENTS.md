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
  - `docs/ShopPaymentArchitecture.md`

## Cross-Project Financial Freedom Context
- This repo should be evaluated as one lane inside Frank's broader financial-freedom system, not in isolation.
- Canonical cross-project references for that system:
  - `docs/FinancialFreedomExecutionStack.md`
  - `docs/Roadmap.md`
  - `/Users/frank_zhang/Documents/文稿 - Frank's MacBook Air/Github项目/paperclip/doc/plans/2026-03-31-paperclip-financial-freedom-positioning.md`
  - `/Users/frank_zhang/Library/Mobile Documents/com~apple~CloudDocs/Obsidian 库/5.知识库/07个人成长/08财务自由之路/1当前财务自由系统的项目分工与顺序（2026-03-31）.md`
- When work touches monetization order, project prioritization, `fzhang.dev`, asset funnels, paid SOPs/templates, bootstrap services, or possible `paperclip` integration, consult the references above before making strategic changes.
- When work touches `shop.fzhang.dev`, payment processors, subscriptions, refunds, billing, entitlement sync, or order mirrors, consult `docs/ShopPaymentArchitecture.md` first.
- `InsForge` should not be introduced by default. Re-evaluate it only if `shop.fzhang.dev` later needs a real internal backend for entitlements, order mirrors, admin operations, and repeated backend iteration after payment integration is already stable.
- Current cross-project operating model:
  - `cash flow survival layer + asset compounding layer + product optionality layer`
  - `MoneyPrinterV2` is the current main execution repo for the asset-compounding layer.
  - `fzhang.dev` is the trust, traffic, and owned-audience surface.
  - The knowledge base is a source-material and evidence ledger, not just storage.
  - `paperclip` is currently later-stage product optionality, not the main short-term monetization engine.
- Guardrail:
  - Do not let `paperclip` or other product bets consume execution budget needed for the current asset loop:
    - close the checklist funnel
    - verify email delivery and tagging
    - publish monetizable long-tail content
    - validate paid SOP / template demand
    - build proof from real traffic, downloads, replies, and purchases
- Promotion rule:
  - Larger product bets should be activated by repeated external proof, not by excitement alone.

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
