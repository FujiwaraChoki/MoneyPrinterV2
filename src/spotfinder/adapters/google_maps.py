"""Google Maps scraper adapter using gosom/google-maps-scraper."""

from __future__ import annotations

import csv
import io
import logging
import os
import platform
import shlex
import subprocess
import zipfile

import requests

from spotfinder.core.errors import AdapterError
from spotfinder.core.types import Business, BusinessSource

logger = logging.getLogger(__name__)

_SCRAPER_ZIP_URL = (
    "https://github.com/gosom/google-maps-scraper/archive/refs/heads/main.zip"
)
_BINARY_NAME = (
    "google-maps-scraper.exe"
    if platform.system() == "Windows"
    else "google-maps-scraper"
)
_SCRAPER_TIMEOUT_S = 300

# Maps CSV column names to Business field names
_CSV_TO_FIELD = {
    "title": "name",
    "category": "category",
    "address": "address",
    "phone": "phone",
    "website": "website_url",
    "link": "google_maps_url",
    "place_id": "google_place_id",
    "latitude": "latitude",
    "longitude": "longitude",
    "rating": "google_rating",
    "reviews": "google_review_count",
}


class GoogleMapsScraper:
    def __init__(self, data_dir: str = ".mp") -> None:
        self._data_dir = os.path.abspath(data_dir)
        os.makedirs(self._data_dir, exist_ok=True)

    def discover(
        self, scan_id: str, query: str, language: str = "es"
    ) -> list[Business]:
        """Run the scraper binary, parse CSV output, return Business objects."""
        self._ensure_binary()
        output_path = os.path.join(self._data_dir, f"results_{scan_id}.csv")
        query_path = os.path.join(self._data_dir, f"query_{scan_id}.txt")
        try:
            self._write_query_file(query_path, query)
            self._run_scraper(query_path, output_path, language)
            return self._parse_csv(output_path, scan_id)
        finally:
            self._cleanup(query_path, output_path)

    def _ensure_binary(self) -> None:
        binary_path = self._binary_path()
        if os.path.exists(binary_path):
            return
        if not self._is_go_installed():
            raise AdapterError(
                code="SCRAPER_NOT_FOUND",
                message="Go is not installed. Required to build google-maps-scraper.",
            )
        self._download_and_build()

    def _binary_path(self) -> str:
        return os.path.join(self._data_dir, _BINARY_NAME)

    def _is_go_installed(self) -> bool:
        try:
            subprocess.run(
                ["go", "version"],
                capture_output=True,
                check=True,
                timeout=10,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _download_and_build(self) -> None:
        logger.info("Downloading google-maps-scraper source...")
        try:
            resp = requests.get(_SCRAPER_ZIP_URL, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise AdapterError(
                code="SCRAPER_FAILED",
                message=f"Failed to download scraper: {exc}",
            ) from exc

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for member in zf.namelist():
                if ".." in member or member.startswith("/"):
                    continue
                zf.extract(member, self._data_dir)

        scraper_dir = self._find_scraper_dir()
        if not scraper_dir:
            raise AdapterError(
                code="SCRAPER_FAILED",
                message="Could not find extracted scraper directory.",
            )

        logger.info("Building google-maps-scraper...")
        try:
            subprocess.run(
                ["go", "mod", "download"],
                cwd=scraper_dir,
                check=True,
                capture_output=True,
                timeout=120,
            )
            subprocess.run(
                ["go", "build", "-o", self._binary_path()],
                cwd=scraper_dir,
                check=True,
                capture_output=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as exc:
            raise AdapterError(
                code="SCRAPER_FAILED",
                message=f"Failed to build scraper: {exc.stderr}",
            ) from exc

    def _find_scraper_dir(self) -> str | None:
        for entry in os.listdir(self._data_dir):
            full = os.path.join(self._data_dir, entry)
            if (
                os.path.isdir(full)
                and entry.startswith("google-maps-scraper")
                and os.path.exists(os.path.join(full, "go.mod"))
            ):
                return full
        return None

    def _write_query_file(self, path: str, query: str) -> None:
        with open(path, "w") as f:
            f.write(query + "\n")

    def _run_scraper(
        self, query_path: str, output_path: str, language: str
    ) -> None:
        binary = self._binary_path()
        args_str = f'-input {shlex.quote(query_path)} -results {shlex.quote(output_path)} -lang {shlex.quote(language)}'
        command = [binary] + shlex.split(args_str)
        logger.info("Running scraper: %s", " ".join(command))
        try:
            result = subprocess.run(
                command,
                timeout=_SCRAPER_TIMEOUT_S,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise AdapterError(
                    code="SCRAPER_FAILED",
                    message=f"Scraper exited with code {result.returncode}",
                    context={"stderr": result.stderr[:500]},
                )
        except subprocess.TimeoutExpired as exc:
            raise AdapterError(
                code="SCRAPER_TIMEOUT",
                message=f"Scraper timed out after {_SCRAPER_TIMEOUT_S}s",
            ) from exc

        if not os.path.exists(output_path):
            raise AdapterError(
                code="SCRAPER_FAILED",
                message=f"Scraper produced no output at {output_path}",
            )

    def _parse_csv(self, csv_path: str, scan_id: str) -> list[Business]:
        businesses: list[Business] = []
        with open(csv_path, "r", newline="", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                biz = self._row_to_business(row, scan_id)
                if biz is not None:
                    businesses.append(biz)
        return businesses

    def _row_to_business(
        self, row: dict[str, str], scan_id: str
    ) -> Business | None:
        name = row.get("title", "").strip()
        if not name:
            return None
        return Business(
            scan_id=scan_id,
            name=name,
            category=row.get("category", "").strip(),
            address=row.get("address", "").strip(),
            phone=row.get("phone", "").strip() or None,
            website_url=row.get("website", "").strip() or None,
            google_maps_url=row.get("link", "").strip() or None,
            google_place_id=row.get("place_id", "").strip() or None,
            latitude=_parse_float(row.get("latitude")),
            longitude=_parse_float(row.get("longitude")),
            google_rating=_parse_float(row.get("rating")),
            google_review_count=_parse_int(row.get("reviews")),
            source=BusinessSource.GOOGLE_MAPS,
        )

    def _cleanup(self, *paths: str) -> None:
        for path in paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass


def _parse_float(value: str | None) -> float | None:
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    if not value or not value.strip():
        return None
    try:
        return int(float(value.strip()))
    except ValueError:
        return None
