import os
import time
import requests

from config import get_instagram_config
from status import info, success, warning, error


class InstagramClientError(RuntimeError):
    """Raised when an Instagram Graph API request fails."""

    def __init__(self, message: str, status_code: int = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class Instagram:
    """
    Client for posting Reels and images via the Instagram Graph API.

    Requires an Instagram Business/Creator account linked to a Facebook Page,
    and a long-lived access token with ``instagram_content_publish`` permission.
    """

    GRAPH_URL = "https://graph.instagram.com/v21.0"

    def __init__(self) -> None:
        config = get_instagram_config()
        self._access_token: str = config["access_token"]
        self._account_id: str = config["account_id"]

        if not self._access_token or not self._account_id:
            raise InstagramClientError(
                "Instagram access_token and account_id must be set in config.json."
            )

    @staticmethod
    def is_configured() -> bool:
        """Return True when Instagram credentials are present."""
        config = get_instagram_config()
        return bool(config["access_token"] and config["account_id"])

    def post_reel(self, video_url: str, caption: str) -> str:
        """
        Publish a Reel to Instagram.

        Args:
            video_url (str): Publicly accessible URL of the MP4 video.
            caption (str): Post caption text.

        Returns:
            media_id (str): Published media ID.
        """
        container_id = self._create_container(
            media_type="REELS",
            media_url=video_url,
            caption=caption,
        )
        info(f" => Instagram: waiting for Reel container {container_id} to process...")
        self._wait_for_container(container_id, max_wait=300)
        media_id = self._publish(container_id)
        success(f" => Instagram: published Reel (media ID: {media_id})")
        return media_id

    def post_image(self, image_url: str, caption: str) -> str:
        """
        Publish a single image to Instagram.

        Args:
            image_url (str): Publicly accessible JPEG URL.
            caption (str): Post caption text.

        Returns:
            media_id (str): Published media ID.
        """
        container_id = self._create_container(
            media_type="IMAGE",
            media_url=image_url,
            caption=caption,
        )
        self._wait_for_container(container_id)
        media_id = self._publish(container_id)
        success(f" => Instagram: published image (media ID: {media_id})")
        return media_id

    def _create_container(self, media_type: str, media_url: str, caption: str) -> str:
        url = f"{self.GRAPH_URL}/{self._account_id}/media"
        params = {
            "caption": caption,
            "access_token": self._access_token,
        }
        if media_type == "REELS":
            params["media_type"] = "REELS"
            params["video_url"] = media_url
        else:
            params["image_url"] = media_url

        resp = requests.post(url, data=params, timeout=60)
        self._check_response(resp)
        return resp.json()["id"]

    def _wait_for_container(self, container_id: str, max_wait: int = 120) -> None:
        url = f"{self.GRAPH_URL}/{container_id}"
        params = {
            "fields": "status_code",
            "access_token": self._access_token,
        }
        deadline = time.time() + max_wait
        while time.time() < deadline:
            resp = requests.get(url, params=params, timeout=30)
            self._check_response(resp)
            status = resp.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise InstagramClientError(
                    f"Instagram container {container_id} failed processing."
                )
            time.sleep(5)

        raise InstagramClientError(
            f"Instagram container {container_id} timed out after {max_wait}s."
        )

    def _publish(self, container_id: str) -> str:
        url = f"{self.GRAPH_URL}/{self._account_id}/media_publish"
        resp = requests.post(url, data={
            "creation_id": container_id,
            "access_token": self._access_token,
        }, timeout=60)
        self._check_response(resp)
        return resp.json()["id"]

    def _check_response(self, resp: requests.Response) -> None:
        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("error", {}).get("message", resp.text)
            except ValueError:
                msg = resp.text
            raise InstagramClientError(
                f"Instagram API HTTP {resp.status_code}: {msg}",
                status_code=resp.status_code,
            )
