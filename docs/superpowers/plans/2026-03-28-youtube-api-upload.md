# YouTube Data API v3 Upload — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Selenium-based YouTube upload with YouTube Data API v3 for stable headless operation.

**Architecture:** New `youtube_auth.py` module handles OAuth 2.0 (token persistence + refresh). `YouTube.upload_video()` uses the authenticated API client for resumable upload. All Selenium/Firefox code is removed from YouTube.py. Other Selenium-using classes (Twitter, AFM, Outreach) are untouched.

**Tech Stack:** `google-api-python-client`, `google-auth-oauthlib`, YouTube Data API v3

**Spec:** `docs/superpowers/specs/2026-03-28-youtube-api-upload-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/youtube_auth.py` | Create | OAuth 2.0: load/refresh credentials, build YouTube API service |
| `src/auth_youtube.py` | Create | CLI script for initial OAuth consent (one-time setup) |
| `src/config.py` | Modify | Add `get_upload_visibility()` getter |
| `config.example.json` | Modify | Add `"upload_visibility": "unlisted"` |
| `src/classes/YouTube.py` | Modify | Remove Selenium, rewrite `__init__`, `upload_video()`, `get_channel_id()` |
| `src/constants.py` | Modify | Remove YouTube DOM selector constants |
| `src/main.py` | Modify | Remove `firefox_profile` from YouTube account flow |
| `tests/test_youtube_auth.py` | Create | Unit tests for OAuth helper |
| `tests/test_youtube_upload.py` | Create | Unit tests for API upload |

---

### Task 1: Add `get_upload_visibility()` config getter

**Files:**
- Modify: `src/config.py:383-403` (append after last function)
- Modify: `config.example.json`

- [ ] **Step 1: Add getter to config.py**

Append to `src/config.py`:

```python
def get_upload_visibility() -> str:
    """
    Gets the YouTube upload visibility setting.

    Returns:
        visibility (str): "unlisted", "public", or "private"
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("upload_visibility", "unlisted")
```

- [ ] **Step 2: Add field to config.example.json**

Add `"upload_visibility": "unlisted"` after the `"gemini_cost_per_call"` line in `config.example.json`.

- [ ] **Step 3: Commit**

```bash
git add src/config.py config.example.json
git commit -m "feat: add upload_visibility config getter"
```

---

### Task 2: Create OAuth helper module with tests

**Files:**
- Create: `src/youtube_auth.py`
- Create: `tests/test_youtube_auth.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_youtube_auth.py`:

```python
import json
import os
import pytest
from unittest.mock import patch, MagicMock


def test_get_token_path_returns_mp_directory():
    """Token file should live in .mp/ directory."""
    with patch("youtube_auth.ROOT_DIR", "/fake/root"):
        from youtube_auth import get_token_path
        # Re-import to pick up patched ROOT_DIR
        import youtube_auth
        youtube_auth.ROOT_DIR = "/fake/root"
        result = youtube_auth.get_token_path()
        assert result == "/fake/root/.mp/youtube_oauth_token.json"


def test_load_credentials_raises_when_no_token_file(tmp_path):
    """Should raise FileNotFoundError when token file doesn't exist."""
    import youtube_auth
    youtube_auth.ROOT_DIR = str(tmp_path)
    os.makedirs(tmp_path / ".mp", exist_ok=True)

    with pytest.raises(FileNotFoundError, match="Run.*auth_youtube.py"):
        youtube_auth.load_credentials()


def test_load_credentials_returns_credentials_from_token_file(tmp_path):
    """Should load and return credentials from saved token file."""
    import youtube_auth
    youtube_auth.ROOT_DIR = str(tmp_path)
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    token_data = {
        "token": "fake-access-token",
        "refresh_token": "fake-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    }
    (mp_dir / "youtube_oauth_token.json").write_text(json.dumps(token_data))

    with patch("youtube_auth.Credentials") as MockCreds:
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = True
        MockCreds.from_authorized_user_info.return_value = mock_creds_instance

        creds = youtube_auth.load_credentials()
        assert creds == mock_creds_instance
        MockCreds.from_authorized_user_info.assert_called_once()


def test_load_credentials_refreshes_expired_token(tmp_path):
    """Should refresh credentials when token is expired but refresh token exists."""
    import youtube_auth
    youtube_auth.ROOT_DIR = str(tmp_path)
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    token_data = {
        "token": "expired-token",
        "refresh_token": "fake-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    }
    (mp_dir / "youtube_oauth_token.json").write_text(json.dumps(token_data))

    with patch("youtube_auth.Credentials") as MockCreds:
        mock_creds_instance = MagicMock()
        mock_creds_instance.valid = False
        mock_creds_instance.expired = True
        mock_creds_instance.refresh_token = "fake-refresh-token"
        mock_creds_instance.to_json.return_value = json.dumps(token_data)
        MockCreds.from_authorized_user_info.return_value = mock_creds_instance

        creds = youtube_auth.load_credentials()
        mock_creds_instance.refresh.assert_called_once()


def test_build_youtube_service_returns_service():
    """Should return a YouTube API service object."""
    import youtube_auth

    mock_creds = MagicMock()
    with patch("youtube_auth.build") as mock_build:
        mock_build.return_value = MagicMock()
        service = youtube_auth.build_youtube_service(mock_creds)
        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds)
        assert service is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/test_youtube_auth.py -v`
Expected: FAIL — `youtube_auth` module does not exist.

- [ ] **Step 3: Implement youtube_auth.py**

Create `src/youtube_auth.py`:

```python
import os
import json

from config import ROOT_DIR
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_token_path() -> str:
    """Returns path to the saved OAuth token file."""
    return os.path.join(ROOT_DIR, ".mp", "youtube_oauth_token.json")


def load_credentials() -> Credentials:
    """
    Loads OAuth credentials from the saved token file.
    Refreshes the token if expired.

    Returns:
        creds (Credentials): Valid Google OAuth credentials.

    Raises:
        FileNotFoundError: If token file does not exist (initial auth needed).
        RuntimeError: If token refresh fails.
    """
    token_path = get_token_path()

    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"YouTube OAuth token not found at {token_path}. "
            "Run `python src/auth_youtube.py` to authenticate."
        )

    with open(token_path, "r") as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError(
                "YouTube OAuth token is invalid and cannot be refreshed. "
                "Run `python src/auth_youtube.py` to re-authenticate."
            )

    return creds


def build_youtube_service(creds: Credentials):
    """
    Builds an authenticated YouTube Data API v3 service client.

    Args:
        creds (Credentials): Valid OAuth credentials.

    Returns:
        service: YouTube API service resource.
    """
    return build("youtube", "v3", credentials=creds)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/test_youtube_auth.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/youtube_auth.py tests/test_youtube_auth.py
git commit -m "feat: add YouTube OAuth helper module with tests"
```

---

### Task 3: Create initial auth CLI script

**Files:**
- Create: `src/auth_youtube.py`

- [ ] **Step 1: Create the auth script**

Create `src/auth_youtube.py`:

```python
"""
One-time OAuth setup for YouTube Data API v3.

Usage:
    1. SSH to the server with port forwarding:
       ssh -L 8080:localhost:8080 user@server

    2. Run this script:
       python src/auth_youtube.py

    3. Open the printed URL in your local browser.

    4. After consent, the token is saved to .mp/youtube_oauth_token.json
"""
import os
import sys
import json

# Add src/ to path (same as main.py)
sys.path.insert(0, os.path.dirname(__file__))

from config import ROOT_DIR, get_google_api_credentials_path
from youtube_auth import get_token_path, SCOPES

from google_auth_oauthlib.flow import InstalledAppFlow


def main():
    credentials_path = get_google_api_credentials_path()
    if not credentials_path or not os.path.exists(credentials_path):
        print(
            "ERROR: google_api_credentials_path is not set or file does not exist.\n"
            "Download OAuth client credentials from Google Cloud Console\n"
            "and set the path in config.json."
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

    print("=" * 60)
    print("YouTube OAuth Setup")
    print("=" * 60)
    print()
    print("Make sure you have SSH port forwarding active:")
    print("  ssh -L 8080:localhost:8080 user@server")
    print()
    print("A browser authorization URL will be printed below.")
    print("Open it in your local browser to complete authentication.")
    print()

    creds = flow.run_local_server(
        host="localhost",
        port=8080,
        open_browser=False,
        success_message="Authentication successful! You can close this tab.",
    )

    token_path = get_token_path()
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    print(f"\nToken saved to: {token_path}")
    print("YouTube upload is now ready to use.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add src/auth_youtube.py
git commit -m "feat: add YouTube OAuth initial setup CLI script"
```

---

### Task 4: Rewrite YouTube class (remove Selenium, add API upload)

**Files:**
- Modify: `src/classes/YouTube.py`
- Create: `tests/test_youtube_upload.py`

- [ ] **Step 1: Write failing tests for upload_video**

Create `tests/test_youtube_upload.py`:

```python
import json
import os
import pytest
from unittest.mock import patch, MagicMock, ANY


@pytest.fixture
def youtube_instance(tmp_path):
    """Create a YouTube instance with mocked dependencies."""
    # Set up minimal .mp directory
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    # Create a dummy video file
    video_path = mp_dir / "test_video.mp4"
    video_path.write_bytes(b"fake video content")

    # Create youtube cache
    cache_data = {
        "accounts": [
            {
                "id": "test-uuid",
                "nickname": "test",
                "niche": "tech",
                "language": "English",
                "videos": [],
            }
        ]
    }
    (mp_dir / "youtube.json").write_text(json.dumps(cache_data))

    with patch("classes.YouTube.ROOT_DIR", str(tmp_path)), \
         patch("classes.YouTube.get_imagemagick_path", return_value="/usr/bin/convert"):
        from classes.YouTube import YouTube

        yt = YouTube(
            account_uuid="test-uuid",
            account_nickname="test",
            niche="tech",
            language="English",
        )
        yt.video_path = str(video_path)
        yt.metadata = {"title": "Test Video", "description": "Test description"}
        yt._niche = "tech"
        return yt


def test_upload_video_calls_api_with_correct_params(youtube_instance):
    """upload_video should call videos().insert() with correct metadata."""
    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_service.videos.return_value.insert.return_value = mock_insert
    mock_insert.next_chunk.return_value = (
        None,
        {"id": "abc123"},
    )

    with patch("classes.YouTube.load_credentials") as mock_creds, \
         patch("classes.YouTube.build_youtube_service", return_value=mock_service), \
         patch("classes.YouTube.get_upload_visibility", return_value="unlisted"), \
         patch("classes.YouTube.finalize_video_analytics"), \
         patch("classes.YouTube._read_analytics", return_value={"pending_costs": []}), \
         patch("classes.YouTube._write_analytics"):
        mock_creds.return_value = MagicMock()

        result = youtube_instance.upload_video()

        assert result is True
        mock_service.videos.return_value.insert.assert_called_once()
        call_kwargs = mock_service.videos.return_value.insert.call_args
        body = call_kwargs[1]["body"]
        assert body["snippet"]["title"] == "Test Video"
        assert body["snippet"]["description"] == "Test description"
        assert body["status"]["privacyStatus"] == "unlisted"


def test_upload_video_returns_false_on_auth_error(youtube_instance):
    """upload_video should return False when authentication fails."""
    with patch("classes.YouTube.load_credentials", side_effect=FileNotFoundError("no token")):
        result = youtube_instance.upload_video()
        assert result is False


def test_upload_video_saves_video_to_cache(youtube_instance, tmp_path):
    """upload_video should add the video to the cache after successful upload."""
    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_service.videos.return_value.insert.return_value = mock_insert
    mock_insert.next_chunk.return_value = (
        None,
        {"id": "xyz789"},
    )

    with patch("classes.YouTube.load_credentials") as mock_creds, \
         patch("classes.YouTube.build_youtube_service", return_value=mock_service), \
         patch("classes.YouTube.get_upload_visibility", return_value="unlisted"), \
         patch("classes.YouTube.get_youtube_cache_path", return_value=str(tmp_path / ".mp" / "youtube.json")), \
         patch("classes.YouTube.finalize_video_analytics"), \
         patch("classes.YouTube._read_analytics", return_value={"pending_costs": []}), \
         patch("classes.YouTube._write_analytics"):
        mock_creds.return_value = MagicMock()

        youtube_instance.upload_video()

        cache_path = tmp_path / ".mp" / "youtube.json"
        cache_data = json.loads(cache_path.read_text())
        videos = cache_data["accounts"][0]["videos"]
        assert len(videos) == 1
        assert videos[0]["title"] == "Test Video"
        assert "xyz789" in videos[0]["url"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/test_youtube_upload.py -v`
Expected: FAIL — YouTube constructor still requires `fp_profile_path`.

- [ ] **Step 3: Rewrite YouTube.py**

Replace the imports section (lines 1-30) of `src/classes/YouTube.py` with:

```python
import re
import base64
import json
import time
import os
import requests
import assemblyai as aai

from utils import *
from cache import *
from .Tts import TTS
from llm_provider import generate_text
from config import *
from status import *
from uuid import uuid4
from constants import *
from typing import List
from moviepy.editor import *
from termcolor import colored
from moviepy.video.fx.all import crop
from moviepy.config import change_settings
from moviepy.video.tools.subtitles import SubtitlesClip
from datetime import datetime
from cost_tracker import record_image_cost, finalize_video as finalize_video_analytics
from youtube_auth import load_credentials, build_youtube_service
from googleapiclient.http import MediaFileUpload
```

Replace the `__init__` method (lines 51-102) with:

```python
    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        niche: str,
        language: str,
    ) -> None:
        self._account_uuid: str = account_uuid
        self._account_nickname: str = account_nickname
        self._niche: str = niche
        self._language: str = language

        self.images = []
        self._pending_video_id = str(uuid4())
```

Replace the `get_channel_id` method (lines 703-716) with:

```python
    def get_channel_id(self) -> str:
        """
        Gets the Channel ID using YouTube Data API.

        Returns:
            channel_id (str): The Channel ID.
        """
        creds = load_credentials()
        service = build_youtube_service(creds)
        response = service.channels().list(mine=True, part="id").execute()
        items = response.get("items", [])
        if not items:
            raise RuntimeError("No YouTube channel found for the authenticated account.")
        self.channel_id = items[0]["id"]
        return self.channel_id
```

Replace the `upload_video` method (lines 718-886) with:

```python
    def upload_video(self) -> bool:
        """
        Uploads the video to YouTube using the Data API v3.

        Returns:
            success (bool): Whether the upload was successful.
        """
        try:
            creds = load_credentials()
            service = build_youtube_service(creds)

            body = {
                "snippet": {
                    "title": self.metadata["title"],
                    "description": self.metadata["description"],
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": get_upload_visibility(),
                },
            }

            media = MediaFileUpload(
                self.video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=10 * 1024 * 1024,
            )

            request = service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            info("Uploading video to YouTube...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    info(f"Upload progress: {int(status.progress() * 100)}%")

            video_id = response["id"]
            url = build_url(video_id)

            success(f"Uploaded Video: {url}")

            # Add video to cache
            self.add_video(
                {
                    "title": self.metadata["title"],
                    "description": self.metadata["description"],
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            # Update pending cost entry with real YouTube video_id
            from cost_tracker import _read_analytics, _write_analytics

            analytics_data = _read_analytics()
            for entry in analytics_data.get("pending_costs", []):
                if entry["video_id"] == self._pending_video_id:
                    entry["video_id"] = video_id
                    break
            _write_analytics(analytics_data)

            # Record analytics data
            finalize_video_analytics(
                video_id=video_id,
                title=self.metadata["title"],
                niche=self._niche,
                upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            return True
        except FileNotFoundError as e:
            error(str(e))
            return False
        except Exception as e:
            error(f"Upload failed: {e}")
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/test_youtube_upload.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/classes/YouTube.py tests/test_youtube_upload.py
git commit -m "feat: replace Selenium upload with YouTube Data API v3"
```

---

### Task 5: Clean up constants.py and main.py

**Files:**
- Modify: `src/constants.py`
- Modify: `src/main.py:69-98` and `src/main.py:155-164`

- [ ] **Step 1: Remove YouTube DOM selectors from constants.py**

Remove these lines (27-33) from `src/constants.py`:

```python
# YouTube Section
YOUTUBE_TEXTBOX_ID = "textbox"
YOUTUBE_MADE_FOR_KIDS_NAME = "VIDEO_MADE_FOR_KIDS_MFK"
YOUTUBE_NOT_MADE_FOR_KIDS_NAME = "VIDEO_MADE_FOR_KIDS_NOT_MFK"
YOUTUBE_NEXT_BUTTON_ID = "next-button"
YOUTUBE_RADIO_BUTTON_XPATH = '//*[@id="radioLabel"]'
YOUTUBE_DONE_BUTTON_ID = "done-button"
```

- [ ] **Step 2: Update YouTube account creation in main.py**

In `src/main.py`, the YouTube account creation block (around line 78-96) currently asks for `firefox_profile`. Remove that prompt and the field from `account_data`:

Replace the account creation block with:

```python
            if user_input.lower() == "yes":
                generated_uuid = str(uuid4())

                success(f" => Generated ID: {generated_uuid}")
                nickname = question(" => Enter a nickname for this account: ")
                niche = question(" => Enter the account niche: ")
                language = question(" => Enter the account language: ")

                account_data = {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "niche": niche,
                    "language": language,
                    "videos": [],
                }

                add_account("youtube", account_data)

                success("Account configured successfully!")
```

- [ ] **Step 3: Update YouTube constructor call in main.py**

In `src/main.py` (around line 158-164), update the YouTube instantiation to remove `firefox_profile`:

```python
                youtube = YouTube(
                    selected_account["id"],
                    selected_account["nickname"],
                    selected_account["niche"],
                    selected_account["language"],
                )
```

- [ ] **Step 4: Run all tests**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/constants.py src/main.py
git commit -m "refactor: remove Selenium artifacts from constants and main"
```

---

### Task 6: Update cron.py for new YouTube constructor

**Files:**
- Modify: `src/cron.py`

- [ ] **Step 1: Update YouTube instantiation in cron.py**

In `src/cron.py` lines 74-80, the YouTube constructor currently passes 5 arguments including `acc["firefox_profile"]`. Replace with:

```python
                youtube = YouTube(
                    acc["id"],
                    acc["nickname"],
                    acc["niche"],
                    acc["language"]
                )
```

- [ ] **Step 2: Run all tests**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/cron.py
git commit -m "refactor: update cron.py for new YouTube constructor"
```

---

### Task 7: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 2: Verify no Selenium references remain in YouTube.py**

Run: `grep -n "selenium\|webdriver\|firefox\|Firefox\|GeckoDriver" src/classes/YouTube.py`
Expected: No output (no matches).

- [ ] **Step 3: Verify YouTube DOM constants are removed**

Run: `grep -n "YOUTUBE_TEXTBOX\|YOUTUBE_MADE_FOR\|YOUTUBE_NEXT\|YOUTUBE_RADIO\|YOUTUBE_DONE" src/constants.py`
Expected: No output (no matches).

- [ ] **Step 4: Verify imports resolve**

Run: `cd /home/server160/refs/MoneyPrinterV2 && venv/bin/python -c "import sys; sys.path.insert(0, 'src'); from classes.YouTube import YouTube; print('OK')"`
Expected: `OK`
