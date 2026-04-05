import importlib
import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

import numpy as np


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


class YouTubeCinematicMotionTests(unittest.TestCase):
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

    def test_build_motion_clip_returns_base_clip_when_motion_disabled(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        base_clip = Mock()
        youtube._build_base_image_clip = Mock(return_value=base_clip)

        with patch.object(self.youtube_module, "get_video_motion_style", return_value="static"):
            actual_clip = youtube._build_motion_clip("frame.png", 3.0, 0)

        self.assertIs(actual_clip, base_clip)

    def test_build_motion_clip_routes_frames_through_cinematic_transform(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        base_clip = Mock()
        transformed_clip = Mock()
        duration_clip = Mock()
        fps_clip = Mock()
        base_clip.fl.return_value = transformed_clip
        transformed_clip.set_duration.return_value = duration_clip
        duration_clip.set_fps.return_value = fps_clip
        youtube._build_base_image_clip = Mock(return_value=base_clip)
        rendered_frame = np.zeros((1920, 1080, 3), dtype=np.uint8)

        with patch.object(self.youtube_module, "get_video_motion_style", return_value="cinematic"), patch.object(
            self.youtube_module, "get_video_zoom_intensity", return_value=1.12
        ), patch.object(self.youtube_module, "get_video_pan_enabled", return_value=True), patch.object(
            self.youtube_module, "get_video_pan_intensity", return_value=0.03
        ), patch.object(
            self.youtube_module,
            "render_motion_frame",
            return_value=rendered_frame,
        ) as render_mock:
            actual_clip = youtube._build_motion_clip("frame.png", 3.0, 1)

            self.assertIs(actual_clip, fps_clip)
            base_clip.fl.assert_called_once()
            self.assertEqual(base_clip.fl.call_args.kwargs["apply_to"], ["mask"])

            transform = base_clip.fl.call_args.args[0]
            frame_getter = Mock(return_value="frame-data")
            actual_frame = transform(frame_getter, 1.5)

            self.assertIs(actual_frame, rendered_frame)
            render_mock.assert_called_once_with(
                "frame-data",
                t=1.5,
                duration=3.0,
                index=1,
                pan_enabled=True,
                pan_intensity=0.03,
                zoom_intensity=1.12,
            )

    def test_build_motion_clip_preserves_requested_duration(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        base_clip = Mock()
        transformed_clip = Mock()
        duration_clip = Mock()
        fps_clip = Mock()
        base_clip.fl.return_value = transformed_clip
        transformed_clip.set_duration.return_value = duration_clip
        duration_clip.set_fps.return_value = fps_clip
        youtube._build_base_image_clip = Mock(return_value=base_clip)

        with patch.object(self.youtube_module, "get_video_motion_style", return_value="cinematic"), patch.object(
            self.youtube_module, "get_video_zoom_intensity", return_value=1.12
        ), patch.object(self.youtube_module, "get_video_pan_enabled", return_value=True), patch.object(
            self.youtube_module, "get_video_pan_intensity", return_value=0.03
        ), patch.object(
            self.youtube_module,
            "render_motion_frame",
            return_value=np.zeros((1920, 1080, 3), dtype=np.uint8),
        ):
            actual_clip = youtube._build_motion_clip("frame.png", 3.5, 0)

        transformed_clip.set_duration.assert_called_once_with(3.5)
        self.assertIs(actual_clip, fps_clip)

    def test_combine_writes_mp4_with_aac_audio_codec(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.tts_path = "/tmp/voice.mp3"
        youtube.images = ["frame-1.png", "frame-2.png"]
        youtube._build_motion_clip = Mock(side_effect=[Mock(duration=1.0), Mock(duration=1.0)])

        tts_clip = Mock()
        tts_clip.duration = 2.0
        tts_clip.set_fps.return_value = tts_clip

        song_clip = Mock()
        song_clip.set_fps.return_value = song_clip
        song_clip.fx.return_value = song_clip

        subtitles_clip = Mock()
        final_clip = Mock()
        final_clip.set_fps.return_value = final_clip
        final_clip.set_audio.return_value = final_clip
        final_clip.set_duration.return_value = final_clip

        expected_path = os.path.join(self.youtube_module.ROOT_DIR, ".mp", "video-id.mp4")

        with patch.object(self.youtube_module, "uuid4", return_value="video-id"), patch.object(
            self.youtube_module, "get_threads", return_value=4
        ), patch.object(
            self.youtube_module, "AudioFileClip", side_effect=[tts_clip, song_clip]
        ), patch.object(
            self.youtube_module, "concatenate_videoclips", return_value=final_clip
        ), patch.object(
            self.youtube_module, "choose_random_song", return_value="/tmp/song.mp3"
        ), patch.object(
            self.youtube_module, "CompositeAudioClip", return_value=Mock()
        ), patch.object(
            youtube, "generate_subtitles", return_value="/tmp/subtitles.srt"
        ), patch.object(
            self.youtube_module, "equalize_subtitles"
        ), patch.object(
            self.youtube_module, "SubtitlesClip", return_value=subtitles_clip
        ), patch.object(
            self.youtube_module, "CompositeVideoClip", return_value=final_clip
        ):
            actual_path = youtube.combine()

        self.assertEqual(actual_path, expected_path)
        final_clip.write_videofile.assert_called_once_with(
            expected_path,
            threads=4,
            audio_codec="aac",
        )

    def test_combine_raises_when_subtitles_fail(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.tts_path = "/tmp/voice.mp3"
        youtube.images = ["frame-1.png", "frame-2.png"]
        youtube._build_motion_clip = Mock(side_effect=[Mock(duration=1.0), Mock(duration=1.0)])

        tts_clip = Mock()
        tts_clip.duration = 2.0
        tts_clip.set_fps.return_value = tts_clip

        song_clip = Mock()
        song_clip.set_fps.return_value = song_clip
        song_clip.fx.return_value = song_clip

        final_clip = Mock()
        final_clip.set_fps.return_value = final_clip
        final_clip.set_audio.return_value = final_clip
        final_clip.set_duration.return_value = final_clip

        with patch.object(self.youtube_module, "uuid4", return_value="video-id"), patch.object(
            self.youtube_module, "get_threads", return_value=4
        ), patch.object(
            self.youtube_module, "AudioFileClip", side_effect=[tts_clip, song_clip]
        ), patch.object(
            self.youtube_module, "concatenate_videoclips", return_value=final_clip
        ), patch.object(
            self.youtube_module, "choose_random_song", return_value="/tmp/song.mp3"
        ), patch.object(
            self.youtube_module, "CompositeAudioClip", return_value=Mock()
        ), patch.object(
            youtube, "generate_subtitles", side_effect=RuntimeError("skip subtitles")
        ):
            with self.assertRaisesRegex(RuntimeError, "Failed to generate subtitles"):
                youtube.combine()

        final_clip.write_videofile.assert_not_called()


if __name__ == "__main__":
    unittest.main()
