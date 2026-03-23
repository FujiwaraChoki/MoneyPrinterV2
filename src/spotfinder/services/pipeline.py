"""Full scan pipeline: discover -> enrich -> score."""

from __future__ import annotations

from spotfinder.adapters.db import Database
from spotfinder.adapters.google_maps import GoogleMapsScraper
from spotfinder.adapters.http_client import HttpClient
from spotfinder.core.errors import SpotFinderError
from spotfinder.core.types import ScanRequest, ScanStatus, ScoringWeights
from spotfinder.services.discover import DiscoveryService
from spotfinder.services.enrich import EnrichmentService
from spotfinder.services.score import ScoringService


class Pipeline:
    def __init__(
        self,
        db: Database,
        scraper: GoogleMapsScraper,
        http_client: HttpClient,
        weights: ScoringWeights | None = None,
    ) -> None:
        self._db = db
        self._discover = DiscoveryService(scraper, db)
        self._enrich = EnrichmentService(http_client, db)
        self._score = ScoringService(db, weights)

    def run(self, scan: ScanRequest) -> None:
        """Ejecuta el pipeline completo."""
        self._db.insert_scan(scan)
        try:
            self._execute(scan)
        except SpotFinderError:
            # Scan already marked FAILED by the failing service stage
            return

    def _execute(self, scan: ScanRequest) -> None:
        businesses = self._discover.run(scan)
        if not businesses:
            _complete_empty(scan, self._db)
            return
        self._enrich.run(scan, businesses)
        self._score.run(scan, businesses)


def _complete_empty(scan: ScanRequest, db: Database) -> None:
    scan.advance_status(ScanStatus.ENRICHING)
    scan.advance_status(ScanStatus.SCORING)
    scan.advance_status(ScanStatus.COMPLETED)
    db.update_scan(scan)
