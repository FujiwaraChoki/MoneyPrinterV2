import os
import sys
import json
import srt_equalizer

from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])

# ---------------------------------------------------------------------------
# Config caching — config.json is read once and cached in memory.
# Call reload_config() if you need to re-read from disk.
# ---------------------------------------------------------------------------
_config_cache: dict | None = None

def _load_config() -> dict:
    """Loads and caches config.json. Returns cached copy on subsequent calls."""
    global _config_cache
    if _config_cache is None:
        with open(os.path.join(ROOT_DIR, "config.json"), "r") as f:
            _config_cache = json.load(f)
    return _config_cache

def reload_config() -> dict:
    """Forces a fresh read of config.json."""
    global _config_cache
    _config_cache = None
    return _load_config()


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
    return _load_config()["email"]

def get_verbose() -> bool:
    """
    Gets the verbose flag from the config file.

    Returns:
        verbose (bool): The verbose flag
    """
    return _load_config()["verbose"]

def get_firefox_profile_path() -> str:
    """
    Gets the path to the Firefox profile.

    Returns:
        path (str): The path to the Firefox profile
    """
    return _load_config()["firefox_profile"]

def get_headless() -> bool:
    """
    Gets the headless flag from the config file.

    Returns:
        headless (bool): The headless flag
    """
    return _load_config()["headless"]

def get_ollama_base_url() -> str:
    """
    Gets the Ollama base URL.

    Returns:
        url (str): The Ollama base URL
    """
    return _load_config().get("ollama_base_url", "http://127.0.0.1:11434")

def get_ollama_model() -> str:
    """
    Gets the Ollama model name from the config file.

    Returns:
        model (str): The Ollama model name, or empty string if not set.
    """
    return _load_config().get("ollama_model", "")

def get_twitter_language() -> str:
    """
    Gets the Twitter language from the config file.

    Returns:
        language (str): The Twitter language
    """
    return _load_config()["twitter_language"]

def get_nanobanana2_api_base_url() -> str:
    """
    Gets the Nano Banana 2 (Gemini image) API base URL.

    Returns:
        url (str): API base URL
    """
    return _load_config().get(
        "nanobanana2_api_base_url",
        "https://generativelanguage.googleapis.com/v1beta",
    )

def get_nanobanana2_api_key() -> str:
    """
    Gets the Nano Banana 2 API key.

    Returns:
        key (str): API key
    """
    configured = _load_config().get("nanobanana2_api_key", "")
    return configured or os.environ.get("GEMINI_API_KEY", "")

def get_nanobanana2_model() -> str:
    """
    Gets the Nano Banana 2 model name.

    Returns:
        model (str): Model name
    """
    return _load_config().get("nanobanana2_model", "gemini-2.5-flash-image")

def get_nanobanana2_aspect_ratio() -> str:
    """
    Gets the aspect ratio for Nano Banana 2 image generation.

    Returns:
        ratio (str): Aspect ratio
    """
    return _load_config().get("nanobanana2_aspect_ratio", "9:16")

def get_gemini_llm_api_key() -> str:
    """
    Gets the Gemini API key used for LLM text generation.
    Falls back to nanobanana2_api_key (same Gemini project) if not set separately.

    Returns:
        key (str): API key
    """
    cfg = _load_config()
    dedicated = cfg.get("gemini_llm_api_key", "")
    if dedicated:
        return dedicated
    # Reuse the image-generation Gemini key as a convenient default
    return cfg.get("nanobanana2_api_key", "") or os.environ.get("GEMINI_API_KEY", "")

def get_gemini_llm_model() -> str:
    """
    Gets the Gemini model name to use for text generation.

    Returns:
        model (str): Model name
    """
    return _load_config().get("gemini_llm_model", "gemini-2.5-flash")

def get_threads() -> int:
    """
    Gets the amount of threads to use for example when writing to a file with MoviePy.

    Returns:
        threads (int): Amount of threads
    """
    return _load_config()["threads"]
    
def get_zip_url() -> str:
    """
    Gets the URL to the zip file containing the songs.

    Returns:
        url (str): The URL to the zip file
    """
    return _load_config()["zip_url"]

def get_is_for_kids() -> bool:
    """
    Gets the is for kids flag from the config file.

    Returns:
        is_for_kids (bool): The is for kids flag
    """
    return _load_config()["is_for_kids"]

def get_google_maps_scraper_zip_url() -> str:
    """
    Gets the URL to the zip file containing the Google Maps scraper.

    Returns:
        url (str): The URL to the zip file
    """
    return _load_config()["google_maps_scraper"]

def get_google_maps_scraper_niche() -> str:
    """
    Gets the niche for the Google Maps scraper.

    Returns:
        niche (str): The niche
    """
    return _load_config()["google_maps_scraper_niche"]

def get_scraper_timeout() -> int:
    """
    Gets the timeout for the scraper.

    Returns:
        timeout (int): The timeout
    """
    return _load_config()["scraper_timeout"] or 300

def get_outreach_message_subject() -> str:
    """
    Gets the outreach message subject.

    Returns:
        subject (str): The outreach message subject
    """
    return _load_config()["outreach_message_subject"]
    
def get_outreach_message_body_file() -> str:
    """
    Gets the outreach message body file.

    Returns:
        file (str): The outreach message body file
    """
    return _load_config()["outreach_message_body_file"]

def get_tts_voice() -> str:
    """
    Gets the TTS voice from the config file.

    Returns:
        voice (str): The TTS voice
    """
    return _load_config().get("tts_voice", "Jasper")

def get_assemblyai_api_key() -> str:
    """
    Gets the AssemblyAI API key.

    Returns:
        key (str): The AssemblyAI API key
    """
    return _load_config()["assembly_ai_api_key"]

def get_stt_provider() -> str:
    """
    Gets the configured STT provider.

    Returns:
        provider (str): The STT provider
    """
    return _load_config().get("stt_provider", "local_whisper")

def get_whisper_model() -> str:
    """
    Gets the local Whisper model name.

    Returns:
        model (str): Whisper model name
    """
    return _load_config().get("whisper_model", "base")

def get_whisper_device() -> str:
    """
    Gets the target device for Whisper inference.

    Returns:
        device (str): Whisper device
    """
    return _load_config().get("whisper_device", "auto")

def get_whisper_compute_type() -> str:
    """
    Gets the compute type for Whisper inference.

    Returns:
        compute_type (str): Whisper compute type
    """
    return _load_config().get("whisper_compute_type", "int8")
    
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
    return _load_config()["font"]

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
    return _load_config()["imagemagick_path"]

def get_script_sentence_length() -> int:
    """
    Gets the forced script's sentence length.
    In case there is no sentence length in config, returns 4 when none

    Returns:
        length (int): Length of script's sentence
    """
    cfg = _load_config()
    if cfg.get("script_sentence_length") is not None:
        return cfg["script_sentence_length"]
    return 4

def get_pexels_api_key() -> str:
    """
    Gets the Pexels API key from the config file.

    Returns:
        key (str): The Pexels API key
    """
    return _load_config().get("pexels_api_key", "")

def get_tts_rate() -> str:
    """
    Gets the TTS speech rate (e.g. '+5%', '-10%').

    Returns:
        rate (str): The TTS rate
    """
    return _load_config().get("tts_rate", "+0%")

def get_tts_pitch() -> str:
    """
    Gets the TTS pitch adjustment (e.g. '+0Hz', '+5Hz').

    Returns:
        pitch (str): The TTS pitch
    """
    return _load_config().get("tts_pitch", "+0Hz")

def get_use_background_music() -> bool:
    """
    Gets whether to use background music.
    False = orijinal ses only (Creator Pool %100 gelir).

    Returns:
        use_music (bool): Whether to use background music
    """
    return _load_config().get("use_background_music", False)

def get_video_format() -> str:
    """
    Gets the video format type for script generation.
    Options: ai_tool_showcase, before_after, quick_tutorial,
             ai_predictions, myth_busting, ai_vs_human

    Returns:
        format_type (str): The video format
    """
    return _load_config().get("video_format", "ai_tool_showcase")

def get_enable_ken_burns() -> bool:
    """
    Gets whether Ken Burns effect (zoom/pan) is enabled.

    Returns:
        enabled (bool): Whether Ken Burns is enabled
    """
    return _load_config().get("enable_ken_burns", True)

def get_enable_loop() -> bool:
    """
    Gets whether loop architecture (last→first crossfade) is enabled.

    Returns:
        enabled (bool): Whether loop is enabled
    """
    return _load_config().get("enable_loop", True)
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        config_json = json.load(file)
        if (config_json.get("script_sentence_length") is not None):
            return config_json["script_sentence_length"]
        else:
            return 4

def get_post_bridge_config() -> dict:
    """
    Gets the Post Bridge configuration with safe defaults.

    Returns:
        config (dict): Sanitized Post Bridge configuration
    """
    defaults = {
        "enabled": False,
        "api_key": "",
        "platforms": ["tiktok", "instagram"],
        "account_ids": [],
        "auto_crosspost": False,
    }
    supported_platforms = {"tiktok", "instagram"}

    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        config_json = json.load(file)

    raw_config = config_json.get("post_bridge", {})
    if not isinstance(raw_config, dict):
        raw_config = {}

    raw_platforms = raw_config.get("platforms")
    normalized_platforms = []
    seen_platforms = set()

    if raw_platforms is None:
        normalized_platforms = defaults["platforms"].copy()
    elif isinstance(raw_platforms, list):
        for platform in raw_platforms:
            normalized_platform = str(platform).strip().lower()
            if (
                normalized_platform in supported_platforms
                and normalized_platform not in seen_platforms
            ):
                normalized_platforms.append(normalized_platform)
                seen_platforms.add(normalized_platform)
    else:
        normalized_platforms = []

    raw_account_ids = raw_config.get("account_ids", defaults["account_ids"])
    normalized_account_ids = []
    if isinstance(raw_account_ids, list):
        for account_id in raw_account_ids:
            try:
                normalized_account_ids.append(int(account_id))
            except (TypeError, ValueError):
                continue

    api_key = str(raw_config.get("api_key", "")).strip()
    if not api_key:
        api_key = os.environ.get("POST_BRIDGE_API_KEY", "").strip()

    return {
        "enabled": bool(raw_config.get("enabled", defaults["enabled"])),
        "api_key": api_key,
        "platforms": normalized_platforms,
        "account_ids": normalized_account_ids,
        "auto_crosspost": bool(
            raw_config.get("auto_crosspost", defaults["auto_crosspost"])
        ),
    }
