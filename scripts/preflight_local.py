#!/usr/bin/env python3
import json
import os
import sys
from typing import Tuple

import requests


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def check_url(url: str, timeout: int = 3) -> Tuple[bool, str]:
    try:
        response = requests.get(url, timeout=timeout)
        return True, f"HTTP {response.status_code}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    if not os.path.exists(CONFIG_PATH):
        fail(f"Falta el archivo de configuración: {CONFIG_PATH}")
        return 1

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    failures = 0

    stt_provider = str(cfg.get("stt_provider", "local_whisper")).lower()

    ok(f"stt_provider={stt_provider}")

    imagemagick_path = cfg.get("imagemagick_path", "")
    if imagemagick_path and os.path.exists(imagemagick_path):
        ok(f"imagemagick_path existe: {imagemagick_path}")
    else:
        warn(
            "imagemagick_path no apunta a un ejecutable válido. "
            "El renderizado de subtítulos de MoviePy puede fallar."
        )

    firefox_profile = cfg.get("firefox_profile", "")
    if firefox_profile:
        if os.path.isdir(firefox_profile):
            ok(f"firefox_profile existe: {firefox_profile}")
        else:
            warn(f"firefox_profile no existe: {firefox_profile}")
    else:
        warn("firefox_profile está vacío. La automatización de Twitter/YouTube lo necesita.")

    # Ollama (LLM)
    base = str(cfg.get("ollama_base_url", "http://127.0.0.1:11434")).rstrip("/")
    reachable, detail = check_url(f"{base}/api/tags")
    if not reachable:
        fail(f"Ollama no es alcanzable en {base}: {detail}")
        failures += 1
    else:
        ok(f"Ollama alcanzable en {base}")
        try:
            tags = requests.get(f"{base}/api/tags", timeout=5).json()
            models = [m.get("name") for m in tags.get("models", [])]
            if models:
                ok(f"Modelos de Ollama disponibles: {', '.join(models[:10])}")
            else:
                warn("No se encontraron modelos en Ollama. Descargá uno primero (ej. 'ollama pull llama3.2:3b').")
        except Exception as exc:
            warn(f"No se pudo validar la lista de modelos de Ollama: {exc}")

    # Nano Banana 2 (image generation)
    api_key = cfg.get("nanobanana2_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
    nb2_base = str(
        cfg.get(
            "nanobanana2_api_base_url",
            "https://generativelanguage.googleapis.com/v1beta",
        )
    ).rstrip("/")
    if api_key:
        ok("nanobanana2_api_key está configurada")
    else:
        fail("nanobanana2_api_key está vacía (y GEMINI_API_KEY no está configurada)")
        failures += 1

    reachable, detail = check_url(nb2_base, timeout=8)
    if not reachable:
        warn(f"No se pudo alcanzar la URL base de Nano Banana 2: {detail}")
    else:
        ok(f"URL base de Nano Banana 2 alcanzable: {nb2_base}")

    if stt_provider == "local_whisper":
        try:
            import faster_whisper  # noqa: F401

            ok("faster-whisper está instalado")
        except Exception as exc:
            fail(f"faster-whisper no se puede importar: {exc}")
            failures += 1

    if failures:
        print("")
        print(f"Verificación previa completada con {failures} problema(s) bloqueante(s).")
        return 1

    print("")
    print("Verificación previa exitosa. La configuración local está lista.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
