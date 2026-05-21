import ollama

from config import get_ollama_base_url

_selected_model: str | None = None


def _client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())


def list_models() -> list[str]:
    """
    Lists all models available on the local Ollama server.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    try:
        response = _client().list()
    except Exception as exc:
        raise RuntimeError(
            f"Unable to list Ollama models from {get_ollama_base_url()}: {exc}"
        ) from exc

    try:
        return sorted(m.model for m in response.models)
    except Exception as exc:
        raise RuntimeError("Ollama returned an unexpected model list response") from exc


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
    Generates text using the local Ollama server.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    model = model_name or _selected_model
    if not model:
        raise RuntimeError(
            "No Ollama model selected. Call select_model() first or pass model_name."
        )

    try:
        response = _client().chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise RuntimeError(f"Ollama chat request failed for model '{model}': {exc}") from exc

    try:
        return response["message"]["content"].strip()
    except Exception as exc:
        raise RuntimeError("Ollama returned an unexpected chat response") from exc
