#!/usr/bin/env python3
"""Download Google Fonts (Playfair Display + Lato) into src/etsy/fonts/.

Idempotent: skips files that already exist.
Run from the repo root: python scripts/download_fonts.py
"""
import os
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(REPO_ROOT, "src", "etsy", "fonts")

FONTS = {
    "PlayfairDisplay-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/"
        "PlayfairDisplay%5Bwght%5D.ttf"
    ),
    "PlayfairDisplay-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/"
        "PlayfairDisplay%5Bwght%5D.ttf"
    ),
    "Lato-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf"
    ),
    "Lato-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf"
    ),
    # DM Sans variable font — clean, modern, premium sans-serif (trending 2024-2026)
    # Same file for Regular and Bold (variable wght axis covers 100-900)
    "DMSans-Regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/dmsans/DMSans%5Bopsz%2Cwght%5D.ttf"
    ),
    "DMSans-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/dmsans/DMSans%5Bopsz%2Cwght%5D.ttf"
    ),
}


def main() -> None:
    os.makedirs(FONTS_DIR, exist_ok=True)
    for filename, url in FONTS.items():
        dest = os.path.join(FONTS_DIR, filename)
        if os.path.exists(dest):
            print(f"  skip  {filename} (already exists)")
            continue
        print(f"  fetch {filename} ...", end="", flush=True)
        urllib.request.urlretrieve(url, dest)
        size_kb = os.path.getsize(dest) // 1024
        print(f" {size_kb} KB")
    print("Done.")


if __name__ == "__main__":
    main()
