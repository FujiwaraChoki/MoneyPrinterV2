"""SQLite schema definition for SpotFinder."""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_requests (
    id TEXT PRIMARY KEY,
    location_query TEXT NOT NULL,
    niche TEXT NOT NULL,
    country_code TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    radius_km REAL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    completed_at TEXT,
    business_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS businesses (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL REFERENCES scan_requests(id),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT,
    website_url TEXT,
    email TEXT,
    google_maps_url TEXT,
    google_place_id TEXT,
    latitude REAL,
    longitude REAL,
    google_rating REAL,
    google_review_count INTEGER,
    source TEXT NOT NULL DEFAULT 'google_maps',
    discovered_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS digital_presences (
    id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL UNIQUE REFERENCES businesses(id),
    has_website INTEGER NOT NULL DEFAULT 0,
    website_status_code INTEGER,
    website_load_time_ms INTEGER,
    website_is_mobile_friendly INTEGER,
    website_has_ssl INTEGER,
    website_technology TEXT,
    has_facebook INTEGER NOT NULL DEFAULT 0,
    facebook_url TEXT,
    has_instagram INTEGER NOT NULL DEFAULT 0,
    instagram_url TEXT,
    has_whatsapp INTEGER NOT NULL DEFAULT 0,
    whatsapp_url TEXT,
    social_media_count INTEGER NOT NULL DEFAULT 0,
    has_online_booking INTEGER NOT NULL DEFAULT 0,
    has_email INTEGER NOT NULL DEFAULT 0,
    enriched_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS opportunity_scores (
    id TEXT PRIMARY KEY,
    business_id TEXT NOT NULL UNIQUE REFERENCES businesses(id),
    digital_gap_score REAL NOT NULL,
    revenue_potential_score REAL NOT NULL,
    accessibility_score REAL NOT NULL,
    opportunity_score REAL NOT NULL,
    scoring_rationale TEXT NOT NULL,
    rank INTEGER NOT NULL DEFAULT 0,
    scored_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_businesses_scan_id
    ON businesses(scan_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_digital_presences_business_id
    ON digital_presences(business_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_business_id
    ON opportunity_scores(business_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_score
    ON opportunity_scores(opportunity_score DESC) WHERE deleted_at IS NULL;
"""
