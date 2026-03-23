"""Business discovery orchestration."""

from __future__ import annotations

from spotfinder.adapters.db import Database
from spotfinder.adapters.google_maps import GoogleMapsScraper
from spotfinder.core.errors import AdapterError
from spotfinder.core.types import Business, ScanRequest, ScanStatus


class DiscoveryService:
    def __init__(self, scraper: GoogleMapsScraper, db: Database) -> None:
        self._scraper = scraper
        self._db = db

    def run(self, scan: ScanRequest) -> list[Business]:
        """Descubre negocios para el escaneo dado."""
        try:
            return self._execute(scan)
        except AdapterError as exc:
            _fail_scan(scan, self._db, str(exc))
            raise

    def _execute(self, scan: ScanRequest) -> list[Business]:
        scan.advance_status(ScanStatus.DISCOVERING)
        self._db.update_scan(scan)

        query = _build_query(scan)
        raw_businesses = self._scraper.discover(scan.id, query)
        unique = _deduplicate(raw_businesses)
        self._db.insert_businesses(unique)

        scan.business_count = len(unique)
        self._db.update_scan(scan)
        return unique


def _build_query(scan: ScanRequest) -> str:
    return f"{scan.niche} en {scan.location_query}"


def _deduplicate(businesses: list[Business]) -> list[Business]:
    seen_place_ids: set[str] = set()
    seen_name_addr: set[tuple[str, str]] = set()
    result: list[Business] = []

    for biz in businesses:
        if biz.google_place_id:
            if biz.google_place_id in seen_place_ids:
                continue
            seen_place_ids.add(biz.google_place_id)
        else:
            key = (biz.name.lower().strip(), biz.address.lower().strip())
            if key in seen_name_addr:
                continue
            seen_name_addr.add(key)
        result.append(biz)

    return result


def _fail_scan(scan: ScanRequest, db: Database, error: str) -> None:
    scan.error_message = error
    scan.advance_status(ScanStatus.FAILED)
    db.update_scan(scan)
