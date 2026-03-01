import requests
import g4f

from status import warning
from config import *
from constants import parse_model


def _generate_with_ollama(prompt: str, model_name: str = None) -> str:
    """
    Generates text using a local Ollama server.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    base_url = get_ollama_base_url().rstrip("/")
    model = model_name or get_ollama_model()

    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        },
        timeout=180
    )
    response.raise_for_status()

    payload = response.json()
    return payload.get("message", {}).get("content", "").strip()


def _generate_with_g4f(prompt: str, model_name: str = None) -> str:
    """
    Generates text using g4f-backed third-party models.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    model_to_use = parse_model(model_name or get_model())

    return g4f.ChatCompletion.create(
        model=model_to_use,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


def generate_text(prompt: str, model_name: str = None) -> str:
    """
    Generates text using the configured provider.

    Providers:
    - local_ollama
    - third_party_g4f

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override

    Returns:
        response (str): Generated text
    """
    provider = str(get_llm_provider() or "local_ollama").lower()

    if provider == "local_ollama":
        return _generate_with_ollama(prompt, model_name=None)

    if provider == "third_party_g4f":
        return _generate_with_g4f(prompt, model_name=model_name)

    warning(f"Unknown llm_provider '{provider}'. Falling back to local_ollama.")
    return _generate_with_ollama(prompt, model_name=None)
