import os
import sys
import json
import srt_equalizer

from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])

_config_cache = None
_config_mtime = None


def _load_config() -> dict:
    """
    Loads config.json with file-level caching. Re-reads only when
    the file's mtime changes, so hot-edits still take effect.
    """
    global _config_cache, _config_mtime
    config_path = os.path.join(ROOT_DIR, "config.json")
    try:
        current_mtime = os.path.getmtime(config_path)
    except OSError:
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}. "
            "Copy config.example.json to config.json and fill in your values."
        )

    if _config_cache is None or current_mtime != _config_mtime:
        with open(config_path, "r") as f:
            _config_cache = json.load(f)
        _config_mtime = current_mtime

    return _config_cache


def reload_config() -> dict:
    """Force a config reload regardless of mtime."""
    global _config_cache, _config_mtime
    _config_cache = None
    _config_mtime = None
    return _load_config()


def assert_folder_structure() -> None:
    """Make sure that the necessary folder structure is present."""
    mp_path = os.path.join(ROOT_DIR, ".mp")
    if not os.path.exists(mp_path):
        if get_verbose():
            print(colored(f"=> Creating .mp folder at {mp_path}", "green"))
        os.makedirs(mp_path)


def get_first_time_running() -> bool:
    """Checks if the program is running for the first time."""
    return not os.path.exists(os.path.join(ROOT_DIR, ".mp"))


def get_email_credentials() -> dict:
    return _load_config()["email"]


def get_verbose() -> bool:
    return _load_config().get("verbose", False)


def get_firefox_profile_path() -> str:
    return _load_config()["firefox_profile"]


def get_headless() -> bool:
    return _load_config().get("headless", False)


def get_ollama_base_url() -> str:
    return _load_config().get("ollama_base_url", "http://127.0.0.1:11434")


def get_ollama_model() -> str:
    return _load_config().get("ollama_model", "")


def get_twitter_language() -> str:
    return _load_config()["twitter_language"]


def get_nanobanana2_api_base_url() -> str:
    return _load_config().get(
        "nanobanana2_api_base_url",
        "https://generativelanguage.googleapis.com/v1beta",
    )


def get_nanobanana2_api_key() -> str:
    configured = _load_config().get("nanobanana2_api_key", "")
    return configured or os.environ.get("GEMINI_API_KEY", "")


def get_nanobanana2_model() -> str:
    return _load_config().get("nanobanana2_model", "gemini-3.1-flash-image-preview")


def get_nanobanana2_aspect_ratio() -> str:
    return _load_config().get("nanobanana2_aspect_ratio", "9:16")


def get_threads() -> int:
    return _load_config()["threads"]


def get_zip_url() -> str:
    return _load_config()["zip_url"]


def get_is_for_kids() -> bool:
    return _load_config()["is_for_kids"]


def get_google_maps_scraper_zip_url() -> str:
    return _load_config()["google_maps_scraper"]


def get_google_maps_scraper_niche() -> str:
    return _load_config()["google_maps_scraper_niche"]


def get_scraper_timeout() -> int:
    return _load_config().get("scraper_timeout") or 300


def get_outreach_message_subject() -> str:
    return _load_config()["outreach_message_subject"]


def get_outreach_message_body_file() -> str:
    return _load_config()["outreach_message_body_file"]


def get_tts_voice() -> str:
    return _load_config().get("tts_voice", "Jasper")


def get_assemblyai_api_key() -> str:
    return _load_config()["assembly_ai_api_key"]


def get_stt_provider() -> str:
    return _load_config().get("stt_provider", "local_whisper")


def get_whisper_model() -> str:
    return _load_config().get("whisper_model", "base")


def get_whisper_device() -> str:
    return _load_config().get("whisper_device", "auto")


def get_whisper_compute_type() -> str:
    return _load_config().get("whisper_compute_type", "int8")


def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
    """Equalizes the subtitles in a SRT file."""
    srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)


def get_font() -> str:
    return _load_config()["font"]


def get_fonts_dir() -> str:
    return os.path.join(ROOT_DIR, "fonts")


def get_imagemagick_path() -> str:
    return _load_config()["imagemagick_path"]


def get_script_sentence_length() -> int:
    return _load_config().get("script_sentence_length", 4)
