import importlib
import os
import sys
import unittest
from unittest.mock import Mock
from unittest.mock import patch

import requests


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class LLMProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_llm_provider = sys.modules.pop("llm_provider", None)
        self.llm_provider = importlib.import_module("llm_provider")
        self.llm_provider._selected_model = None

    def tearDown(self) -> None:
        self.llm_provider._selected_model = None
        sys.modules.pop("llm_provider", None)
        if self._original_llm_provider is not None:
            sys.modules["llm_provider"] = self._original_llm_provider

    def make_response(self, payload: dict) -> Mock:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = payload
        return response

    def test_get_active_model_returns_selected_model(self) -> None:
        self.assertIsNone(self.llm_provider.get_active_model())

        self.llm_provider.select_model("google/gemini-2.5-flash")

        self.assertEqual(
            self.llm_provider.get_active_model(),
            "google/gemini-2.5-flash",
        )

    def test_list_models_returns_selected_model_or_configured_model(self) -> None:
        with patch.object(
            self.llm_provider,
            "get_openrouter_model",
            return_value="openai/gpt-4.1-mini",
            create=True,
        ):
            self.assertEqual(
                self.llm_provider.list_models(),
                ["openai/gpt-4.1-mini"],
            )

        self.llm_provider.select_model("google/gemini-2.5-flash")

        with patch.object(
            self.llm_provider,
            "get_openrouter_model",
            return_value="openai/gpt-4.1-mini",
            create=True,
        ):
            self.assertEqual(
                self.llm_provider.list_models(),
                ["google/gemini-2.5-flash"],
            )

    def test_generate_text_posts_to_openrouter_and_strips_content(self) -> None:
        response = self.make_response(
            {"choices": [{"message": {"content": "  OpenRouter reply  \n"}}]}
        )

        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            return_value=response,
        ) as post_mock:
            self.llm_provider.select_model("google/gemini-2.5-flash")

            result = self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(result, "OpenRouter reply")
        post_mock.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer secret-key",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [{"role": "user", "content": "Write a tagline"}],
            },
            timeout=60,
        )
        response.raise_for_status.assert_called_once_with()

    def test_generate_text_requires_selected_model_when_no_override_is_passed(self) -> None:
        with self.assertRaises(RuntimeError) as raised:
            self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(
            str(raised.exception),
            "No OpenRouter model selected. Call select_model() first or pass model_name.",
        )

    def test_generate_text_uses_explicit_model_name_over_selected_model(self) -> None:
        response = self.make_response(
            {"choices": [{"message": {"content": "  Override reply  \n"}}]}
        )

        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            return_value=response,
        ) as post_mock:
            self.llm_provider.select_model("google/gemini-2.5-flash")

            result = self.llm_provider.generate_text(
                "Write a tagline",
                model_name="openai/gpt-4.1-mini",
            )

        self.assertEqual(result, "Override reply")
        post_mock.assert_called_once()
        self.assertEqual(
            post_mock.call_args.kwargs["json"]["model"],
            "openai/gpt-4.1-mini",
        )

    def test_generate_text_wraps_request_failures(self) -> None:
        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            side_effect=requests.Timeout("timed out"),
        ):
            self.llm_provider.select_model("google/gemini-2.5-flash")

            with self.assertRaises(RuntimeError) as raised:
                self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(
            str(raised.exception),
            "OpenRouter request failed: timed out",
        )
        self.assertIsInstance(raised.exception.__cause__, requests.Timeout)

    def test_generate_text_wraps_raise_for_status_failures(self) -> None:
        response = self.make_response(
            {"choices": [{"message": {"content": "  unused  \n"}}]}
        )
        response.raise_for_status.side_effect = requests.HTTPError("bad gateway")

        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            return_value=response,
        ):
            self.llm_provider.select_model("google/gemini-2.5-flash")

            with self.assertRaises(RuntimeError) as raised:
                self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(
            str(raised.exception),
            "OpenRouter request failed: bad gateway",
        )
        self.assertIsInstance(raised.exception.__cause__, requests.HTTPError)

    def test_generate_text_raises_when_response_content_is_missing(self) -> None:
        response = self.make_response({"choices": [{"message": {}}]})

        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            return_value=response,
        ):
            self.llm_provider.select_model("google/gemini-2.5-flash")

            with self.assertRaises(RuntimeError) as raised:
                self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(
            str(raised.exception),
            "OpenRouter response did not contain message content.",
        )

    def test_generate_text_raises_when_api_key_is_missing(self) -> None:
        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
        ) as post_mock:
            self.llm_provider.select_model("google/gemini-2.5-flash")

            with self.assertRaises(RuntimeError) as raised:
                self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(
            str(raised.exception),
            "OpenRouter API key is not configured.",
        )
        post_mock.assert_not_called()

    def test_generate_text_falls_back_to_secondary_model_after_request_failure(self) -> None:
        primary_error = requests.Timeout("timed out")
        secondary_response = self.make_response(
            {"choices": [{"message": {"content": "  Fallback reply  \n"}}]}
        )

        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_fallback_models",
            return_value=["google/gemma-4-31b-it"],
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            side_effect=[primary_error, secondary_response],
        ) as post_mock:
            self.llm_provider.select_model("google/gemma-4-26b-a4b-it")

            result = self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(result, "Fallback reply")
        self.assertEqual(post_mock.call_count, 2)
        self.assertEqual(post_mock.call_args_list[0].kwargs["json"]["model"], "google/gemma-4-26b-a4b-it")
        self.assertEqual(post_mock.call_args_list[1].kwargs["json"]["model"], "google/gemma-4-31b-it")

    def test_generate_text_falls_back_when_primary_response_has_no_content(self) -> None:
        primary_response = self.make_response({"choices": [{"message": {}}]})
        secondary_response = self.make_response(
            {"choices": [{"message": {"content": "  Recovered reply  \n"}}]}
        )

        with patch.object(
            self.llm_provider,
            "get_openrouter_api_key",
            return_value="secret-key",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_base_url",
            return_value="https://openrouter.ai/api/v1",
            create=True,
        ), patch.object(
            self.llm_provider,
            "get_openrouter_fallback_models",
            return_value=["google/gemma-4-31b-it"],
            create=True,
        ), patch.object(
            self.llm_provider.requests,
            "post",
            side_effect=[primary_response, secondary_response],
        ):
            self.llm_provider.select_model("google/gemma-4-26b-a4b-it")

            result = self.llm_provider.generate_text("Write a tagline")

        self.assertEqual(result, "Recovered reply")


if __name__ == "__main__":
    unittest.main()
