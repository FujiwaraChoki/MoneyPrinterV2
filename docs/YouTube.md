# YouTube Shorts Automater

MPV2 uses a similar implementation of V1 (see [MPV1](https://github.com/FujiwaraChoki/MoneyPrinter)), to generate Video-Files and upload them to YouTube Shorts.

In contrast to V1, V2 uses AI generated images as the visuals for the video, instead of using stock footage. This makes the videos more unique and less likely to be flagged by YouTube. V2 also supports music right from the get-go.

## Relevant Configuration

In your `config.json`, you need the following attributes filled out, so that the bot can function correctly.

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
