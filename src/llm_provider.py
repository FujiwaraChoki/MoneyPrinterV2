import os

import ollama

from config import get_ollama_base_url, get_llm_provider, get_openrouter_api_key, get_openrouter_model

_selected_model: str | None = None


def _ollama_client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())


def _openrouter_client():
    from openai import OpenAI
    api_key = get_openrouter_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key not set. Add 'openrouter_api_key' to config.json "
            "or set the OPENROUTER_API_KEY environment variable."
        )
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def list_models() -> list[str]:
    """
    Lists available models for the configured provider.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    provider = get_llm_provider()
    if provider == "openrouter":
        return [get_openrouter_model()]
    response = _ollama_client().list()
    return sorted(m.model for m in response.models)


def select_model(model: str) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): A model name for the configured provider.
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
    Generates text using the configured LLM provider.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    provider = get_llm_provider()
    model = model_name or _selected_model

    if provider == "openrouter":
        if not model:
            model = get_openrouter_model()
        client = _openrouter_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    # Default: Ollama
    if not model:
        raise RuntimeError(
            "No Ollama model selected. Call select_model() first or pass model_name."
        )
    response = _ollama_client().chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()
