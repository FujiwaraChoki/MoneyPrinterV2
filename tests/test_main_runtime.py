import importlib
import json
import os
import shutil
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config


class MainRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config_dir = os.path.join(
            ROOT_DIR,
            "tests",
            ".config-fixtures",
            self.__class__.__name__,
            self._testMethodName,
        )
        shutil.rmtree(self.config_dir, ignore_errors=True)
        os.makedirs(self.config_dir, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.config_dir, True)

        with open(
            os.path.join(ROOT_DIR, "config.example.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            example_config = json.load(handle)

        example_config["imagemagick_path"] = "/opt/homebrew/bin/magick"

        with open(
            os.path.join(self.config_dir, "config.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(example_config, handle)

        self._modules_to_reset = [
            "main",
            "art",
            "cache",
            "utils",
            "status",
            "llm_provider",
            "kittentts",
            "classes.Tts",
            "classes.YouTube",
            "classes.Twitter",
            "classes.Outreach",
            "classes.AFM",
            "post_bridge_integration",
        ]
        self._original_modules = {}

        for module_name in self._modules_to_reset:
            if module_name in sys.modules:
                self._original_modules[module_name] = sys.modules[module_name]
            sys.modules.pop(module_name, None)

        self._original_root_dir = config.ROOT_DIR
        config.ROOT_DIR = self.config_dir
        self.addCleanup(self.restore_modules)

        self.main = importlib.import_module("main")

    def restore_modules(self) -> None:
        config.ROOT_DIR = self._original_root_dir
        for module_name in self._modules_to_reset:
            sys.modules.pop(module_name, None)
        sys.modules.update(self._original_modules)

    def test_bootstrap_runtime_selects_configured_openrouter_model(self) -> None:
        with patch.object(self.main, "fetch_songs") as fetch_songs_mock, patch.object(
            self.main,
            "get_openrouter_model",
            return_value="google/gemini-2.5-flash",
        ), patch.object(
            self.main,
            "get_openrouter_api_key",
            return_value="test-openrouter-key",
        ), patch.object(
            self.main,
            "select_model",
        ) as select_model_mock, patch.object(
            self.main,
            "success",
        ) as success_mock:
            self.main.bootstrap_runtime()

        fetch_songs_mock.assert_called_once_with()
        select_model_mock.assert_called_once_with("google/gemini-2.5-flash")
        success_mock.assert_called_once_with(
            "Using configured OpenRouter model: google/gemini-2.5-flash"
        )

    def test_bootstrap_runtime_exits_when_openrouter_api_key_missing(self) -> None:
        with patch.object(self.main, "fetch_songs") as fetch_songs_mock, patch.object(
            self.main,
            "get_openrouter_model",
            return_value="google/gemini-2.5-flash",
        ), patch.object(
            self.main,
            "get_openrouter_api_key",
            return_value="",
        ), patch.object(
            self.main,
            "error",
        ) as error_mock, patch.object(
            self.main,
            "select_model",
        ) as select_model_mock:
            with self.assertRaises(SystemExit) as raised:
                self.main.bootstrap_runtime()

        self.assertEqual(raised.exception.code, 1)
        fetch_songs_mock.assert_called_once_with()
        error_mock.assert_called_once_with(
            "No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY."
        )
        select_model_mock.assert_not_called()

    def test_bootstrap_runtime_exits_when_openrouter_model_missing(self) -> None:
        with patch.object(self.main, "fetch_songs") as fetch_songs_mock, patch.object(
            self.main,
            "get_openrouter_model",
            return_value="",
        ), patch.object(
            self.main,
            "get_openrouter_api_key",
            return_value="test-openrouter-key",
        ), patch.object(
            self.main,
            "error",
        ) as error_mock, patch.object(
            self.main,
            "select_model",
        ) as select_model_mock:
            with self.assertRaises(SystemExit) as raised:
                self.main.bootstrap_runtime()

        self.assertEqual(raised.exception.code, 1)
        fetch_songs_mock.assert_called_once_with()
        error_mock.assert_called_once_with(
            "No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL."
        )
        select_model_mock.assert_not_called()

    def test_build_cron_command_uses_default_two_arg_path(self) -> None:
        self.assertEqual(
            self.main.build_cron_command("youtube", "yt-1"),
            [
                sys.executable,
                os.path.join(self.main.ROOT_DIR, "src", "cron.py"),
                "youtube",
                "yt-1",
            ],
        )

    def test_build_cron_command_appends_override_model_when_provided(self) -> None:
        self.assertEqual(
            self.main.build_cron_command("twitter", "tw-1", "override/model"),
            [
                sys.executable,
                os.path.join(self.main.ROOT_DIR, "src", "cron.py"),
                "twitter",
                "tw-1",
                "override/model",
            ],
        )

    def test_build_crontab_block_uses_daily_schedule_and_log_file(self) -> None:
        block = self.main.build_crontab_block("youtube", "yt-1", 1)

        self.assertIn("# MONEYPRINTER_V2 youtube yt-1 BEGIN", block)
        self.assertIn("0 10 * * *", block)
        self.assertIn("PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", block)
        self.assertIn("export PATH", block)
        self.assertIn(
            os.path.join(self.main.ROOT_DIR, "src", "cron.py"),
            block,
        )
        self.assertIn(
            os.path.join(self.main.ROOT_DIR, ".mp", "cron-youtube-yt-1.log"),
            block,
        )
        self.assertIn("# MONEYPRINTER_V2 youtube yt-1 END", block)

    def test_build_crontab_block_accepts_custom_schedule_expressions(self) -> None:
        block = self.main.build_crontab_block(
            "youtube",
            "yt-1",
            ["15 9 * * 1,3,5", "45 16 * * 1,3,5"],
        )

        self.assertIn("15 9 * * 1,3,5", block)
        self.assertIn("45 16 * * 1,3,5", block)

    def test_build_custom_cron_schedules_supports_custom_days_and_times(self) -> None:
        self.assertEqual(
            self.main.build_custom_cron_schedules([1, 3, 5], ["09:15", "16:45"]),
            ["15 9 * * 1,3,5", "45 16 * * 1,3,5"],
        )

    def test_merge_crontab_block_replaces_existing_job_block_only(self) -> None:
        existing = "\n".join(
            [
                "MAILTO=\"\"",
                "# MONEYPRINTER_V2 youtube yt-1 BEGIN",
                "old youtube line",
                "# MONEYPRINTER_V2 youtube yt-1 END",
                "15 9 * * * echo keep-me",
            ]
        )

        merged = self.main.merge_crontab_block(
            existing,
            "youtube",
            "yt-1",
            "# MONEYPRINTER_V2 youtube yt-1 BEGIN\nnew youtube line\n# MONEYPRINTER_V2 youtube yt-1 END",
        )

        self.assertIn("MAILTO=\"\"", merged)
        self.assertIn("15 9 * * * echo keep-me", merged)
        self.assertIn("new youtube line", merged)
        self.assertNotIn("old youtube line", merged)

    def test_install_cron_job_treats_missing_crontab_as_empty(self) -> None:
        missing = subprocess.CompletedProcess(
            ["crontab", "-l"],
            1,
            stdout="",
            stderr="no crontab for cris\n",
        )
        written = subprocess.CompletedProcess(
            ["crontab", "-"],
            0,
            stdout="",
            stderr="",
        )

        with patch.object(
            self.main.subprocess,
            "run",
            side_effect=[missing, written],
        ) as run_mock:
            self.main.install_cron_job("youtube", "yt-1", 1)

        self.assertEqual(run_mock.call_count, 2)
        write_call = run_mock.call_args_list[1]
        self.assertEqual(write_call.args[0], ["crontab", "-"])
        self.assertIn("0 10 * * *", write_call.kwargs["input"])
        self.assertIn("youtube yt-1", write_call.kwargs["input"])

    def test_main_guides_cron_setup_with_custom_days_and_times(self) -> None:
        youtube_instance = Mock()

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["3", "4"])

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Choose schedule days" in message:
                return "3"
            if "Enter weekdays" in message:
                return "1,3,5"
            if "Enter time(s)" in message:
                return "09:15, 16:45"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "install_cron_job",
        ) as install_cron_job_mock:
            self.main.main()

        install_cron_job_mock.assert_called_once_with(
            "youtube",
            "yt-1",
            ["15 9 * * 1,3,5", "45 16 * * 1,3,5"],
        )

    def test_install_cron_job_raises_clear_error_when_crontab_binary_missing(self) -> None:
        with patch.object(
            self.main.subprocess,
            "run",
            side_effect=FileNotFoundError("No such file or directory: 'crontab'"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "crontab command is not available",
            ):
                self.main.install_cron_job("youtube", "yt-1", 1)

    def test_main_retries_failed_youtube_upload_with_same_video(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.side_effect = [False, True]
        youtube_instance.metadata = {"title": "A title"}
        youtube_instance.video_path = "/tmp/generated-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["1", "4"])

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Do you want to upload this video to YouTube" in message:
                return "yes"
            if "Do you want to cross-post one of these Shorts" in message:
                return "no"
            if "Retry YouTube upload with the same video" in message:
                return "yes"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
        ) as crosspost_mock:
            self.main.main()

        self.assertEqual(youtube_instance.upload_video.call_count, 2)
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/generated-short.mp4",
            title="A title",
            interactive=True,
            return_details=True,
        )

    def test_main_stops_retrying_youtube_upload_when_user_declines(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.return_value = False
        youtube_instance.metadata = {"title": "A title"}
        youtube_instance.video_path = "/tmp/generated-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["1", "4"])

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Do you want to upload this video to YouTube" in message:
                return "yes"
            if "Do you want to cross-post one of these Shorts" in message:
                return "no"
            if "Retry YouTube upload with the same video" in message:
                return "no"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
        ) as crosspost_mock:
            self.main.main()

        youtube_instance.upload_video.assert_called_once_with()
        crosspost_mock.assert_not_called()

    def test_main_skips_retry_prompt_after_upload_has_started(self) -> None:
        youtube_instance = Mock()
        youtube_instance.metadata = {"title": "A title"}
        youtube_instance.video_path = "/tmp/generated-short.mp4"

        def fail_after_attach():
            youtube_instance.last_upload_retry_allowed = False
            return False

        youtube_instance.upload_video.side_effect = fail_after_attach

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["1", "4"])

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Do you want to upload this video to YouTube" in message:
                return "yes"
            if "Do you want to cross-post one of these Shorts" in message:
                return "no"
            if "Retry YouTube upload with the same video" in message:
                raise AssertionError("Retry prompt should not be shown after upload started")
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "warning",
        ) as warning_mock, patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
        ) as crosspost_mock:
            self.main.main()

        youtube_instance.upload_video.assert_called_once_with()
        crosspost_mock.assert_not_called()
        self.assertIn("may already exist", warning_mock.call_args_list[-1].args[0])

    def test_main_retries_upload_for_selected_cached_short(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.return_value = True
        youtube_instance.metadata = {"title": "Cached title"}
        youtube_instance.video_path = "/tmp/cached-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "topic": "Storm topic",
                "script": "A script",
                "uploaded": False,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "yes"
            if "Enter the short number to publish" in message:
                return "1"
            if "Do you want to upload this video to YouTube" in message:
                return "yes"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "info",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch("main.os.path.exists", return_value=True):
            self.main.main()

        youtube_instance.load_cached_video.assert_called_once_with(cached_videos[0])
        youtube_instance.upload_video.assert_called_once_with()
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/cached-short.mp4",
            title="Cached title",
            interactive=True,
            return_details=True,
        )

    def test_main_skips_auto_crosspost_when_cached_short_already_crossposted(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.return_value = True
        youtube_instance.metadata = {"title": "Cached title"}
        youtube_instance.video_path = "/tmp/cached-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "topic": "Storm topic",
                "script": "A script",
                "uploaded": True,
                "crossposts": {
                    "tiktok": {"status": "success", "post_id": "post-123"},
                },
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "info",
        ) as info_mock, patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_crosspost_result",
        ) as record_crosspost_result_mock, patch("main.os.path.exists", return_value=True):
            self.main.main()

        youtube_instance.load_cached_video.assert_called_once_with(cached_videos[0])
        youtube_instance.upload_video.assert_not_called()
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/cached-short.mp4",
            title="Cached title",
            interactive=True,
            return_details=True,
            excluded_platforms=["youtube", "tiktok"],
        )
        record_crosspost_result_mock.assert_not_called()

    def test_main_shows_cached_short_metadata_preview_before_retry_upload(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.return_value = True
        youtube_instance.metadata = {"title": "Cached title"}
        youtube_instance.video_path = "/tmp/cached-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description for preview text",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "topic": "Storm topic",
                "script": "A script",
                "uploaded": True,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "yes"
            if "Enter the short number to publish" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "info",
        ) as info_mock, patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value=None,
        ), patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch("main.os.path.exists", return_value=True):
            self.main.main()

        preview_messages = [call.args[0] for call in info_mock.call_args_list if call.args]
        self.assertTrue(any("Selected Short title: Cached title" in message for message in preview_messages))
        self.assertTrue(any("Cached description for preview text" in message for message in preview_messages))

    def test_main_crossposts_selected_cached_short(self) -> None:
        youtube_instance = Mock()
        youtube_instance.video_path = "/tmp/cached-short.mp4"
        youtube_instance.metadata = {"title": "Cached title", "description": "Cached description"}
        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "uploaded": True,
                "crossposts": {"tiktok": {"status": "success", "post_id": "old-post"}},
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={
                "posted": True,
                "platforms": {
                    "tiktok": {"status": "success", "post_id": "post-123"},
                    "instagram": {"status": "success", "post_id": "post-123"},
                },
            },
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_crosspost_result",
        ) as record_crosspost_result_mock, patch("main.os.path.exists", return_value=True):
            self.main.main()

        crosspost_mock.assert_called_once_with(
            video_path="/tmp/cached-short.mp4",
            title="Cached title",
            description="Cached description",
            interactive=True,
            return_details=True,
            excluded_platforms=["youtube", "tiktok"],
        )
        record_crosspost_result_mock.assert_called_once_with(
            cached_videos[0],
            {
                "posted": True,
                "platforms": {
                    "tiktok": {"status": "success", "post_id": "post-123"},
                    "instagram": {"status": "success", "post_id": "post-123"},
                },
            },
        )

    def test_cached_short_prompts_accept_single_letter_yes(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.return_value = True
        youtube_instance.metadata = {"title": "Cached title"}
        youtube_instance.video_path = "/tmp/cached-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "topic": "Storm topic",
                "script": "A script",
                "uploaded": True,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "y"
            if "Enter the short number to publish" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            side_effect=[
                {"posted": False, "platforms": {}},
                {"posted": True, "platforms": {"tiktok": {"status": "success", "post_id": "post-123"}}},
            ],
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_crosspost_result",
        ), patch("main.os.path.exists", return_value=True):
            self.main.main()

        youtube_instance.load_cached_video.assert_called_once_with(cached_videos[0])
        youtube_instance.upload_video.assert_not_called()
        self.assertEqual(crosspost_mock.call_count, 1)

    def test_cached_short_retry_prompt_accepts_direct_short_number(self) -> None:
        youtube_instance = Mock()
        youtube_instance.upload_video.return_value = True
        youtube_instance.metadata = {"title": "Cached title"}
        youtube_instance.video_path = "/tmp/cached-short.mp4"

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "topic": "Storm topic",
                "script": "A script",
                "uploaded": True,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={"posted": False, "platforms": {}},
        ), patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_crosspost_result",
        ), patch("main.os.path.exists", return_value=True):
            self.main.main()

        youtube_instance.load_cached_video.assert_called_once_with(cached_videos[0])
        youtube_instance.upload_video.assert_not_called()

    def test_cached_short_crosspost_prompt_accepts_direct_short_number(self) -> None:
        youtube_instance = Mock()
        youtube_instance.video_path = "/tmp/cached-short.mp4"
        youtube_instance.metadata = {"title": "Cached title", "description": "Cached description"}
        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "uploaded": True,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={"posted": True, "platforms": {"tiktok": {"status": "success", "post_id": "post-123"}}},
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_crosspost_result",
        ), patch("main.os.path.exists", return_value=True):
            self.main.main()

        crosspost_mock.assert_called_once_with(
            video_path="/tmp/cached-short.mp4",
            title="Cached title",
            description="Cached description",
            interactive=True,
            return_details=True,
            excluded_platforms=["youtube"],
        )

    def test_main_warns_when_selected_cached_short_file_is_missing(self) -> None:
        youtube_instance = Mock()

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Missing file",
                "description": "Cached description",
                "path": "/tmp/missing-short.mp4",
                "date": "2026-04-05 10:00:00",
                "uploaded": False,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "yes"
            if "Enter the short number to publish" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "warning",
        ) as warning_mock, patch("main.os.path.exists", return_value=False):
            self.main.main()

        youtube_instance.load_cached_video.assert_not_called()
        youtube_instance.upload_video.assert_not_called()
        self.assertIn("no longer exists", warning_mock.call_args_list[-1].args[0].lower())

    def test_maybe_upload_youtube_video_uses_post_bridge_as_primary_youtube_publisher(self) -> None:
        youtube_instance = Mock()
        youtube_instance.video_path = "/tmp/generated-short.mp4"
        youtube_instance.subject = "Storm topic"
        youtube_instance.script = "A script"
        youtube_instance.metadata = {
            "title": "A title",
            "description": "A description",
        }

        with patch.object(
            self.main,
            "question",
            return_value="yes",
        ), patch.object(
            self.main,
            "get_post_bridge_config",
            return_value={
                "enabled": True,
                "api_key": "token",
                "platforms": ["youtube", "tiktok"],
                "account_ids": [12, 34],
                "auto_crosspost": False,
            },
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={
                "posted": True,
                "platforms": {
                    "youtube": {"status": "success", "post_id": "post-yt"},
                    "tiktok": {"status": "success", "post_id": "post-tt"},
                },
            },
        ) as crosspost_mock:
            result = self.main.maybe_upload_youtube_video(youtube_instance)

        self.assertTrue(result)
        youtube_instance.upload_video.assert_not_called()
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/generated-short.mp4",
            title="A title",
            description="A description",
            interactive=True,
            return_details=True,
            include_youtube=True,
            skip_confirmation=True,
        )
        youtube_instance.record_post_bridge_publish_result.assert_called_once()

    def test_maybe_upload_youtube_video_skips_already_posted_platforms_for_cached_short(self) -> None:
        youtube_instance = Mock()
        youtube_instance.video_path = "/tmp/generated-short.mp4"
        youtube_instance.subject = "Storm topic"
        youtube_instance.script = "A script"
        youtube_instance.metadata = {
            "title": "A title",
            "description": "A description",
        }
        cached_video = {
            "path": "/tmp/generated-short.mp4",
            "uploaded": True,
            "crossposts": {
                "tiktok": {"status": "success", "post_id": "post-tt"},
            },
        }

        with patch.object(
            self.main,
            "question",
            return_value="yes",
        ), patch.object(
            self.main,
            "get_post_bridge_config",
            return_value={
                "enabled": True,
                "api_key": "token",
                "platforms": ["youtube", "tiktok", "instagram"],
                "account_ids": [12, 34, 56],
                "auto_crosspost": False,
            },
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={
                "posted": True,
                "platforms": {
                    "instagram": {"status": "success", "post_id": "post-ig"},
                },
            },
        ) as crosspost_mock:
            result = self.main.maybe_upload_youtube_video(
                youtube_instance,
                cached_video=cached_video,
            )

        self.assertTrue(result)
        youtube_instance.upload_video.assert_not_called()
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/generated-short.mp4",
            title="A title",
            description="A description",
            interactive=True,
            return_details=True,
            include_youtube=True,
            skip_confirmation=True,
            excluded_platforms=["youtube", "tiktok"],
        )
        youtube_instance.record_post_bridge_publish_result.assert_not_called()
        youtube_instance.record_crosspost_result.assert_called_once_with(
            cached_video,
            {
                "posted": True,
                "platforms": {
                    "instagram": {"status": "success", "post_id": "post-ig"},
                },
            },
        )

    def test_main_asks_once_to_publish_cached_short_when_post_bridge_handles_youtube(self) -> None:
        youtube_instance = Mock()
        youtube_instance.video_path = "/tmp/cached-short.mp4"
        youtube_instance.subject = "Storm topic"
        youtube_instance.script = "A script"
        youtube_instance.metadata = {
            "title": "Cached title",
            "description": "Cached description",
        }

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "topic": "Storm topic",
                "script": "A script",
                "uploaded": False,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "get_post_bridge_config",
            return_value={
                "enabled": True,
                "api_key": "token",
                "platforms": ["youtube", "tiktok"],
                "account_ids": [12, 34],
                "auto_crosspost": True,
            },
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={
                "posted": True,
                "platforms": {
                    "youtube": {"status": "success", "post_id": "post-yt"},
                    "tiktok": {"status": "success", "post_id": "post-tt"},
                },
            },
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_post_bridge_publish_result",
        ) as record_publish_result_mock, patch("main.os.path.exists", return_value=True):
            self.main.main()

        youtube_instance.load_cached_video.assert_called_once_with(cached_videos[0])
        youtube_instance.upload_video.assert_not_called()
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/cached-short.mp4",
            title="Cached title",
            description="Cached description",
            interactive=True,
            return_details=True,
            include_youtube=True,
            skip_confirmation=True,
        )
        record_publish_result_mock.assert_called_once()

    def test_main_asks_once_to_publish_cached_short_when_selenium_handles_youtube(self) -> None:
        youtube_instance = Mock()
        youtube_instance.video_path = "/tmp/cached-short.mp4"
        youtube_instance.metadata = {
            "title": "Cached title",
            "description": "Cached description",
        }
        youtube_instance.upload_video.return_value = True

        youtube_module = types.ModuleType("classes.YouTube")
        youtube_module.YouTube = Mock(return_value=youtube_instance)
        tts_module = types.ModuleType("classes.Tts")
        tts_module.TTS = Mock(return_value=Mock())

        option_answers = iter(["2", "4"])
        cached_videos = [
            {
                "title": "Cached title",
                "description": "Cached description",
                "path": "/tmp/cached-short.mp4",
                "date": "2026-04-05 10:00:00",
                "uploaded": False,
            }
        ]

        def fake_question(message: str, *_args, **_kwargs) -> str:
            if "Select an account to start" in message:
                return "1"
            if "Select an option" in message:
                return next(option_answers)
            if "Publish one of these Shorts" in message:
                return "1"
            raise AssertionError(f"Unexpected question prompt: {message}")

        with patch.dict(
            sys.modules,
            {
                "classes.YouTube": youtube_module,
                "classes.Tts": tts_module,
            },
        ), patch("builtins.input", return_value="1"), patch.object(
            self.main,
            "get_accounts",
            return_value=[
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "true crime",
                    "language": "english",
                }
            ],
        ), patch.object(
            self.main,
            "get_post_bridge_config",
            return_value={
                "enabled": False,
                "api_key": "",
                "platforms": ["tiktok"],
                "account_ids": [34],
                "auto_crosspost": True,
            },
        ), patch.object(
            self.main,
            "question",
            side_effect=fake_question,
        ), patch.object(
            self.main,
            "rem_temp_files",
        ), patch.object(
            self.main,
            "maybe_crosspost_youtube_short",
            return_value={
                "posted": True,
                "platforms": {
                    "tiktok": {"status": "success", "post_id": "post-tt"},
                },
            },
        ) as crosspost_mock, patch.object(
            youtube_instance,
            "get_videos",
            return_value=cached_videos,
        ), patch.object(
            youtube_instance,
            "record_crosspost_result",
        ) as record_crosspost_result_mock, patch("main.os.path.exists", return_value=True):
            self.main.main()

        youtube_instance.load_cached_video.assert_called_once_with(cached_videos[0])
        youtube_instance.upload_video.assert_called_once_with()
        crosspost_mock.assert_called_once_with(
            video_path="/tmp/cached-short.mp4",
            title="Cached title",
            description="Cached description",
            interactive=True,
            return_details=True,
        )
        record_crosspost_result_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
