import importlib
import builtins
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


class StartupImportTests(unittest.TestCase):
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

    def restore_modules(self) -> None:
        config.ROOT_DIR = self._original_root_dir
        for module_name in self._modules_to_reset:
            sys.modules.pop(module_name, None)
        sys.modules.update(self._original_modules)

    def test_main_imports_with_example_config(self) -> None:
        importlib.import_module("main")

    def test_youtube_imports_without_assemblyai_installed(self) -> None:
        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "assemblyai":
                raise ModuleNotFoundError("No module named 'assemblyai'")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=fake_import):
            try:
                importlib.import_module("classes.YouTube")
            except ModuleNotFoundError as exc:
                self.fail(str(exc))


if __name__ == "__main__":
    unittest.main()
