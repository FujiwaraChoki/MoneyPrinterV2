"""Unit tests for MiniMax config getters."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestMiniMaxConfigGetters(unittest.TestCase):
    """Tests for MiniMax-related config getters in config.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "config.json")

    def _write_config(self, data):
        with open(self.config_path, "w") as f:
            json.dump(data, f)

    @patch("config.ROOT_DIR")
    def test_get_llm_provider_default(self, mock_root):
        mock_root.__class__ = str
        self._write_config({"verbose": True})

        # Patch ROOT_DIR to our tmpdir
        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            result = config.get_llm_provider()
            self.assertEqual(result, "ollama")
        finally:
            config.ROOT_DIR = original_root

    @patch("config.ROOT_DIR")
    def test_get_llm_provider_minimax(self, mock_root):
        self._write_config({"llm_provider": "minimax"})

        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            result = config.get_llm_provider()
            self.assertEqual(result, "minimax")
        finally:
            config.ROOT_DIR = original_root

    @patch("config.ROOT_DIR")
    def test_get_minimax_api_key_from_config(self, mock_root):
        self._write_config({"minimax_api_key": "sk-test-123"})

        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            result = config.get_minimax_api_key()
            self.assertEqual(result, "sk-test-123")
        finally:
            config.ROOT_DIR = original_root

    @patch("config.ROOT_DIR")
    @patch.dict(os.environ, {"MINIMAX_API_KEY": "env-key-456"})
    def test_get_minimax_api_key_from_env(self, mock_root):
        self._write_config({"minimax_api_key": ""})

        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            result = config.get_minimax_api_key()
            self.assertEqual(result, "env-key-456")
        finally:
            config.ROOT_DIR = original_root

    @patch("config.ROOT_DIR")
    def test_get_minimax_api_key_config_takes_priority(self, mock_root):
        self._write_config({"minimax_api_key": "config-key"})

        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            with patch.dict(os.environ, {"MINIMAX_API_KEY": "env-key"}):
                result = config.get_minimax_api_key()
                self.assertEqual(result, "config-key")
        finally:
            config.ROOT_DIR = original_root

    @patch("config.ROOT_DIR")
    def test_get_minimax_model_default(self, mock_root):
        self._write_config({})

        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            result = config.get_minimax_model()
            self.assertEqual(result, "MiniMax-M2.5")
        finally:
            config.ROOT_DIR = original_root

    @patch("config.ROOT_DIR")
    def test_get_minimax_model_custom(self, mock_root):
        self._write_config({"minimax_model": "MiniMax-M2.5-highspeed"})

        import config

        original_root = config.ROOT_DIR
        config.ROOT_DIR = self.tmpdir
        try:
            result = config.get_minimax_model()
            self.assertEqual(result, "MiniMax-M2.5-highspeed")
        finally:
            config.ROOT_DIR = original_root


if __name__ == "__main__":
    unittest.main()
