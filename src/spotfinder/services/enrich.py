"""Digital presence enrichment orchestration."""

from __future__ import annotations

from spotfinder.adapters.db import Database
from spotfinder.adapters.email_extractor import EmailExtractor
from spotfinder.adapters.http_client import HttpClient
from spotfinder.adapters.social_finder import SocialFinder
from spotfinder.adapters.website_checker import WebsiteChecker
from spotfinder.core.errors import AdapterError
from spotfinder.core.types import (
    Business,
    DigitalPresence,
    ScanRequest,
    ScanStatus,
)


class EnrichmentService:
    def __init__(self, http_client: HttpClient, db: Database) -> None:
        self._http = http_client
        self._checker = WebsiteChecker(http_client)
        self._social = SocialFinder()
        self._email = EmailExtractor()
        self._db = db

    def run(
        self, scan: ScanRequest, businesses: list[Business],
    ) -> list[DigitalPresence]:
        """Enriquece todos los negocios con datos de presencia digital."""
        try:
            return self._execute(scan, businesses)
        except AdapterError as exc:
            _fail_scan(scan, self._db, str(exc))
            raise

    def _execute(
        self, scan: ScanRequest, businesses: list[Business],
    ) -> list[DigitalPresence]:
        scan.advance_status(ScanStatus.ENRICHING)
        self._db.update_scan(scan)

        enriched_ids = self._db.get_enriched_business_ids(scan.id)
        unenriched = [b for b in businesses if b.id not in enriched_ids]
        total = len(businesses)
        results: list[DigitalPresence] = []

        for idx, biz in enumerate(unenriched, start=len(enriched_ids) + 1):
            print(f"  Enriqueciendo [{idx}/{total}] {biz.name}...")
            presence = self._enrich_one(biz)
            self._db.insert_digital_presence(presence)
            results.append(presence)

        already = self._db.get_digital_presences_by_scan(scan.id)
        return already

    def _enrich_one(self, biz: Business) -> DigitalPresence:
        if not biz.website_url:
            return _minimal_presence(biz.id)
        return self._enrich_with_website(biz)

    def _enrich_with_website(self, biz: Business) -> DigitalPresence:
        assert biz.website_url is not None
        check = self._checker.check(biz.website_url)

        html = _fetch_html(self._http, biz.website_url)
        socials = self._social.find(html, biz.website_url) if html else {}
        email = self._email.extract(html) if html else None

        presence = _build_presence(biz.id, check, socials, email)
        return presence


def _fetch_html(http: HttpClient, url: str) -> str | None:
    try:
        response = http.get(url)
        if 200 <= response.status_code < 300:
            return response.body
    except AdapterError:
        pass
    return None


def _minimal_presence(business_id: str) -> DigitalPresence:
    return DigitalPresence(business_id=business_id)


def _build_presence(
    business_id: str,
    check: dict[str, object],
    socials: dict[str, str | None],
    email: str | None,
) -> DigitalPresence:
    presence = DigitalPresence(
        business_id=business_id,
        has_website=True,
        website_status_code=check.get("status_code"),
        website_load_time_ms=check.get("load_time_ms"),
        website_is_mobile_friendly=check.get("is_mobile_friendly"),
        website_has_ssl=check.get("has_ssl"),
        website_technology=check.get("cms"),
        has_facebook=socials.get("facebook_url") is not None,
        facebook_url=socials.get("facebook_url"),
        has_instagram=socials.get("instagram_url") is not None,
        instagram_url=socials.get("instagram_url"),
        has_whatsapp=socials.get("whatsapp_url") is not None,
        whatsapp_url=socials.get("whatsapp_url"),
        has_email=email is not None,
    )
    presence.compute_social_count()
    return presence


def _fail_scan(scan: ScanRequest, db: Database, error: str) -> None:
    scan.error_message = error
    scan.advance_status(ScanStatus.FAILED)
    db.update_scan(scan)
