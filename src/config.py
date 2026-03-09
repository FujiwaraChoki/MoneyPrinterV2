import os
import json
import srt_equalizer

from termcolor import colored

# Resolve project root relative to this file's location (src/config.py → project root)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_config_cache: dict = None


def _get_config() -> dict:
    """
    Loads and caches config.json. Raises a clear error if it's missing.
    """
    global _config_cache
    if _config_cache is None:
        config_path = os.path.join(ROOT_DIR, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"config.json not found at {config_path}. "
                "Copy config.example.json to config.json and fill in your values."
            )
        with open(config_path, "r") as f:
            _config_cache = json.load(f)
    return _config_cache


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
    return _get_config()["email"]

def get_verbose() -> bool:
    """
    Gets the verbose flag from the config file.

    Returns:
        verbose (bool): The verbose flag
    """
    return _get_config()["verbose"]

def get_firefox_profile_path() -> str:
    """
    Gets the path to the Firefox profile.

    Returns:
        path (str): The path to the Firefox profile
    """
    return _get_config()["firefox_profile"]

def get_headless() -> bool:
    """
    Gets the headless flag from the config file.

    Returns:
        headless (bool): The headless flag
    """
    return _get_config()["headless"]

def get_model() -> str:
    """
    Gets the model from the config file.

    Returns:
        model (str): The model
    """
    return _get_config()["llm"]

def get_twitter_language() -> str:
    """
    Gets the Twitter language from the config file.

    Returns:
        language (str): The Twitter language
    """
    return _get_config()["twitter_language"]

def get_image_model() -> str:
    """
    Gets the Image Model from the config file.

    Returns:
        model (str): The image model
    """
    return _get_config()["image_model"]

def get_threads() -> int:
    """
    Gets the amount of threads to use for example when writing to a file with MoviePy.

    Returns:
        threads (int): Amount of threads
    """
    return _get_config()["threads"]

def get_image_prompt_llm() -> str:
    """
    Gets the image prompt for LLM from the config file.

    Returns:
        prompt (str): The image prompt
    """
    return _get_config()["image_prompt_llm"]

def get_zip_url() -> str:
    """
    Gets the URL to the zip file containing the songs.

    Returns:
        url (str): The URL to the zip file
    """
    return _get_config()["zip_url"]

def get_is_for_kids() -> bool:
    """
    Gets the is for kids flag from the config file.

    Returns:
        is_for_kids (bool): The is for kids flag
    """
    return _get_config()["is_for_kids"]

def get_google_maps_scraper_zip_url() -> str:
    """
    Gets the URL to the zip file containing the Google Maps scraper.

    Returns:
        url (str): The URL to the zip file
    """
    return _get_config()["google_maps_scraper"]

def get_google_maps_scraper_niche() -> str:
    """
    Gets the niche for the Google Maps scraper.

    Returns:
        niche (str): The niche
    """
    return _get_config()["google_maps_scraper_niche"]

def get_scraper_timeout() -> int:
    """
    Gets the timeout for the scraper.

    Returns:
        timeout (int): The timeout
    """
    return _get_config().get("scraper_timeout") or 300

def get_outreach_message_subject() -> str:
    """
    Gets the outreach message subject.

    Returns:
        subject (str): The outreach message subject
    """
    return _get_config()["outreach_message_subject"]

def get_outreach_message_body_file() -> str:
    """
    Gets the outreach message body file.

    Returns:
        file (str): The outreach message body file
    """
    return _get_config()["outreach_message_body_file"]

def get_assemblyai_api_key() -> str:
    """
    Gets the AssemblyAI API key.

    Returns:
        key (str): The AssemblyAI API key
    """
    return _get_config()["assembly_ai_api_key"]

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
    return _get_config()["font"]

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
    return _get_config()["imagemagick_path"]

def get_script_sentence_length() -> int:
    """
    Gets the forced script's sentence length.
    In case there is no sentence length in config, returns 4 when none

    Returns:
        length (int): Length of script's sentence
    """
    return _get_config().get("script_sentence_length") or 4
