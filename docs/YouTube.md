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

## Custom Topics

By default, MPV2 asks the LLM to come up with a video idea based on the account's niche. If you already know what the Short should be about, pick **Upload Short with custom topic** from the YouTube menu instead of **Upload Short**.

You will be prompted for the topic / video idea, e.g. `Why index funds beat stock picking`. The topic generation step is skipped and your text is used as the subject for the script, title, description and image prompts. Everything else (script, metadata, images, voiceover, subtitles, upload, Post Bridge cross-post) works exactly the same.

Leaving the topic empty returns you to the menu without generating anything.

## Roadmap

Here are some features that are planned for the future:

- [ ] Subtitles (using either AssemblyAI or locally assembling them)
