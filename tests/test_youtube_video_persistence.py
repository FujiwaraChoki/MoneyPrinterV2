import importlib
import json
import os
import shutil
import sys
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config


class YouTubeVideoPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config_dir = os.path.join(
            ROOT_DIR,
            "tests",
            ".config-fixtures",
            self.__class__.__name__,
            self._testMethodName,
        )
        shutil.rmtree(self.config_dir, ignore_errors=True)
        os.makedirs(os.path.join(self.config_dir, ".mp"), exist_ok=True)
        self.addCleanup(shutil.rmtree, self.config_dir, True)

        with open(
            os.path.join(ROOT_DIR, "config.example.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            example_config = json.load(handle)

        example_config["imagemagick_path"] = "/opt/homebrew/bin/magick"

        with open(
            os.path.join(self.config_dir, "config.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(example_config, handle)

        with open(
            os.path.join(self.config_dir, ".mp", "youtube.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                {
                    "accounts": [
                        {
                            "id": "acct-1",
                            "nickname": "demo",
                            "firefox_profile": "/tmp/profile",
                            "niche": "science",
                            "language": "english",
                            "videos": [],
                        }
                    ]
                },
                handle,
                indent=4,
            )

        self._modules_to_reset = ["cache", "utils", "classes.YouTube", "llm_provider"]
        self._original_modules = {}

        for module_name in self._modules_to_reset:
            if module_name in sys.modules:
                self._original_modules[module_name] = sys.modules[module_name]
            sys.modules.pop(module_name, None)

        self._original_root_dir = config.ROOT_DIR
        config.ROOT_DIR = self.config_dir
        self.addCleanup(self.restore_modules)

        self.cache = importlib.import_module("cache")
        self.utils = importlib.import_module("utils")
        self.youtube_module = importlib.import_module("classes.YouTube")

    def restore_modules(self) -> None:
        config.ROOT_DIR = self._original_root_dir
        for module_name in self._modules_to_reset:
            sys.modules.pop(module_name, None)
        sys.modules.update(self._original_modules)

    def test_rem_temp_files_keeps_rendered_videos(self) -> None:
        mp_dir = os.path.join(self.config_dir, ".mp")
        video_path = os.path.join(mp_dir, "final.mp4")
        image_path = os.path.join(mp_dir, "frame.png")

        with open(video_path, "wb") as handle:
            handle.write(b"video")
        with open(image_path, "wb") as handle:
            handle.write(b"image")

        self.utils.rem_temp_files()

        self.assertTrue(os.path.exists(video_path))
        self.assertFalse(os.path.exists(image_path))

    def test_add_video_persists_generated_video_in_cache(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"

        video_record = {
            "title": "Ancient computer",
            "date": "04/04/2026, 12:00:00",
            "path": "/tmp/final.mp4",
            "uploaded": False,
        }

        youtube.add_video(video_record)

        with open(self.cache.get_youtube_cache_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["accounts"][0]["videos"], [video_record])

    def test_generate_video_persists_topic_and_script_fields(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"
        youtube.images = []

        def fake_generate_topic() -> str:
            youtube.subject = "The Dyatlov Pass incident"
            return youtube.subject

        def fake_generate_script() -> str:
            youtube.script = "Nine hikers fled their tent into the night."
            return youtube.script

        def fake_generate_metadata() -> dict:
            youtube.metadata = {
                "title": "Dyatlov Pass mystery",
                "description": "A short documentary about Dyatlov Pass.",
            }
            return youtube.metadata

        with patch.object(
            self.youtube_module.YouTube,
            "generate_topic",
            side_effect=fake_generate_topic,
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_script",
            side_effect=fake_generate_script,
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_metadata",
            side_effect=fake_generate_metadata,
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_prompts",
            return_value=[],
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_script_to_speech",
            return_value="/tmp/tts.mp3",
        ), patch.object(
            self.youtube_module.YouTube,
            "combine",
            return_value="/tmp/final.mp4",
        ), patch.object(
            self.youtube_module.YouTube,
            "add_video",
        ) as add_video_mock:
            youtube.generate_video(Mock())

        add_video_mock.assert_called_once()
        persisted_video = add_video_mock.call_args.args[0]
        self.assertEqual(persisted_video["topic"], "The Dyatlov Pass incident")
        self.assertEqual(
            persisted_video["script"],
            "Nine hikers fled their tent into the night.",
        )
        self.assertEqual(persisted_video["path"], "/tmp/final.mp4")
        self.assertFalse(persisted_video["uploaded"])


if __name__ == "__main__":
    unittest.main()
