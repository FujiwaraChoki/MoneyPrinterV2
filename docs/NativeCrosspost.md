# Native Instagram & TikTok Cross-posting

MPV2 can cross-post generated YouTube Shorts directly to **Instagram Reels** and **TikTok** using their official APIs — no paid third-party service required.

This is an alternative to the existing [Post Bridge](PostBridge.md) integration. Both can be used simultaneously.

## Instagram Setup

### Prerequisites

1. An **Instagram Business** or **Creator** account
2. That account linked to a **Facebook Page**
3. A **Meta Developer account** at [developers.facebook.com](https://developers.facebook.com)

### Getting your credentials

1. Go to [Meta App Dashboard](https://developers.facebook.com/apps/) and create an app
2. Add the **Instagram API** product with **Instagram login**
3. Generate a **User Access Token** with the `instagram_content_publish` and `instagram_business_basic` permissions
4. Find your **Instagram Business Account ID** via the Graph API Explorer:
   ```
   GET /me/accounts → pick your Page → GET /{page-id}?fields=instagram_business_account
   ```
5. Exchange your short-lived token for a **long-lived token** (60-day expiry)

### Configuration

In `config.json`:

```json
{
  "instagram": {
    "enabled": true,
    "access_token": "YOUR_LONG_LIVED_TOKEN",
    "account_id": "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID",
    "auto_crosspost": false
  }
}
```

Or via environment variables:
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`

**Note:** Instagram requires that the video file is accessible via a **public URL**. If your videos are generated on a local machine or private server, you'll need to host them somewhere publicly accessible (e.g., a VPS with a simple HTTP server, or an S3/R2 bucket).

### Limitations

- Only **JPEG** images are supported for image posts
- Rate limit: **100 API-published posts per 24 hours**
- Access tokens expire after 60 days and must be refreshed

---

## TikTok Setup

### Prerequisites

1. A **TikTok account**
2. A registered app at [developers.tiktok.com](https://developers.tiktok.com)
3. The **Content Posting API** product added to your app
4. Approval for the `video.publish` scope

### Important: The Audit Requirement

TikTok requires your app to **pass an audit** before posts are publicly visible. Until then, all posts are created with `SELF_ONLY` visibility (only you can see them).

The audit checks that your integration meets TikTok's UX guidelines. MPV2 will warn you if your posts are being published as `SELF_ONLY`.

### Getting your access token

1. Register your app at [TikTok Developer Portal](https://developers.tiktok.com)
2. Add the **Content Posting API** product
3. Complete the OAuth flow to get a **user access token** with `video.publish` scope
4. (Optional) Submit your app for audit to enable public posting

### Configuration

In `config.json`:

```json
{
  "tiktok": {
    "enabled": true,
    "client_key": "YOUR_CLIENT_KEY",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN",
    "auto_crosspost": false
  }
}
```

Or via environment variables:
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`
- `TIKTOK_ACCESS_TOKEN`

### Limitations

- Rate limit: **6 requests per minute** per user
- Video uploads are direct file uploads (no public URL needed, unlike Instagram)
- Public visibility requires passing TikTok's app audit

---

## Usage

### Interactive mode

When you upload a YouTube Short, MPV2 will ask if you want to cross-post:

```
Cross-post this video to Instagram as a Reel? (Yes/No): yes
Cross-post this video to TikTok? (Yes/No): yes
```

### Auto cross-post (CRON mode)

Set `auto_crosspost` to `true` for either platform in `config.json`. When running via CRON jobs, the video will be automatically cross-posted after a successful YouTube upload.

### Using alongside Post Bridge

Native cross-posting and Post Bridge can coexist. MPV2 will run Post Bridge first (if enabled), then native cross-posting. You can use one for Instagram and the other for TikTok, or any combination.
