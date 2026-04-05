import importlib
import json
import os
import shutil
import sys
import types
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class UtilsCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config_dir = os.path.join(
            ROOT_DIR,
            "tests",
            ".config-fixtures",
            self.__class__.__name__,
            self._testMethodName,
        )
        shutil.rmtree(self.config_dir, ignore_errors=True)
        os.makedirs(os.path.join(self.config_dir, ".mp", "debug-frames"), exist_ok=True)
        self.addCleanup(shutil.rmtree, self.config_dir, True)

        self._modules_to_reset = ["cache", "config", "utils", "status", "srt_equalizer", "termcolor"]
        self._original_modules = {
            module_name: sys.modules.pop(module_name, None)
            for module_name in self._modules_to_reset
        }

        sys.modules["srt_equalizer"] = types.ModuleType("srt_equalizer")
        sys.modules["termcolor"] = types.SimpleNamespace(
            colored=lambda message, *_args, **_kwargs: message
        )

        self.config = importlib.import_module("config")
        self._original_root_dir = self.config.ROOT_DIR
        self.config.ROOT_DIR = self.config_dir
        self.utils = importlib.import_module("utils")
        self.addCleanup(self.restore_modules)

    def restore_modules(self) -> None:
        self.config.ROOT_DIR = self._original_root_dir
        for module_name in self._modules_to_reset:
            sys.modules.pop(module_name, None)
        for module_name, module in self._original_modules.items():
            if module is not None:
                sys.modules[module_name] = module

    def test_rem_temp_files_removes_temp_directories_and_keeps_rendered_videos(self) -> None:
        mp_dir = os.path.join(self.config_dir, ".mp")
        video_path = os.path.join(mp_dir, "final.mp4")
        json_path = os.path.join(mp_dir, "youtube.json")
        image_path = os.path.join(mp_dir, "frame.png")
        debug_dir = os.path.join(mp_dir, "debug-frames")
        debug_file = os.path.join(debug_dir, "frame-start.png")

        with open(video_path, "wb") as handle:
            handle.write(b"video")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "accounts": [
                        {
                            "id": "acct-1",
                            "videos": [
                                {
                                    "path": video_path,
                                    "uploaded": False,
                                }
                            ],
                        }
                    ]
                },
                handle,
                indent=4,
            )
        with open(image_path, "wb") as handle:
            handle.write(b"image")
        with open(debug_file, "wb") as handle:
            handle.write(b"debug")

        self.utils.rem_temp_files()

        self.assertTrue(os.path.exists(video_path))
        self.assertTrue(os.path.exists(json_path))
        self.assertFalse(os.path.exists(image_path))
        self.assertFalse(os.path.exists(debug_dir))


if __name__ == "__main__":
    unittest.main()
