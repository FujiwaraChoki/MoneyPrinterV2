import os
import time
import requests

from config import get_tiktok_config
from status import info, success, warning, error


class TikTokClientError(RuntimeError):
    """Raised when a TikTok API request fails."""

    def __init__(self, message: str, status_code: int = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class TikTok:
    """
    Client for posting videos via the TikTok Content Posting API.

    Requires a registered TikTok developer app with ``video.publish`` scope
    and a valid user access token. Public visibility requires passing
    TikTok's app audit; until then posts are SELF_ONLY.
    """

    API_BASE = "https://open.tiktokapis.com"

    def __init__(self) -> None:
        config = get_tiktok_config()
        self._access_token: str = config["access_token"]

        if not self._access_token:
            raise TikTokClientError(
                "TikTok access_token must be set in config.json."
            )

    @staticmethod
    def is_configured() -> bool:
        """Return True when TikTok credentials are present."""
        config = get_tiktok_config()
        return bool(config["access_token"])

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def get_creator_info(self) -> dict:
        """
        Query the creator's info to determine available privacy levels.

        Returns:
            creator_info (dict): Creator info payload from TikTok.
        """
        url = f"{self.API_BASE}/v2/post/publish/creator_info/query/"
        resp = requests.post(url, headers=self._headers(), json={}, timeout=30)
        self._check_response(resp)
        return resp.json().get("data", {})

    def post_video(self, video_path: str, title: str) -> str:
        """
        Upload and publish a video to TikTok.

        The method determines the best available privacy level. If the app
        has not passed TikTok's audit, posts will be SELF_ONLY.

        Args:
            video_path (str): Absolute path to the MP4 file.
            title (str): Video title / description (max 150 chars).

        Returns:
            publish_id (str): TikTok publish ID for status tracking.
        """
        if not os.path.exists(video_path):
            raise TikTokClientError(f"Video file not found: {video_path}")

        creator_info = self.get_creator_info()
        privacy_options = creator_info.get("privacy_level_options", ["SELF_ONLY"])
        privacy = (
            "PUBLIC_TO_EVERYONE"
            if "PUBLIC_TO_EVERYONE" in privacy_options
            else privacy_options[0]
        )

        if privacy != "PUBLIC_TO_EVERYONE":
            warning(
                f" => TikTok: posting as '{privacy}' — your app may not have "
                "passed the TikTok audit yet. Videos won't be publicly visible."
            )

        file_size = os.path.getsize(video_path)
        info(f" => TikTok: initializing upload ({file_size} bytes, privacy={privacy})...")

        # Step 1: Initialize the upload
        init_url = f"{self.API_BASE}/v2/post/publish/video/init/"
        init_body = {
            "post_info": {
                "title": title[:150],
                "privacy_level": privacy,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
            },
        }
        resp = requests.post(
            init_url, headers=self._headers(), json=init_body, timeout=30
        )
        self._check_response(resp)
        data = resp.json().get("data", {})
        upload_url = data.get("upload_url")
        publish_id = data.get("publish_id")

        if not upload_url:
            raise TikTokClientError(
                f"TikTok did not return an upload_url: {resp.json()}"
            )

        # Step 2: Upload the video binary
        info(f" => TikTok: uploading video...")
        with open(video_path, "rb") as f:
            put_resp = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                },
                data=f,
                timeout=300,
            )
        if put_resp.status_code not in (200, 201):
            raise TikTokClientError(
                f"TikTok upload failed with HTTP {put_resp.status_code}",
                status_code=put_resp.status_code,
            )

        success(f" => TikTok: uploaded video (publish_id={publish_id})")
        return publish_id

    def check_publish_status(self, publish_id: str) -> dict:
        """
        Poll the publish status of a video.

        Args:
            publish_id (str): The publish ID returned from post_video.

        Returns:
            status (dict): Status payload from TikTok.
        """
        url = f"{self.API_BASE}/v2/post/publish/status/fetch/"
        resp = requests.post(
            url,
            headers=self._headers(),
            json={"publish_id": publish_id},
            timeout=30,
        )
        self._check_response(resp)
        return resp.json().get("data", {})

    def _check_response(self, resp: requests.Response) -> None:
        if resp.status_code >= 400:
            try:
                body = resp.json()
                err = body.get("error", {})
                msg = err.get("message", resp.text) if isinstance(err, dict) else str(err)
            except ValueError:
                msg = resp.text
            raise TikTokClientError(
                f"TikTok API HTTP {resp.status_code}: {msg}",
                status_code=resp.status_code,
            )
