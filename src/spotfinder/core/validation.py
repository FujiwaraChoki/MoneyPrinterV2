"""Input validation for SpotFinder.

Pure functions. Fail loudly with ValidationError at system boundaries.
"""

from __future__ import annotations

from urllib.parse import urlparse

from spotfinder.core.errors import ValidationError


def validate_location(location_query: str) -> str:
    cleaned = location_query.strip()
    if not cleaned:
        raise ValidationError(
            code="INVALID_LOCATION",
            message="Location query must be non-empty",
        )
    return cleaned


def validate_coordinates(
    lat: float | None,
    lng: float | None,
    radius_km: float | None,
) -> tuple[float, float, float] | None:
    provided = [v is not None for v in (lat, lng, radius_km)]
    if not any(provided):
        return None
    if not all(provided):
        raise ValidationError(
            code="INVALID_COORDINATES",
            message="lat, lng, and radius_km must all be provided together",
            context={"lat": lat, "lng": lng, "radius_km": radius_km},
        )

    assert lat is not None and lng is not None and radius_km is not None
    _validate_lat(lat)
    _validate_lng(lng)
    _validate_radius(radius_km)

    return (lat, lng, radius_km)


def validate_niche(niche: str) -> str:
    cleaned = niche.strip().lower()
    if not cleaned:
        raise ValidationError(
            code="INVALID_NICHE",
            message="Niche must be non-empty",
        )
    return cleaned


def validate_country_code(code: str) -> str:
    cleaned = code.strip().upper()
    if len(cleaned) != 2 or not cleaned.isalpha():
        raise ValidationError(
            code="INVALID_COUNTRY_CODE",
            message="Country code must be exactly 2 alphabetic characters",
            context={"received": code},
        )
    return cleaned


def validate_url(url: str) -> str:
    stripped = url.strip()
    parsed = urlparse(stripped)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(
            code="INVALID_URL",
            message="URL must start with http:// or https://",
            context={"received": stripped},
        )
    if not parsed.hostname:
        raise ValidationError(
            code="INVALID_URL",
            message="URL must have a host",
            context={"received": stripped},
        )
    return stripped


def validate_email(email: str) -> str:
    stripped = email.strip()
    parts = stripped.split("@")
    if len(parts) != 2:
        raise ValidationError(
            code="INVALID_EMAIL",
            message="Email must contain exactly one @",
            context={"received": stripped},
        )
    local, domain = parts
    if not local or not domain:
        raise ValidationError(
            code="INVALID_EMAIL",
            message="Email must have non-empty local and domain parts",
            context={"received": stripped},
        )
    return stripped


# --- Private helpers ---


def _validate_lat(lat: float) -> None:
    if not -90 <= lat <= 90:
        raise ValidationError(
            code="INVALID_COORDINATES",
            message="Latitude must be between -90 and 90",
            context={"lat": lat},
        )


def _validate_lng(lng: float) -> None:
    if not -180 <= lng <= 180:
        raise ValidationError(
            code="INVALID_COORDINATES",
            message="Longitude must be between -180 and 180",
            context={"lng": lng},
        )


def _validate_radius(radius_km: float) -> None:
    if radius_km <= 0 or radius_km > 100:
        raise ValidationError(
            code="INVALID_RADIUS",
            message="Radius must be > 0 and <= 100 km",
            context={"radius_km": radius_km},
        )
