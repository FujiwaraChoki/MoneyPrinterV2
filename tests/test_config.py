import json
import os
import time

import config


class TestConfigCaching:
    def test_load_returns_dict(self, patch_root_dir):
        result = config._load_config()
        assert isinstance(result, dict)
        assert "verbose" in result

    def test_cache_reuses_same_object(self, patch_root_dir):
        first = config._load_config()
        second = config._load_config()
        assert first is second

    def test_cache_invalidates_on_file_change(self, patch_root_dir):
        first = config._load_config()
        assert first["verbose"] is False

        # Modify config file
        config_path = os.path.join(str(patch_root_dir), "config.json")
        data = json.loads(open(config_path).read())
        data["verbose"] = True

        # Ensure mtime changes (some filesystems have 1s resolution)
        time.sleep(0.05)
        with open(config_path, "w") as f:
            json.dump(data, f)
        # Force different mtime
        future = time.time() + 1
        os.utime(config_path, (future, future))

        second = config._load_config()
        assert second["verbose"] is True

    def test_reload_config_forces_refresh(self, patch_root_dir):
        config._load_config()
        old_cache = config._config_cache

        result = config.reload_config()
        assert result is not old_cache

    def test_missing_config_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "ROOT_DIR", str(tmp_path))
        config._config_cache = None
        config._config_mtime = None
        try:
            config._load_config()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass
        finally:
            config._config_cache = None
            config._config_mtime = None


class TestConfigGetters:
    def test_get_verbose(self, patch_root_dir):
        assert config.get_verbose() is False

    def test_get_headless(self, patch_root_dir):
        assert config.get_headless() is True

    def test_get_ollama_model(self, patch_root_dir):
        assert config.get_ollama_model() == "test-model"

    def test_get_ollama_base_url(self, patch_root_dir):
        assert config.get_ollama_base_url() == "http://127.0.0.1:11434"

    def test_get_threads(self, patch_root_dir):
        assert config.get_threads() == 2

    def test_get_is_for_kids(self, patch_root_dir):
        assert config.get_is_for_kids() is False

    def test_get_twitter_language(self, patch_root_dir):
        assert config.get_twitter_language() == "English"

    def test_get_script_sentence_length(self, patch_root_dir):
        assert config.get_script_sentence_length() == 4

    def test_get_script_sentence_length_default(self, patch_root_dir):
        """When key is missing, should default to 4."""
        config_path = os.path.join(str(patch_root_dir), "config.json")
        data = json.loads(open(config_path).read())
        del data["script_sentence_length"]
        with open(config_path, "w") as f:
            json.dump(data, f)
        future = time.time() + 1
        os.utime(config_path, (future, future))

        assert config.get_script_sentence_length() == 4

    def test_get_stt_provider(self, patch_root_dir):
        assert config.get_stt_provider() == "local_whisper"

    def test_get_nanobanana2_api_key_from_config(self, patch_root_dir):
        assert config.get_nanobanana2_api_key() == "test-key"

    def test_get_nanobanana2_api_key_from_env(self, patch_root_dir, monkeypatch):
        """Falls back to GEMINI_API_KEY env var when config value is empty."""
        config_path = os.path.join(str(patch_root_dir), "config.json")
        data = json.loads(open(config_path).read())
        data["nanobanana2_api_key"] = ""
        with open(config_path, "w") as f:
            json.dump(data, f)
        future = time.time() + 1
        os.utime(config_path, (future, future))

        monkeypatch.setenv("GEMINI_API_KEY", "env-key-123")
        assert config.get_nanobanana2_api_key() == "env-key-123"

    def test_get_email_credentials(self, patch_root_dir):
        creds = config.get_email_credentials()
        assert creds["smtp_server"] == "smtp.gmail.com"
        assert creds["smtp_port"] == 587

    def test_get_fonts_dir(self, patch_root_dir):
        fonts = config.get_fonts_dir()
        assert fonts.endswith("fonts")


class TestFolderStructure:
    def test_assert_folder_structure_creates_mp(self, patch_root_dir):
        mp_path = os.path.join(str(patch_root_dir), ".mp")
        # Remove it first
        os.rmdir(mp_path)
        assert not os.path.exists(mp_path)

        config.assert_folder_structure()
        assert os.path.isdir(mp_path)

    def test_assert_folder_structure_noop_when_exists(self, patch_root_dir):
        mp_path = os.path.join(str(patch_root_dir), ".mp")
        assert os.path.isdir(mp_path)
        config.assert_folder_structure()  # Should not raise
        assert os.path.isdir(mp_path)

    def test_get_first_time_running(self, patch_root_dir):
        # .mp exists, so not first time
        assert config.get_first_time_running() is False

    def test_get_first_time_running_true(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "ROOT_DIR", str(tmp_path))
        # No .mp directory
        assert config.get_first_time_running() is True
