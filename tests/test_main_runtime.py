import importlib
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


class MainRuntimeTests(unittest.TestCase):
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

        self._modules_to_reset = [
            "main",
            "art",
            "cache",
            "utils",
            "status",
            "llm_provider",
            "kittentts",
            "classes.Tts",
            "classes.YouTube",
            "classes.Twitter",
            "classes.Outreach",
            "classes.AFM",
            "post_bridge_integration",
        ]
        self._original_modules = {}

        for module_name in self._modules_to_reset:
            if module_name in sys.modules:
                self._original_modules[module_name] = sys.modules[module_name]
            sys.modules.pop(module_name, None)

        self._original_root_dir = config.ROOT_DIR
        config.ROOT_DIR = self.config_dir
        self.addCleanup(self.restore_modules)

        self.main = importlib.import_module("main")

    def restore_modules(self) -> None:
        config.ROOT_DIR = self._original_root_dir
        for module_name in self._modules_to_reset:
            sys.modules.pop(module_name, None)
        sys.modules.update(self._original_modules)

    def test_bootstrap_runtime_selects_configured_openrouter_model(self) -> None:
        with patch.object(self.main, "fetch_songs") as fetch_songs_mock, patch.object(
            self.main,
            "get_openrouter_model",
            return_value="google/gemini-2.5-flash",
        ), patch.object(
            self.main,
            "get_openrouter_api_key",
            return_value="test-openrouter-key",
        ), patch.object(
            self.main,
            "select_model",
        ) as select_model_mock, patch.object(
            self.main,
            "success",
        ) as success_mock:
            self.main.bootstrap_runtime()

        fetch_songs_mock.assert_called_once_with()
        select_model_mock.assert_called_once_with("google/gemini-2.5-flash")
        success_mock.assert_called_once_with(
            "Using configured OpenRouter model: google/gemini-2.5-flash"
        )

    def test_bootstrap_runtime_exits_when_openrouter_api_key_missing(self) -> None:
        with patch.object(self.main, "fetch_songs") as fetch_songs_mock, patch.object(
            self.main,
            "get_openrouter_model",
            return_value="google/gemini-2.5-flash",
        ), patch.object(
            self.main,
            "get_openrouter_api_key",
            return_value="",
        ), patch.object(
            self.main,
            "error",
        ) as error_mock, patch.object(
            self.main,
            "select_model",
        ) as select_model_mock:
            with self.assertRaises(SystemExit) as raised:
                self.main.bootstrap_runtime()

        self.assertEqual(raised.exception.code, 1)
        fetch_songs_mock.assert_called_once_with()
        error_mock.assert_called_once_with(
            "No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY."
        )
        select_model_mock.assert_not_called()

    def test_bootstrap_runtime_exits_when_openrouter_model_missing(self) -> None:
        with patch.object(self.main, "fetch_songs") as fetch_songs_mock, patch.object(
            self.main,
            "get_openrouter_model",
            return_value="",
        ), patch.object(
            self.main,
            "get_openrouter_api_key",
            return_value="test-openrouter-key",
        ), patch.object(
            self.main,
            "error",
        ) as error_mock, patch.object(
            self.main,
            "select_model",
        ) as select_model_mock:
            with self.assertRaises(SystemExit) as raised:
                self.main.bootstrap_runtime()

        self.assertEqual(raised.exception.code, 1)
        fetch_songs_mock.assert_called_once_with()
        error_mock.assert_called_once_with(
            "No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL."
        )
        select_model_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
