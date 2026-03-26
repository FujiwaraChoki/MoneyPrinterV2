import os
import sys
import json
import srt_equalizer
import shutil
from typing import Optional

from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])

# Config caching to avoid reading file on every call
_CONFIG: Optional[dict] = None
_CONFIG_PATH: str = os.path.join(ROOT_DIR, "config.json")

def _load_config(force_reload: bool = False) -> dict:
    """
    Loads the config.json file and caches it in memory.
    Subsequent calls return the cached version unless force_reload=True.

    Returns:
        config (dict): The parsed config.json contents

    Raises:
        FileNotFoundError: If config.json does not exist
        json.JSONDecodeError: If config.json contains invalid JSON
    """
    global _CONFIG
    if _CONFIG is None or force_reload:
        if not os.path.exists(_CONFIG_PATH):
            raise FileNotFoundError(
                f"Config file not found at {_CONFIG_PATH}. "
                "Copy config.example.json to config.json and fill in values."
            )
        with open(_CONFIG_PATH, "r") as f:
            _CONFIG = json.load(f)
    return _CONFIG

def reload_config() -> None:
    """Reloads config from disk, discarding cache."""
    _load_config(force_reload=True)

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

def get_email_credentials() -> dict:
    """
    Gets the email credentials from the config file.

    Returns:
        credentials (dict): The email credentials
    """
    config = _load_config()
    return config["email"]

def get_verbose() -> bool:
    """
    Gets the verbose flag from the config file.

    Returns:
        verbose (bool): The verbose flag
    """
    config = _load_config()
    return config["verbose"]

def get_firefox_profile_path() -> str:
    """
    Gets the path to the Firefox profile.

    Returns:
        path (str): The path to the Firefox profile
    """
    config = _load_config()
    return config["firefox_profile"]

def get_headless() -> bool:
    """
    Gets the headless flag from the config file.

    Returns:
        headless (bool): The headless flag
    """
    config = _load_config()
    return config["headless"]

def get_ollama_base_url() -> str:
    """
    Gets the Ollama base URL.

    Returns:
        url (str): The Ollama base URL
    """
    config = _load_config()
    return config.get("ollama_base_url", "http://127.0.0.1:11434")

def get_ollama_model() -> str:
    """
    Gets the Ollama model name from the config file.

    Returns:
        model (str): The Ollama model name, or empty string if not set.
    """
    config = _load_config()
    return config.get("ollama_model", "")

def get_twitter_language() -> str:
    """
    Gets the Twitter language from the config file.

    Returns:
        language (str): The Twitter language
    """
    config = _load_config()
    return config["twitter_language"]

def get_nanobanana2_api_base_url() -> str:
    """
    Gets the Nano Banana 2 (Gemini image) API base URL.

    Returns:
        url (str): API base URL
    """
    config = _load_config()
    return config.get(
        "nanobanana2_api_base_url",
        "https://generativelanguage.googleapis.com/v1beta",
    )

def get_nanobanana2_api_key() -> str:
    """
    Gets the Nano Banana 2 API key.

    Returns:
        key (str): API key
    """
    config = _load_config()
    configured = config.get("nanobanana2_api_key", "")
    return configured or os.environ.get("GEMINI_API_KEY", "")

def get_openrouter_api_key() -> str:
    """
    Gets the OpenRouter API key for free image generation.

    Returns:
        key (str): API key (free signup at openrouter.ai)
    """
    config = _load_config()
    return config.get("openrouter_api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")

def get_openrouter_image_model() -> str:
    """
    Gets the OpenRouter image model (free tier like flux-schnell).

    Returns:
        model (str): Model name
    """
    config = _load_config()
    return config.get("openrouter_image_model", "flux-schnell")

def get_image_provider() -> str:
    """
    Gets the image provider ('openrouter', 'gemini', etc.).

    Returns:
        provider (str): Provider name
    """
    config = _load_config()
    return config.get("image_provider", "openrouter")

def get_use_image_fallback() -> bool:
    """
    Gets flag for static image fallback if gen fails.

    Returns:
        fallback (bool): Use fallback
    """
    config = _load_config()
    return config.get("use_image_fallback", True)

def get_nanobanana2_model() -> str:
    """
    Gets the Nano Banana 2 model name.

    Returns:
        model (str): Model name
    """
    config = _load_config()
    return config.get("nanobanana2_model", "gemini-3.1-flash-image-preview")

def get_nanobanana2_aspect_ratio() -> str:
    """
    Gets the aspect ratio for Nano Banana 2 image generation.

    Returns:
        ratio (str): Aspect ratio
    """
    config = _load_config()
    return config.get("nanobanana2_aspect_ratio", "9:16")

def get_threads() -> int:
    """
    Gets the amount of threads to use for example when writing to a file with MoviePy.

    Returns:
        threads (int): Amount of threads
    """
    config = _load_config()
    return config["threads"]

def get_zip_url() -> str:
    """
    Gets the URL to the zip file containing the songs.

    Returns:
        url (str): The URL to the zip file
    """
    config = _load_config()
    return config["zip_url"]

def get_is_for_kids() -> bool:
    """
    Gets the is for kids flag from the config file.

    Returns:
        is_for_kids (bool): The is for kids flag
    """
    config = _load_config()
    return config["is_for_kids"]

def get_google_maps_scraper_zip_url() -> str:
    """
    Gets the URL to the zip file containing the Google Maps scraper.

    Returns:
        url (str): The URL to the zip file
    """
    config = _load_config()
    return config["google_maps_scraper"]

def get_google_maps_scraper_niche() -> str:
    """
    Gets the niche for the Google Maps scraper.

    Returns:
        niche (str): The niche
    """
    config = _load_config()
    return config["google_maps_scraper_niche"]

def get_scraper_timeout() -> int:
    """
    Gets the timeout for the scraper.

    Returns:
        timeout (int): The timeout
    """
    config = _load_config()
    return config.get("scraper_timeout") or 300

def get_outreach_message_subject() -> str:
    """
    Gets the outreach message subject.

    Returns:
        subject (str): The outreach message subject
    """
    config = _load_config()
    return config["outreach_message_subject"]

def get_outreach_message_body_file() -> str:
    """
    Gets the outreach message body file.

    Returns:
        file (str): The outreach message body file
    """
    config = _load_config()
    return config["outreach_message_body_file"]

def get_tts_voice() -> str:
    """
    Gets the TTS voice from the config file.

    Returns:
        voice (str): The TTS voice
    """
    config = _load_config()
    return config.get("tts_voice", "Jasper")

def get_assemblyai_api_key() -> str:
    """
    Gets the AssemblyAI API key.

    Returns:
        key (str): The AssemblyAI API key
    """
    config = _load_config()
    return config["assembly_ai_api_key"]

def get_stt_provider() -> str:
    """
    Gets the configured STT provider.

    Returns:
        provider (str): The STT provider
    """
    config = _load_config()
    return config.get("stt_provider", "local_whisper")

def get_whisper_model() -> str:
    """
    Gets the local Whisper model name.

    Returns:
        model (str): Whisper model name
    """
    config = _load_config()
    return config.get("whisper_model", "base")

def get_whisper_device() -> str:
    """
    Gets the target device for Whisper inference.

    Returns:
        device (str): Whisper device
    """
    config = _load_config()
    return config.get("whisper_device", "auto")

def get_whisper_compute_type() -> str:
    """
    Gets the compute type for Whisper inference.

    Returns:
        compute_type (str): Whisper compute type
    """
    config = _load_config()
    return config.get("whisper_compute_type", "int8")

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

def get_font() -> str:
    """
    Gets the font from the config file.

    Returns:
        font (str): The font
    """
    config = _load_config()
    return config["font"]

def get_fonts_dir() -> str:
    """
    Gets the fonts directory.

    Returns:
        dir (str): The fonts directory
    """
    return os.path.join(ROOT_DIR, "fonts")

def get_imagemagick_path() -> str:
    """
    Gets the path to ImageMagick.

    Returns:
        path (str): The path to ImageMagick
    """
    config = _load_config()
    return config["imagemagick_path"]

def get_script_sentence_length() -> int:
    """
    Gets the forced script's sentence length.
    In case there is no sentence length in config, returns 4 when none

    Returns:
        length (int): Length of script's sentence
    """
    config = _load_config()
    if config.get("script_sentence_length") is not None:
        return config["script_sentence_length"]
    else:
        return 4

def validate_config() -> None:
    """
    Validates the configuration file and raises errors for missing required values.

    Raises:
        ValueError: If any required configuration is missing or invalid.
    """
    config = _load_config()

    required_fields = {
        "firefox_profile": "Path to Firefox profile (e.g., ~/.mozilla/firefox/xxxxx.default-release)",
        "imagemagick_path": "Path to ImageMagick convert binary (e.g., /usr/bin/convert or C:\\...\\magick.exe)",
        # "nanobanana2_api_key": "Google Gemini API key for image generation (optional, use openrouter instead)",
    }

    missing = []
    for key, description in required_fields.items():
        value = config.get(key)
        if not value:
            missing.append(f"- {key}: {description}")

    if missing:
        raise ValueError(
            "Missing or empty required configuration in config.json:\n" + "\n".join(missing) +
            "\n\nCopy config.example.json to config.json and fill in the values."
        )

    # Validate that firefox_profile path exists and is a directory
    fp_path = config["firefox_profile"]
    if not os.path.isdir(fp_path):
        raise ValueError(
            f"Firefox profile path does not exist or is not a directory: {fp_path}\n"
            "Create a Firefox profile and update firefox_profile in config.json."
        )

    # Validate that imagemagick_path points to an existing file or executable in PATH
    im_path = config["imagemagick_path"]
    if not os.path.isfile(im_path) and not shutil.which(im_path):
        raise ValueError(
            f"ImageMagick binary not found at: {im_path}\n"
            "Install ImageMagick and set the correct path in config.json."
        )
