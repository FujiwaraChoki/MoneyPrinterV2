# Post Bridge Integration

MoneyPrinter V2 can hand off a generated Short to [Post Bridge](https://api.post-bridge.com/reference) after render time. In the current repo there are two supported patterns:

1. Standard YouTube browser upload first, then Post Bridge cross-posts to other platforms.
2. Post Bridge becomes the primary publisher, including YouTube, when `youtube` is present in `post_bridge.platforms`.

## Basic Setup

1. Create a Post Bridge account.
2. Connect the social accounts you want to publish to.
3. Create an API key.
4. Add a `post_bridge` block to `config.json`, or export `POST_BRIDGE_API_KEY`.

### Cross-post after the normal YouTube upload

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

### Let Post Bridge publish YouTube too

```json
{
  "post_bridge": {
    "enabled": true,
    "api_key": "pb_your_api_key_here",
    "platforms": ["youtube", "tiktok", "instagram"],
    "account_ids": [],
    "auto_crosspost": false
  }
}
```

## Configuration Semantics

| Key | Description |
| --- | --- |
| `enabled` | Turns the integration on. |
| `api_key` | Post Bridge API key. Falls back to `POST_BRIDGE_API_KEY`. |
| `platforms` | Ordered list of target platforms. Include `youtube` if you want Post Bridge to handle the primary publish step. |
| `account_ids` | Optional exact Post Bridge account IDs. Keep the order aligned with `platforms`. |
| `auto_crosspost` | When `true`, cron and interactive runs skip the extra confirmation prompt. |

## Interactive Behavior

### When `youtube` is not in `platforms`

- MoneyPrinter V2 uploads the Short through the Firefox-driven YouTube flow.
- After a successful upload, it can offer to cross-post the same asset through Post Bridge.

### When `youtube` is in `platforms`

- The publish prompt changes from YouTube-only language to all configured platforms.
- Post Bridge handles the publish step for YouTube and any other configured platforms in one go.

### Account selection

- If `account_ids` is configured, those IDs are used directly.
- If not, MoneyPrinter V2 asks Post Bridge for connected accounts on the requested platforms.
- If there is exactly one account for a platform, it is selected automatically.
- If there are multiple accounts for a platform, the CLI prompts you to choose one.
- After interactive selection, the chosen IDs are printed so you can paste them back into `config.json`.

## Cron Behavior

- Cron only uses Post Bridge automatically when `auto_crosspost` is `true`.
- If prompts would be required in a non-interactive cron run, the publish is skipped instead of hanging.
- Cron log files are stored in `.mp/cron-youtube-<account-id>.log`.

## Current Payload Behavior

- The generated Short title becomes the base caption.
- TikTok receives a platform-specific title override.
- When `youtube` is included, the generated description is also passed through as a YouTube caption override.
- Re-runs avoid reposting platforms that are already marked successful in the local cache.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| Prompt never appears | Verify `post_bridge.enabled` is `true` and a valid API key is present. |
| Cron skips publishing | Set `auto_crosspost` to `true`, and configure `account_ids` if multiple accounts exist. |
| No accounts are found | Confirm the accounts are connected in Post Bridge and match the requested `platforms`. |
| YouTube is still using the browser upload path | Add `youtube` to `post_bridge.platforms`. |
