import importlib
import os
import sys
import types
import unittest
from unittest.mock import mock_open
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class VideoMotionConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_modules = {
            "config": sys.modules.pop("config", None),
            "srt_equalizer": sys.modules.get("srt_equalizer"),
            "termcolor": sys.modules.get("termcolor"),
        }
        sys.modules["srt_equalizer"] = types.ModuleType("srt_equalizer")
        sys.modules["termcolor"] = types.SimpleNamespace(
            colored=lambda message, *_args, **_kwargs: message
        )
        self.config = importlib.import_module("config")
        self.addCleanup(self.restore_modules)

    def restore_modules(self) -> None:
        sys.modules.pop("config", None)
        if self._original_modules["config"] is not None:
            sys.modules["config"] = self._original_modules["config"]

        if self._original_modules["srt_equalizer"] is None:
            sys.modules.pop("srt_equalizer", None)
        else:
            sys.modules["srt_equalizer"] = self._original_modules["srt_equalizer"]

        if self._original_modules["termcolor"] is None:
            sys.modules.pop("termcolor", None)
        else:
            sys.modules["termcolor"] = self._original_modules["termcolor"]

    def test_video_zoom_intensity_defaults_to_more_noticeable_value(self) -> None:
        with patch("builtins.open", mock_open(read_data="{}")):
            zoom = self.config.get_video_zoom_intensity()

        self.assertEqual(zoom, 1.12)


if __name__ == "__main__":
    unittest.main()
