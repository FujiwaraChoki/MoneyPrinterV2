import os
import sys
import json
import srt_equalizer

from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])

# ---------------------------------------------------------------------------
# Config caching: load config.json once and reuse across all getter calls.
# ---------------------------------------------------------------------------
_config_cache = None


def _load_config() -> dict:
    """Load config.json from disk and cache it in memory."""
    global _config_cache
    if _config_cache is None:
        config_path = os.path.join(ROOT_DIR, "config.json")
        with open(config_path, "r") as file:
            _config_cache = json.load(file)
    return _config_cache


def _get(key: str, default=None):
    """Convenience helper to read a value from the cached config."""
    return _load_config().get(key, default)


# ---------------------------------------------------------------------------
# .env support: sensitive keys are read from environment variables first,
# falling back to config.json. Users should put secrets in a .env file.
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    # python-dotenv is optional; secrets can also be set via shell exports
    pass


# ---------------------------------------------------------------------------
# Folder structure helpers
# ---------------------------------------------------------------------------
def assert_folder_structure() -> None:
    """
    Make sure that the nessecary folder structure is present.

    Returns:
        None
    """
    # Create the .mp folder
    if not os.path.exists(os.path.join(ROOT_DIR, ".mp")):
        if get_verbose():
            print(colored(f"=> Creating .mp folder at {os.path.join(ROOT_DIR, '.mp')}", "green"))
        os.makedirs(os.path.join(ROOT_DIR, ".mp"))

def get_first_time_running() -> bool:
    """
    Checks if the program is running for the first time by checking if .mp folder exists.

    Returns:
        exists (bool): True if the program is running for the first time, False otherwise
    """
    return not os.path.exists(os.path.join(ROOT_DIR, ".mp"))


# ---------------------------------------------------------------------------
# Sensitive credentials — .env takes priority over config.json
# ---------------------------------------------------------------------------
def get_email_credentials() -> dict:
    """
    Gets the email credentials. Values in .env override config.json.

    Returns:
        credentials (dict): The email credentials
    """
    config_creds = _get("email", {})
    return {
        "username": os.environ.get("EMAIL_USERNAME", config_creds.get("username", "")),
        "password": os.environ.get("EMAIL_PASSWORD", config_creds.get("password", "")),
        "smtp_server": config_creds.get("smtp_server", ""),
        "smtp_port": config_creds.get("smtp_port", 587),
    }

def get_nanobanana2_api_key() -> str:
    """
    Gets the Gemini / Nano Banana 2 API key.
    Priority: GEMINI_API_KEY env var > config.json nanobanana2_api_key.

    Returns:
        key (str): API key
    """
    env_key = os.environ.get("GEMINI_API_KEY", "")
    if env_key:
        return env_key
    return _get("nanobanana2_api_key", "")

def get_assemblyai_api_key() -> str:
    """
    Gets the AssemblyAI API key.
    Priority: ASSEMBLYAI_API_KEY env var > config.json assembly_ai_api_key.

    Returns:
        key (str): The AssemblyAI API key
    """
    env_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    if env_key:
        return env_key
    return _get("assembly_ai_api_key", "")


# ---------------------------------------------------------------------------
# Non-sensitive config getters (read from cached config.json)
# ---------------------------------------------------------------------------
def get_verbose() -> bool:
    """Gets the verbose flag from the config file."""
    return _get("verbose", False)

def get_firefox_profile_path() -> str:
    """Gets the path to the Firefox profile."""
    return _get("firefox_profile", "")

def get_headless() -> bool:
    """Gets the headless flag from the config file."""
    return _get("headless", False)

def get_ollama_base_url() -> str:
    """Gets the Ollama base URL."""
    return _get("ollama_base_url", "http://127.0.0.1:11434")

def get_ollama_model() -> str:
    """Gets the Ollama model name from the config file."""
    return _get("ollama_model", "")

def get_twitter_language() -> str:
    """Gets the Twitter language from the config file."""
    return _get("twitter_language", "en")

def get_nanobanana2_api_base_url() -> str:
    """Gets the Nano Banana 2 (Gemini image) API base URL."""
    return _get(
        "nanobanana2_api_base_url",
        "https://generativelanguage.googleapis.com/v1beta",
    )

def get_nanobanana2_model() -> str:
    """Gets the Nano Banana 2 model name."""
    return _get("nanobanana2_model", "gemini-3.1-flash-image-preview")

def get_nanobanana2_aspect_ratio() -> str:
    """Gets the aspect ratio for Nano Banana 2 image generation."""
    return _get("nanobanana2_aspect_ratio", "9:16")

def get_threads() -> int:
    """Gets the amount of threads to use for example when writing to a file with MoviePy."""
    return _get("threads", 2)

def get_zip_url() -> str:
    """Gets the URL to the zip file containing the songs."""
    return _get("zip_url", "")

def get_is_for_kids() -> bool:
    """Gets the is for kids flag from the config file."""
    return _get("is_for_kids", False)

def get_google_maps_scraper_zip_url() -> str:
    """Gets the URL to the zip file containing the Google Maps scraper."""
    return _get("google_maps_scraper", "")

def get_google_maps_scraper_niche() -> str:
    """Gets the niche for the Google Maps scraper."""
    return _get("google_maps_scraper_niche", "")

def get_scraper_timeout() -> int:
    """Gets the timeout for the scraper."""
    return _get("scraper_timeout", 300)

def get_outreach_message_subject() -> str:
    """Gets the outreach message subject."""
    return _get("outreach_message_subject", "")

def get_outreach_message_body_file() -> str:
    """Gets the outreach message body file."""
    return _get("outreach_message_body_file", "")

def get_tts_voice() -> str:
    """Gets the TTS voice from the config file."""
    return _get("tts_voice", "Jasper")

def get_stt_provider() -> str:
    """Gets the configured STT provider."""
    return _get("stt_provider", "local_whisper")

def get_whisper_model() -> str:
    """Gets the local Whisper model name."""
    return _get("whisper_model", "base")

def get_whisper_device() -> str:
    """Gets the target device for Whisper inference."""
    return _get("whisper_device", "auto")

def get_whisper_compute_type() -> str:
    """Gets the compute type for Whisper inference."""
    return _get("whisper_compute_type", "int8")

def get_font() -> str:
    """Gets the font from the config file."""
    return _get("font", "")

def get_fonts_dir() -> str:
    """Gets the fonts directory."""
    return os.path.join(ROOT_DIR, "fonts")

def get_imagemagick_path() -> str:
    """Gets the path to ImageMagick."""
    return _get("imagemagick_path", "")

def get_script_sentence_length() -> int:
    """Gets the forced script's sentence length (default: 4)."""
    return _get("script_sentence_length", 4)


# ---------------------------------------------------------------------------
# Subtitle equalization
# ---------------------------------------------------------------------------
def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
    """
    Equalizes the subtitles in a SRT file.

    Args:
        srt_path (str): The path to the SRT file
        max_chars (int): The maximum amount of characters in a subtitle

    Returns:
        None
    """
    srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)
