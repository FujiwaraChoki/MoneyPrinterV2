import importlib
import json
import os
import sys
import tempfile
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config


class StartupImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._modules_to_reset = [
            "main",
            "llm_provider",
            "kittentts",
            "ollama",
            "classes.Tts",
            "classes.YouTube",
            "classes.Twitter",
            "classes.AFM",
        ]
        self._original_modules = {}

        for module_name in self._modules_to_reset:
            if module_name in sys.modules:
                self._original_modules[module_name] = sys.modules[module_name]
            sys.modules.pop(module_name, None)

    def test_main_imports_with_example_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(
                os.path.join(ROOT_DIR, "config.example.json"),
                "r",
                encoding="utf-8",
            ) as handle:
                example_config = json.load(handle)

            example_config["imagemagick_path"] = "/opt/homebrew/bin/magick"

            with open(
                os.path.join(temp_dir, "config.json"),
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(example_config, handle)

            original_root_dir = config.ROOT_DIR
            config.ROOT_DIR = temp_dir

            try:
                importlib.import_module("main")
            finally:
                config.ROOT_DIR = original_root_dir
                for module_name in self._modules_to_reset:
                    sys.modules.pop(module_name, None)
                sys.modules.update(self._original_modules)


if __name__ == "__main__":
    unittest.main()
