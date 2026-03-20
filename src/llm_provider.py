import os

import ollama

from config import (
    get_llm_provider,
    get_minimax_api_key,
    get_minimax_model,
    get_ollama_base_url,
)

_selected_model: str | None = None
_selected_provider: str | None = None


def _ollama_client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())


def _minimax_client():
    """Returns an OpenAI client configured for the MiniMax API."""
    from openai import OpenAI

    api_key = get_minimax_api_key()
    if not api_key:
        api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "MiniMax API key not configured. Set 'minimax_api_key' in config.json "
            "or the MINIMAX_API_KEY environment variable."
        )
    return OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.io/v1",
    )


def get_provider() -> str:
    """Returns the active LLM provider name."""
    return _selected_provider or get_llm_provider()


def list_models() -> list[str]:
    """
    Lists all models available on the local Ollama server.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    response = _ollama_client().list()
    return sorted(m.model for m in response.models)


def select_model(model: str, provider: str | None = None) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): A model name.
        provider (str): Optional provider override ('ollama' or 'minimax').
    """
    global _selected_model, _selected_provider
    _selected_model = model
    if provider is not None:
        _selected_provider = provider


def get_active_model() -> str | None:
    """
    Returns the currently selected model, or None if none has been selected.
    """
    return _selected_model


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using the configured LLM provider.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    provider = get_provider()

    if provider == "minimax":
        return _generate_text_minimax(prompt, model_name)
    return _generate_text_ollama(prompt, model_name)


def _generate_text_ollama(prompt: str, model_name: str = None) -> str:
    """Generates text using the local Ollama server."""
    model = model_name or _selected_model
    if not model:
        raise RuntimeError(
            "No Ollama model selected. Call select_model() first or pass model_name."
        )

    response = _ollama_client().chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"].strip()


def _generate_text_minimax(prompt: str, model_name: str = None) -> str:
    """Generates text using the MiniMax cloud API (OpenAI-compatible)."""
    model = model_name or _selected_model or get_minimax_model()
    if not model:
        raise RuntimeError(
            "No MiniMax model selected. Set 'minimax_model' in config.json "
            "or call select_model() first."
        )

    client = _minimax_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = response.choices[0].message.content or ""
    # Strip <think>...</think> tags that some MiniMax models may include
    import re

    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content
