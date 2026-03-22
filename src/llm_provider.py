import ollama
from openai import OpenAI

from config import get_ollama_base_url, get_grok_api_key

_selected_model: str | None = None
_provider: str = "ollama"  # "ollama" or "grok"


def set_provider(provider: str) -> None:
    global _provider
    _provider = provider


def get_provider() -> str:
    return _provider


def _client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())


def _grok_client() -> OpenAI:
    return OpenAI(
        api_key=get_grok_api_key(),
        base_url="https://api.x.ai/v1",
    )


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


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using the configured LLM provider.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    if _provider == "grok":
        return _generate_grok(prompt, model_name)
    return _generate_ollama(prompt, model_name)


def _generate_ollama(prompt: str, model_name: str = None) -> str:
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


def _generate_grok(prompt: str, model_name: str = None) -> str:
    model = model_name or _selected_model or "grok-3-mini"
    client = _grok_client()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()
