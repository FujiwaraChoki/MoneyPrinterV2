# AFM

This class is responsible for the Affiliate Marketing part of MPV2. It uses the `g4f` package (as all other classes) as it's way to utilize the power of LLMs, in this case, to generate tweets, based on information about an **Amazon Product**. MPV2 will scrape the page of the product, and save the **product title**, and **product features**, thus having enough information to be able to create a pitch for the product, and post it on Twitter.

## Relevant Configuration

In your `config.json`, you need the following attributes filled out, so that the bot can function correctly.

```json
{
  "firefox_profile": "The path to your Firefox profile (used to log in to Twitter)",
  "headless": true,
  "llm": "The Large Language Model you want to use to generate the tweet.",
  "threads": 4
}
```

## Roadmap

Here are some features that are planned for the future:

- [ ] Scrape more information about the product, to be able to create a more detailed pitch.
- [ ] Join online communities related to the product, and post a pitch (with a link to the product) there.
- [ ] Reply to tweets that are related to the product, with a pitch for the product.
