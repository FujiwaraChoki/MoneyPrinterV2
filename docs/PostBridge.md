# Post Bridge Integration

Cross-post your generated YouTube Shorts to **TikTok** and **Instagram Reels** automatically using [Post Bridge](https://postbridge.app).

## Why Post Bridge?

- **No OAuth tokens to manage** — Post Bridge handles all platform auth for you.
- **One API call** to post to TikTok and Instagram simultaneously.
- **Scheduling support** — schedule posts or use auto-queue for optimal timing.

## Setup

1. **Create a Post Bridge account** at [postbridge.app](https://postbridge.app).
2. **Connect your TikTok and Instagram accounts** in the Post Bridge dashboard.
3. **Generate an API key** from Settings > API Keys.
4. **Add the config** to your `config.json`:

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

| Key              | Type     | Default                    | Description                                                                                                  |
| ---------------- | -------- | -------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `enabled`        | boolean  | `false`                    | Enable/disable the Post Bridge integration.                                                                  |
| `api_key`        | string   | `""`                       | Your Post Bridge API key.                                                                                    |
| `platforms`      | string[] | `["tiktok", "instagram"]`  | Platforms to cross-post to.                                                                                  |
| `account_ids`    | number[] | `[]`                       | Specific account IDs to post to. If empty, you'll be prompted to choose when multiple accounts are connected.|
| `auto_crosspost` | boolean  | `false`                    | Skip the confirmation prompt and always cross-post after YouTube upload.                                     |

### Account IDs

If you have multiple TikTok or Instagram accounts connected to Post Bridge, you'll be prompted to pick which one to use on the first run. The output will show the account IDs so you can add them to `account_ids` in your config to skip the prompt next time:

```json
"account_ids": [12, 34]
```

## How It Works

1. After your YouTube Shorts video is uploaded, MoneyPrinterV2 prompts:
   ```
   Cross-post to tiktok, instagram via Post Bridge?
   Yes/No:
   ```
2. If you have multiple accounts per platform and no `account_ids` configured, you'll be asked to pick:
   ```
   Multiple tiktok accounts found:
     1. @mybrand (ID: 12)
     2. @personal (ID: 34)
   Select tiktok account (1-2):
   ```
3. If you confirm (or `auto_crosspost` is `true`):
   - The video is uploaded to Post Bridge.
   - A post is created on your selected TikTok and Instagram accounts.
   - The video title is automatically set on TikTok.
4. Post Bridge handles all platform APIs, rate limits, and format requirements.

## API Reference

Full API documentation: [api.post-bridge.com/reference](https://api.post-bridge.com/reference)

### Endpoints Used

| Method | Endpoint                      | Purpose                 |
| ------ | ----------------------------- | ----------------------- |
| GET    | `/v1/social-accounts`         | List connected accounts |
| POST   | `/v1/media/create-upload-url` | Get signed upload URL   |
| PUT    | `{upload_url}`                | Upload video file       |
| POST   | `/v1/posts`                   | Create and publish post |

## Troubleshooting

| Issue                         | Solution                                                          |
| ----------------------------- | ----------------------------------------------------------------- |
| "API key is missing"          | Add your `api_key` to the `post_bridge` config block.             |
| "No connected accounts"       | Connect TikTok/Instagram in the Post Bridge dashboard first.      |
| "Failed to upload media"      | Check the video file exists and is under the platform size limit.  |
| Cross-post fails but YT works | Post Bridge errors don't affect the YouTube upload.               |
