import requests

from config import get_nanobanana2_api_key

_GEMINI_MODEL = "gemini-1.5-flash"
_GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent"

_selected_model: str | None = None


def list_models() -> list[str]:
    """
    Returns the available Gemini model.
    """
    return [_GEMINI_MODEL]


def select_model(model: str) -> None:
    """
    No-op for Gemini — model is fixed to gemini-1.5-flash.
    """
    global _selected_model
    _selected_model = model


def get_active_model() -> str | None:
    return _selected_model or _GEMINI_MODEL


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using the Google Gemini API.

    Args:
        prompt (str): User prompt
        model_name (str): Ignored — always uses gemini-1.5-flash

    Returns:
        response (str): Generated text
    """
    api_key = get_nanobanana2_api_key()
    if not api_key:
        raise RuntimeError("Gemini API key not set. Add nanobanana2_api_key to config.json.")

    response = requests.post(
        _GEMINI_URL,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
