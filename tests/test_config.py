import json
import os
import shutil
import sys
import unittest
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config


class ConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.config_dir = os.path.join(
            ROOT_DIR,
            "tests",
            ".config-fixtures",
            self.__class__.__name__,
            self._testMethodName,
        )
        shutil.rmtree(self.config_dir, ignore_errors=True)
        os.makedirs(self.config_dir, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.config_dir, True)

    def write_config(self, payload: dict) -> None:
        with open(os.path.join(self.config_dir, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def patch_root_dir(self):
        return patch.object(config, "ROOT_DIR", self.config_dir)


class PostBridgeConfigTests(ConfigTestCase):
    def test_missing_platforms_uses_defaults(self) -> None:
        self.write_config({"post_bridge": {"enabled": True}})

        with self.patch_root_dir():
            post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], ["tiktok", "instagram"])

    def test_supported_twitter_platform_is_preserved(self) -> None:
        self.write_config(
            {
                "post_bridge": {
                    "enabled": True,
                    "platforms": ["twitter", "instagram", "twitter"],
                }
            }
        )

        with self.patch_root_dir():
            post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], ["twitter", "instagram"])

    def test_supported_youtube_platform_is_preserved(self) -> None:
        self.write_config(
            {
                "post_bridge": {
                    "enabled": True,
                    "platforms": ["youtube", "instagram", "youtube"],
                }
            }
        )

        with self.patch_root_dir():
            post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], ["youtube", "instagram"])

    def test_invalid_or_empty_platforms_do_not_expand_to_defaults(self) -> None:
        self.write_config(
            {
                "post_bridge": {
                    "enabled": True,
                    "platforms": ["tik-tok"],
                }
            }
        )

        with self.patch_root_dir():
            post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], [])

    def test_non_list_platforms_fail_closed(self) -> None:
        self.write_config(
            {
                "post_bridge": {
                    "enabled": True,
                    "platforms": "tiktok",
                }
            }
        )

        with self.patch_root_dir():
            post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], [])

    def test_non_object_post_bridge_config_falls_back_to_defaults(self) -> None:
        self.write_config(
            {
                "post_bridge": None,
            }
        )

        with self.patch_root_dir():
            post_bridge_config = config.get_post_bridge_config()

        self.assertEqual(post_bridge_config["platforms"], ["tiktok", "instagram"])
        self.assertEqual(post_bridge_config["account_ids"], [])
        self.assertFalse(post_bridge_config["enabled"])


class OpenRouterConfigTests(ConfigTestCase):
    def test_api_key_prefers_config_value_over_env(self) -> None:
        self.write_config({"openrouter_api_key": "config-key"})

        with self.patch_root_dir(), patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=False):
            api_key = config.get_openrouter_api_key()

        self.assertEqual(api_key, "config-key")

    def test_api_key_uses_env_when_config_empty_or_missing(self) -> None:
        for payload in ({"openrouter_api_key": ""}, {}):
            with self.subTest(payload=payload):
                self.write_config(payload)

                with self.patch_root_dir(), patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=False):
                    api_key = config.get_openrouter_api_key()

                self.assertEqual(api_key, "env-key")

    def test_api_key_falls_back_to_empty_string_when_missing_everywhere(self) -> None:
        self.write_config({})

        with self.patch_root_dir(), patch.dict(os.environ, {"OPENROUTER_API_KEY": "env-key"}, clear=False):
            os.environ.pop("OPENROUTER_API_KEY", None)
            api_key = config.get_openrouter_api_key()

        self.assertEqual(api_key, "")

    def test_model_prefers_config_value_over_env(self) -> None:
        self.write_config({"openrouter_model": "config-model"})

        with self.patch_root_dir(), patch.dict(os.environ, {"OPENROUTER_MODEL": "env-model"}, clear=False):
            model = config.get_openrouter_model()

        self.assertEqual(model, "config-model")

    def test_model_uses_env_when_config_empty_or_missing(self) -> None:
        for payload in ({"openrouter_model": ""}, {}):
            with self.subTest(payload=payload):
                self.write_config(payload)

                with self.patch_root_dir(), patch.dict(os.environ, {"OPENROUTER_MODEL": "env-model"}, clear=False):
                    model = config.get_openrouter_model()

                self.assertEqual(model, "env-model")

    def test_model_falls_back_to_empty_string_when_missing_everywhere(self) -> None:
        self.write_config({})

        with self.patch_root_dir(), patch.dict(os.environ, {"OPENROUTER_MODEL": "env-model"}, clear=False):
            os.environ.pop("OPENROUTER_MODEL", None)
            model = config.get_openrouter_model()

        self.assertEqual(model, "")

    def test_base_url_uses_config_or_default(self) -> None:
        test_cases = [
            ({"openrouter_base_url": "https://custom.openrouter.test/api/v1"}, "https://custom.openrouter.test/api/v1"),
            ({"openrouter_base_url": ""}, "https://openrouter.ai/api/v1"),
            ({}, "https://openrouter.ai/api/v1"),
        ]

        for payload, expected in test_cases:
            with self.subTest(payload=payload):
                self.write_config(payload)

                with self.patch_root_dir():
                    base_url = config.get_openrouter_base_url()

                self.assertEqual(base_url, expected)

    def test_image_provider_defaults_to_googleai_studio(self) -> None:
        self.write_config({})

        with self.patch_root_dir():
            provider = config.get_image_provider()

        self.assertEqual(provider, "googleai_studio")

    def test_openrouter_image_models_prefers_config_list(self) -> None:
        self.write_config(
            {
                "openrouter_image_models": [
                    "sourceful/riverflow-v2-fast-preview",
                    "sourceful/riverflow-v2-fast",
                ]
            }
        )

        with self.patch_root_dir(), patch.dict(
            os.environ,
            {"OPENROUTER_IMAGE_MODELS": "ignored/model"},
            clear=False,
        ):
            models = config.get_openrouter_image_models()

        self.assertEqual(
            models,
            [
                "sourceful/riverflow-v2-fast-preview",
                "sourceful/riverflow-v2-fast",
            ],
        )

    def test_openrouter_image_models_use_env_when_config_missing(self) -> None:
        self.write_config({})

        with self.patch_root_dir(), patch.dict(
            os.environ,
            {
                "OPENROUTER_IMAGE_MODELS": " model-a , model-b ,, model-c ",
            },
            clear=False,
        ):
            models = config.get_openrouter_image_models()

        self.assertEqual(models, ["model-a", "model-b", "model-c"])


class VideoMotionConfigTests(ConfigTestCase):
    def test_script_sentence_length_defaults_to_six(self) -> None:
        self.write_config({})

        with self.patch_root_dir():
            sentence_length = config.get_script_sentence_length()

        self.assertEqual(sentence_length, 6)

    def test_video_motion_style_defaults_to_static(self) -> None:
        self.write_config({})

        with self.patch_root_dir():
            style = config.get_video_motion_style()

        self.assertEqual(style, "static")

    def test_video_motion_style_normalizes_cinematic(self) -> None:
        self.write_config({"video_motion_style": "  CiNeMaTiC  "})

        with self.patch_root_dir():
            style = config.get_video_motion_style()

        self.assertEqual(style, "cinematic")

    def test_video_motion_style_invalid_values_fall_back_to_static(self) -> None:
        self.write_config({"video_motion_style": "flashy"})

        with self.patch_root_dir():
            style = config.get_video_motion_style()

        self.assertEqual(style, "static")

    def test_video_zoom_intensity_defaults_to_safe_value(self) -> None:
        self.write_config({})

        with self.patch_root_dir():
            zoom = config.get_video_zoom_intensity()

        self.assertEqual(zoom, 1.12)

    def test_video_zoom_intensity_invalid_or_too_small_falls_back(self) -> None:
        for payload in (
            {"video_zoom_intensity": "abc"},
            {"video_zoom_intensity": 0.9},
            {"video_zoom_intensity": 1.0},
        ):
            with self.subTest(payload=payload):
                self.write_config(payload)

                with self.patch_root_dir():
                    zoom = config.get_video_zoom_intensity()

                self.assertEqual(zoom, 1.12)

    def test_video_pan_enabled_defaults_to_true(self) -> None:
        self.write_config({})

        with self.patch_root_dir():
            pan_enabled = config.get_video_pan_enabled()

        self.assertTrue(pan_enabled)

    def test_video_pan_intensity_defaults_to_safe_value(self) -> None:
        self.write_config({})

        with self.patch_root_dir():
            pan_intensity = config.get_video_pan_intensity()

        self.assertEqual(pan_intensity, 0.03)

    def test_video_pan_intensity_invalid_or_non_positive_falls_back(self) -> None:
        for payload in (
            {"video_pan_intensity": "abc"},
            {"video_pan_intensity": 0},
            {"video_pan_intensity": -0.1},
        ):
            with self.subTest(payload=payload):
                self.write_config(payload)

                with self.patch_root_dir():
                    pan_intensity = config.get_video_pan_intensity()

                self.assertEqual(pan_intensity, 0.03)


if __name__ == "__main__":
    unittest.main()
