# YouTube Shorts Workflow

This repository is now documented around the YouTube Shorts pipeline. The top-level CLI opens a YouTube-only product surface and lets you generate, review, publish, and schedule Shorts for one or more cached accounts.

## What The Current Flow Does

- generates a topic, script, title, and description
- generates vertical images for the Short
- synthesizes narration and subtitles
- renders the final vertical video
- uploads through a logged-in Firefox profile or publishes through Post Bridge
- stores the resulting metadata so you can review or republish later

## First-Time Setup

Before you launch the CLI, make sure you have:

- a valid `firefox_profile` already signed into the target YouTube account
- OpenRouter credentials configured
- image generation credentials configured
- ImageMagick installed and reachable from `config.json`

Run:

```bash
python scripts/preflight_local.py
```

## Account Setup In The CLI

When you start `money`, the app loads cached YouTube accounts from local storage.

- If no accounts exist yet, the CLI prompts you to create one.
- Each cached account stores a nickname, Firefox profile path, niche, and language.
- You can add more accounts later or delete old ones from the account picker.

The niche and language fields are used to steer prompt generation and metadata tone.

## YouTube Menu

After selecting an account, the current submenu offers:

- `Upload Short`
- `Show all Shorts`
- `Setup CRON Job`
- `View CRON Jobs`

### Upload Short

Generates a new Short for the selected account and then offers the publish step.

### Show all Shorts

Displays saved Shorts with publish status and cross-post status. This is the entry point for revisiting generated videos that were rendered earlier but not published yet.

### Setup CRON Job

The scheduler now supports custom weekday and time selection.

- Every day
- Weekdays only
- Custom weekday numbers
- One or more `HH:MM` times in 24-hour format

The resulting cron entries are installed with account-specific markers so they can be inspected or replaced safely.

### View CRON Jobs

Prints the installed cron lines for the selected account.

## Publish Modes

There are two current publish paths:

1. Browser-driven YouTube upload using the cached Firefox profile.
2. Post Bridge publish, which can optionally include YouTube as the primary publishing target.

If you keep `post_bridge.platforms` limited to non-YouTube platforms, MoneyPrinter V2 uploads to YouTube first and only then offers cross-posting. If you include `youtube` in that list, Post Bridge can take over the publishing step entirely.

## Output And Cache

Generated files, cached metadata, and logs live under `.mp/`. This local cache is what powers the `Show all Shorts` workflow and lets the app avoid reposting platforms that are already marked successful.

## Related Docs

- [Configuration.md](./Configuration.md)
- [PostBridge.md](./PostBridge.md)
- [Roadmap.md](./Roadmap.md)
