import ollama
import requests

from config import (
    get_ollama_base_url,
    get_openrouter_api_key,
    get_openrouter_model,
)

_selected_model: str | None = None


def _client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())


def list_models() -> list[str]:
    """
    Lists all models available on the local Ollama server.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    response = _client().list()
    return sorted(m.model for m in response.models)


def select_model(model: str) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): An Ollama model name (must be already pulled).
    """
    global _selected_model
    _selected_model = model


def get_active_model() -> str | None:
    """
    Returns the currently selected model, or None if none has been selected.
    """
    return _selected_model


def _generate_openrouter(prompt: str, model: str) -> str:
    """
    Generates text using the OpenRouter API.

    Args:
        prompt (str): User prompt
        model (str): OpenRouter model name

    Returns:
        response (str): Generated text
    """
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {get_openrouter_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using OpenRouter if an API key is configured,
    otherwise the local Ollama server.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    if get_openrouter_api_key():
        model = model_name or get_openrouter_model()
        if not model:
            raise RuntimeError(
                "OpenRouter API key is set but no openrouter_model is configured."
            )

        return _generate_openrouter(prompt, model)

    model = model_name or _selected_model
    if not model:
        raise RuntimeError(
            "No Ollama model selected. Call select_model() first or pass model_name."
        )

    response = _client().chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"].strip()
