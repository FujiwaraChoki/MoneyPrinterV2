import mimetypes
import os
import time
from typing import Optional
from typing import Sequence

import requests


class PostBridgeClientError(RuntimeError):
    """
    Raised when a Post Bridge request fails.
    """

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PostBridge:
    """
    Thin client for the Post Bridge API.

    Docs: https://api.post-bridge.com/reference
    """

    API_BASE = "https://api.post-bridge.com/v1"
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        api_key: str,
        session: Optional[requests.Session] = None,
        max_retries: int = 3,
    ) -> None:
        self._session = session or requests.Session()
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._max_retries = max_retries

    def list_social_accounts(
        self,
        platforms: Optional[Sequence[str]] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Fetch connected social accounts with pagination support.

        Args:
            platforms (Sequence[str] | None): Optional platform filters.
            limit (int): Page size to request from the API.

        Returns:
            accounts (list[dict]): Social account data.
        """
        params = [("limit", limit)]
        if platforms:
            for platform in platforms:
                params.append(("platform", platform))

        return self._list_paginated_request(
            f"{self.API_BASE}/social-accounts",
            params=params,
            invalid_payload_message="Post Bridge returned an invalid social accounts payload.",
            max_items=None,
        )

    def list_posts(
        self,
        platforms: Optional[Sequence[str]] = None,
        statuses: Optional[Sequence[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        Fetch posts with optional platform and status filters.

        Args:
            platforms (Sequence[str] | None): Optional platform filters.
            statuses (Sequence[str] | None): Optional post status filters.
            limit (int): Max number of posts to return.
            offset (int): Initial pagination offset.

        Returns:
            posts (list[dict]): Post data.
        """
        params = [("limit", limit), ("offset", offset)]
        if platforms:
            for platform in platforms:
                params.append(("platform", platform))
        if statuses:
            for status in statuses:
                params.append(("status", status))

        return self._list_paginated_request(
            f"{self.API_BASE}/posts",
            params=params,
            invalid_payload_message="Post Bridge returned an invalid posts payload.",
            max_items=limit,
        )

    def list_post_results(
        self,
        post_ids: Optional[Sequence[str]] = None,
        platforms: Optional[Sequence[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Fetch post results with optional post ID and platform filters.

        Args:
            post_ids (Sequence[str] | None): Optional post IDs.
            platforms (Sequence[str] | None): Optional platform filters.
            limit (int): Max number of results to return.
            offset (int): Initial pagination offset.

        Returns:
            post_results (list[dict]): Post result data.
        """
        params = [("limit", limit), ("offset", offset)]
        if post_ids:
            for post_id in post_ids:
                params.append(("post_id", post_id))
        if platforms:
            for platform in platforms:
                params.append(("platform", platform))

        return self._list_paginated_request(
            f"{self.API_BASE}/post-results",
            params=params,
            invalid_payload_message="Post Bridge returned an invalid post results payload.",
            max_items=limit,
        )

    def upload_media(self, file_path: str) -> str:
        """
        Upload a local media file to Post Bridge and return its media ID.

        Args:
            file_path (str): Absolute path to a local media file.

        Returns:
            media_id (str): Uploaded media ID.
        """
        if not os.path.exists(file_path):
            raise PostBridgeClientError(f"Media file does not exist: {file_path}")

        file_name = os.path.basename(file_path)
        mime_type = self._guess_mime_type(file_path)
        file_size = os.path.getsize(file_path)

        upload_response = self._request_json(
            "POST",
            f"{self.API_BASE}/media/create-upload-url",
            json={
                "name": file_name,
                "mime_type": mime_type,
                "size_bytes": file_size,
            },
        )

        media_id = upload_response.get("media_id")
        upload_url = upload_response.get("upload_url")

        if not media_id or not upload_url:
            raise PostBridgeClientError(
                "Post Bridge did not return a media_id and upload_url."
            )

        with open(file_path, "rb") as media_file:
            self._request(
                "PUT",
                upload_url,
                data=media_file,
                headers={"Content-Type": mime_type},
                timeout=600,
                expected_statuses={200, 201},
                use_default_headers=False,
            )

        return media_id

    def create_post(
        self,
        caption: str,
        social_account_ids: Sequence[int],
        media_ids: Optional[Sequence[str]] = None,
        platform_configurations: Optional[dict] = None,
        scheduled_at: Optional[str] = None,
        processing_enabled: bool = True,
    ) -> dict:
        """
        Create a post on one or more social accounts.

        Args:
            caption (str): Post caption.
            social_account_ids (Sequence[int]): Target social account IDs.
            media_ids (Sequence[str] | None): Optional media IDs to attach.
            platform_configurations (dict | None): Optional platform overrides.
            scheduled_at (str | None): Optional ISO8601 schedule time.
            processing_enabled (bool): Allow Post Bridge video processing.

        Returns:
            result (dict): Created post response.
        """
        payload = {
            "caption": caption,
            "social_accounts": list(social_account_ids),
            "processing_enabled": processing_enabled,
        }

        if media_ids:
            payload["media"] = list(media_ids)
        if platform_configurations:
            payload["platform_configurations"] = platform_configurations
        if scheduled_at:
            payload["scheduled_at"] = scheduled_at

        return self._request_json(
            "POST",
            f"{self.API_BASE}/posts",
            json=payload,
        )

    def _list_paginated_request(
        self,
        url: str,
        *,
        params: Optional[list[tuple[str, object]]] = None,
        invalid_payload_message: str,
        max_items: Optional[int],
    ) -> list[dict]:
        """
        Fetch list endpoints that use the standard paginated response shape.

        Args:
            url (str): Endpoint URL.
            params (list[tuple[str, object]] | None): Query params for the first page.
            invalid_payload_message (str): Error message for invalid payloads.
            max_items (int | None): Optional max number of items to return.

        Returns:
            items (list[dict]): Collected items.
        """
        items = []
        next_url = url
        is_first_request = True

        while next_url and (max_items is None or len(items) < max_items):
            response_json = self._request_json(
                "GET",
                next_url,
                params=params if is_first_request else None,
            )
            is_first_request = False

            page_items = response_json.get("data", response_json)
            if not isinstance(page_items, list):
                raise PostBridgeClientError(invalid_payload_message)

            if max_items is None:
                items.extend(page_items)
            else:
                remaining = max_items - len(items)
                items.extend(page_items[:remaining])

            meta = response_json.get("meta", {})
            next_url = meta.get("next") if isinstance(meta, dict) else None

        return items

    def _guess_mime_type(self, file_path: str) -> str:
        guessed_type = mimetypes.guess_type(file_path)[0]
        if guessed_type in {"image/png", "image/jpeg", "video/mp4", "video/quicktime"}:
            return guessed_type
        return "video/mp4"

    def _request_json(self, method: str, url: str, **kwargs) -> dict:
        response = self._request(method, url, **kwargs)

        try:
            response_json = response.json()
        except ValueError as exc:
            raise PostBridgeClientError(
                "Post Bridge returned a non-JSON response.",
                status_code=response.status_code,
            ) from exc

        if not isinstance(response_json, dict):
            return {"data": response_json}

        return response_json

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[dict] = None,
        timeout: int = 60,
        expected_statuses: Optional[set[int]] = None,
        use_default_headers: bool = True,
        **kwargs,
    ) -> requests.Response:
        if expected_statuses is None:
            expected_statuses = {200}

        merged_headers = dict(self._headers) if use_default_headers else {}
        if headers:
            merged_headers.update(headers)

        last_exception = None

        for attempt in range(1, self._max_retries + 1):
            try:
                request_data = kwargs.get("data")
                if hasattr(request_data, "seek"):
                    request_data.seek(0)

                response = self._session.request(
                    method,
                    url,
                    headers=merged_headers,
                    timeout=timeout,
                    **kwargs,
                )
            except requests.RequestException as exc:
                last_exception = exc
                if attempt == self._max_retries:
                    break
                time.sleep(0.5 * attempt)
                continue

            if response.status_code in expected_statuses:
                return response

            if (
                response.status_code in self.RETRYABLE_STATUS_CODES
                and attempt < self._max_retries
            ):
                time.sleep(0.5 * attempt)
                continue

            raise PostBridgeClientError(
                self._build_http_error(response),
                status_code=response.status_code,
            )

        raise PostBridgeClientError(
            f"Request to Post Bridge failed: {last_exception}",
        ) from last_exception

    def _build_http_error(self, response: requests.Response) -> str:
        try:
            response_json = response.json()
        except ValueError:
            response_json = None

        details = None

        if isinstance(response_json, dict):
            if isinstance(response_json.get("error"), list):
                details = "; ".join(str(item) for item in response_json["error"])
            elif response_json.get("error"):
                details = str(response_json["error"])
            elif response_json.get("message"):
                details = str(response_json["message"])

        if details is None:
            body = response.text.strip()
            details = body or "No response body."

        return f"Post Bridge API returned HTTP {response.status_code}: {details}"
