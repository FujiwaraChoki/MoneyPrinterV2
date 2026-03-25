import pytest
from unittest.mock import patch, MagicMock

import llm_provider


class TestModelSelection:
    def setup_method(self):
        llm_provider._selected_model = None

    def test_select_model(self):
        llm_provider.select_model("llama3.2:3b")
        assert llm_provider.get_active_model() == "llama3.2:3b"

    def test_get_active_model_default_none(self):
        assert llm_provider.get_active_model() is None

    def test_select_model_overrides(self):
        llm_provider.select_model("model-a")
        llm_provider.select_model("model-b")
        assert llm_provider.get_active_model() == "model-b"


class TestGenerateText:
    def setup_method(self):
        llm_provider._selected_model = None

    def test_raises_when_no_model_selected(self):
        with pytest.raises(RuntimeError, match="No Ollama model selected"):
            llm_provider.generate_text("hello")

    @patch.object(llm_provider, "_client")
    def test_generates_text_with_selected_model(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {"content": "  Generated response  "}
        }
        mock_client_fn.return_value = mock_client

        llm_provider.select_model("test-model")
        result = llm_provider.generate_text("test prompt")

        assert result == "Generated response"
        mock_client.chat.assert_called_once_with(
            model="test-model",
            messages=[{"role": "user", "content": "test prompt"}],
        )

    @patch.object(llm_provider, "_client")
    def test_model_name_overrides_selected(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {"content": "ok"}
        }
        mock_client_fn.return_value = mock_client

        llm_provider.select_model("default-model")
        llm_provider.generate_text("prompt", model_name="override-model")

        mock_client.chat.assert_called_once_with(
            model="override-model",
            messages=[{"role": "user", "content": "prompt"}],
        )

    @patch.object(llm_provider, "_client")
    def test_retries_on_failure(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.chat.side_effect = [
            ConnectionError("server down"),
            {"message": {"content": "recovered"}},
        ]
        mock_client_fn.return_value = mock_client

        llm_provider.select_model("test-model")
        result = llm_provider.generate_text("prompt")

        assert result == "recovered"
        assert mock_client.chat.call_count == 2


class TestListModels:
    @patch.object(llm_provider, "_client")
    def test_list_models(self, mock_client_fn):
        mock_model_a = MagicMock()
        mock_model_a.model = "zeta:latest"
        mock_model_b = MagicMock()
        mock_model_b.model = "alpha:latest"

        mock_response = MagicMock()
        mock_response.models = [mock_model_a, mock_model_b]

        mock_client = MagicMock()
        mock_client.list.return_value = mock_response
        mock_client_fn.return_value = mock_client

        models = llm_provider.list_models()
        assert models == ["alpha:latest", "zeta:latest"]
