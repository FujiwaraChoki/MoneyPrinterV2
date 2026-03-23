"""Website quality checker — SSL, load time, mobile, CMS detection."""

from __future__ import annotations

import re
from dataclasses import dataclass

from spotfinder.adapters.http_client import HttpClient, HttpResponse
from spotfinder.core.errors import AdapterError

_CMS_SIGNATURES: list[tuple[str, list[str]]] = [
    ("WordPress", ["wp-content", "wp-includes"]),
    ("Wix", ["wix.com", "_wix"]),
    ("Squarespace", ["squarespace.com", "sqsp"]),
    ("Shopify", ["cdn.shopify.com"]),
    ("Webflow", ["webflow.com"]),
]

_VIEWPORT_PATTERN = re.compile(
    r'<meta[^>]+name\s*=\s*["\']viewport["\']', re.IGNORECASE
)


@dataclass
class WebsiteCheckResult:
    is_reachable: bool
    status_code: int | None
    load_time_ms: int | None
    has_ssl: bool | None
    is_mobile_friendly: bool | None
    technology: str | None


class WebsiteChecker:
    def __init__(self, http_client: HttpClient) -> None:
        self._http = http_client

    def check(self, url: str) -> WebsiteCheckResult:
        """Check SSL, load time, mobile-friendliness, CMS detection."""
        url = self._normalize_url(url)
        has_ssl = self._check_ssl(url)
        try:
            response = self._http.get(url, use_cache=False)
        except AdapterError:
            return WebsiteCheckResult(
                is_reachable=False,
                status_code=None,
                load_time_ms=None,
                has_ssl=has_ssl,
                is_mobile_friendly=None,
                technology=None,
            )

        if response.status_code >= 400:
            return WebsiteCheckResult(
                is_reachable=False,
                status_code=response.status_code,
                load_time_ms=response.elapsed_ms,
                has_ssl=has_ssl,
                is_mobile_friendly=None,
                technology=None,
            )

        body = response.body or ""
        return WebsiteCheckResult(
            is_reachable=True,
            status_code=response.status_code,
            load_time_ms=response.elapsed_ms,
            has_ssl=has_ssl,
            is_mobile_friendly=_detect_mobile_friendly(body),
            technology=_detect_cms(body),
        )

    def _normalize_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            return f"https://{url}"
        return url

    def _check_ssl(self, url: str) -> bool:
        if not url.startswith("https://"):
            return False
        try:
            self._http.head(url)
            return True
        except AdapterError:
            return False


def _detect_mobile_friendly(html: str) -> bool:
    return bool(_VIEWPORT_PATTERN.search(html))


def _detect_cms(html: str) -> str:
    html_lower = html.lower()
    for cms_name, signatures in _CMS_SIGNATURES:
        for sig in signatures:
            if sig.lower() in html_lower:
                return cms_name
    return "Custom/Other"
