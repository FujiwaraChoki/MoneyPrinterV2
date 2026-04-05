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


class YouTubeTopicDedupTests(unittest.TestCase):
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
                            "niche": "strange real events",
                            "language": "english",
                            "videos": [
                                {
                                    "title": "Dyatlov Pass: The Unexplained Deaths",
                                    "topic": "The Dyatlov Pass incident in 1959",
                                    "description": "Nine hikers died under mysterious conditions in the Ural Mountains in 1959.",
                                    "uploaded": True,
                                },
                                {
                                    "title": "Boston's Deadly Molasses Flood of 1919",
                                    "topic": "The Great Molasses Flood in Boston",
                                    "description": "A massive tank burst and flooded Boston with molasses in 1919.",
                                    "uploaded": True,
                                },
                            ],
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

        self.youtube_module = importlib.import_module("classes.YouTube")

    def restore_modules(self) -> None:
        config.ROOT_DIR = self._original_root_dir
        for module_name in self._modules_to_reset:
            sys.modules.pop(module_name, None)
        sys.modules.update(self._original_modules)

    def build_youtube(self):
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._account_uuid = "acct-1"
        youtube._niche = "strange real events"
        youtube._language = "english"
        return youtube

    def test_find_similar_video_ignores_generic_shared_mystery_words(self) -> None:
        youtube = self.build_youtube()

        similar_video = youtube._find_similar_video(
            "The Joyita Ghost Ship Vanishing",
            [
                {
                    "title": "SS Ourang Medan: The Ghost Ship Mystery",
                    "topic": "A ghost ship found drifting in the Malacca Strait",
                }
            ],
        )

        self.assertIsNone(similar_video)

    def test_generate_topic_retries_when_candidate_matches_previous_story(self) -> None:
        youtube = self.build_youtube()
        youtube.generate_response = Mock(
            side_effect=[
                "The Dyatlov Pass Incident Still Makes No Sense",
                "The Taos Hum That No One Could Explain",
            ]
        )

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "warning",
        ), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            topic = youtube.generate_topic()

        self.assertEqual(topic, "The Taos Hum That No One Could Explain")
        self.assertEqual(youtube.generate_response.call_count, 2)
        first_prompt = youtube.generate_response.call_args_list[0].args[0]
        self.assertIn("previously covered stories", first_prompt)
        self.assertIn("Dyatlov Pass: The Unexplained Deaths", first_prompt)

    def test_generate_topic_raises_after_repeated_similar_candidates(self) -> None:
        youtube = self.build_youtube()
        youtube.generate_response = Mock(
            side_effect=[
                "The Dyatlov Pass Incident Still Makes No Sense",
                "Inside the Dyatlov Pass Mystery",
                "Why the Dyatlov Pass Hikers Ran",
                "The Unsolved Dyatlov Pass Case",
                "The Strange Deaths at Dyatlov Pass",
            ]
        )

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "warning",
        ), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Generated topic remained too similar to previous videos",
            ):
                youtube.generate_topic()

        self.assertEqual(youtube.generate_response.call_count, 5)


if __name__ == "__main__":
    unittest.main()
