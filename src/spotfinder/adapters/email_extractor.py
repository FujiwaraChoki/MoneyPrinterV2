"""Email address extraction from HTML content."""

from __future__ import annotations

import re

_EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)
_MAILTO_PATTERN = re.compile(
    r'href\s*=\s*["\']mailto:([^"\'?]+)', re.IGNORECASE
)

_GENERIC_PREFIXES = frozenset({
    "noreply",
    "no-reply",
    "info",
    "admin",
    "webmaster",
    "support",
    "contact",
    "hello",
    "mail",
    "sales",
})


class EmailExtractor:
    def extract(self, html: str) -> str | None:
        """Extract the best email from HTML.

        Prefer mailto: links, then regex matches.
        Filter generic addresses. Return the most specific one, or None.
        """
        mailto_emails = _MAILTO_PATTERN.findall(html)
        regex_emails = _EMAIL_PATTERN.findall(html)

        all_emails = _deduplicate(mailto_emails + regex_emails)
        valid_emails = [e for e in all_emails if _is_valid_email(e)]
        if not valid_emails:
            return None

        personal = [e for e in valid_emails if not _is_generic(e)]
        if personal:
            return personal[0]

        return valid_emails[0]


def _deduplicate(emails: list[str]) -> list[str]:
    """Preserve order, remove duplicates (case-insensitive)."""
    seen: set[str] = set()
    result: list[str] = []
    for email in emails:
        lower = email.lower().strip()
        if lower not in seen:
            seen.add(lower)
            result.append(email.strip())
    return result


def _is_valid_email(email: str) -> bool:
    """Basic structural validation."""
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.endswith(".png") or domain.endswith(".jpg"):
        return False
    return True


def _is_generic(email: str) -> bool:
    """Check if the email uses a generic prefix."""
    local = email.split("@")[0].lower()
    return local in _GENERIC_PREFIXES
