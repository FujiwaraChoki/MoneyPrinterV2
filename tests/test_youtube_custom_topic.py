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


def _stub_module(name: str, **attrs) -> None:
    """Registers a lightweight stand-in for a heavy third-party module so that
    classes.YouTube can be imported without Selenium, MoviePy, etc."""
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    module.__all__ = list(attrs.keys())
    sys.modules.setdefault(name, module)


_stub_module("kittentts", KittenTTS=object)
_stub_module("soundfile")
_stub_module("classes.Tts", TTS=object)
_stub_module("ollama", Client=object)
_stub_module("assemblyai")
_stub_module("moviepy")
_stub_module("moviepy.editor")
_stub_module("moviepy.video")
_stub_module("moviepy.video.fx")
_stub_module("moviepy.video.fx.all", crop=lambda *a, **k: None)
_stub_module("moviepy.video.tools")
_stub_module("moviepy.video.tools.subtitles", SubtitlesClip=object)
_stub_module("moviepy.config", change_settings=lambda *a, **k: None)
_stub_module("selenium_firefox")
_stub_module("selenium", webdriver=types.SimpleNamespace(Firefox=object))
_stub_module("selenium.webdriver", Firefox=object)
_stub_module("selenium.webdriver.common")
_stub_module("selenium.webdriver.common.by", By=object)
_stub_module("selenium.webdriver.firefox")
_stub_module("selenium.webdriver.firefox.service", Service=object)
_stub_module("selenium.webdriver.firefox.options", Options=object)
_stub_module("webdriver_manager")
_stub_module("webdriver_manager.firefox", GeckoDriverManager=object)

# Other test modules register throwaway stand-ins for these modules (e.g.
# ``classes.YouTube = object``). Drop them so the real class is imported here.
for _stubbed in ("classes.YouTube", "llm_provider"):
    sys.modules.pop(_stubbed, None)

with patch("config.get_imagemagick_path", return_value="/usr/bin/convert"):
    from classes.YouTube import YouTube


def _make_youtube() -> YouTube:
    """Builds a YouTube instance without running __init__ (which launches
    Firefox) and stubs every pipeline step after topic selection."""
    youtube = YouTube.__new__(YouTube)
    youtube._niche = "Personal finance"
    youtube._language = "English"
    youtube.image_prompts = []
    youtube.generate_topic = Mock(side_effect=lambda: setattr(youtube, "subject", "LLM topic"))
    youtube.generate_script = Mock()
    youtube.generate_metadata = Mock()
    youtube.generate_prompts = Mock()
    youtube.generate_image = Mock()
    youtube.generate_script_to_speech = Mock()
    youtube.combine = Mock(return_value="video.mp4")
    return youtube


class YouTubeCustomTopicTests(unittest.TestCase):
    @patch("classes.YouTube.get_verbose", return_value=False)
    def test_custom_topic_skips_llm_topic_generation(self, _verbose_mock) -> None:
        youtube = _make_youtube()

        youtube.generate_video(Mock(), topic="Why index funds beat stock picking")

        youtube.generate_topic.assert_not_called()
        self.assertEqual(youtube.subject, "Why index funds beat stock picking")
        youtube.generate_script.assert_called_once()
        youtube.combine.assert_called_once()

    @patch("classes.YouTube.get_verbose", return_value=False)
    def test_no_topic_falls_back_to_llm_topic_generation(self, _verbose_mock) -> None:
        youtube = _make_youtube()

        youtube.generate_video(Mock())

        youtube.generate_topic.assert_called_once()
        self.assertEqual(youtube.subject, "LLM topic")

    @patch("classes.YouTube.get_verbose", return_value=False)
    def test_blank_topic_falls_back_to_llm_topic_generation(self, _verbose_mock) -> None:
        youtube = _make_youtube()

        youtube.generate_video(Mock(), topic="   ")

        youtube.generate_topic.assert_called_once()
        self.assertEqual(youtube.subject, "LLM topic")

    def test_set_topic_normalizes_whitespace(self) -> None:
        youtube = _make_youtube()

        stored = youtube.set_topic("  How to   budget\n on a low income  ")

        self.assertEqual(stored, "How to budget on a low income")
        self.assertEqual(youtube.subject, stored)

    def test_set_topic_rejects_empty_topic(self) -> None:
        youtube = _make_youtube()

        with self.assertRaises(ValueError):
            youtube.set_topic("   ")


if __name__ == "__main__":
    unittest.main()
