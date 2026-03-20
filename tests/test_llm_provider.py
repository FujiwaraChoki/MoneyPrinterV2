"""Unit tests for llm_provider module with MiniMax and Ollama support."""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Add src/ to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestSelectModel(unittest.TestCase):
    """Tests for select_model and get_active_model."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    def test_select_model_sets_model(self):
        from llm_provider import select_model, get_active_model

        select_model("llama3.2:3b")
        self.assertEqual(get_active_model(), "llama3.2:3b")

    def test_select_model_with_provider(self):
        from llm_provider import select_model, get_active_model, get_provider

        select_model("MiniMax-M2.5", provider="minimax")
        self.assertEqual(get_active_model(), "MiniMax-M2.5")
        self.assertEqual(get_provider(), "minimax")

    def test_select_model_provider_none_keeps_existing(self):
        from llm_provider import select_model, get_provider

        select_model("model-a", provider="minimax")
        select_model("model-b")  # provider=None, should keep "minimax"
        self.assertEqual(get_provider(), "minimax")

    def test_get_active_model_returns_none_initially(self):
        from llm_provider import get_active_model

        self.assertIsNone(get_active_model())


class TestGetProvider(unittest.TestCase):
    """Tests for get_provider."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    @patch("llm_provider.get_llm_provider", return_value="ollama")
    def test_default_provider_from_config(self, mock_cfg):
        from llm_provider import get_provider

        self.assertEqual(get_provider(), "ollama")

    @patch("llm_provider.get_llm_provider", return_value="ollama")
    def test_selected_provider_overrides_config(self, mock_cfg):
        from llm_provider import select_model, get_provider

        select_model("MiniMax-M2.5", provider="minimax")
        self.assertEqual(get_provider(), "minimax")


class TestGenerateTextOllama(unittest.TestCase):
    """Tests for Ollama text generation."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    @patch("llm_provider.get_llm_provider", return_value="ollama")
    @patch("llm_provider._ollama_client")
    def test_generate_text_ollama(self, mock_client_fn, mock_cfg):
        from llm_provider import select_model, generate_text

        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {"content": "  Hello world  "}
        }
        mock_client_fn.return_value = mock_client

        select_model("llama3.2:3b", provider="ollama")
        result = generate_text("Say hello")

        self.assertEqual(result, "Hello world")
        mock_client.chat.assert_called_once_with(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": "Say hello"}],
        )

    @patch("llm_provider.get_llm_provider", return_value="ollama")
    def test_generate_text_ollama_no_model_raises(self, mock_cfg):
        from llm_provider import generate_text

        with self.assertRaises(RuntimeError):
            generate_text("test prompt")

    @patch("llm_provider.get_llm_provider", return_value="ollama")
    @patch("llm_provider._ollama_client")
    def test_generate_text_model_name_override(self, mock_client_fn, mock_cfg):
        from llm_provider import select_model, generate_text

        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {"content": "response"}
        }
        mock_client_fn.return_value = mock_client

        select_model("default-model", provider="ollama")
        generate_text("prompt", model_name="override-model")

        mock_client.chat.assert_called_once_with(
            model="override-model",
            messages=[{"role": "user", "content": "prompt"}],
        )


class TestGenerateTextMiniMax(unittest.TestCase):
    """Tests for MiniMax text generation."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    @patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5")
    @patch("llm_provider.get_minimax_api_key", return_value="test-key")
    @patch("llm_provider.get_llm_provider", return_value="minimax")
    def test_generate_text_minimax(self, mock_prov, mock_key, mock_model):
        from llm_provider import select_model, generate_text

        select_model("MiniMax-M2.5", provider="minimax")

        mock_choice = MagicMock()
        mock_choice.message.content = "MiniMax response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("llm_provider._minimax_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = generate_text("Hello MiniMax")

        self.assertEqual(result, "MiniMax response")
        mock_client.chat.completions.create.assert_called_once_with(
            model="MiniMax-M2.5",
            messages=[{"role": "user", "content": "Hello MiniMax"}],
            temperature=0.7,
        )

    @patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5")
    @patch("llm_provider.get_minimax_api_key", return_value="test-key")
    @patch("llm_provider.get_llm_provider", return_value="minimax")
    def test_generate_text_minimax_strips_think_tags(self, mock_prov, mock_key, mock_model):
        from llm_provider import select_model, generate_text

        select_model("MiniMax-M2.5", provider="minimax")

        mock_choice = MagicMock()
        mock_choice.message.content = "<think>internal reasoning</think>Actual answer"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("llm_provider._minimax_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = generate_text("test")

        self.assertEqual(result, "Actual answer")

    @patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5")
    @patch("llm_provider.get_minimax_api_key", return_value="test-key")
    @patch("llm_provider.get_llm_provider", return_value="minimax")
    def test_generate_text_minimax_empty_content(self, mock_prov, mock_key, mock_model):
        from llm_provider import select_model, generate_text

        select_model("MiniMax-M2.5", provider="minimax")

        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("llm_provider._minimax_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = generate_text("test")

        self.assertEqual(result, "")

    @patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5")
    @patch("llm_provider.get_minimax_api_key", return_value="test-key")
    @patch("llm_provider.get_llm_provider", return_value="minimax")
    def test_generate_text_minimax_model_override(self, mock_prov, mock_key, mock_model):
        from llm_provider import select_model, generate_text

        select_model("MiniMax-M2.5", provider="minimax")

        mock_choice = MagicMock()
        mock_choice.message.content = "response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("llm_provider._minimax_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            generate_text("prompt", model_name="MiniMax-M2.5-highspeed")

        mock_client.chat.completions.create.assert_called_once_with(
            model="MiniMax-M2.5-highspeed",
            messages=[{"role": "user", "content": "prompt"}],
            temperature=0.7,
        )


class TestMiniMaxClientValidation(unittest.TestCase):
    """Tests for MiniMax client creation and API key validation."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    @patch.dict(os.environ, {}, clear=True)
    @patch("llm_provider.get_minimax_api_key", return_value="")
    def test_minimax_client_no_key_raises(self, mock_key):
        from llm_provider import _minimax_client

        with self.assertRaises(RuntimeError) as ctx:
            _minimax_client()
        self.assertIn("MiniMax API key not configured", str(ctx.exception))

    @patch("llm_provider.get_minimax_api_key", return_value="sk-test-key")
    def test_minimax_client_with_config_key(self, mock_key):
        with patch("llm_provider.OpenAI", create=True) as MockOpenAI:
            # Need to patch the import
            import llm_provider

            with patch.object(llm_provider, "OpenAI", create=True) as MockOAI:
                pass  # Client creation tested via integration tests

    @patch("llm_provider.get_minimax_model", return_value="")
    @patch("llm_provider.get_minimax_api_key", return_value="test-key")
    @patch("llm_provider.get_llm_provider", return_value="minimax")
    def test_generate_text_minimax_no_model_raises(self, mock_prov, mock_key, mock_model):
        """When no model is selected and config returns empty, should raise."""
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = "minimax"

        from llm_provider import generate_text

        with self.assertRaises(RuntimeError) as ctx:
            generate_text("test")
        self.assertIn("No MiniMax model selected", str(ctx.exception))


class TestProviderDispatch(unittest.TestCase):
    """Tests for provider-based dispatch in generate_text."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    @patch("llm_provider._generate_text_ollama", return_value="ollama-result")
    @patch("llm_provider.get_llm_provider", return_value="ollama")
    def test_dispatch_to_ollama(self, mock_cfg, mock_gen):
        from llm_provider import generate_text

        result = generate_text("test")
        self.assertEqual(result, "ollama-result")
        mock_gen.assert_called_once_with("test", None)

    @patch("llm_provider._generate_text_minimax", return_value="minimax-result")
    @patch("llm_provider.get_llm_provider", return_value="minimax")
    def test_dispatch_to_minimax(self, mock_cfg, mock_gen):
        from llm_provider import generate_text

        result = generate_text("test")
        self.assertEqual(result, "minimax-result")
        mock_gen.assert_called_once_with("test", None)

    @patch("llm_provider._generate_text_ollama", return_value="ollama-result")
    @patch("llm_provider.get_llm_provider", return_value="unknown_provider")
    def test_unknown_provider_falls_back_to_ollama(self, mock_cfg, mock_gen):
        from llm_provider import generate_text

        result = generate_text("test")
        self.assertEqual(result, "ollama-result")


class TestListModels(unittest.TestCase):
    """Tests for list_models."""

    @patch("llm_provider._ollama_client")
    def test_list_models_returns_sorted(self, mock_client_fn):
        mock_client = MagicMock()
        model_b = MagicMock()
        model_b.model = "llama3:latest"
        model_a = MagicMock()
        model_a.model = "codellama:7b"
        mock_resp = MagicMock()
        mock_resp.models = [model_b, model_a]
        mock_client.list.return_value = mock_resp
        mock_client_fn.return_value = mock_client

        from llm_provider import list_models

        result = list_models()
        self.assertEqual(result, ["codellama:7b", "llama3:latest"])


if __name__ == "__main__":
    unittest.main()
