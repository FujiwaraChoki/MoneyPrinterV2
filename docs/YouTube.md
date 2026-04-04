# Legacy YouTube Automation

This document describes the older browser-driven YouTube workflow.

MoneyPrinterV2 now uses Post Bridge as the primary publishing backend for generated videos. See [PostBridge.md](./PostBridge.md) for the current flow.

The legacy implementation used a Firefox profile plus Selenium to upload videos directly to YouTube Shorts after generation.

## Relevant Configuration

If you are still experimenting with the legacy code path, you need the following attributes filled out:

```json
{
  "firefox_profile": "The path to your Firefox profile (used to log in to YouTube)",
  "headless": true,
  "llm": "The Large Language Model you want to use to generate the video script.",
  "image_model": "What AI Model you want to use to generate images.",
  "threads": 4,
  "is_for_kids": true
}
```

## Roadmap

Here are some features that are planned for the future:

- [ ] Subtitles (using either AssemblyAI or locally assembling them)
