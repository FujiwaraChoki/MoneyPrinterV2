import os
import sys
import types
import unittest
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


class LlmProviderErrorHandlingTests(unittest.TestCase):
    def test_list_models_wraps_ollama_connection_errors(self) -> None:
        with patch.object(llm_provider, "_client", side_effect=ConnectionError("down")):
            with self.assertRaisesRegex(RuntimeError, "Unable to list Ollama models"):
                llm_provider.list_models()

    def test_generate_text_wraps_ollama_chat_errors(self) -> None:
        class FailingClient:
            def chat(self, **kwargs):
                raise TimeoutError("timed out")

        with patch.object(llm_provider, "_client", return_value=FailingClient()):
            with self.assertRaisesRegex(RuntimeError, "Ollama chat request failed for model 'llama3'"):
                llm_provider.generate_text("hello", model_name="llama3")

    def test_generate_text_wraps_malformed_chat_response(self) -> None:
        class MalformedClient:
            def chat(self, **kwargs):
                return {"message": {}}

        with patch.object(llm_provider, "_client", return_value=MalformedClient()):
            with self.assertRaisesRegex(RuntimeError, "unexpected chat response"):
                llm_provider.generate_text("hello", model_name="llama3")


if __name__ == "__main__":
    unittest.main()
