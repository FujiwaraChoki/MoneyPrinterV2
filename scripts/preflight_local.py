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
        fail(f"Missing config file: {CONFIG_PATH}")
        return 1

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    failures = 0

    llm_provider = str(cfg.get("llm_provider", "local_ollama")).lower()
    image_provider = str(cfg.get("image_provider", "local_automatic1111")).lower()
    stt_provider = str(cfg.get("stt_provider", "local_whisper")).lower()

    ok(f"llm_provider={llm_provider}")
    ok(f"image_provider={image_provider}")
    ok(f"stt_provider={stt_provider}")

    imagemagick_path = cfg.get("imagemagick_path", "")
    if imagemagick_path and os.path.exists(imagemagick_path):
        ok(f"imagemagick_path exists: {imagemagick_path}")
    else:
        warn(
            "imagemagick_path is not set to a valid executable path. "
            "MoviePy subtitle rendering may fail."
        )

    firefox_profile = cfg.get("firefox_profile", "")
    if firefox_profile:
        if os.path.isdir(firefox_profile):
            ok(f"firefox_profile exists: {firefox_profile}")
        else:
            warn(f"firefox_profile does not exist: {firefox_profile}")
    else:
        warn("firefox_profile is empty. Twitter/YouTube automation requires this.")

    if llm_provider == "local_ollama":
        base = str(cfg.get("ollama_base_url", "http://127.0.0.1:11434")).rstrip("/")
        model = cfg.get("ollama_model", "")
        reachable, detail = check_url(f"{base}/api/tags")
        if not reachable:
            fail(f"Ollama is not reachable at {base}: {detail}")
            failures += 1
        else:
            ok(f"Ollama reachable at {base}")
            try:
                tags = requests.get(f"{base}/api/tags", timeout=5).json()
                models = [m.get("name") for m in tags.get("models", [])]
                if model in models:
                    ok(f"Ollama model available: {model}")
                else:
                    warn(
                        f"Ollama model not found: {model}. "
                        f"Installed: {', '.join(models[:10]) or 'none'}"
                    )
            except Exception as exc:
                warn(f"Could not validate Ollama model list: {exc}")

    if image_provider == "local_automatic1111":
        base = str(
            cfg.get("automatic1111_base_url", "http://127.0.0.1:7860")
        ).rstrip("/")
        reachable, detail = check_url(f"{base}/sdapi/v1/sd-models")
        if not reachable:
            fail(
                f"AUTOMATIC1111 API is not reachable at {base}: {detail} "
                "(start webui with --api)"
            )
            failures += 1
        else:
            ok(f"AUTOMATIC1111 API reachable at {base}")

    if image_provider == "third_party_nanobanana2":
        api_key = cfg.get("nanobanana2_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        base = str(
            cfg.get(
                "nanobanana2_api_base_url",
                "https://generativelanguage.googleapis.com/v1beta",
            )
        ).rstrip("/")
        if api_key:
            ok("nanobanana2_api_key is set")
        else:
            fail("nanobanana2_api_key is empty (and GEMINI_API_KEY is not set)")
            failures += 1

        reachable, detail = check_url(base, timeout=8)
        if not reachable:
            warn(f"Nano Banana 2 base URL could not be reached: {detail}")
        else:
            ok(f"Nano Banana 2 base URL reachable: {base}")

    if stt_provider == "local_whisper":
        try:
            import faster_whisper  # noqa: F401

            ok("faster-whisper is installed")
        except Exception as exc:
            fail(f"faster-whisper is not importable: {exc}")
            failures += 1

    if failures:
        print("")
        print(f"Preflight completed with {failures} blocking issue(s).")
        return 1

    print("")
    print("Preflight passed. Local setup looks ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
