import time
import random
import ollama
import requests

from config import get_ollama_base_url, get_gemini_llm_api_key, get_gemini_llm_model

_selected_model: str | None = None

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ollama_client() -> ollama.Client:
    return ollama.Client(host=get_ollama_base_url())


def _gemini_generate(prompt: str, model: str, api_key: str) -> str:
    """
    Calls the Gemini generateContent REST endpoint with exponential back-off
    to avoid hitting rate limits (429 errors).
    """
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    endpoint = f"{base_url}/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
    }

    max_retries = 6
    base_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.post(
                endpoint,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            if response.status_code == 429:
                # Rate limited — wait with jitter and retry
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                print(f"[llm_provider] Rate limited (429). Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue

            response.raise_for_status()
            body = response.json()

            candidates = body.get("candidates", [])
            for candidate in candidates:
                content = candidate.get("content", {})
                for part in content.get("parts", []):
                    text = part.get("text")
                    if text:
                        return text.strip()

            raise RuntimeError(f"Gemini returned no text content. Response: {body}")

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                print(f"[llm_provider] Request error: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise

    raise RuntimeError("Gemini text generation failed after maximum retries.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_models() -> list[str]:
    """
    Lists all models available on the local Ollama server.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    response = _ollama_client().list()
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
    Generates text using Gemini (preferred) or falls back to local Ollama.

    Provider selection order:
      1. If a Gemini API key is configured in config.json → use Gemini Flash
      2. Otherwise → use local Ollama with the selected model

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override (Ollama only)

    Returns:
        response (str): Generated text
    """
    gemini_key = get_gemini_llm_api_key()
    if gemini_key:
        gemini_model = get_gemini_llm_model()
        return _gemini_generate(prompt, gemini_model, gemini_key)

    # Fallback: Ollama
    model = model_name or _selected_model
    if not model:
        raise RuntimeError(
            "No model configured. Set gemini_llm_api_key in config.json "
            "or call select_model() for Ollama."
        )

    response = _ollama_client().chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"].strip()
