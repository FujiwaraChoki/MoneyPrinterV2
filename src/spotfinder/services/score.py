"""Opportunity scoring orchestration."""

from __future__ import annotations

from spotfinder.adapters.db import Database
from spotfinder.core.errors import AdapterError, ScoringError
from spotfinder.core.scoring import compute_opportunity_score
from spotfinder.core.types import (
    Business,
    INDUSTRIES,
    OpportunityScore,
    ScanRequest,
    ScanStatus,
    ScoringWeights,
)

_DEFAULT_TIER = 2


class ScoringService:
    def __init__(
        self, db: Database, weights: ScoringWeights | None = None,
    ) -> None:
        self._db = db
        self._weights = weights or ScoringWeights()

    def run(
        self, scan: ScanRequest, businesses: list[Business],
    ) -> list[OpportunityScore]:
        """Puntua todos los negocios descubiertos."""
        try:
            return self._execute(scan, businesses)
        except (AdapterError, ScoringError) as exc:
            _fail_scan(scan, self._db, str(exc))
            raise

    def _execute(
        self, scan: ScanRequest, businesses: list[Business],
    ) -> list[OpportunityScore]:
        scan.advance_status(ScanStatus.SCORING)
        self._db.update_scan(scan)

        tier = _resolve_industry_tier(scan.niche)
        scores = _score_all(businesses, self._db, tier, self._weights)
        ranked = _assign_ranks(scores)

        for score in ranked:
            self._db.insert_score(score)

        scan.advance_status(ScanStatus.COMPLETED)
        self._db.update_scan(scan)
        return ranked


def _resolve_industry_tier(niche: str) -> int:
    niche_lower = niche.lower().strip()
    for profile in INDUSTRIES.values():
        if profile.slug == niche_lower:
            return profile.tier
        all_terms = profile.search_terms_en + profile.search_terms_es
        if niche_lower in [t.lower() for t in all_terms]:
            return profile.tier
    return _DEFAULT_TIER


def _score_all(
    businesses: list[Business],
    db: Database,
    tier: int,
    weights: ScoringWeights,
) -> list[OpportunityScore]:
    scores: list[OpportunityScore] = []
    for biz in businesses:
        presence = db.get_digital_presence(biz.id)
        score = compute_opportunity_score(biz, presence, tier, weights)
        scores.append(score)
    return scores


def _assign_ranks(scores: list[OpportunityScore]) -> list[OpportunityScore]:
    sorted_scores = sorted(
        scores, key=lambda s: s.opportunity_score, reverse=True,
    )
    for rank, score in enumerate(sorted_scores, start=1):
        score.rank = rank
    return sorted_scores


def _fail_scan(scan: ScanRequest, db: Database, error: str) -> None:
    scan.error_message = error
    scan.advance_status(ScanStatus.FAILED)
    db.update_scan(scan)
