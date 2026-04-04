#!/usr/bin/env python3
import json
import os
import sys
from typing import Tuple

import requests


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_openrouter_api_key(cfg: dict) -> str:
    configured = cfg.get("openrouter_api_key", "")
    return str(configured or os.environ.get("OPENROUTER_API_KEY", ""))


def resolve_openrouter_model(cfg: dict) -> str:
    configured = cfg.get("openrouter_model", "")
    return str(configured or os.environ.get("OPENROUTER_MODEL", ""))


def resolve_openrouter_base_url(cfg: dict) -> str:
    return str(cfg.get("openrouter_base_url", "") or DEFAULT_OPENROUTER_BASE_URL)


def check_url(url: str, timeout: int = 3) -> Tuple[bool, str]:
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return True, f"HTTP {response.status_code}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    if not os.path.exists(CONFIG_PATH):
        fail(f"Missing config file: {CONFIG_PATH}")
        return 1

    cfg = load_config()

    failures = 0

    stt_provider = str(cfg.get("stt_provider", "local_whisper")).lower()

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

    openrouter_api_key = resolve_openrouter_api_key(cfg)
    if openrouter_api_key:
        ok("OpenRouter API key is set")
    else:
        fail("No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY.")
        failures += 1

    openrouter_model = resolve_openrouter_model(cfg)
    if openrouter_model:
        ok(f"OpenRouter model configured: {openrouter_model}")
    else:
        fail("No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL.")
        failures += 1

    base = resolve_openrouter_base_url(cfg).rstrip("/")
    reachable, detail = check_url(f"{base}/models")
    if not reachable:
        fail(f"OpenRouter is not reachable at {base}: {detail}")
        failures += 1
    else:
        ok(f"OpenRouter reachable at {base}")

    # Nano Banana 2 (image generation)
    api_key = cfg.get("nanobanana2_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
    nb2_base = str(
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

    reachable, detail = check_url(nb2_base, timeout=8)
    if not reachable:
        warn(f"Nano Banana 2 base URL could not be reached: {detail}")
    else:
        ok(f"Nano Banana 2 base URL reachable: {nb2_base}")

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
