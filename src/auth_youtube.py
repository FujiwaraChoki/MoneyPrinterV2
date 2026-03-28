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

# Add src/ to path (same as main.py)
sys.path.insert(0, os.path.dirname(__file__))

from config import get_google_api_credentials_path
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
