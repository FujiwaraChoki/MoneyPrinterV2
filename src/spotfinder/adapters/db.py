"""SQLite adapter. ALL SQL lives here."""

from __future__ import annotations

import os
import sqlite3

from spotfinder.adapters.db_mappers import (
    business_to_tuple,
    row_to_business,
    row_to_presence,
    row_to_scan,
    row_to_score,
)
from spotfinder.adapters.db_schema import SCHEMA_SQL, SCHEMA_VERSION
from spotfinder.core.errors import StorageError
from spotfinder.core.types import (
    Business,
    DigitalPresence,
    OpportunityScore,
    ScanRequest,
)


class Database:
    def __init__(self, db_path: str = "~/.spotfinder/spotfinder.db") -> None:
        self._db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(SCHEMA_SQL)
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if row is None:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(code="DB_MIGRATION_FAILED", message=f"Schema init failed: {exc}") from exc

    # --- ScanRequest ---

    def insert_scan(self, scan: ScanRequest) -> None:
        self._write(
            """INSERT INTO scan_requests
               (id, location_query, niche, country_code, latitude, longitude,
                radius_km, status, created_at, completed_at, business_count, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (scan.id, scan.location_query, scan.niche, scan.country_code,
             scan.latitude, scan.longitude, scan.radius_km, scan.status.value,
             scan.created_at, scan.completed_at, scan.business_count, scan.error_message),
            "insert scan",
        )

    def update_scan(self, scan: ScanRequest) -> None:
        self._write(
            """UPDATE scan_requests
               SET status=?, completed_at=?, business_count=?, error_message=?, latitude=?, longitude=?
               WHERE id=?""",
            (scan.status.value, scan.completed_at, scan.business_count,
             scan.error_message, scan.latitude, scan.longitude, scan.id),
            "update scan",
        )

    def get_scan(self, scan_id: str) -> ScanRequest | None:
        row = self._fetch_one("SELECT * FROM scan_requests WHERE id=? AND deleted_at IS NULL", (scan_id,), "get scan")
        return row_to_scan(row) if row else None

    def list_scans(self, limit: int = 20) -> list[ScanRequest]:
        rows = self._fetch_all(
            "SELECT * FROM scan_requests WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT ?",
            (limit,), "list scans",
        )
        return [row_to_scan(r) for r in rows]

    # --- Business ---

    def insert_businesses(self, businesses: list[Business]) -> int:
        if not businesses:
            return 0
        conn = self._connect()
        try:
            cursor = conn.executemany(
                """INSERT OR IGNORE INTO businesses
                   (id, scan_id, name, category, address, phone, website_url, email,
                    google_maps_url, google_place_id, latitude, longitude,
                    google_rating, google_review_count, source, discovered_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [business_to_tuple(b) for b in businesses],
            )
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as exc:
            raise StorageError(code="DB_WRITE_FAILED", message=f"insert businesses: {exc}") from exc

    def get_businesses(self, scan_id: str) -> list[Business]:
        rows = self._fetch_all(
            "SELECT * FROM businesses WHERE scan_id=? AND deleted_at IS NULL ORDER BY name",
            (scan_id,), "get businesses",
        )
        return [row_to_business(r) for r in rows]

    def get_business(self, business_id: str) -> Business | None:
        row = self._fetch_one("SELECT * FROM businesses WHERE id=? AND deleted_at IS NULL", (business_id,), "get business")
        return row_to_business(row) if row else None

    # --- DigitalPresence ---

    def insert_presence(self, presence: DigitalPresence) -> None:
        self._write(
            """INSERT OR REPLACE INTO digital_presences
               (id, business_id, has_website, website_status_code, website_load_time_ms,
                website_is_mobile_friendly, website_has_ssl, website_technology,
                has_facebook, facebook_url, has_instagram, instagram_url,
                has_whatsapp, whatsapp_url, social_media_count, has_online_booking,
                has_email, enriched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (presence.id, presence.business_id, presence.has_website,
             presence.website_status_code, presence.website_load_time_ms,
             presence.website_is_mobile_friendly, presence.website_has_ssl,
             presence.website_technology, presence.has_facebook, presence.facebook_url,
             presence.has_instagram, presence.instagram_url, presence.has_whatsapp,
             presence.whatsapp_url, presence.social_media_count,
             presence.has_online_booking, presence.has_email, presence.enriched_at),
            "insert presence",
        )

    def get_presence(self, business_id: str) -> DigitalPresence | None:
        row = self._fetch_one(
            "SELECT * FROM digital_presences WHERE business_id=? AND deleted_at IS NULL",
            (business_id,), "get presence",
        )
        return row_to_presence(row) if row else None

    def get_unenriched_business_ids(self, scan_id: str) -> list[str]:
        rows = self._fetch_all(
            """SELECT b.id FROM businesses b
               LEFT JOIN digital_presences dp ON b.id=dp.business_id AND dp.deleted_at IS NULL
               WHERE b.scan_id=? AND b.deleted_at IS NULL AND dp.id IS NULL""",
            (scan_id,), "get unenriched IDs",
        )
        return [row["id"] for row in rows]

    # --- OpportunityScore ---

    def insert_score(self, score: OpportunityScore) -> None:
        self._write(
            """INSERT OR REPLACE INTO opportunity_scores
               (id, business_id, digital_gap_score, revenue_potential_score,
                accessibility_score, opportunity_score, scoring_rationale, rank, scored_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (score.id, score.business_id, score.digital_gap_score,
             score.revenue_potential_score, score.accessibility_score,
             score.opportunity_score, score.scoring_rationale, score.rank, score.scored_at),
            "insert score",
        )

    def get_scores(self, scan_id: str, limit: int = 50) -> list[OpportunityScore]:
        rows = self._fetch_all(
            """SELECT os.* FROM opportunity_scores os
               JOIN businesses b ON os.business_id=b.id
               WHERE b.scan_id=? AND b.deleted_at IS NULL
               ORDER BY os.opportunity_score DESC LIMIT ?""",
            (scan_id, limit), "get scores",
        )
        return [row_to_score(r) for r in rows]

    # --- ScanRequest extras ---

    def get_latest_scan(self) -> ScanRequest | None:
        row = self._fetch_one(
            "SELECT * FROM scan_requests WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 1",
            (), "get latest scan",
        )
        return row_to_scan(row) if row else None

    # --- DigitalPresence extras ---

    def get_digital_presences_by_scan(self, scan_id: str) -> list[DigitalPresence]:
        rows = self._fetch_all(
            """SELECT dp.* FROM digital_presences dp
               JOIN businesses b ON dp.business_id=b.id
               WHERE b.scan_id=? AND b.deleted_at IS NULL AND dp.deleted_at IS NULL""",
            (scan_id,), "get presences by scan",
        )
        return [row_to_presence(r) for r in rows]

    # --- Internal helpers ---

    def _write(self, sql: str, params: tuple[object, ...], label: str) -> None:
        conn = self._connect()
        try:
            conn.execute(sql, params)
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(code="DB_WRITE_FAILED", message=f"{label}: {exc}") from exc

    def _fetch_one(self, sql: str, params: tuple[object, ...], label: str) -> sqlite3.Row | None:
        conn = self._connect()
        try:
            return conn.execute(sql, params).fetchone()
        except sqlite3.Error as exc:
            raise StorageError(code="DB_READ_FAILED", message=f"{label}: {exc}") from exc

    def _fetch_all(self, sql: str, params: tuple[object, ...], label: str) -> list[sqlite3.Row]:
        conn = self._connect()
        try:
            return conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(code="DB_READ_FAILED", message=f"{label}: {exc}") from exc
