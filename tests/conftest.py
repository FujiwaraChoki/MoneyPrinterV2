import os
import json
import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """
    Creates a minimal project structure that mirrors MoneyPrinterV2 layout.
    Returns the project root directory.
    """
    mp_dir = tmp_path / ".mp"
    mp_dir.mkdir()

    config = {
        "verbose": False,
        "firefox_profile": "",
        "headless": True,
        "ollama_base_url": "http://127.0.0.1:11434",
        "ollama_model": "test-model",
        "twitter_language": "English",
        "nanobanana2_api_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "nanobanana2_api_key": "test-key",
        "nanobanana2_model": "gemini-3.1-flash-image-preview",
        "nanobanana2_aspect_ratio": "9:16",
        "threads": 2,
        "zip_url": "",
        "is_for_kids": False,
        "google_maps_scraper": "",
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@test.com",
            "password": "password",
        },
        "google_maps_scraper_niche": "restaurants",
        "scraper_timeout": 300,
        "outreach_message_subject": "Hello {{COMPANY_NAME}}",
        "outreach_message_body_file": "outreach.html",
        "stt_provider": "local_whisper",
        "whisper_model": "base",
        "whisper_device": "auto",
        "whisper_compute_type": "int8",
        "assembly_ai_api_key": "test-key",
        "tts_voice": "Jasper",
        "font": "bold_font.ttf",
        "imagemagick_path": "/usr/bin/convert",
        "script_sentence_length": 4,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    return tmp_path


@pytest.fixture
def patch_root_dir(tmp_project, monkeypatch):
    """
    Patches ROOT_DIR in config module to point to our tmp project.
    """
    import config

    monkeypatch.setattr(config, "ROOT_DIR", str(tmp_project))
    yield tmp_project
