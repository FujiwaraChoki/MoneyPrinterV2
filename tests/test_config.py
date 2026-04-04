import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config


class PostBridgeConfigTests(unittest.TestCase):
    def write_config(self, directory: str, payload: dict) -> None:
        with open(os.path.join(directory, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def read_config(self, directory: str) -> dict:
        with open(os.path.join(directory, "config.json"), "r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_missing_platforms_uses_publish_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {"post_bridge": {"enabled": True}})

            with patch.object(config, "ROOT_DIR", temp_dir):
                post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(
            post_bridge_config["platforms"],
            ["youtube", "tiktok", "instagram"],
        )

    def test_legacy_auto_crosspost_maps_to_auto_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(
                temp_dir,
                {"post_bridge": {"enabled": True, "auto_crosspost": True}},
            )

            with patch.object(config, "ROOT_DIR", temp_dir):
                post_bridge_config = config.get_post_bridge_config()

        self.assertTrue(post_bridge_config["auto_publish"])

    def test_invalid_platforms_are_filtered_but_youtube_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(
                temp_dir,
                {
                    "post_bridge": {
                        "enabled": True,
                        "platforms": ["youtube", "tik-tok", "instagram"],
                    }
                },
            )

            with patch.object(config, "ROOT_DIR", temp_dir):
                post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], ["youtube", "instagram"])

    def test_update_config_section_preserves_unrelated_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(
                temp_dir,
                {
                    "verbose": True,
                    "post_bridge": {"enabled": False},
                    "video_publishing": {"niche": "finance"},
                },
            )

            with patch.object(config, "ROOT_DIR", temp_dir):
                config.update_config_section(
                    "post_bridge",
                    {
                        "enabled": True,
                        "platforms": ["youtube"],
                    },
                )

            saved_config = self.read_config(temp_dir)

        self.assertTrue(saved_config["verbose"])
        self.assertEqual(saved_config["video_publishing"]["niche"], "finance")
        self.assertEqual(saved_config["post_bridge"]["platforms"], ["youtube"])

    def test_video_publishing_defaults_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.write_config(temp_dir, {})

            with patch.object(config, "ROOT_DIR", temp_dir):
                video_config = config.get_video_publishing_config()

        self.assertEqual(video_config["profile_name"], "Default Publisher")
        self.assertEqual(video_config["language"], "English")
        self.assertEqual(video_config["niche"], "")


if __name__ == "__main__":
    unittest.main()
