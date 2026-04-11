import os
import sys
import types
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

fake_kittentts = types.ModuleType("kittentts")
fake_kittentts.KittenTTS = object
sys.modules.setdefault("kittentts", fake_kittentts)

fake_ollama = types.ModuleType("ollama")
fake_ollama.Client = object
sys.modules.setdefault("ollama", fake_ollama)

fake_termcolor = types.ModuleType("termcolor")
fake_termcolor.colored = lambda text, *_args, **_kwargs: text
sys.modules.setdefault("termcolor", fake_termcolor)

fake_status = types.ModuleType("status")
fake_status.info = lambda *args, **kwargs: None
fake_status.success = lambda *args, **kwargs: None
fake_status.warning = lambda *args, **kwargs: None
fake_status.error = lambda *args, **kwargs: None
fake_status.question = lambda *_args, **_kwargs: ""
sys.modules.setdefault("status", fake_status)

fake_cache = types.ModuleType("cache")
fake_cache.get_accounts = lambda _provider: []
sys.modules.setdefault("cache", fake_cache)

fake_config = types.ModuleType("config")
fake_config.get_verbose = lambda: False
fake_config.get_post_bridge_config = lambda: {}
sys.modules.setdefault("config", fake_config)

fake_llm_provider = types.ModuleType("llm_provider")
fake_llm_provider.select_model = lambda model: None
sys.modules.setdefault("llm_provider", fake_llm_provider)

fake_tts_module = types.ModuleType("classes.Tts")
fake_tts_module.TTS = object
sys.modules.setdefault("classes.Tts", fake_tts_module)

fake_twitter_module = types.ModuleType("classes.Twitter")
fake_twitter_module.Twitter = object
sys.modules.setdefault("classes.Twitter", fake_twitter_module)

fake_youtube_module = types.ModuleType("classes.YouTube")
fake_youtube_module.YouTube = object
sys.modules.setdefault("classes.YouTube", fake_youtube_module)

import cron


class CronPostBridgeTests(unittest.TestCase):
    @patch("cron.maybe_crosspost_youtube_short")
    @patch("cron.YouTube")
    @patch("cron.TTS")
    @patch("cron.get_accounts")
    @patch("cron.select_model")
    @patch("cron.get_verbose")
    def test_crosspost_does_not_run_when_youtube_upload_fails(
        self,
        get_verbose_mock,
        select_model_mock,
        get_accounts_mock,
        tts_cls_mock,
        youtube_cls_mock,
        crosspost_mock,
    ) -> None:
        get_verbose_mock.return_value = False
        get_accounts_mock.return_value = [
            {
                "id": "yt-1",
                "nickname": "Channel",
                "firefox_profile": "/tmp/profile",
                "niche": "finance",
                "language": "English",
            }
        ]
        youtube_instance = youtube_cls_mock.return_value
        youtube_instance.upload_video.return_value = False
        youtube_instance.video_path = "/tmp/video.mp4"
        youtube_instance.metadata = {"title": "Title"}

        with patch.object(
            sys,
            "argv",
            ["cron.py", "youtube", "yt-1", "llama3.2:3b"],
        ):
            cron.main()

        select_model_mock.assert_called_once_with("llama3.2:3b")
        tts_cls_mock.assert_called_once()
        youtube_instance.generate_video.assert_called_once()
        youtube_instance.upload_video.assert_called_once()
        crosspost_mock.assert_not_called()

    @patch("cron.Twitter")
    @patch("cron.get_accounts")
    @patch("cron.select_model")
    @patch("cron.get_verbose")
    @patch("cron.error")
    def test_twitter_missing_account_id_exits_with_error(
        self,
        error_mock,
        get_verbose_mock,
        select_model_mock,
        get_accounts_mock,
        twitter_cls_mock,
    ) -> None:
        get_verbose_mock.return_value = False
        get_accounts_mock.return_value = [{"id": "twitter-1"}]

        with patch.object(
            sys,
            "argv",
            ["cron.py", "twitter", "missing-id", "llama3.2:3b"],
        ), patch("cron.sys.exit", side_effect=SystemExit(1)) as exit_mock:
            with self.assertRaises(SystemExit):
                cron.main()

        select_model_mock.assert_called_once_with("llama3.2:3b")
        error_mock.assert_called_once_with('Twitter account UUID "missing-id" was not found in cache.')
        exit_mock.assert_called_once_with(1)
        twitter_cls_mock.assert_not_called()

    @patch("cron.YouTube")
    @patch("cron.TTS")
    @patch("cron.get_accounts")
    @patch("cron.select_model")
    @patch("cron.get_verbose")
    @patch("cron.error")
    def test_youtube_missing_account_id_exits_with_error(
        self,
        error_mock,
        get_verbose_mock,
        select_model_mock,
        get_accounts_mock,
        tts_cls_mock,
        youtube_cls_mock,
    ) -> None:
        get_verbose_mock.return_value = False
        get_accounts_mock.return_value = [{"id": "youtube-1"}]

        with patch.object(
            sys,
            "argv",
            ["cron.py", "youtube", "missing-id", "llama3.2:3b"],
        ), patch("cron.sys.exit", side_effect=SystemExit(1)) as exit_mock:
            with self.assertRaises(SystemExit):
                cron.main()

        select_model_mock.assert_called_once_with("llama3.2:3b")
        error_mock.assert_called_once_with('YouTube account UUID "missing-id" was not found in cache.')
        exit_mock.assert_called_once_with(1)
        tts_cls_mock.assert_called_once()
        youtube_cls_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
