import json
from urllib import error, request

try:
    import ollama
except ImportError:
    ollama = None

from config import (
    get_llm_provider,
    get_ollama_base_url,
    get_openai_api_key,
    get_openai_base_url,
)

_selected_model: str | None = None
_selected_provider: str | None = None


def _normalize_provider(provider: str | None = None) -> str:
    """
    Resolves the provider to use for the current request.

    Args:
        provider (str | None): optional provider override

    Returns:
        provider (str): normalized provider name
    """
    return (provider or _selected_provider or get_llm_provider() or "ollama").strip().lower()


def _ollama_client() -> "ollama.Client":
    """
    Returns an initialized Ollama client.

    Returns:
        client (ollama.Client): Ollama client
    """
    if ollama is None:
        raise RuntimeError(
            "The 'ollama' package is not installed. Install requirements or switch llm_provider to 'openai'."
        )

    return ollama.Client(host=get_ollama_base_url())


def _openai_headers() -> dict:
    """
    Builds headers for the OpenAI API.

    Returns:
        headers (dict): request headers
    """
    api_key = get_openai_api_key()
    if not api_key:
        raise RuntimeError(
            "No OpenAI API key configured. Set openai_api_key in config.json or OPENAI_API_KEY in your environment."
        )

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _openai_request(method: str, path: str, payload: dict | None = None) -> dict:
    """
    Sends an HTTP request to the OpenAI API and returns the parsed JSON body.

    Args:
        method (str): HTTP method
        path (str): endpoint path under the configured base URL
        payload (dict | None): optional JSON payload

    Returns:
        data (dict): parsed JSON response
    """
    base_url = get_openai_base_url().rstrip("/")
    body = None if payload is None else json.dumps(payload).encode("utf-8")

    req = request.Request(
        url=f"{base_url}/{path.lstrip('/')}",
        data=body,
        headers=_openai_headers(),
        method=method,
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
            message = parsed.get("error", {}).get("message", raw)
        except json.JSONDecodeError:
            message = raw or str(exc)
        raise RuntimeError(f"OpenAI API request failed: {message}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not connect to OpenAI API: {exc.reason}") from exc


def _extract_openai_output_text(response: dict) -> str:
    """
    Extracts text from a Responses API payload.

    Args:
        response (dict): raw response JSON

    Returns:
        text (str): generated text content
    """
    outputs = response.get("output", [])
    collected_parts: list[str] = []

    for item in outputs:
        if item.get("type") != "message":
            continue

        for content in item.get("content", []):
            if content.get("type") == "output_text":
                collected_parts.append(content.get("text", ""))

    text = "\n".join(part.strip() for part in collected_parts if part and part.strip()).strip()
    if text:
        return text

    raise RuntimeError("OpenAI API returned no text output.")


def list_models(provider: str | None = None) -> list[str]:
    """
    Lists all models available on the active provider.

    Args:
        provider (str | None): optional provider override

    Returns:
        models (list[str]): sorted model names
    """
    resolved_provider = _normalize_provider(provider)

    if resolved_provider == "openai":
        response = _openai_request("GET", "models")
        return sorted(model["id"] for model in response.get("data", []))

    response = _ollama_client().list()
    return sorted(m.model for m in response.models)


def select_model(model: str, provider: str | None = None) -> None:
    """
    Sets the provider/model to use for all subsequent generate_text calls.

    Args:
        model (str): model name
        provider (str | None): provider override
    """
    global _selected_model, _selected_provider
    _selected_model = model
    _selected_provider = _normalize_provider(provider)


def get_active_model() -> str | None:
    """
    Returns the currently selected model, or None if none has been selected.
    """
    return _selected_model


def get_active_provider() -> str:
    """
    Returns the currently selected provider.
    """
    return _normalize_provider()


def generate_text(
    prompt: str,
    model_name: str = None,
    provider: str | None = None,
) -> str:
    """
    Generates text using the configured LLM provider.

    Args:
        prompt (str): user prompt
        model_name (str): optional model override
        provider (str | None): optional provider override

    Returns:
        response (str): generated text
    """
    resolved_provider = _normalize_provider(provider)
    model = model_name or _selected_model
    if not model:
        raise RuntimeError(
            "No model selected. Set a configured model, call select_model(), or pass model_name."
        )

    if resolved_provider == "openai":
        response = _openai_request(
            "POST",
            "responses",
            {
                "model": model,
                "input": prompt,
            },
        )
        return _extract_openai_output_text(response)

    response = _ollama_client().chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"].strip()
