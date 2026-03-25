import json
import os

import config


class TestValidateConfig:
    def test_valid_config_no_issues(self, patch_root_dir):
        issues = config.validate_config()
        # imagemagick_path won't exist in tmp, so filter that out
        non_path_issues = [i for i in issues if "imagemagick_path" not in i]
        assert non_path_issues == []

    def test_missing_required_key(self):
        cfg = {"headless": True}
        issues = config.validate_config(cfg)
        missing = [i for i in issues if "Missing required key" in i]
        assert len(missing) > 0

    def test_wrong_type(self):
        cfg = {
            "verbose": "yes",  # should be bool
            "headless": True,
            "threads": 2,
            "is_for_kids": False,
            "font": "bold.ttf",
            "imagemagick_path": "/usr/bin/convert",
            "twitter_language": "English",
            "email": {"smtp_server": "s", "smtp_port": 587, "username": "u", "password": "p"},
            "zip_url": "",
        }
        issues = config.validate_config(cfg)
        type_issues = [i for i in issues if "wrong type" in i]
        assert any("verbose" in i for i in type_issues)

    def test_missing_email_subkeys(self):
        cfg = {
            "verbose": True,
            "headless": True,
            "threads": 2,
            "is_for_kids": False,
            "font": "bold.ttf",
            "imagemagick_path": "/usr/bin/convert",
            "twitter_language": "English",
            "email": {"smtp_server": "s"},
            "zip_url": "",
        }
        issues = config.validate_config(cfg)
        email_issues = [i for i in issues if "email." in i]
        assert len(email_issues) == 3  # missing smtp_port, username, password

    def test_invalid_stt_provider(self):
        cfg = {
            "verbose": True,
            "headless": True,
            "threads": 2,
            "is_for_kids": False,
            "font": "bold.ttf",
            "imagemagick_path": "/usr/bin/convert",
            "twitter_language": "English",
            "email": {"smtp_server": "s", "smtp_port": 587, "username": "u", "password": "p"},
            "stt_provider": "google_cloud",
            "zip_url": "",
        }
        issues = config.validate_config(cfg)
        stt_issues = [i for i in issues if "stt_provider" in i]
        assert len(stt_issues) == 1

    def test_imagemagick_path_missing_on_disk(self):
        cfg = {
            "verbose": True,
            "headless": True,
            "threads": 2,
            "is_for_kids": False,
            "font": "bold.ttf",
            "imagemagick_path": "/nonexistent/path/magick",
            "twitter_language": "English",
            "email": {"smtp_server": "s", "smtp_port": 587, "username": "u", "password": "p"},
            "zip_url": "",
        }
        issues = config.validate_config(cfg)
        path_issues = [i for i in issues if "does not exist on disk" in i]
        assert len(path_issues) == 1

    def test_config_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "ROOT_DIR", str(tmp_path))
        # No config.json in tmp_path
        issues = config.validate_config()
        assert any("not found" in i for i in issues)

    def test_valid_stt_providers_accepted(self):
        for provider in ("local_whisper", "third_party_assemblyai"):
            cfg = {
                "verbose": True,
                "headless": True,
                "threads": 2,
                "is_for_kids": False,
                "font": "bold.ttf",
                "imagemagick_path": "/usr/bin/convert",
                "twitter_language": "English",
                "email": {"smtp_server": "s", "smtp_port": 587, "username": "u", "password": "p"},
                "stt_provider": provider,
                "zip_url": "",
            }
            issues = config.validate_config(cfg)
            stt_issues = [i for i in issues if "stt_provider" in i]
            assert len(stt_issues) == 0
