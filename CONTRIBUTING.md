# Contributing

MoneyPrinter V2 is currently maintained around a YouTube Shorts-first workflow. Contributions are welcome when they make that workflow more reliable, easier to operate, or better documented.

## Before You Open A PR

1. Make sure your change fits the current repo direction: Shorts generation, publishing, scheduling, diagnostics, or closely related tooling.
2. For larger changes, open an issue or discussion first so the scope and direction are clear.
3. Keep each PR focused. Small, reviewable changes move faster than broad refactors.

## Pull Request Expectations

1. Target the repository's active default branch.
2. Use a clear title and description that explain the behavior change.
3. Include tests when you change runtime behavior.
4. Update docs when setup, configuration, or operator workflow changes.
5. Avoid unrelated cleanup in the same PR.

## Local Validation

Run the checks that match your change before opening a PR. Common examples are:

```bash
python -m pytest
python scripts/preflight_local.py
```

If you only changed docs, say so in the PR description.

## Scope Guidance

This repo no longer treats Twitter bots, affiliate marketing, outreach automation, or other fork-era product categories as the public top-level product surface. PRs that reintroduce those areas should be discussed before implementation.

## Code Of Conduct

Project participants are expected to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
*** Delete File: /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter/docs/AffiliateMarketing.md
*** Delete File: /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter/docs/TwitterBot.md
*** Delete File: /Users/cris/.config/superpowers/worktrees/MoneyPrinterV2/mpv2-openrouter/.github/FUNDING.yml
