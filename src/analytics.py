import os
import json

from config import ROOT_DIR, get_google_api_credentials_path
from cost_tracker import _read_analytics, _write_analytics
from status import error, info, success, warning


SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_PATH = os.path.join(ROOT_DIR, ".mp", "google_token.json")


def _get_youtube_service():
    """Build and return an authenticated YouTube Data API v3 service.

    Uses OAuth 2.0 installed-app flow. On first run, opens a local
    server for the OAuth consent flow (headless-friendly: prints URL).
    Subsequent calls use the cached token.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None

    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            warning(f"Token file corrupted, re-authenticating: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                warning(f"Token refresh failed, re-authenticating: {e}")
                creds = None

        if not creds or not creds.valid:
            credentials_path = get_google_api_credentials_path()
            if not credentials_path or not os.path.exists(credentials_path):
                error(
                    "Google API credentials not configured. Set google_api_credentials_path in config.json."
                )
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=False)
            except (ValueError, OSError) as e:
                error(f"OAuth flow failed: {e}")
                return None

        try:
            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
            os.chmod(TOKEN_PATH, 0o600)
        except OSError as e:
            warning(f"Failed to save token file: {e}")

    try:
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        error(f"Failed to build YouTube service: {e}")
        return None


def fetch_metrics_for_video(video_id: str) -> dict | None:
    """Fetch current metrics for a single video from YouTube Data API.

    Returns:
        dict with keys: views, likes, comments, fetched_at
        None if the API call fails.
    """
    from datetime import datetime

    service = _get_youtube_service()
    if service is None:
        return None

    try:
        response = (
            service.videos()
            .list(
                part="statistics",
                id=video_id,
            )
            .execute()
        )

        items = response.get("items", [])
        if not items:
            warning(f"No video found for ID: {video_id}")
            return None

        stats = items[0]["statistics"]
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        error(f"Failed to fetch metrics for {video_id}: {e}")
        return None


def fetch_all_metrics(analytics_path: str | None = None) -> int:
    """Fetch metrics for all tracked videos and append to metrics_history.

    Returns:
        count of successfully updated videos.
    """
    data = _read_analytics(analytics_path)
    updated = 0

    for video in data["videos"]:
        video_id = video["video_id"]
        info(f"Fetching metrics for: {video.get('title', video_id)}")
        metrics = fetch_metrics_for_video(video_id)

        if metrics is not None:
            video["metrics_history"].append(metrics)
            updated += 1
            success(
                f"  views={metrics['views']}, likes={metrics['likes']}, comments={metrics['comments']}"
            )

    _write_analytics(data, analytics_path)
    return updated
