"""Geocoding via OpenStreetMap Nominatim (free, no API key)."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

from spotfinder.adapters.http_client import HttpClient
from spotfinder.core.errors import AdapterError

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


@dataclass
class GeoResult:
    latitude: float
    longitude: float
    display_name: str


class Geocoder:
    def __init__(self, http_client: HttpClient) -> None:
        self._http = http_client

    def geocode(self, location_query: str) -> GeoResult:
        """Convert location string to coordinates via Nominatim.

        Raises:
            AdapterError(code='GEOCODING_FAILED'): on HTTP or parse failure.
            AdapterError(code='GEOCODING_NO_RESULTS'): if no results found.
        """
        query_encoded = quote_plus(location_query)
        url = f"{_NOMINATIM_URL}?q={query_encoded}&format=json&limit=1"

        try:
            response = self._http.get(url, use_cache=True)
        except AdapterError as exc:
            raise AdapterError(
                code="GEOCODING_FAILED",
                message=f"HTTP request failed for geocoding: {location_query}",
                context={"original_error": str(exc)},
            ) from exc

        if response.status_code != 200:
            raise AdapterError(
                code="GEOCODING_FAILED",
                message=f"Nominatim returned status {response.status_code}",
                context={"location_query": location_query},
            )

        return self._parse_response(response.body or "[]", location_query)

    def _parse_response(self, body: str, query: str) -> GeoResult:
        import json

        try:
            results = json.loads(body)
        except json.JSONDecodeError as exc:
            raise AdapterError(
                code="GEOCODING_FAILED",
                message="Failed to parse Nominatim JSON response",
                context={"body_preview": body[:200]},
            ) from exc

        if not results:
            raise AdapterError(
                code="GEOCODING_NO_RESULTS",
                message=f"No geocoding results for: {query}",
                context={"location_query": query},
            )

        first = results[0]
        try:
            return GeoResult(
                latitude=float(first["lat"]),
                longitude=float(first["lon"]),
                display_name=first.get("display_name", query),
            )
        except (KeyError, ValueError) as exc:
            raise AdapterError(
                code="GEOCODING_FAILED",
                message="Invalid data in Nominatim response",
                context={"result": str(first)[:200]},
            ) from exc
