"""Row-to-dataclass mappers for the SQLite adapter."""

from __future__ import annotations

import sqlite3

from spotfinder.core.types import (
    Business,
    BusinessSource,
    DigitalPresence,
    OpportunityScore,
    ScanRequest,
    ScanStatus,
)


def row_to_scan(row: sqlite3.Row) -> ScanRequest:
    return ScanRequest(
        id=row["id"], location_query=row["location_query"],
        niche=row["niche"], country_code=row["country_code"],
        latitude=row["latitude"], longitude=row["longitude"],
        radius_km=row["radius_km"], status=ScanStatus(row["status"]),
        created_at=row["created_at"], completed_at=row["completed_at"],
        business_count=row["business_count"],
        error_message=row["error_message"],
    )


def row_to_business(row: sqlite3.Row) -> Business:
    return Business(
        id=row["id"], scan_id=row["scan_id"], name=row["name"],
        category=row["category"], address=row["address"],
        phone=row["phone"], website_url=row["website_url"],
        email=row["email"], google_maps_url=row["google_maps_url"],
        google_place_id=row["google_place_id"],
        latitude=row["latitude"], longitude=row["longitude"],
        google_rating=row["google_rating"],
        google_review_count=row["google_review_count"],
        source=BusinessSource(row["source"]),
        discovered_at=row["discovered_at"],
    )


def row_to_presence(row: sqlite3.Row) -> DigitalPresence:
    return DigitalPresence(
        id=row["id"], business_id=row["business_id"],
        has_website=bool(row["has_website"]),
        website_status_code=row["website_status_code"],
        website_load_time_ms=row["website_load_time_ms"],
        website_is_mobile_friendly=_opt_bool(row["website_is_mobile_friendly"]),
        website_has_ssl=_opt_bool(row["website_has_ssl"]),
        website_technology=row["website_technology"],
        has_facebook=bool(row["has_facebook"]),
        facebook_url=row["facebook_url"],
        has_instagram=bool(row["has_instagram"]),
        instagram_url=row["instagram_url"],
        has_whatsapp=bool(row["has_whatsapp"]),
        whatsapp_url=row["whatsapp_url"],
        social_media_count=row["social_media_count"],
        has_online_booking=bool(row["has_online_booking"]),
        has_email=bool(row["has_email"]),
        enriched_at=row["enriched_at"],
    )


def row_to_score(row: sqlite3.Row) -> OpportunityScore:
    return OpportunityScore(
        id=row["id"], business_id=row["business_id"],
        digital_gap_score=row["digital_gap_score"],
        revenue_potential_score=row["revenue_potential_score"],
        accessibility_score=row["accessibility_score"],
        opportunity_score=row["opportunity_score"],
        scoring_rationale=row["scoring_rationale"],
        rank=row["rank"], scored_at=row["scored_at"],
    )


def row_to_score_and_business(
    row: sqlite3.Row,
) -> tuple[OpportunityScore, Business]:
    # JOIN produces: os.* (10 cols including deleted_at), then b.* (17 cols)
    score = OpportunityScore(
        id=row[0], business_id=row[1],
        digital_gap_score=row[2], revenue_potential_score=row[3],
        accessibility_score=row[4], opportunity_score=row[5],
        scoring_rationale=row[6], rank=row[7], scored_at=row[8],
    )
    o = 10  # offset past opportunity_scores columns + deleted_at
    business = Business(
        id=row[o], scan_id=row[o + 1], name=row[o + 2],
        category=row[o + 3], address=row[o + 4], phone=row[o + 5],
        website_url=row[o + 6], email=row[o + 7],
        google_maps_url=row[o + 8], google_place_id=row[o + 9],
        latitude=row[o + 10], longitude=row[o + 11],
        google_rating=row[o + 12], google_review_count=row[o + 13],
        source=BusinessSource(row[o + 14]), discovered_at=row[o + 15],
    )
    return (score, business)


def business_to_tuple(b: Business) -> tuple[object, ...]:
    return (
        b.id, b.scan_id, b.name, b.category, b.address, b.phone,
        b.website_url, b.email, b.google_maps_url, b.google_place_id,
        b.latitude, b.longitude, b.google_rating, b.google_review_count,
        b.source.value, b.discovered_at,
    )


def _opt_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)
