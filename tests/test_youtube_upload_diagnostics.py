import importlib
import os
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

    def test_upload_video_succeeds_when_short_url_is_not_immediately_available(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        browser = Mock()
        youtube.browser = browser
        youtube.video_path = "/tmp/a685a34.mp4"
        youtube.metadata = {"title": "A title", "description": "A description"}
        youtube.subject = "Storm topic"
        youtube.script = "A script"
        youtube.channel_id = "channel-123"

        file_picker = Mock()
        file_input = Mock()
        file_picker.find_element.return_value = file_input
        radio_buttons = [Mock(), Mock(), Mock()]

        def fake_find_element(by, value):
            if by == self.youtube_module.By.TAG_NAME and value == "ytcp-uploads-file-picker":
                return file_picker
            if by == self.youtube_module.By.NAME:
                return Mock()
            if by == self.youtube_module.By.ID:
                return Mock()
            raise AssertionError(f"Unexpected find_element call: {(by, value)}")

        def fake_find_elements(by, value):
            if by == self.youtube_module.By.XPATH:
                return radio_buttons
            if by == self.youtube_module.By.TAG_NAME and value == "ytcp-video-row":
                first_video = Mock()
                anchor = Mock()
                anchor.get_attribute.return_value = None
                first_video.find_element.return_value = anchor
                return [first_video]
            raise AssertionError(f"Unexpected find_elements call: {(by, value)}")

        browser.find_element.side_effect = fake_find_element
        browser.find_elements.side_effect = fake_find_elements

        with patch.object(
            self.youtube_module.YouTube,
            "get_channel_id",
            side_effect=lambda: setattr(youtube, "channel_id", "channel-123"),
        ), patch.object(
            self.youtube_module, "get_verbose", return_value=False
        ), patch.object(
            self.youtube_module.time, "sleep"
        ), patch.object(
            youtube,
            "_get_upload_metadata_textboxes",
            return_value=(Mock(), Mock()),
        ), patch.object(
            youtube,
            "_set_upload_metadata_text",
        ), patch.object(
            youtube,
            "add_video",
        ) as add_video_mock, patch.object(
            self.youtube_module,
            "warning",
        ) as warning_mock:
            result = youtube.upload_video()

        self.assertTrue(result)
        warning_mock.assert_called()
        self.assertIn("did not return a Short URL yet", warning_mock.call_args.args[0])
        add_video_mock.assert_called_once()
        persisted_video = add_video_mock.call_args.args[0]
        self.assertEqual(persisted_video["title"], "A title")
        self.assertEqual(persisted_video["description"], "A description")
        self.assertEqual(persisted_video["path"], "/tmp/a685a34.mp4")
        self.assertTrue(persisted_video["uploaded"])
        self.assertEqual(persisted_video.get("url", ""), "")
        browser.quit.assert_called_once_with()
        self.assertIsNone(youtube.browser)

    def test_set_upload_audience_selection_uses_not_for_kids_and_verifies_state(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        audience_option = Mock()
        youtube.browser.find_element.return_value = audience_option
        youtube.browser.execute_script.side_effect = [None, True]

        with patch.object(self.youtube_module, "get_is_for_kids", return_value=False), patch.object(
            self.youtube_module.time,
            "sleep",
        ):
            youtube._set_upload_audience_selection()

        youtube.browser.find_element.assert_called_once_with(
            self.youtube_module.By.NAME,
            self.youtube_module.YOUTUBE_NOT_MADE_FOR_KIDS_NAME,
        )
        self.assertEqual(youtube.browser.execute_script.call_count, 2)
        self.assertIs(youtube.browser.execute_script.call_args_list[0].args[1], audience_option)
        self.assertIs(youtube.browser.execute_script.call_args_list[1].args[1], audience_option)

    def test_set_upload_visibility_public_selects_first_option_and_verifies_state(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.browser = Mock()
        public_option = Mock()
        private_option = Mock()
        unlisted_option = Mock()
        youtube.browser.find_elements.return_value = [public_option, private_option, unlisted_option]
        youtube.browser.execute_script.side_effect = [None, True]

        with patch.object(self.youtube_module.time, "sleep"):
            youtube._set_upload_visibility_public()

        youtube.browser.find_elements.assert_called_once_with(
            self.youtube_module.By.XPATH,
            self.youtube_module.YOUTUBE_RADIO_BUTTON_XPATH,
        )
        self.assertEqual(youtube.browser.execute_script.call_count, 2)
        self.assertIs(youtube.browser.execute_script.call_args_list[0].args[1], public_option)
        self.assertIs(youtube.browser.execute_script.call_args_list[1].args[1], public_option)

    def test_upload_video_marks_short_not_for_kids_and_public(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        browser = Mock()
        youtube.browser = browser
        youtube.video_path = "/tmp/a685a34.mp4"
        youtube.metadata = {"title": "A title", "description": "A description"}
        youtube.subject = "Storm topic"
        youtube.script = "A script"
        youtube.channel_id = "channel-123"

        file_picker = Mock()
        file_input = Mock()
        file_picker.find_element.return_value = file_input

        next_button = Mock()
        done_button = Mock()
        made_for_kids_option = Mock()
        not_for_kids_option = Mock()
        public_option = Mock()
        private_option = Mock()
        unlisted_option = Mock()

        def fake_find_element(by, value):
            if by == self.youtube_module.By.TAG_NAME and value == "ytcp-uploads-file-picker":
                return file_picker
            if by == self.youtube_module.By.NAME and value == self.youtube_module.YOUTUBE_MADE_FOR_KIDS_NAME:
                return made_for_kids_option
            if by == self.youtube_module.By.NAME and value == self.youtube_module.YOUTUBE_NOT_MADE_FOR_KIDS_NAME:
                return not_for_kids_option
            if by == self.youtube_module.By.ID and value == self.youtube_module.YOUTUBE_NEXT_BUTTON_ID:
                return next_button
            if by == self.youtube_module.By.ID and value == self.youtube_module.YOUTUBE_DONE_BUTTON_ID:
                return done_button
            raise AssertionError(f"Unexpected find_element call: {(by, value)}")

        def fake_find_elements(by, value):
            if by == self.youtube_module.By.XPATH and value == self.youtube_module.YOUTUBE_RADIO_BUTTON_XPATH:
                return [public_option, private_option, unlisted_option]
            raise AssertionError(f"Unexpected find_elements call: {(by, value)}")

        browser.find_element.side_effect = fake_find_element
        browser.find_elements.side_effect = fake_find_elements

        with patch.object(
            self.youtube_module.YouTube,
            "get_channel_id",
            side_effect=lambda: setattr(youtube, "channel_id", "channel-123"),
        ), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ), patch.object(
            self.youtube_module,
            "get_is_for_kids",
            return_value=False,
        ), patch.object(
            self.youtube_module.time,
            "sleep",
        ), patch.object(
            youtube,
            "_get_upload_metadata_textboxes",
            return_value=(Mock(), Mock()),
        ), patch.object(
            youtube,
            "_set_upload_metadata_text",
        ), patch.object(
            youtube,
            "_fetch_uploaded_short_url",
            return_value="https://youtube.com/shorts/abc123",
        ), patch.object(
            youtube,
            "add_video",
        ):
            result = youtube.upload_video()

        self.assertTrue(result)
        not_for_kids_option.click.assert_called_once_with()
        public_option.click.assert_called_once_with()
        unlisted_option.click.assert_not_called()


if __name__ == "__main__":
    unittest.main()
