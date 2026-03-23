"""Core data types for SpotFinder.

Every entity, every field, every invariant.
Zero external imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4


def _uuid7_fallback() -> str:
    """UUID v7-ish: timestamp prefix for sortability, random suffix."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    base = uuid4()
    hex_time = f"{now_ms:012x}"
    hex_rand = base.hex[12:]
    combined = hex_time + hex_rand
    return f"{combined[:8]}-{combined[8:12]}-7{combined[13:16]}-{combined[16:20]}-{combined[20:32]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScanStatus(str, Enum):
    PENDING = "pending"
    DISCOVERING = "discovering"
    ENRICHING = "enriching"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


_STATUS_ORDER = {
    ScanStatus.PENDING: 0,
    ScanStatus.DISCOVERING: 1,
    ScanStatus.ENRICHING: 2,
    ScanStatus.SCORING: 3,
    ScanStatus.COMPLETED: 4,
    ScanStatus.FAILED: 5,
}


class BusinessSource(str, Enum):
    GOOGLE_MAPS = "google_maps"
    YELP = "yelp"
    PAGES_AMARILLAS = "pages_amarillas"
    MANUAL = "manual"


@dataclass
class ScanRequest:
    """A single run of the scanner against a location + niche."""

    location_query: str
    niche: str
    country_code: str
    id: str = field(default_factory=_uuid7_fallback)
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = None
    status: ScanStatus = ScanStatus.PENDING
    created_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None
    business_count: int = 0
    error_message: str | None = None

    def advance_status(self, new_status: ScanStatus) -> None:
        """Transition status forward only. Any state can jump to FAILED."""
        if new_status == ScanStatus.FAILED:
            self.status = new_status
            self.completed_at = _now_iso()
            return
        current_order = _STATUS_ORDER[self.status]
        new_order = _STATUS_ORDER[new_status]
        if new_order <= current_order:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}: "
                "status must advance forward"
            )
        self.status = new_status
        if new_status == ScanStatus.COMPLETED:
            self.completed_at = _now_iso()


@dataclass
class Business:
    """A single business discovered in the target area."""

    scan_id: str
    name: str
    category: str
    address: str
    id: str = field(default_factory=_uuid7_fallback)
    phone: str | None = None
    website_url: str | None = None
    email: str | None = None
    google_maps_url: str | None = None
    google_place_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_rating: float | None = None
    google_review_count: int | None = None
    source: BusinessSource = BusinessSource.GOOGLE_MAPS
    discovered_at: str = field(default_factory=_now_iso)
    deleted_at: str | None = None


@dataclass
class DigitalPresence:
    """Digital footprint assessment for a single business. One-to-one."""

    business_id: str
    id: str = field(default_factory=_uuid7_fallback)
    has_website: bool = False
    website_status_code: int | None = None
    website_load_time_ms: int | None = None
    website_is_mobile_friendly: bool | None = None
    website_has_ssl: bool | None = None
    website_technology: str | None = None
    has_facebook: bool = False
    facebook_url: str | None = None
    has_instagram: bool = False
    instagram_url: str | None = None
    has_whatsapp: bool = False
    whatsapp_url: str | None = None
    social_media_count: int = 0
    has_online_booking: bool = False
    has_email: bool = False
    enriched_at: str = field(default_factory=_now_iso)

    def compute_social_count(self) -> None:
        self.social_media_count = sum([
            self.has_facebook,
            self.has_instagram,
            self.has_whatsapp,
        ])


@dataclass
class OpportunityScore:
    """Computed opportunity score for a business. One-to-one."""

    business_id: str
    digital_gap_score: float
    revenue_potential_score: float
    accessibility_score: float
    opportunity_score: float
    scoring_rationale: str
    id: str = field(default_factory=_uuid7_fallback)
    rank: int = 0
    scored_at: str = field(default_factory=_now_iso)


@dataclass(frozen=True)
class ScoringWeights:
    """Configurable weights for the opportunity score formula."""

    digital_gap: float = 0.50
    revenue_potential: float = 0.30
    accessibility: float = 0.20

    def __post_init__(self) -> None:
        total = self.digital_gap + self.revenue_potential + self.accessibility
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total:.3f}"
            )


@dataclass(frozen=True)
class IndustryProfile:
    """A target industry with its search terms and revenue data."""

    slug: str
    name_en: str
    name_es: str
    search_terms_en: list[str]
    search_terms_es: list[str]
    avg_revenue_usd: int
    gross_margin_pct: float
    website_adoption_pct: float
    tier: Literal[1, 2, 3]


# --- 15 Target Industries ---

INDUSTRIES: dict[str, IndustryProfile] = {
    "hvac": IndustryProfile(
        slug="hvac",
        name_en="HVAC",
        name_es="Climatización y Refrigeración",
        search_terms_en=["hvac", "air conditioning repair", "heating contractor"],
        search_terms_es=["aire acondicionado", "refrigeración", "climatización"],
        avg_revenue_usd=1_500_000,
        gross_margin_pct=0.45,
        website_adoption_pct=0.50,
        tier=1,
    ),
    "plumbing": IndustryProfile(
        slug="plumbing",
        name_en="Plumbing",
        name_es="Plomería",
        search_terms_en=["plumber", "plumbing contractor", "plumbing repair"],
        search_terms_es=["plomero", "plomería", "sanitario"],
        avg_revenue_usd=800_000,
        gross_margin_pct=0.50,
        website_adoption_pct=0.45,
        tier=1,
    ),
    "electrical": IndustryProfile(
        slug="electrical",
        name_en="Electrical Contractors",
        name_es="Electricistas",
        search_terms_en=["electrician", "electrical contractor", "electrical repair"],
        search_terms_es=["electricista", "instalaciones eléctricas", "técnico electricista"],
        avg_revenue_usd=900_000,
        gross_margin_pct=0.45,
        website_adoption_pct=0.48,
        tier=1,
    ),
    "roofing": IndustryProfile(
        slug="roofing",
        name_en="Roofing",
        name_es="Techados",
        search_terms_en=["roofing contractor", "roof repair", "roofer"],
        search_terms_es=["techador", "reparación de techos", "techados"],
        avg_revenue_usd=1_200_000,
        gross_margin_pct=0.40,
        website_adoption_pct=0.42,
        tier=1,
    ),
    "dental": IndustryProfile(
        slug="dental",
        name_en="Dental Practices",
        name_es="Consultorios Dentales",
        search_terms_en=["dentist", "dental clinic", "dental office"],
        search_terms_es=["dentista", "odontólogo", "clínica dental"],
        avg_revenue_usd=1_000_000,
        gross_margin_pct=0.35,
        website_adoption_pct=0.65,
        tier=1,
    ),
    "law": IndustryProfile(
        slug="law",
        name_en="Law Firms",
        name_es="Estudios Jurídicos",
        search_terms_en=["lawyer", "law firm", "attorney"],
        search_terms_es=["abogado", "estudio jurídico", "bufete de abogados"],
        avg_revenue_usd=500_000,
        gross_margin_pct=0.55,
        website_adoption_pct=0.60,
        tier=1,
    ),
    "auto_repair": IndustryProfile(
        slug="auto_repair",
        name_en="Auto Repair",
        name_es="Talleres Mecánicos",
        search_terms_en=["auto repair", "mechanic", "car repair shop"],
        search_terms_es=["taller mecánico", "mecánico automotriz", "taller de autos"],
        avg_revenue_usd=600_000,
        gross_margin_pct=0.50,
        website_adoption_pct=0.35,
        tier=1,
    ),
    "construction": IndustryProfile(
        slug="construction",
        name_en="General Construction",
        name_es="Construcción General",
        search_terms_en=["general contractor", "construction company", "builder"],
        search_terms_es=["constructora", "empresa de construcción", "contratista"],
        avg_revenue_usd=2_000_000,
        gross_margin_pct=0.25,
        website_adoption_pct=0.40,
        tier=2,
    ),
    "medical": IndustryProfile(
        slug="medical",
        name_en="Medical Clinics",
        name_es="Clínicas Médicas",
        search_terms_en=["medical clinic", "doctor", "family medicine"],
        search_terms_es=["clínica médica", "consultorio médico", "médico general"],
        avg_revenue_usd=800_000,
        gross_margin_pct=0.35,
        website_adoption_pct=0.55,
        tier=2,
    ),
    "landscaping": IndustryProfile(
        slug="landscaping",
        name_en="Landscaping",
        name_es="Jardinería y Paisajismo",
        search_terms_en=["landscaping", "lawn care", "garden service"],
        search_terms_es=["jardinería", "paisajismo", "mantenimiento de jardines"],
        avg_revenue_usd=400_000,
        gross_margin_pct=0.45,
        website_adoption_pct=0.30,
        tier=2,
    ),
    "pest_control": IndustryProfile(
        slug="pest_control",
        name_en="Pest Control",
        name_es="Control de Plagas",
        search_terms_en=["pest control", "exterminator", "fumigation"],
        search_terms_es=["fumigación", "control de plagas", "fumigador"],
        avg_revenue_usd=350_000,
        gross_margin_pct=0.50,
        website_adoption_pct=0.38,
        tier=2,
    ),
    "veterinary": IndustryProfile(
        slug="veterinary",
        name_en="Veterinary Clinics",
        name_es="Veterinarias",
        search_terms_en=["veterinarian", "vet clinic", "animal hospital"],
        search_terms_es=["veterinaria", "clínica veterinaria", "veterinario"],
        avg_revenue_usd=600_000,
        gross_margin_pct=0.40,
        website_adoption_pct=0.55,
        tier=2,
    ),
    "accounting": IndustryProfile(
        slug="accounting",
        name_en="Accounting & Tax",
        name_es="Contabilidad e Impuestos",
        search_terms_en=["accountant", "tax preparation", "bookkeeper"],
        search_terms_es=["contador", "estudio contable", "asesor impositivo"],
        avg_revenue_usd=300_000,
        gross_margin_pct=0.60,
        website_adoption_pct=0.50,
        tier=2,
    ),
    "real_estate": IndustryProfile(
        slug="real_estate",
        name_en="Real Estate Agencies",
        name_es="Inmobiliarias",
        search_terms_en=["real estate agency", "realtor", "property management"],
        search_terms_es=["inmobiliaria", "agencia inmobiliaria", "bienes raíces"],
        avg_revenue_usd=500_000,
        gross_margin_pct=0.30,
        website_adoption_pct=0.65,
        tier=3,
    ),
    "restaurants": IndustryProfile(
        slug="restaurants",
        name_en="Restaurants",
        name_es="Restaurantes",
        search_terms_en=["restaurant", "dining", "food"],
        search_terms_es=["restaurante", "gastronomía", "comida"],
        avg_revenue_usd=500_000,
        gross_margin_pct=0.10,
        website_adoption_pct=0.55,
        tier=3,
    ),
}
