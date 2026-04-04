import os
import sys
import types
import unittest
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
    @patch("cron.publish_video")
    @patch("cron.YouTube")
    @patch("cron.TTS")
    @patch("cron.get_video_publishing_config")
    @patch("cron.ensure_post_bridge_publishing_ready", return_value=True)
    @patch("cron.select_model")
    @patch("cron.get_verbose")
    def test_publish_mode_generates_and_publishes_video(
        self,
        get_verbose_mock,
        select_model_mock,
        _ensure_ready_mock,
        get_video_config_mock,
        tts_cls_mock,
        youtube_cls_mock,
        publish_video_mock,
    ) -> None:
        get_verbose_mock.return_value = False
        get_video_config_mock.return_value = {
            "profile_name": "Default Publisher",
            "niche": "finance",
            "language": "English",
        }
        youtube_instance = youtube_cls_mock.return_value
        youtube_instance.video_path = "/tmp/video.mp4"
        youtube_instance.metadata = {
            "title": "Title",
            "description": "Description",
        }
        publish_video_mock.return_value = True

        with patch.object(sys, "argv", ["cron.py", "publish", "llama3.2:3b"]):
            cron.main()

        select_model_mock.assert_called_once_with("llama3.2:3b")
        tts_cls_mock.assert_called_once()
        youtube_instance.generate_video.assert_called_once()
        publish_video_mock.assert_called_once_with(
            video_path="/tmp/video.mp4",
            title="Title",
            description="Description",
            interactive=False,
        )

    def test_legacy_youtube_mode_exits_with_migration_message(self) -> None:
        with patch.object(sys, "argv", ["cron.py", "youtube", "llama3.2:3b"]), patch(
            "cron.get_ollama_model",
            return_value="llama3.2:3b",
        ), patch("cron.select_model"):
            with self.assertRaises(SystemExit) as raised:
                cron.main()

        self.assertEqual(raised.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
