"""Social media link extractor from HTML content."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HREF_PATTERN = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

_FACEBOOK_PATTERNS = re.compile(
    r'https?://(?:www\.)?(?:facebook\.com|fb\.com|fb\.me)/[^\s"\'<>]+',
    re.IGNORECASE,
)
_INSTAGRAM_PATTERNS = re.compile(
    r'https?://(?:www\.)?instagram\.com/[^\s"\'<>]+',
    re.IGNORECASE,
)
_WHATSAPP_PATTERNS = re.compile(
    r'https?://(?:wa\.me|api\.whatsapp\.com|whatsapp\.com)/[^\s"\'<>]+',
    re.IGNORECASE,
)

_BOOKING_KEYWORDS = re.compile(
    r'(?:calendly\.com|booking|reserv|agendar|appointment|turno)',
    re.IGNORECASE,
)


@dataclass
class SocialPresence:
    facebook_url: str | None
    instagram_url: str | None
    whatsapp_url: str | None
    has_online_booking: bool


class SocialFinder:
    def find(self, html: str, base_url: str) -> SocialPresence:
        """Parse HTML for social media links and booking indicators."""
        hrefs = _HREF_PATTERN.findall(html)
        href_text = " ".join(hrefs)
        searchable = html + " " + href_text

        facebook_url = _first_match(_FACEBOOK_PATTERNS, searchable)
        instagram_url = _first_match(_INSTAGRAM_PATTERNS, searchable)
        whatsapp_url = _first_match(_WHATSAPP_PATTERNS, searchable)
        has_online_booking = _detect_booking(html, hrefs)

        return SocialPresence(
            facebook_url=_clean_url(facebook_url),
            instagram_url=_clean_url(instagram_url),
            whatsapp_url=_clean_url(whatsapp_url),
            has_online_booking=has_online_booking,
        )


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if match:
        return match.group(0)
    return None


def _clean_url(url: str | None) -> str | None:
    """Strip trailing punctuation that might have been captured."""
    if url is None:
        return None
    return url.rstrip(".,;:!?)\"'")


def _detect_booking(html: str, hrefs: list[str]) -> bool:
    for href in hrefs:
        if _BOOKING_KEYWORDS.search(href):
            return True
    return bool(_BOOKING_KEYWORDS.search(html))
