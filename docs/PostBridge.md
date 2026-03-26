# Post Bridge Integration

MoneyPrinterV2 can optionally hand off a successfully uploaded YouTube Short to [Post Bridge](https://api.post-bridge.com/reference), which then publishes the same asset to connected TikTok and Instagram accounts.

## What Post Bridge Does

Post Bridge is a publishing API for social platforms. In this integration, MoneyPrinterV2 uses it to:

1. Look up your connected social accounts.
2. Request a signed upload URL for the generated video.
3. Upload the video asset to Post Bridge storage.
4. Create a post for the selected TikTok and Instagram accounts.

MoneyPrinterV2 still owns video generation and the initial YouTube upload. Post Bridge only starts after YouTube upload succeeds.

## Setup

1. Create a Post Bridge account.
2. Connect the TikTok and Instagram accounts you want to publish to.
3. Generate an API key from Post Bridge.
4. Add the `post_bridge` block to `config.json`, or set `POST_BRIDGE_API_KEY` in your environment.

```json
{
  "post_bridge": {
    "enabled": true,
    "api_key": "pb_your_api_key_here",
    "platforms": ["tiktok", "instagram"],
    "account_ids": [],
    "auto_crosspost": false
  }
}
```

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `boolean` | `false` | Enables the Post Bridge integration. |
| `api_key` | `string` | `""` | Post Bridge API key. Falls back to `POST_BRIDGE_API_KEY` when blank. |
| `platforms` | `string[]` | `["tiktok", "instagram"]` when omitted | Platform filters used when looking up connected accounts. Unsupported values inside the list are ignored. |
| `account_ids` | `number[]` | `[]` | Exact Post Bridge account IDs to post to. When provided, MoneyPrinterV2 uses these directly and skips account lookup. |
| `auto_crosspost` | `boolean` | `false` | Automatically cross-post after a successful YouTube upload. |

## How The Integration Works

### Interactive YouTube flow

- If `enabled` is `false`, nothing happens.
- If `enabled` is `true` and `auto_crosspost` is `false`, MoneyPrinterV2 asks whether to cross-post after a successful YouTube upload.
- If `account_ids` is configured, those IDs are used directly.
- If `account_ids` is empty, MoneyPrinterV2 fetches connected Post Bridge accounts for the configured platforms.
- If there is exactly one connected account for a platform, it is selected automatically.
- If there are multiple connected accounts for a platform, MoneyPrinterV2 prompts you to choose one.
- After interactive selection, the chosen IDs are printed so you can copy them into `config.json`, but the app does not edit your config file for you.

### Cron / scheduled uploads

- Cron uses the same integration after a successful YouTube upload.
- If `auto_crosspost` is `false`, cron skips Post Bridge and logs why.
- If `auto_crosspost` is `true`, cron cross-posts automatically.
- If `account_ids` is empty and multiple connected accounts exist for a platform, cron skips cross-posting instead of hanging on an interactive prompt.

## Current v1 Behavior

- The generated YouTube title is used as the default caption.
- TikTok receives the YouTube title as its platform-specific `title` override.
- Post Bridge account lookup follows the API’s pagination.
- Instagram cover-image customization is intentionally not included in this v1 integration.
- Cross-posting only runs after `upload_video()` returns success.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| Cross-post prompt never appears | Verify `post_bridge.enabled` is `true`. |
| Cross-post is skipped in cron | Set `auto_crosspost` to `true`. |
| No accounts are found | Make sure the accounts are connected in Post Bridge and that `platforms` matches the accounts you connected. |
| Cron skips because multiple accounts exist | Add the desired `account_ids` to `config.json` so cron does not need to prompt. |
| API key seems ignored | Set `post_bridge.api_key`, or leave it blank and export `POST_BRIDGE_API_KEY`. |
