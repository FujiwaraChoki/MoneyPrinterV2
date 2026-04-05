import importlib
import sys
import unittest
from unittest.mock import patch


ROOT_DIR = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
SRC_DIR = __import__("os").path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class YouTubeImageProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_modules = {
            "classes.YouTube": sys.modules.pop("classes.YouTube", None),
            "llm_provider": sys.modules.pop("llm_provider", None),
        }
        self.youtube_module = importlib.import_module("classes.YouTube")
        self.addCleanup(self.restore_modules)

    def restore_modules(self) -> None:
        sys.modules.pop("classes.YouTube", None)
        sys.modules.pop("llm_provider", None)
        for module_name, module in self._original_modules.items():
            if module is not None:
                sys.modules[module_name] = module

    def test_generate_image_uses_openrouter_before_google_fallback(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)

        with patch.object(
            self.youtube_module,
            "get_image_provider",
            return_value="openrouter_then_googleai",
        ), patch.object(
            self.youtube_module.YouTube,
            "_sanitize_image_prompt",
            side_effect=lambda text: text,
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_image_openrouter",
            return_value=None,
        ) as openrouter_mock, patch.object(
            self.youtube_module.YouTube,
            "generate_image_nanobanana2",
            return_value="/tmp/google.png",
        ) as google_mock:
            result = youtube.generate_image("prompt")

        self.assertEqual(result, "/tmp/google.png")
        openrouter_mock.assert_called_once_with("prompt")
        google_mock.assert_called_once_with("prompt")

    def test_generate_image_short_circuits_when_openrouter_succeeds(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)

        with patch.object(
            self.youtube_module,
            "get_image_provider",
            return_value="openrouter_then_googleai",
        ), patch.object(
            self.youtube_module.YouTube,
            "_sanitize_image_prompt",
            side_effect=lambda text: text,
        ), patch.object(
            self.youtube_module.YouTube,
            "generate_image_openrouter",
            return_value="/tmp/openrouter.png",
        ) as openrouter_mock, patch.object(
            self.youtube_module.YouTube,
            "generate_image_nanobanana2",
        ) as google_mock:
            result = youtube.generate_image("prompt")

        self.assertEqual(result, "/tmp/openrouter.png")
        openrouter_mock.assert_called_once_with("prompt")
        google_mock.assert_not_called()

    def test_generate_image_sanitizes_prompt_before_openrouter(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)

        with patch.object(
            self.youtube_module,
            "get_image_provider",
            return_value="openrouter_only",
        ), patch.object(
            self.youtube_module.YouTube,
            "_sanitize_image_prompt",
            return_value="safe prompt",
        ) as sanitize_mock, patch.object(
            self.youtube_module.YouTube,
            "generate_image_openrouter",
            return_value="/tmp/openrouter.png",
        ) as openrouter_mock:
            result = youtube.generate_image("risky prompt")

        self.assertEqual(result, "/tmp/openrouter.png")
        sanitize_mock.assert_called_once_with("risky prompt")
        openrouter_mock.assert_called_once_with("safe prompt")


if __name__ == "__main__":
    unittest.main()
