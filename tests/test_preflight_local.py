import importlib
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock
from unittest.mock import patch

import requests


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

preflight_local = importlib.import_module("preflight_local")


class PreflightLocalTests(unittest.TestCase):
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

        self.config_path = os.path.join(self.config_dir, "config.json")

    def write_config(self, payload: dict) -> None:
        with open(self.config_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def patch_config_path(self):
        return patch.object(preflight_local, "CONFIG_PATH", self.config_path)

    def make_config(self, **overrides: str) -> dict:
        payload = {
            "openrouter_api_key": "config-key",
            "openrouter_model": "config-model",
            "openrouter_base_url": "https://router.example/api/v1",
            "nanobanana2_api_key": "nb2-key",
            "stt_provider": "assembly_ai",
        }
        payload.update(overrides)
        return payload

    def run_main(self, payload: dict, env: dict | None = None, response: Mock | None = None):
        self.write_config(payload)
        env_patch = env or {}
        http_response = response or Mock(status_code=200)

        with self.patch_config_path(), patch.dict(os.environ, env_patch, clear=True), patch.object(
            preflight_local.requests,
            "get",
            return_value=http_response,
        ) as get_mock:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = preflight_local.main()

        return exit_code, stdout.getvalue(), get_mock

    def test_resolve_openrouter_api_key_and_model_prefer_config_values(self) -> None:
        payload = {
            "openrouter_api_key": "config-key",
            "openrouter_model": "config-model",
        }

        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "env-key",
                "OPENROUTER_MODEL": "env-model",
            },
            clear=True,
        ):
            self.assertEqual(
                preflight_local.resolve_openrouter_api_key(payload),
                "config-key",
            )
            self.assertEqual(
                preflight_local.resolve_openrouter_model(payload),
                "config-model",
            )

    def test_resolve_openrouter_api_key_and_model_fall_back_to_env(self) -> None:
        payload = {
            "openrouter_api_key": "",
            "openrouter_model": "",
        }

        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "env-key",
                "OPENROUTER_MODEL": "env-model",
            },
            clear=True,
        ):
            self.assertEqual(
                preflight_local.resolve_openrouter_api_key(payload),
                "env-key",
            )
            self.assertEqual(
                preflight_local.resolve_openrouter_model(payload),
                "env-model",
            )

    def test_resolve_openrouter_base_url_defaults_when_empty_or_missing(self) -> None:
        test_cases = [
            ({}, "https://openrouter.ai/api/v1"),
            ({"openrouter_base_url": ""}, "https://openrouter.ai/api/v1"),
        ]

        for payload, expected in test_cases:
            with self.subTest(payload=payload):
                self.assertEqual(
                    preflight_local.resolve_openrouter_base_url(payload),
                    expected,
                )

    def test_main_fails_when_openrouter_api_key_is_missing(self) -> None:
        exit_code, output, _ = self.run_main(
            self.make_config(openrouter_api_key=""),
            env={"OPENROUTER_MODEL": "env-model"},
        )

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY.",
            output,
        )

    def test_main_fails_when_openrouter_model_is_missing(self) -> None:
        exit_code, output, _ = self.run_main(
            self.make_config(openrouter_model=""),
            env={"OPENROUTER_API_KEY": "env-key"},
        )

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL.",
            output,
        )

    def test_main_checks_openrouter_models_endpoint_using_resolved_base_url(self) -> None:
        exit_code, output, get_mock = self.run_main(
            self.make_config(openrouter_base_url="https://openrouter.example/api/v1"),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "https://openrouter.example/api/v1/models",
            [call.args[0] for call in get_mock.call_args_list],
        )
        self.assertIn(
            "[OK] OpenRouter reachable at https://openrouter.example/api/v1",
            output,
        )

    def test_main_fails_when_openrouter_models_endpoint_returns_http_error(self) -> None:
        response = Mock(status_code=503)
        response.raise_for_status.side_effect = requests.HTTPError("503 Server Error")

        exit_code, output, _ = self.run_main(
            self.make_config(openrouter_base_url="https://openrouter.example/api/v1"),
            response=response,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "OpenRouter is not reachable at https://openrouter.example/api/v1: 503 Server Error",
            output,
        )

    def test_setup_local_preserves_openrouter_values_and_cleans_ollama_fields(self) -> None:
        repo_root = os.path.join(self.config_dir, "setup-repo")
        scripts_dir = os.path.join(repo_root, "scripts")
        venv_bin_dir = os.path.join(repo_root, "venv", "bin")
        os.makedirs(scripts_dir, exist_ok=True)
        os.makedirs(venv_bin_dir, exist_ok=True)

        shutil.copyfile(
            os.path.join(ROOT_DIR, "scripts", "setup_local.sh"),
            os.path.join(scripts_dir, "setup_local.sh"),
        )
        shutil.copyfile(
            os.path.join(ROOT_DIR, "scripts", "install_money_command.py"),
            os.path.join(scripts_dir, "install_money_command.py"),
        )

        with open(os.path.join(repo_root, "requirements.txt"), "w", encoding="utf-8") as handle:
            handle.write("")

        with open(os.path.join(repo_root, "config.json"), "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "llm_provider": "local_ollama",
                    "ollama_base_url": "http://127.0.0.1:11434",
                    "ollama_model": "llama3.2:3b",
                    "openrouter_base_url": "https://stale.example/api/v1",
                    "openrouter_api_key": "preserve-key",
                    "openrouter_model": "preserve-model",
                },
                handle,
            )

        with open(os.path.join(scripts_dir, "preflight_local.py"), "w", encoding="utf-8") as handle:
            handle.write("print('stub preflight')\n")

        wrapper_path = os.path.join(venv_bin_dir, "python")
        with open(wrapper_path, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env bash\n"
                "if [[ \"${1:-}\" == \"-m\" && \"${2:-}\" == \"ensurepip\" ]]; then exit 0; fi\n"
                "if [[ \"${1:-}\" == \"-m\" && \"${2:-}\" == \"pip\" ]]; then exit 0; fi\n"
                "exec python3 \"$@\"\n"
            )
        os.chmod(wrapper_path, 0o755)

        env = os.environ.copy()
        env["HOME"] = os.path.join(repo_root, "home")
        os.makedirs(env["HOME"], exist_ok=True)

        subprocess.run(
            ["bash", os.path.join(scripts_dir, "setup_local.sh")],
            cwd=repo_root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

        launcher_path = os.path.join(env["HOME"], ".local", "bin", "money")
        shell_rc_path = os.path.join(env["HOME"], ".zshrc")

        with open(os.path.join(repo_root, "config.json"), "r", encoding="utf-8") as handle:
            config = json.load(handle)

        self.assertEqual(config["openrouter_base_url"], "https://openrouter.ai/api/v1")
        self.assertEqual(config["openrouter_api_key"], "preserve-key")
        self.assertEqual(config["openrouter_model"], "preserve-model")
        self.assertNotEqual(config.get("llm_provider"), "local_ollama")
        self.assertIn(config.get("ollama_model", ""), ("", None))
        self.assertIn(config.get("ollama_base_url", ""), ("", None))
        self.assertTrue(os.path.exists(launcher_path))

        with open(launcher_path, "r", encoding="utf-8") as handle:
            launcher_contents = handle.read()

        with open(shell_rc_path, "r", encoding="utf-8") as handle:
            shell_rc_contents = handle.read()

        self.assertIn('exec "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/src/main.py" "$@"', launcher_contents)
        self.assertIn('export PATH="$HOME/.local/bin:$PATH"', shell_rc_contents)


if __name__ == "__main__":
    unittest.main()
