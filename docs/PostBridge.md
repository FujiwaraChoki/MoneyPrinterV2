# Post Bridge Video Publishing

MoneyPrinterV2 now uses [Post Bridge](https://api.post-bridge.com/reference) as the primary backend for publishing generated videos.

## What Post Bridge Does

In the current flow, MoneyPrinterV2 still generates the video locally, but Post Bridge handles publishing:

1. Fetch the connected social accounts that should receive the video.
2. Request a signed upload URL for the generated media.
3. Upload the local video asset to Post Bridge storage.
4. Create a post for the selected platform accounts.
5. Expose publish history and per-platform URLs through the Post Bridge API.

This replaces the old browser-driven YouTube upload path for normal usage.

## Setup

1. Create a Post Bridge account.
2. Connect the social accounts you want to publish to.
3. Generate an API key from Post Bridge.
4. Run the in-app publisher setup wizard, or configure `video_publishing` and `post_bridge` manually in `config.json`.

```json
{
  "video_publishing": {
    "profile_name": "Default Publisher",
    "niche": "finance",
    "language": "English"
  },
  "post_bridge": {
    "enabled": true,
    "api_key": "pb_your_api_key_here",
    "platforms": ["youtube", "tiktok", "instagram"],
    "account_ids": [101, 202, 303],
    "auto_publish": false
  }
}
```

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `video_publishing.profile_name` | `string` | `"Default Publisher"` | Friendly label shown in the CLI wizard. |
| `video_publishing.niche` | `string` | `""` | Topic or niche used for generated videos. |
| `video_publishing.language` | `string` | `"English"` | Language used for generated videos. |
| `post_bridge.enabled` | `boolean` | `false` | Enables Post Bridge publishing. |
| `post_bridge.api_key` | `string` | `""` | Post Bridge API key. Falls back to `POST_BRIDGE_API_KEY` when blank. |
| `post_bridge.platforms` | `string[]` | `["youtube", "tiktok", "instagram"]` when omitted | Platforms targeted for publishing. |
| `post_bridge.account_ids` | `number[]` | `[]` | Exact Post Bridge account IDs to publish to. The setup wizard stores one account per selected platform. |
| `post_bridge.auto_publish` | `boolean` | `false` | Automatically publish after generation. Interactive runs prompt when disabled; cron runs skip. |

## Publish Flow

### Interactive publishing

- Use the `Video Publishing` menu in `src/main.py`.
- `Setup Publisher` runs the config-writing wizard.
- `Publish Video` generates a video locally and publishes it through Post Bridge.
- `Show Recent Publishes` fetches recent posts and post results live from the API.

### Scheduled publishing

- Cron now uses `publish` mode instead of `youtube`.
- `scripts/publish_video.sh` runs the publish cron entrypoint directly.
- If `post_bridge.auto_publish` is `false`, cron skips publishing and logs why.

## Content Mapping

- Global caption: generated description
- `youtube.title`: generated title
- `youtube.caption`: generated description
- `tiktok.title`: generated title

Only configured platform overrides are sent.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| The publisher wizard cannot continue | Verify `video_publishing.niche` and a Post Bridge API key are set. |
| No accounts are found | Make sure the accounts are connected in Post Bridge and that `post_bridge.platforms` matches the connected accounts. |
| Cron skips publishing | Set `post_bridge.auto_publish` to `true`. |
| Publish history is empty | Confirm that posts exist for the configured platforms and that the API key has access. |
| Old cron commands stopped working | Use `publish` mode instead of `youtube`. |
