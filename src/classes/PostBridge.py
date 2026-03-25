import os
import requests

from utils import info, success, error, warning, question
from config import get_verbose


class PostBridge:
    """
    Class for cross-posting videos to TikTok and Instagram via Post Bridge API.

    Docs: https://api.post-bridge.com/reference
    """

    API_BASE = "https://api.post-bridge.com/v1"

    def __init__(self, api_key: str) -> None:
        """
        Constructor for PostBridge Class.

        Args:
            api_key (str): Post Bridge API key.

        Returns:
            None
        """
        self._api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_social_accounts(self, platforms: list = None) -> list:
        """
        Fetch connected social accounts, optionally filtered by platform.

        Args:
            platforms (list): Platform names to filter by
                (e.g. ["tiktok", "instagram"]).

        Returns:
            accounts (list): List of social account objects with id,
                platform, and username.
        """
        try:
            params = []
            if platforms:
                for p in platforms:
                    params.append(("platform", p))

            response = requests.get(
                f"{self.API_BASE}/social-accounts",
                headers=self._headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            accounts = data.get("data", data) if isinstance(data, dict) else data

            if get_verbose():
                info(f"Found {len(accounts)} connected account(s).")

            return accounts

        except requests.exceptions.RequestException as e:
            error(f"Failed to fetch social accounts: {str(e)}")
            return []

    def upload_media(self, file_path: str) -> str:
        """
        Upload a local media file to Post Bridge via signed URL.

        Args:
            file_path (str): Absolute path to the video/image file.

        Returns:
            media_id (str): The media ID to use when creating a post,
                or None on failure.
        """
        if not os.path.exists(file_path):
            error(f"File not found: {file_path}")
            return None

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        ext = os.path.splitext(file_name)[1].lower()
        mime_types = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        mime_type = mime_types.get(ext, "video/mp4")

        try:
            # Step 1: Get a signed upload URL from Post Bridge
            if get_verbose():
                info(f"Requesting upload URL for {file_name}...")

            url_response = requests.post(
                f"{self.API_BASE}/media/create-upload-url",
                headers=self._headers,
                json={
                    "name": file_name,
                    "mime_type": mime_type,
                    "size_bytes": file_size,
                },
                timeout=30,
            )
            url_response.raise_for_status()
            upload_data = url_response.json()

            media_id = upload_data.get("media_id") or upload_data.get("id")
            upload_url = upload_data.get("upload_url")

            if not media_id or not upload_url:
                error("Post Bridge did not return a valid upload URL.")
                return None

            # Step 2: PUT the file to the signed URL
            if get_verbose():
                size_mb = file_size / (1024 * 1024)
                info(f"Uploading {file_name} ({size_mb:.1f} MB)...")

            with open(file_path, "rb") as f:
                put_response = requests.put(
                    upload_url,
                    headers={"Content-Type": mime_type},
                    data=f,
                    timeout=600,
                )
                put_response.raise_for_status()

            success(f"Media uploaded successfully (ID: {media_id}).")
            return media_id

        except requests.exceptions.RequestException as e:
            error(f"Failed to upload media: {str(e)}")
            return None

    def create_post(
        self,
        caption: str,
        social_account_ids: list,
        media_ids: list = None,
        platform_configurations: dict = None,
        scheduled_at: str = None,
    ) -> dict:
        """
        Create a post on one or more social platforms via Post Bridge.

        Args:
            caption (str): The post caption / text content.
            social_account_ids (list): List of social account IDs to post to.
            media_ids (list): List of media IDs from upload_media().
            platform_configurations (dict): Optional per-platform overrides,
                e.g. {"tiktok": {"title": "..."}, "youtube": {"title": "..."}}.
            scheduled_at (str): ISO 8601 datetime to schedule the post.
                Omit to post immediately.

        Returns:
            result (dict): API response with post ID and status,
                or None on failure.
        """
        body = {
            "caption": caption,
            "social_accounts": social_account_ids,
        }

        if media_ids:
            body["media"] = media_ids
        if platform_configurations:
            body["platform_configurations"] = platform_configurations
        if scheduled_at:
            body["scheduled_at"] = scheduled_at

        try:
            if get_verbose():
                info(
                    f"Creating post on {len(social_account_ids)} account(s)..."
                )

            response = requests.post(
                f"{self.API_BASE}/posts",
                headers=self._headers,
                json=body,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            post_id = result.get("id", "unknown")
            status = result.get("status", "unknown")
            success(f"Post created (ID: {post_id}, status: {status}).")

            if result.get("warnings"):
                for w in result["warnings"]:
                    warning(f"Post Bridge warning: {w}")

            return result

        except requests.exceptions.RequestException as e:
            error(f"Failed to create post: {str(e)}")
            return None

    def resolve_account_ids(
        self,
        account_ids: list = None,
        platforms: list = None,
    ) -> list:
        """
        Resolve which account IDs to post to. One account per platform max.

        If account_ids are provided in config, use those directly.
        Otherwise, fetch accounts filtered by platform:
          - One account per platform: use it automatically.
          - Multiple per platform: prompt the user to pick one.
        Prints the selected IDs so the user can save them to config.

        Args:
            account_ids (list): Pre-configured account IDs (from config).
            platforms (list): Platform names to filter by.

        Returns:
            ids (list): List of account IDs (one per platform),
                or empty list on failure.
        """
        if account_ids:
            if get_verbose():
                info(f"Using configured account IDs: {account_ids}")
            return account_ids

        accounts = self.get_social_accounts(platforms)
        if not accounts:
            error("No connected social accounts found for the selected platforms.")
            return []

        # Group by platform — enforce one account per platform
        by_platform = {}
        for a in accounts:
            p = a.get("platform", "unknown")
            by_platform.setdefault(p, []).append(a)

        selected_ids = []
        for platform, platform_accounts in by_platform.items():
            if len(platform_accounts) == 1:
                acct = platform_accounts[0]
                info(f"  {platform}: @{acct.get('username', '?')}")
                selected_ids.append(acct["id"])
            else:
                info(f"\n  Multiple {platform} accounts found:")
                for i, acct in enumerate(platform_accounts, 1):
                    info(f"    {i}. @{acct.get('username', '?')} (ID: {acct['id']})")
                choice = question(f"  Select {platform} account (1-{len(platform_accounts)}): ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(platform_accounts):
                        selected_ids.append(platform_accounts[idx]["id"])
                        success(f"  Selected: @{platform_accounts[idx].get('username', '?')}")
                    else:
                        warning(f"  Invalid choice. Skipping {platform}.")
                except ValueError:
                    warning(f"  Invalid input. Skipping {platform}.")

        if selected_ids:
            info(f"\nTip: To skip this prompt next time, add to your config:")
            info(f'  "account_ids": {selected_ids}')

        return selected_ids

    def upload_and_post(
        self,
        video_path: str,
        caption: str,
        account_ids: list = None,
        platforms: list = None,
        platform_configurations: dict = None,
    ) -> dict:
        """
        Convenience method: upload a video and post it in one call.

        Args:
            video_path (str): Path to the video file.
            caption (str): Post caption.
            account_ids (list): Pre-configured account IDs. If provided,
                skips account lookup entirely.
            platforms (list): Platform names to filter by (used only if
                account_ids is not set).
            platform_configurations (dict): Optional per-platform overrides.

        Returns:
            result (dict): API response, or None on failure.
        """
        resolved_ids = self.resolve_account_ids(account_ids, platforms)
        if not resolved_ids:
            return None

        # Upload media
        media_id = self.upload_media(video_path)
        if not media_id:
            return None

        # Create post
        return self.create_post(
            caption=caption,
            social_account_ids=resolved_ids,
            media_ids=[media_id],
            platform_configurations=platform_configurations,
        )
