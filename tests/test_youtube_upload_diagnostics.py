import importlib
import sys
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
SRC_DIR = __import__("os").path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class YouTubeUploadDiagnosticsTests(unittest.TestCase):
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

    def test_upload_video_logs_failure_step_and_exception(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        browser = Mock()
        youtube.browser = browser

        with patch.object(
            self.youtube_module.YouTube,
            "get_channel_id",
            side_effect=RuntimeError("boom"),
        ), patch.object(self.youtube_module, "error") as error_mock:
            result = youtube.upload_video()

        self.assertFalse(result)
        browser.quit.assert_called_once_with()
        self.assertIsNone(youtube.browser)
        error_mock.assert_called_once()
        message = error_mock.call_args.args[0]
        self.assertIn("Failed to upload YouTube video", message)
        self.assertIn("initialize channel context", message)
        self.assertIn("boom", message)

    def test_get_upload_metadata_textboxes_retries_until_two_inputs_exist(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()

        title_el = Mock()
        description_el = Mock()
        youtube.browser.find_elements.side_effect = [[], [title_el], [title_el, description_el]]

        with patch.object(self.youtube_module.time, "sleep"):
            actual_title, actual_description = youtube._get_upload_metadata_textboxes(
                max_attempts=3,
                delay_seconds=0,
            )

        self.assertIs(actual_title, title_el)
        self.assertIs(actual_description, description_el)

    def test_get_upload_metadata_textboxes_raises_clear_error_after_timeout(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        youtube.browser.find_elements.return_value = []

        with patch.object(self.youtube_module.time, "sleep"):
            with self.assertRaisesRegex(
                RuntimeError,
                "Could not find YouTube metadata textboxes",
            ):
                youtube._get_upload_metadata_textboxes(max_attempts=2, delay_seconds=0)

    def test_upload_video_recreates_browser_when_previous_attempt_closed_it(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = None
        youtube.service = "service"
        youtube.options = "options"

        fresh_browser = Mock()

        with patch.object(
            self.youtube_module.webdriver,
            "Firefox",
            return_value=fresh_browser,
        ) as firefox_mock, patch.object(
            self.youtube_module.YouTube,
            "get_channel_id",
            side_effect=RuntimeError("boom"),
        ), patch.object(self.youtube_module, "error"):
            result = youtube.upload_video()

        self.assertFalse(result)
        firefox_mock.assert_called_once_with(service="service", options="options")
        fresh_browser.quit.assert_called_once_with()
        self.assertIsNone(youtube.browser)


if __name__ == "__main__":
    unittest.main()
