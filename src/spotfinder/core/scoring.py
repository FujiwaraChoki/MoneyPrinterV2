"""Opportunity scoring for SpotFinder.

Pure scoring logic. Zero external imports beyond core types and errors.
"""

from __future__ import annotations

from spotfinder.core.errors import ScoringError
from spotfinder.core.types import (
    Business,
    DigitalPresence,
    OpportunityScore,
    ScoringWeights,
)

# Deductions from a perfect 1.0 digital gap (no presence at all)
_DIGITAL_DEDUCTIONS: list[tuple[str, float]] = [
    ("has_website", 0.25),
    ("website_has_ssl", 0.10),
    ("website_is_mobile_friendly", 0.10),
    ("has_facebook", 0.10),
    ("has_instagram", 0.10),
    ("has_whatsapp", 0.05),
    ("has_online_booking", 0.15),
    ("has_email", 0.05),
]

_TIER_SCORES: dict[int, float] = {1: 1.0, 2: 0.7, 3: 0.4}


def compute_digital_gap(presence: DigitalPresence) -> float:
    score = 1.0
    for attr, deduction in _DIGITAL_DEDUCTIONS:
        val = getattr(presence, attr, None)
        if val is True:
            score -= deduction
    return round(max(score, 0.0), 4)


def compute_revenue_potential(business: Business, industry_tier: int) -> float:
    if industry_tier not in _TIER_SCORES:
        raise ScoringError(
            code="SCORE_OUT_OF_RANGE",
            message=f"Unknown industry tier: {industry_tier}",
            context={"tier": industry_tier},
        )

    tier_score = _TIER_SCORES[industry_tier]

    rating = business.google_rating
    google_rating_score = (rating - 1.0) / 4.0 if rating is not None else 0.3

    review_count = business.google_review_count
    review_count_score = min(review_count / 100, 1.0) if review_count is not None else 0.1

    address_score = 1.0 if business.address else 0.0
    phone_score = 1.0 if business.phone else 0.0

    return round(
        tier_score * 0.25
        + google_rating_score * 0.25
        + review_count_score * 0.30
        + address_score * 0.10
        + phone_score * 0.10,
        4,
    )


def compute_accessibility(
    business: Business,
    presence: DigitalPresence,
) -> float:
    email_score = 1.0 if presence.has_email else 0.0
    phone_score = 1.0 if business.phone else 0.0
    whatsapp_score = 1.0 if presence.has_whatsapp else 0.0

    has_website_contact = (
        presence.has_website and (presence.has_email or bool(business.phone))
    )
    website_contact_score = 1.0 if has_website_contact else 0.0

    return round(
        email_score * 0.35
        + phone_score * 0.30
        + whatsapp_score * 0.20
        + website_contact_score * 0.15,
        4,
    )


def compute_opportunity_score(
    business: Business,
    presence: DigitalPresence,
    industry_tier: int,
    weights: ScoringWeights,
) -> OpportunityScore:
    digital_gap = compute_digital_gap(presence)
    revenue = compute_revenue_potential(business, industry_tier)
    accessibility = compute_accessibility(business, presence)

    total = (
        digital_gap * weights.digital_gap
        + revenue * weights.revenue_potential
        + accessibility * weights.accessibility
    )

    rationale = generate_rationale(business, digital_gap, revenue, accessibility)

    return OpportunityScore(
        business_id=business.id,
        digital_gap_score=round(digital_gap, 4),
        revenue_potential_score=round(revenue, 4),
        accessibility_score=round(accessibility, 4),
        opportunity_score=round(total, 4),
        scoring_rationale=rationale,
    )


def generate_rationale(
    business: Business,
    digital_gap: float,
    revenue: float,
    accessibility: float,
) -> str:
    gap_label = _level_label(digital_gap)
    revenue_label = _level_label(revenue)
    access_label = _level_label(accessibility)

    return (
        f"{business.name} presenta una brecha digital {gap_label.es} "
        f"con potencial de ingreso {revenue_label.es} "
        f"y accesibilidad {access_label.es}. "
        f"({business.name} has a {gap_label.en} digital gap "
        f"with {revenue_label.en} revenue potential "
        f"and {access_label.en} accessibility.)"
    )


class _LevelLabel:
    __slots__ = ("es", "en")

    def __init__(self, es: str, en: str) -> None:
        self.es = es
        self.en = en


_HIGH = _LevelLabel("alta", "high")
_MEDIUM = _LevelLabel("media", "medium")
_LOW = _LevelLabel("baja", "low")


def _level_label(score: float) -> _LevelLabel:
    if score >= 0.7:
        return _HIGH
    if score >= 0.4:
        return _MEDIUM
    return _LOW
