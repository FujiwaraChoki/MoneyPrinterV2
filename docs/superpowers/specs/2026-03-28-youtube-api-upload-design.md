# YouTube Data API v3 Upload — Design Spec

**Date**: 2026-03-28
**Status**: Approved

## Purpose

Replace the fragile Selenium-based YouTube upload with YouTube Data API v3 for stable, headless-compatible automated video uploads.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Upload method | YouTube Data API v3 | Stable, no browser dependency, headless-friendly |
| Initial visibility | Unlisted (hardcoded) | Safe default; config-based switching planned for later |
| Selenium code | Remove entirely from YouTube.py | No reason to maintain dead code |
| OAuth flow | Local redirect + SSH port forward | OOB is deprecated by Google; service accounts unsuitable for YouTube uploads |
| Video generation | No changes | LLM → image → TTS → MoviePy pipeline is stable and unrelated |

## Scope

### In Scope

- Remove Selenium/Firefox initialization from `YouTube.__init__()`
- Replace `upload_video()` with YouTube Data API v3 resumable upload
- Replace `get_channel_id()` with API-based retrieval
- Create OAuth 2.0 auth helper module and initial auth script
- Add `upload_visibility` config getter (defaulting to "unlisted")
- Remove YouTube DOM selector constants from `constants.py`
- Add `google-auth-oauthlib` to requirements.txt

### Out of Scope

- `generate_video()` pipeline (LLM, image gen, TTS, MoviePy)
- Other Selenium-based classes (Twitter, AFM, Outreach)
- Analytics / cost_tracker integration (existing calls preserved as-is)
- Public/private visibility switching (future work)

## Architecture

### Authentication

```
Initial setup (one-time):
  python src/auth_youtube.py
    → Prints authorization URL
    → User opens URL via SSH port forward (ssh -L 8080:localhost:8080)
    → User consents in browser → redirect to localhost:8080
    → Token saved to .mp/youtube_oauth_token.json

Runtime (automatic):
  upload_video()
    → Reads .mp/youtube_oauth_token.json
    → Uses refresh token to obtain access token
    → If refresh fails → raises error with instructions to re-run auth_youtube.py
```

- **Token file**: `.mp/youtube_oauth_token.json`
- **Credentials file**: Path from `config.json` → `google_api_credentials_path` (existing field)
- **Required OAuth scope**: `https://www.googleapis.com/auth/youtube.upload`

### Upload Flow

```
upload_video()
  1. Load OAuth credentials (token file + refresh)
  2. Build YouTube API service client
  3. Call videos.insert() with resumable upload:
     - snippet.title = self.metadata["title"]
     - snippet.description = self.metadata["description"]
     - snippet.categoryId = "22" (People & Blogs)
     - status.privacyStatus = "unlisted"
     - media_body = self.video_path (MP4)
  4. Execute resumable upload with retry on transient errors
  5. Extract video_id from API response
  6. Update cache (add_video) and cost_tracker (finalize_video_analytics)
  7. Return True on success, raise on failure
```

### Error Handling

- Token file missing → raise with message: "Run `python src/auth_youtube.py` first"
- Token refresh failure → raise with message: "Token expired. Re-run `python src/auth_youtube.py`"
- Upload API error (quota, network) → raise with details from API response
- No bare `except:` — all errors propagated with context

### File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/youtube_auth.py` | **New** | OAuth 2.0 helper: `get_authenticated_service()`, `load_credentials()` |
| `src/auth_youtube.py` | **New** | CLI script for initial OAuth consent flow |
| `src/classes/YouTube.py` | **Modify** | Remove Selenium from `__init__`, rewrite `upload_video()` and `get_channel_id()` |
| `src/config.py` | **Modify** | Add `get_upload_visibility()` |
| `src/constants.py` | **Modify** | Remove `YOUTUBE_TEXTBOX_ID`, `YOUTUBE_MADE_FOR_KIDS_NAME`, `YOUTUBE_NOT_MADE_FOR_KIDS_NAME`, `YOUTUBE_NEXT_BUTTON_ID`, `YOUTUBE_RADIO_BUTTON_XPATH`, `YOUTUBE_DONE_BUTTON_ID` |
| `config.example.json` | **Modify** | Add `"upload_visibility": "unlisted"` |
| `requirements.txt` | **Modify** | Add `google-auth-oauthlib` |

### Removed Code

From `YouTube.__init__()`:
- `self.options` (Firefox Options)
- `self.service` (GeckoDriverManager Service)
- `self.browser` (webdriver.Firefox)
- Firefox profile path validation and argument setting
- `get_headless()` usage

From `YouTube.py` imports:
- `selenium_firefox`, `selenium.webdriver`, `selenium.webdriver.common.by`, `selenium.webdriver.firefox.service`, `selenium.webdriver.firefox.options`, `webdriver_manager.firefox`

### Config

`config.example.json` additions:
```json
{
  "upload_visibility": "unlisted"
}
```

`google_api_credentials_path` already exists in config — reused for OAuth client credentials.

## Testing

- `youtube_auth.py`: Unit test `load_credentials()` with mocked token file
- `upload_video()`: Unit test with mocked YouTube API client (verify correct parameters passed)
- Manual integration test: Run full pipeline and verify video appears as unlisted on YouTube
