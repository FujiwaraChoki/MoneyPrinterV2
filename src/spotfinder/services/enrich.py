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

        unenriched_ids = set(self._db.get_unenriched_business_ids(scan.id))
        unenriched = [b for b in businesses if b.id in unenriched_ids]
        already_done = len(businesses) - len(unenriched)
        total = len(businesses)
        results: list[DigitalPresence] = []

        for idx, biz in enumerate(unenriched, start=already_done + 1):
            print(f"  Enriqueciendo [{idx}/{total}] {biz.name}...")
            presence = self._enrich_one(biz)
            self._db.insert_presence(presence)
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
        socials = self._social.find(html, biz.website_url) if html else None
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
    check: object,
    socials: object | None,
    email: str | None,
) -> DigitalPresence:
    fb = getattr(socials, "facebook_url", None) if socials else None
    ig = getattr(socials, "instagram_url", None) if socials else None
    wa = getattr(socials, "whatsapp_url", None) if socials else None
    booking = getattr(socials, "has_online_booking", False) if socials else False

    presence = DigitalPresence(
        business_id=business_id,
        has_website=True,
        website_status_code=getattr(check, "status_code", None),
        website_load_time_ms=getattr(check, "load_time_ms", None),
        website_is_mobile_friendly=getattr(check, "is_mobile_friendly", None),
        website_has_ssl=getattr(check, "has_ssl", None),
        website_technology=getattr(check, "technology", None),
        has_facebook=fb is not None,
        facebook_url=fb,
        has_instagram=ig is not None,
        instagram_url=ig,
        has_whatsapp=wa is not None,
        whatsapp_url=wa,
        has_online_booking=booking,
        has_email=email is not None,
    )
    presence.compute_social_count()
    return presence


def _fail_scan(scan: ScanRequest, db: Database, error: str) -> None:
    scan.error_message = error
    scan.advance_status(ScanStatus.FAILED)
    db.update_scan(scan)
