import ollama
from openai import OpenAI

from config import get_ollama_base_url, get_llm_provider, get_groq_api_key, get_groq_base_url, get_groq_model

_selected_model: str | None = None


def _ollama_client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())

def _groq_client() -> OpenAI:
    return OpenAI(
        api_key=get_groq_api_key(),
        base_url=get_groq_base_url(),
    )


def list_models() -> list[str]:
    """
    Lists all models available on the configured provider.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    provider = get_llm_provider()
    if provider == "groq":
        return [get_groq_model()]
        
    response = _ollama_client().list()
    return sorted(m.model for m in response.models)


def select_model(model: str) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): An model name.
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
    
    if provider == "groq":
        model = model_name or _selected_model or get_groq_model()
        if not model:
            raise RuntimeError("No Groq model selected or configured.")
            
        client = _groq_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

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
