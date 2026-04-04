import requests

from config import get_openrouter_api_key
from config import get_openrouter_base_url
from config import get_openrouter_model

_selected_model: str | None = None


def list_models() -> list[str]:
    """
    Temporary compatibility shim until main.py stops importing list_models().
    """
    model = _selected_model or get_openrouter_model()
    return [model] if model else []


def select_model(model: str) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): An OpenRouter model name.
    """
    global _selected_model
    _selected_model = model


def get_active_model() -> str | None:
    """
    Returns the currently selected model, or None if none has been selected.
    """
    return _selected_model


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using the OpenRouter chat completions API.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    model = model_name or _selected_model
    if not model:
        raise RuntimeError(
            "No OpenRouter model selected. Call select_model() first or pass model_name."
        )

    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError("OpenRouter API key is not configured.")

    base_url = get_openrouter_base_url().rstrip("/")

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (IndexError, KeyError, TypeError, ValueError):
        raise RuntimeError("OpenRouter response did not contain message content.")

    if not isinstance(content, str):
        raise RuntimeError("OpenRouter response did not contain message content.")

    return content.strip()
