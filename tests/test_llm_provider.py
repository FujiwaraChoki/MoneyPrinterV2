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

fake_ollama = types.ModuleType("ollama")
fake_ollama.Client = object
sys.modules.setdefault("ollama", fake_ollama)

fake_config = types.ModuleType("config")
fake_config.get_ollama_base_url = lambda: "http://127.0.0.1:11434"
sys.modules.setdefault("config", fake_config)

import llm_provider


class LlmProviderTests(unittest.TestCase):
    @patch("llm_provider._client")
    def test_generate_text_returns_stripped_message_content(self, client_factory_mock: Mock) -> None:
        client = Mock()
        client.chat.return_value = {"message": {"content": " hello world \n"}}
        client_factory_mock.return_value = client

        text = llm_provider.generate_text("Say hello", model_name="llama3.2:3b")

        self.assertEqual(text, "hello world")
        client.chat.assert_called_once()

    @patch("llm_provider.get_ollama_base_url")
    @patch("llm_provider._client")
    def test_generate_text_wraps_client_errors_with_context(
        self,
        client_factory_mock: Mock,
        base_url_mock: Mock,
    ) -> None:
        client = Mock()
        client.chat.side_effect = ConnectionError("connection refused")
        client_factory_mock.return_value = client
        base_url_mock.return_value = "http://127.0.0.1:11434"

        with self.assertRaises(RuntimeError) as context:
            llm_provider.generate_text("Say hello", model_name="llama3.2:3b")

        message = str(context.exception)
        self.assertIn("http://127.0.0.1:11434", message)
        self.assertIn("llama3.2:3b", message)
        self.assertIn("connection refused", message)

    @patch("llm_provider._client")
    def test_generate_text_raises_when_message_content_is_missing(
        self, client_factory_mock: Mock
    ) -> None:
        client = Mock()
        client.chat.return_value = {}
        client_factory_mock.return_value = client

        with self.assertRaises(RuntimeError) as context:
            llm_provider.generate_text("Say hello", model_name="llama3.2:3b")

        self.assertIn("message.content", str(context.exception))


if __name__ == "__main__":
    unittest.main()
