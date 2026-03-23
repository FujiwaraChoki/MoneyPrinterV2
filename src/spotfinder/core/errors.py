"""Typed error hierarchy for SpotFinder.

Services throw. Handlers catch. Core returns.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SpotFinderError(Exception):
    """Base error. All SpotFinder errors inherit from this."""

    code: str
    message: str
    context: dict[str, object] = field(default_factory=dict)

    def __str__(self) -> str:
        ctx = f" {self.context}" if self.context else ""
        return f"[{self.code}] {self.message}{ctx}"


@dataclass(frozen=True)
class ValidationError(SpotFinderError):
    """Invalid input at the system boundary.

    Codes: INVALID_LOCATION, INVALID_NICHE, INVALID_COUNTRY_CODE,
           INVALID_URL, INVALID_COORDINATES, INVALID_RADIUS
    """


@dataclass(frozen=True)
class AdapterError(SpotFinderError):
    """External I/O failure.

    Codes: SCRAPER_TIMEOUT, SCRAPER_FAILED, SCRAPER_NOT_FOUND,
           HTTP_UNREACHABLE, HTTP_TIMEOUT, GEOCODING_FAILED,
           GEOCODING_NO_RESULTS
    """


@dataclass(frozen=True)
class ScoringError(SpotFinderError):
    """Invariant violation in scoring logic.

    Codes: SCORE_OUT_OF_RANGE, MISSING_DIGITAL_PRESENCE
    """


@dataclass(frozen=True)
class StorageError(SpotFinderError):
    """Database read/write failure.

    Codes: DB_WRITE_FAILED, DB_READ_FAILED, DB_MIGRATION_FAILED,
           DB_NOT_FOUND
    """
