import os
import sys
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from classes.PostBridge import PostBridge


class MockResponse:
    def __init__(self, status_code: int, json_data=None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


class PostBridgeClientTests(unittest.TestCase):
    @patch("classes.PostBridge.time.sleep")
    def test_list_social_accounts_follows_pagination(self, _sleep_mock) -> None:
        session = Mock()
        session.request.side_effect = [
            MockResponse(
                200,
                {
                    "data": [{"id": 11, "platform": "tiktok", "username": "brand"}],
                    "meta": {
                        "next": "https://api.post-bridge.com/v1/social-accounts?offset=1&limit=1"
                    },
                },
            ),
            MockResponse(
                200,
                {
                    "data": [{"id": 12, "platform": "instagram", "username": "brand_ig"}],
                    "meta": {"next": None},
                },
            ),
        ]
        client = PostBridge("token", session=session)

        accounts = client.list_social_accounts(
            platforms=["tiktok", "instagram"],
            limit=1,
        )

        self.assertEqual(
            accounts,
            [
                {"id": 11, "platform": "tiktok", "username": "brand"},
                {"id": 12, "platform": "instagram", "username": "brand_ig"},
            ],
        )
        self.assertEqual(session.request.call_count, 2)

        first_call = session.request.call_args_list[0]
        self.assertEqual(first_call.args[0], "GET")
        self.assertEqual(
            first_call.args[1],
            "https://api.post-bridge.com/v1/social-accounts",
        )
        self.assertEqual(
            first_call.kwargs["params"],
            [("limit", 1), ("platform", "tiktok"), ("platform", "instagram")],
        )

        second_call = session.request.call_args_list[1]
        self.assertEqual(second_call.args[1], "https://api.post-bridge.com/v1/social-accounts?offset=1&limit=1")
        self.assertIsNone(second_call.kwargs["params"])

    @patch("classes.PostBridge.time.sleep")
    def test_create_post_retries_after_rate_limit(self, sleep_mock) -> None:
        session = Mock()
        session.request.side_effect = [
            MockResponse(429, {"message": "Too many requests"}),
            MockResponse(200, {"id": "post-123", "status": "processing"}),
        ]
        client = PostBridge("token", session=session)

        response = client.create_post(
            caption="Hello world",
            social_account_ids=[12, 34],
            media_ids=["media-1"],
        )

        self.assertEqual(response["id"], "post-123")
        self.assertEqual(session.request.call_count, 2)
        sleep_mock.assert_called_once()

    def test_upload_media_does_not_forward_api_bearer_token_to_signed_upload_url(self) -> None:
        session = Mock()
        session.request.side_effect = [
            MockResponse(
                200,
                {
                    "media_id": "media-123",
                    "upload_url": "https://signed-upload.example/path",
                },
            ),
            MockResponse(200, {}),
        ]
        client = PostBridge("token", session=session)

        with patch("classes.PostBridge.os.path.exists", return_value=True), patch(
            "classes.PostBridge.os.path.getsize", return_value=5
        ), patch("classes.PostBridge.mimetypes.guess_type", return_value=("video/mp4", None)), patch(
            "builtins.open",
            unittest.mock.mock_open(read_data=b"video"),
        ):
            media_id = client.upload_media("/tmp/video.mp4")

        self.assertEqual(media_id, "media-123")
        upload_call = session.request.call_args_list[1]
        self.assertEqual(upload_call.args[0], "PUT")
        self.assertEqual(upload_call.args[1], "https://signed-upload.example/path")
        self.assertEqual(upload_call.kwargs["headers"], {"Content-Type": "video/mp4"})

    @patch("classes.PostBridge.time.sleep")
    def test_request_rewinds_streamed_upload_body_before_retry(self, sleep_mock) -> None:
        session = Mock()
        session.request.side_effect = [
            MockResponse(500, {"message": "temporary error"}),
            MockResponse(200, {}),
        ]
        client = PostBridge("token", session=session)

        stream = unittest.mock.mock_open(read_data=b"video").return_value
        stream.seek = Mock()

        client._request(
            "PUT",
            "https://signed-upload.example/path",
            data=stream,
            headers={"Content-Type": "video/mp4"},
            expected_statuses={200},
            use_default_headers=False,
        )

        self.assertEqual(stream.seek.call_count, 2)
        stream.seek.assert_any_call(0)
        sleep_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
