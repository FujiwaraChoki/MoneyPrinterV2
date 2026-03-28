# Twitter Bot

This bot is designed to automate the process of growing a Twitter account. Once you created a new account, provide the path to the Firefox Profile and the bot will start posting tweets based on the subject you provided during the account creation.

When creating a Twitter account in the app, also set a `character/context` for that account. This acts like a persistent persona so the bot keeps a more stable voice, tone, and point of view across posts.

## Relevant Configuration

In your `config.json`, you need the following attributes filled out, so that the bot can function correctly.

```json
{
  "twitter_language": "Arabic",
  "twitter_dialect": "Egyptian Arabic",
  "headless": true,
  "llm": "The Large Language Model you want to use, check Configuration.md for more information",
}
```
