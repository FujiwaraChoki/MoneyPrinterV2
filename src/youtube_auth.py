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
