import importlib
import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def _module(name: str, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _gecko_driver_manager(*_args, **_kwargs):
    manager = Mock()
    manager.install.return_value = "geckodriver"
    return manager


class YouTubeUploadTextInputTests(unittest.TestCase):
    def setUp(self) -> None:
        managed_modules = [
            "classes.YouTube",
            "classes.Tts",
            "llm_provider",
            "assemblyai",
            "srt_equalizer",
            "termcolor",
            "selenium",
            "selenium.webdriver",
            "selenium.webdriver.common",
            "selenium.webdriver.common.by",
            "selenium.webdriver.common.keys",
            "selenium.webdriver.firefox",
            "selenium.webdriver.firefox.service",
            "selenium.webdriver.firefox.options",
            "webdriver_manager",
            "webdriver_manager.firefox",
        ]
        self._original_modules = {
            module_name: sys.modules.pop(module_name, None)
            for module_name in managed_modules
        }

        sys.modules.update(
            {
                "classes.Tts": _module("classes.Tts", TTS=object),
                "assemblyai": _module("assemblyai"),
                "srt_equalizer": _module("srt_equalizer"),
                "termcolor": _module(
                    "termcolor",
                    colored=lambda message, *_args, **_kwargs: message,
                ),
                "selenium": _module("selenium", webdriver=Mock()),
                "selenium.webdriver": _module("selenium.webdriver"),
                "selenium.webdriver.common": _module("selenium.webdriver.common"),
                "selenium.webdriver.common.by": _module(
                    "selenium.webdriver.common.by",
                    By=SimpleNamespace(ID="id", NAME="name", XPATH="xpath", TAG_NAME="tag"),
                ),
                "selenium.webdriver.common.keys": _module(
                    "selenium.webdriver.common.keys",
                    Keys=SimpleNamespace(COMMAND="<COMMAND>", CONTROL="<CONTROL>", BACKSPACE="<BACKSPACE>"),
                ),
                "selenium.webdriver.firefox": _module("selenium.webdriver.firefox"),
                "selenium.webdriver.firefox.service": _module(
                    "selenium.webdriver.firefox.service",
                    Service=object,
                ),
                "selenium.webdriver.firefox.options": _module(
                    "selenium.webdriver.firefox.options",
                    Options=object,
                ),
                "webdriver_manager": _module("webdriver_manager"),
                "webdriver_manager.firefox": _module(
                    "webdriver_manager.firefox",
                    GeckoDriverManager=_gecko_driver_manager,
                ),
            }
        )

        self.youtube_module = importlib.import_module("classes.YouTube")
        self.addCleanup(self.restore_modules)

    def restore_modules(self) -> None:
        for module_name in [
            "classes.YouTube",
            "classes.Tts",
            "llm_provider",
            "assemblyai",
            "srt_equalizer",
            "termcolor",
            "selenium",
            "selenium.webdriver",
            "selenium.webdriver.common",
            "selenium.webdriver.common.by",
            "selenium.webdriver.common.keys",
            "selenium.webdriver.firefox",
            "selenium.webdriver.firefox.service",
            "selenium.webdriver.firefox.options",
            "webdriver_manager",
            "webdriver_manager.firefox",
        ]:
            sys.modules.pop(module_name, None)

        for module_name, module in self._original_modules.items():
            if module is not None:
                sys.modules[module_name] = module

    def test_set_upload_metadata_text_uses_browser_script_to_replace_text(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        youtube.browser.execute_script.side_effect = [None, "New title"]
        text_element = Mock()

        with patch.object(self.youtube_module.time, "sleep"):
            youtube._set_upload_metadata_text(text_element, "New title")

        self.assertEqual(youtube.browser.execute_script.call_count, 2)
        update_args = youtube.browser.execute_script.call_args_list[0].args
        self.assertEqual(len(update_args), 3)
        update_script, updated_element, updated_value = update_args
        self.assertIn("textContent", update_script)
        self.assertIn("dispatchEvent", update_script)
        self.assertIs(updated_element, text_element)
        self.assertEqual(updated_value, "New title")
        verify_script, verify_element = youtube.browser.execute_script.call_args_list[1].args
        self.assertIn("return", verify_script)
        self.assertIs(verify_element, text_element)
        text_element.click.assert_not_called()
        text_element.clear.assert_not_called()
        text_element.send_keys.assert_not_called()

    def test_set_upload_metadata_text_raises_when_studio_keeps_old_value(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        youtube.browser.execute_script.side_effect = [None, "a685a34.mp4"]
        text_element = Mock()

        with patch.object(self.youtube_module.time, "sleep"):
            with self.assertRaisesRegex(
                RuntimeError,
                "Failed to apply YouTube metadata text",
            ):
                youtube._set_upload_metadata_text(text_element, "New title")

    def test_upload_video_uses_metadata_text_helper_for_title(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        youtube.video_path = "/tmp/a685a34.mp4"
        youtube.metadata = {"title": "A title", "description": "A description"}

        file_picker = Mock()
        file_input = Mock()
        file_picker.find_element.return_value = file_input
        youtube.browser.find_element.return_value = file_picker
        title_el = Mock()
        description_el = Mock()

        with patch.object(self.youtube_module.YouTube, "get_channel_id"), patch.object(
            self.youtube_module, "get_verbose", return_value=False
        ), patch.object(
            self.youtube_module.time, "sleep"
        ), patch.object(
            youtube,
            "_get_upload_metadata_textboxes",
            return_value=(title_el, description_el),
        ), patch.object(
            youtube,
            "_set_upload_metadata_text",
            side_effect=RuntimeError("stop after title"),
        ) as set_text_mock, patch.object(
            self.youtube_module, "error"
        ) as error_mock:
            result = youtube.upload_video()

        self.assertFalse(result)
        set_text_mock.assert_called_once_with(
            title_el,
            "A title",
            focus_delay_seconds=1,
        )
        error_message = error_mock.call_args.args[0]
        self.assertIn("set video title", error_message)

    def test_upload_video_disables_retry_after_file_attach_failure(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        youtube.video_path = "/tmp/a685a34.mp4"
        youtube.metadata = {"title": "A title", "description": "A description"}

        file_picker = Mock()
        file_input = Mock()
        file_picker.find_element.return_value = file_input
        youtube.browser.find_element.return_value = file_picker
        title_el = Mock()
        description_el = Mock()

        with patch.object(self.youtube_module.YouTube, "get_channel_id"), patch.object(
            self.youtube_module, "get_verbose", return_value=False
        ), patch.object(
            self.youtube_module.time, "sleep"
        ), patch.object(
            youtube,
            "_get_upload_metadata_textboxes",
            return_value=(title_el, description_el),
        ), patch.object(
            youtube,
            "_set_upload_metadata_text",
            side_effect=RuntimeError("stop after title"),
        ), patch.object(
            self.youtube_module, "error"
        ):
            result = youtube.upload_video()

        self.assertFalse(result)
        self.assertFalse(youtube.last_upload_retry_allowed)


if __name__ == "__main__":
    unittest.main()
