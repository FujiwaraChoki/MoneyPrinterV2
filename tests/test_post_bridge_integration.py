import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config
import post_bridge_integration
from post_bridge_integration import get_publish_history
from post_bridge_integration import publish_video
from post_bridge_integration import resolve_social_account_ids
from post_bridge_integration import run_post_bridge_setup_wizard


class PostBridgeIntegrationTests(unittest.TestCase):
    def write_config(self, directory: str, payload: dict) -> None:
        with open(os.path.join(directory, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def read_config(self, directory: str) -> dict:
        with open(os.path.join(directory, "config.json"), "r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_resolve_social_account_ids_interactive_prompts_for_ambiguous_accounts(self) -> None:
        client = Mock()
        client.list_social_accounts.return_value = [
            {"id": 21, "platform": "tiktok", "username": "brand"},
            {"id": 22, "platform": "tiktok", "username": "personal"},
            {"id": 31, "platform": "instagram", "username": "brand_ig"},
        ]
        prompt = Mock(side_effect=["2"])

        account_ids = resolve_social_account_ids(
            client=client,
            configured_account_ids=[],
            platforms=["tiktok", "instagram"],
            interactive=True,
            prompt_fn=prompt,
        )

        self.assertEqual(account_ids, [22, 31])
        prompt.assert_called_once()

    def test_resolve_social_account_ids_skips_non_interactive_when_multiple_accounts_exist(self) -> None:
        client = Mock()
        client.list_social_accounts.return_value = [
            {"id": 21, "platform": "tiktok", "username": "brand"},
            {"id": 22, "platform": "tiktok", "username": "personal"},
        ]

        account_ids = resolve_social_account_ids(
            client=client,
            configured_account_ids=[],
            platforms=["tiktok"],
            interactive=False,
        )

        self.assertEqual(account_ids, [])

    @patch("post_bridge_integration.ensure_post_bridge_publishing_ready", return_value=True)
    @patch("post_bridge_integration.PostBridge")
    @patch("post_bridge_integration.get_post_bridge_config")
    def test_cron_mode_skips_when_auto_publish_is_disabled(
        self,
        get_config_mock,
        post_bridge_cls_mock,
        _ensure_ready_mock,
    ) -> None:
        get_config_mock.return_value = {
            "enabled": True,
            "api_key": "token",
            "platforms": ["youtube", "tiktok"],
            "account_ids": [12, 34],
            "auto_publish": False,
        }

        with tempfile.NamedTemporaryFile(suffix=".mp4") as media_file:
            result = publish_video(
                video_path=media_file.name,
                title="My title",
                description="My description",
                interactive=False,
            )

        self.assertIsNone(result)
        post_bridge_cls_mock.assert_not_called()

    @patch("post_bridge_integration.get_video_publishing_config")
    @patch("post_bridge_integration.get_post_bridge_config")
    def test_readiness_allows_fixed_account_ids_without_platform_filters(
        self,
        get_config_mock,
        get_video_config_mock,
    ) -> None:
        get_config_mock.return_value = {
            "enabled": True,
            "api_key": "token",
            "platforms": [],
            "account_ids": [12, 34],
            "auto_publish": True,
        }
        get_video_config_mock.return_value = {
            "profile_name": "Default Publisher",
            "niche": "finance",
            "language": "English",
        }

        self.assertTrue(
            post_bridge_integration.ensure_post_bridge_publishing_ready(
                interactive=False,
            )
        )

    @patch("post_bridge_integration.ensure_post_bridge_publishing_ready", return_value=True)
    @patch("post_bridge_integration.PostBridge")
    @patch("post_bridge_integration.get_post_bridge_config")
    def test_interactive_publish_uploads_and_posts(
        self,
        get_config_mock,
        post_bridge_cls_mock,
        _ensure_ready_mock,
    ) -> None:
        get_config_mock.return_value = {
            "enabled": True,
            "api_key": "token",
            "platforms": ["youtube", "tiktok"],
            "account_ids": [12, 34],
            "auto_publish": False,
        }
        client = post_bridge_cls_mock.return_value
        client.upload_media.return_value = "media-123"
        client.create_post.return_value = {"id": "post-123", "warnings": []}

        with tempfile.NamedTemporaryFile(suffix=".mp4") as media_file:
            result = publish_video(
                video_path=media_file.name,
                title="My title",
                description="My description",
                interactive=True,
                prompt_fn=lambda _: "yes",
            )

        self.assertTrue(result)
        client.upload_media.assert_called_once()
        client.create_post.assert_called_once_with(
            caption="My description",
            social_account_ids=[12, 34],
            media_ids=["media-123"],
            platform_configurations={
                "youtube": {"title": "My title", "caption": "My description"},
                "tiktok": {"title": "My title"},
            },
        )

    @patch("post_bridge_integration.PostBridge")
    def test_setup_wizard_persists_selected_accounts(self, post_bridge_cls_mock) -> None:
        client = post_bridge_cls_mock.return_value
        client.list_social_accounts.return_value = [
            {"id": 11, "platform": "youtube", "username": "yt_brand"},
            {"id": 21, "platform": "tiktok", "username": "tt_brand"},
            {"id": 31, "platform": "instagram", "username": "ig_brand"},
        ]

        responses = iter(
            [
                "Launch Profile",
                "finance",
                "English",
                "pb_live_token",
                "",
                "yes",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"verbose": True})

            with patch.object(config, "ROOT_DIR", temp_dir):
                result = run_post_bridge_setup_wizard(prompt_fn=lambda _: next(responses))

            saved_config = self.read_config(temp_dir)

        self.assertIsNotNone(result)
        self.assertEqual(saved_config["video_publishing"]["profile_name"], "Launch Profile")
        self.assertEqual(saved_config["video_publishing"]["niche"], "finance")
        self.assertEqual(
            saved_config["post_bridge"]["platforms"],
            ["youtube", "tiktok", "instagram"],
        )
        self.assertEqual(saved_config["post_bridge"]["account_ids"], [11, 21, 31])
        self.assertTrue(saved_config["post_bridge"]["auto_publish"])

    @patch.dict(os.environ, {"POST_BRIDGE_API_KEY": "pb_env_token"}, clear=False)
    @patch("post_bridge_integration.PostBridge")
    def test_setup_wizard_does_not_persist_env_only_api_key(self, post_bridge_cls_mock) -> None:
        client = post_bridge_cls_mock.return_value
        client.list_social_accounts.return_value = [
            {"id": 11, "platform": "youtube", "username": "yt_brand"},
            {"id": 21, "platform": "tiktok", "username": "tt_brand"},
            {"id": 31, "platform": "instagram", "username": "ig_brand"},
        ]

        responses = iter(
            [
                "",
                "finance",
                "",
                "",
                "",
                "no",
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(
                temp_dir,
                {
                    "post_bridge": {
                        "enabled": False,
                        "api_key": "",
                    }
                },
            )

            with patch.object(config, "ROOT_DIR", temp_dir):
                result = run_post_bridge_setup_wizard(prompt_fn=lambda _: next(responses))

            saved_config = self.read_config(temp_dir)

        self.assertIsNotNone(result)
        self.assertEqual(saved_config["post_bridge"]["api_key"], "")
        self.assertFalse(saved_config["post_bridge"]["auto_publish"])

    @patch("post_bridge_integration.PostBridge")
    @patch("post_bridge_integration.get_post_bridge_config")
    def test_get_publish_history_merges_posts_and_results(
        self,
        get_config_mock,
        post_bridge_cls_mock,
    ) -> None:
        get_config_mock.return_value = {
            "enabled": True,
            "api_key": "token",
            "platforms": ["youtube", "tiktok"],
            "account_ids": [12, 34],
            "auto_publish": True,
        }
        client = post_bridge_cls_mock.return_value
        client.list_social_accounts.return_value = [
            {"id": 12, "platform": "youtube", "username": "yt_brand"},
            {"id": 34, "platform": "instagram", "username": "ig_brand"},
        ]
        client.list_posts.return_value = [
            {
                "id": "post-1",
                "created_at": "2026-03-26T10:00:00Z",
                "status": "posted",
                "caption": "hello",
                "platform_configurations": {
                    "youtube": {"title": "Title"},
                },
                "social_accounts": [12, 34],
            }
        ]
        client.list_post_results.return_value = [
            {
                "post_id": "post-1",
                "success": True,
                "platform_data": {"url": "https://youtube.com/watch?v=abc"},
            },
            {
                "post_id": "post-1",
                "success": True,
                "platform_data": {"url": "https://instagram.com/p/123"},
            },
        ]

        history = get_publish_history(limit=5)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["id"], "post-1")
        self.assertEqual(
            history[0]["urls"],
            [
                "https://youtube.com/watch?v=abc",
                "https://instagram.com/p/123",
            ],
        )
        self.assertEqual(history[0]["platforms"], ["youtube", "instagram"])


if __name__ == "__main__":
    unittest.main()
