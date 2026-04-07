import importlib
import json
import os
import shutil
import sys
import time
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

        with open(self.cache.get_youtube_cache_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        payload["accounts"][0]["videos"] = [
            {
                "title": "Ancient computer",
                "date": "04/04/2026, 12:00:00",
                "path": video_path,
                "uploaded": False,
            }
        ]

        with open(self.cache.get_youtube_cache_path(), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)

        with open(video_path, "wb") as handle:
            handle.write(b"video")
        with open(image_path, "wb") as handle:
            handle.write(b"image")

        # Backdate image so it's older than the 2-hour stale threshold
        old_ts = time.time() - 3 * 3600
        os.utime(image_path, (old_ts, old_ts))

        self.utils.rem_temp_files()

        self.assertTrue(os.path.exists(video_path))
        self.assertFalse(os.path.exists(image_path))

    def test_rem_temp_files_removes_untracked_rendered_videos(self) -> None:
        mp_dir = os.path.join(self.config_dir, ".mp")
        tracked_video_path = os.path.join(mp_dir, "final.mp4")
        untracked_video_path = os.path.join(mp_dir, "old-render.mp4")

        with open(self.cache.get_youtube_cache_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        payload["accounts"][0]["videos"] = [
            {
                "title": "Ancient computer",
                "date": "04/04/2026, 12:00:00",
                "path": tracked_video_path,
                "uploaded": False,
            }
        ]

        with open(self.cache.get_youtube_cache_path(), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)

        with open(tracked_video_path, "wb") as handle:
            handle.write(b"tracked")
        with open(untracked_video_path, "wb") as handle:
            handle.write(b"untracked")

        # Backdate untracked video so it's older than the 2-hour stale threshold
        old_ts = time.time() - 3 * 3600
        os.utime(untracked_video_path, (old_ts, old_ts))

        self.utils.rem_temp_files()

        self.assertTrue(os.path.exists(tracked_video_path))
        self.assertFalse(os.path.exists(untracked_video_path))

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

    def test_load_cached_video_backfills_missing_description_from_script(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)

        youtube.load_cached_video(
            {
                "title": "Ancient computer",
                "script": "Nine hikers fled their tent into the night.",
                "topic": "Dyatlov Pass incident",
                "path": "./.mp/final.mp4",
            }
        )

        self.assertEqual(youtube.metadata["title"], "Ancient computer")
        self.assertEqual(
            youtube.metadata["description"],
            "Nine hikers fled their tent into the night.",
        )
        self.assertTrue(youtube.video_path.endswith(os.path.join(".mp", "final.mp4")))

    def test_record_crosspost_result_persists_platform_status(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"

        initial_video = {
            "title": "Ancient computer",
            "date": "04/04/2026, 12:00:00",
            "path": "/tmp/final.mp4",
            "uploaded": True,
        }
        youtube.add_video(initial_video)

        youtube.record_crosspost_result(
            initial_video,
            {
                "posted": True,
                "platforms": {
                    "tiktok": {"status": "success", "post_id": "post-123"},
                    "instagram": {"status": "success", "post_id": "post-123"},
                },
            },
        )

        with open(self.cache.get_youtube_cache_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        stored_video = payload["accounts"][0]["videos"][0]
        self.assertEqual(stored_video["crossposts"]["tiktok"]["status"], "success")
        self.assertEqual(stored_video["crossposts"]["instagram"]["post_id"], "post-123")

    def test_record_crosspost_result_merges_existing_platform_status(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"

        with open(self.cache.get_youtube_cache_path(), "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "accounts": [
                        {
                            "id": "acct-1",
                            "nickname": "Channel",
                            "videos": [
                                {
                                    "path": "/tmp/final.mp4",
                                    "uploaded": True,
                                    "crossposts": {
                                        "tiktok": {
                                            "status": "success",
                                            "post_id": "post-tt",
                                        }
                                    },
                                }
                            ],
                        }
                    ]
                },
                handle,
            )

        youtube.record_crosspost_result(
            {
                "path": "/tmp/final.mp4",
                "crossposts": {
                    "tiktok": {"status": "success", "post_id": "post-tt"},
                },
            },
            {
                "platforms": {
                    "instagram": {"status": "success", "post_id": "post-ig"},
                }
            },
        )

        with open(self.cache.get_youtube_cache_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        stored_video = payload["accounts"][0]["videos"][0]
        self.assertEqual(stored_video["crossposts"]["tiktok"]["post_id"], "post-tt")
        self.assertEqual(stored_video["crossposts"]["instagram"]["post_id"], "post-ig")

    def test_record_post_bridge_publish_result_marks_youtube_uploaded_and_filters_youtube_crosspost(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"
        youtube.subject = "Ancient computer"
        youtube.script = "A story about a machine ahead of its time."
        youtube.metadata = {
            "title": "Ancient computer",
            "description": "A short documentary about the ancient computer.",
        }
        youtube.video_path = "/tmp/final.mp4"

        youtube.record_post_bridge_publish_result(
            {
                "posted": True,
                "platforms": {
                    "youtube": {"status": "success", "post_id": "post-yt"},
                    "tiktok": {"status": "success", "post_id": "post-tt"},
                },
            }
        )

        with open(self.cache.get_youtube_cache_path(), "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        stored_video = payload["accounts"][0]["videos"][0]
        self.assertTrue(stored_video["uploaded"])
        self.assertEqual(stored_video["title"], "Ancient computer")
        self.assertNotIn("youtube", stored_video.get("crossposts", {}))
        self.assertEqual(stored_video["crossposts"]["tiktok"]["post_id"], "post-tt")

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

    def test_generate_video_raises_when_image_generation_returns_none(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"
        youtube.images = []

        def fake_generate_topic() -> str:
            youtube.subject = "Broadcast intrusion mystery"
            return youtube.subject

        def fake_generate_script() -> str:
            youtube.script = "A strange voice interrupted television signals."
            return youtube.script

        def fake_generate_metadata() -> dict:
            youtube.metadata = {
                "title": "Broadcast intrusion mystery",
                "description": "A short documentary about a broadcast interruption.",
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
            return_value=["prompt-1"],
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_image",
            return_value=None,
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_script_to_speech",
        ) as tts_mock, patch.object(
            self.youtube_module.YouTube,
            "combine",
        ) as combine_mock:
            with self.assertRaisesRegex(RuntimeError, "Failed to generate image for prompt"):
                youtube.generate_video(Mock())

        tts_mock.assert_not_called()
        combine_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
