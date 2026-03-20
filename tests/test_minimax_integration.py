"""Integration tests for MiniMax LLM provider.

These tests require a valid MINIMAX_API_KEY environment variable.
Skip automatically if the key is not set.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")


@unittest.skipUnless(MINIMAX_API_KEY, "MINIMAX_API_KEY not set")
class TestMiniMaxIntegration(unittest.TestCase):
    """Live integration tests against the MiniMax API."""

    def setUp(self):
        import llm_provider

        llm_provider._selected_model = None
        llm_provider._selected_provider = None

    def test_generate_text_m25(self):
        """Test basic text generation with MiniMax-M2.5."""
        from unittest.mock import patch

        with patch("llm_provider.get_llm_provider", return_value="minimax"), \
             patch("llm_provider.get_minimax_api_key", return_value=MINIMAX_API_KEY), \
             patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5"):
            from llm_provider import select_model, generate_text

            select_model("MiniMax-M2.5", provider="minimax")
            result = generate_text("Say exactly: hello world")

            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)

    def test_generate_text_m25_highspeed(self):
        """Test text generation with MiniMax-M2.5-highspeed."""
        from unittest.mock import patch

        with patch("llm_provider.get_llm_provider", return_value="minimax"), \
             patch("llm_provider.get_minimax_api_key", return_value=MINIMAX_API_KEY), \
             patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5-highspeed"):
            from llm_provider import select_model, generate_text

            select_model("MiniMax-M2.5-highspeed", provider="minimax")
            result = generate_text("What is 2+2? Reply with just the number.")

            self.assertIsInstance(result, str)
            self.assertIn("4", result)

    def test_generate_text_model_override(self):
        """Test model_name override for MiniMax."""
        from unittest.mock import patch

        with patch("llm_provider.get_llm_provider", return_value="minimax"), \
             patch("llm_provider.get_minimax_api_key", return_value=MINIMAX_API_KEY), \
             patch("llm_provider.get_minimax_model", return_value="MiniMax-M2.5"):
            from llm_provider import select_model, generate_text

            select_model("MiniMax-M2.5", provider="minimax")
            result = generate_text(
                "Reply with exactly: OK",
                model_name="MiniMax-M2.5-highspeed",
            )

            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()
