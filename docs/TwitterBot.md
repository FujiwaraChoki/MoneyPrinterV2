# Twitter Bot

This bot is designed to automate the process of growing a Twitter account. Once you created a new account, provide the path to the Firefox Profile and the bot will start posting tweets based on the subject you provided during the account creation.

## Ground posts with recent X research

The bot can use Xquik to search recent public X posts before generation. This
gives the LLM current source material instead of relying only on its training
data.

Enable `xquik` in `config.json` and set `XQUIK_API_KEY`:

```json
{
  "xquik": {
    "enabled": true,
    "api_key": "",
    "search_limit": 5
  }
}
```

Each generated post runs 1 metered search when enabled. Results stay in memory
and enter the local LLM prompt. MPV2 excludes replies, reposts, and quotes. It
generates without research if the request fails.

Create an API key in the [Xquik dashboard]. Review [Xquik search usage and
pricing] before enabling the integration.

[Xquik dashboard]: https://dashboard.xquik.com/en/account?tab=api-keys
[Xquik search usage and pricing]: https://github.com/Xquik-dev/x-twitter-scraper#run-one-request

## Relevant Configuration

In your `config.json`, you need the following attributes filled out, so that the bot can function correctly.

```json
{
  "twitter_language": "Any Language, formatting doesn't matter",
  "headless": true,
  "llm": "The Large Language Model you want to use, check Configuration.md for more information",
}
```
