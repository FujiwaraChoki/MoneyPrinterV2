# Upload-Post Integration

Cross-post your YouTube Shorts to TikTok and Instagram automatically using [Upload-Post](https://upload-post.com).

## What is Upload-Post?

Upload-Post is an API that allows you to upload videos and images to multiple social media platforms (TikTok, Instagram, YouTube, LinkedIn, Pinterest, etc.) with a single API call.

- **Website:** https://upload-post.com
- **API Docs:** https://docs.upload-post.com
- **Free tier available**

## Setup

1. Create an account at [upload-post.com](https://upload-post.com)
2. Connect your TikTok and/or Instagram accounts
3. Get your API key from the dashboard
4. Add the configuration to your `config.json`:

```json
{
  "upload_post": {
    "enabled": true,
    "api_key": "your-api-key-here",
    "username": "your-username",
    "platforms": ["tiktok", "instagram"],
    "auto_crosspost": false
  }
}
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable/disable Upload-Post integration |
| `api_key` | string | `""` | Your Upload-Post API key |
| `username` | string | `""` | Your Upload-Post username |
| `platforms` | array | `["tiktok", "instagram"]` | Platforms to cross-post to |
| `auto_crosspost` | bool | `false` | Automatically cross-post without asking |

## Usage

After uploading a video to YouTube, MPV2 will ask:

```
📱 Cross-post to TikTok/Instagram via Upload-Post?
Yes/No: 
```

If you select "Yes", the video will be uploaded to the configured platforms.

If `auto_crosspost` is set to `true`, it will automatically cross-post without asking.

## Supported Platforms

Upload-Post supports:
- TikTok
- Instagram (Reels)
- YouTube Shorts
- LinkedIn
- Pinterest
- Twitter/X
- Facebook

For this integration, we focus on TikTok and Instagram since YouTube is already handled by MPV2.

## Troubleshooting

### "API key or username is missing"
Make sure you've added both `api_key` and `username` to your config.json.

### "Upload failed"
- Check that your Upload-Post account has the platforms connected
- Verify your API key is correct
- Check the Upload-Post dashboard for any account issues

## Links

- [Upload-Post Website](https://upload-post.com)
- [API Documentation](https://docs.upload-post.com)
- [Pricing](https://upload-post.com/pricing)
