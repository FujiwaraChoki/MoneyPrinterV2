"""Shared HTTP client with caching, retry, and rate limiting."""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from spotfinder.core.errors import AdapterError

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

_MAX_ATTEMPTS = 3
_BASE_DELAY_S = 1.0
_JITTER_FACTOR = 0.25


@dataclass
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    body: str | None
    elapsed_ms: int
    from_cache: bool


class HttpClient:
    def __init__(
        self,
        timeout_s: int = 10,
        cache_dir: str = "~/.spotfinder/cache",
        cache_ttl_hours: int = 24,
        min_domain_gap_s: float = 1.0,
    ) -> None:
        self._timeout_s = timeout_s
        self._cache_dir = os.path.expanduser(cache_dir)
        self._cache_ttl_s = cache_ttl_hours * 3600
        self._min_domain_gap_s = min_domain_gap_s
        self._last_request_by_domain: dict[str, float] = {}
        os.makedirs(self._cache_dir, exist_ok=True)

    def get(self, url: str, use_cache: bool = True) -> HttpResponse:
        """GET with retry, disk cache, and rate limiting."""
        if use_cache:
            cached = self._read_cache(url)
            if cached is not None:
                return cached
        response = self._request_with_retry("GET", url)
        if use_cache and 200 <= response.status_code < 300:
            self._write_cache(url, response)
        return response

    def head(self, url: str) -> HttpResponse:
        """HEAD request, no caching, with retry."""
        return self._request_with_retry("HEAD", url)

    def _request_with_retry(self, method: str, url: str) -> HttpResponse:
        self._rate_limit(url)
        last_error: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                start = time.monotonic()
                resp = requests.request(
                    method,
                    url,
                    timeout=self._timeout_s,
                    headers={"User-Agent": random.choice(_USER_AGENTS)},
                    allow_redirects=True,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                self._record_request_time(url)
                result = HttpResponse(
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    body=resp.text if method == "GET" else None,
                    elapsed_ms=elapsed_ms,
                    from_cache=False,
                )
                if 400 <= resp.status_code < 500:
                    return result
                if resp.status_code >= 500:
                    last_error = AdapterError(
                        code="HTTP_UNREACHABLE",
                        message=f"Server error {resp.status_code} for {url}",
                    )
                    self._backoff(attempt)
                    continue
                return result
            except requests.exceptions.Timeout as exc:
                last_error = exc
                self._backoff(attempt)
            except requests.exceptions.RequestException as exc:
                last_error = exc
                self._backoff(attempt)
        raise AdapterError(
            code="HTTP_UNREACHABLE",
            message=f"Failed after {_MAX_ATTEMPTS} attempts: {url}",
            context={"last_error": str(last_error)},
        )

    def _backoff(self, attempt: int) -> None:
        delay = _BASE_DELAY_S * (2 ** attempt)
        jitter = delay * _JITTER_FACTOR * (2 * random.random() - 1)
        time.sleep(delay + jitter)

    def _rate_limit(self, url: str) -> None:
        domain = urlparse(url).netloc
        last_time = self._last_request_by_domain.get(domain)
        if last_time is not None:
            elapsed = time.monotonic() - last_time
            if elapsed < self._min_domain_gap_s:
                time.sleep(self._min_domain_gap_s - elapsed)

    def _record_request_time(self, url: str) -> None:
        domain = urlparse(url).netloc
        self._last_request_by_domain[domain] = time.monotonic()

    def _cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def _cache_body_path(self, key: str) -> str:
        return os.path.join(self._cache_dir, key)

    def _cache_meta_path(self, key: str) -> str:
        return os.path.join(self._cache_dir, f"{key}.meta.json")

    def _read_cache(self, url: str) -> HttpResponse | None:
        key = self._cache_key(url)
        meta_path = self._cache_meta_path(key)
        body_path = self._cache_body_path(key)
        if not os.path.exists(meta_path) or not os.path.exists(body_path):
            return None
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            cached_at = meta["cached_at"]
            if time.time() - cached_at > self._cache_ttl_s:
                return None
            with open(body_path, "r", encoding="utf-8", errors="replace") as f:
                body = f.read()
            return HttpResponse(
                status_code=meta["status_code"],
                headers=meta.get("headers", {}),
                body=body,
                elapsed_ms=0,
                from_cache=True,
            )
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def _write_cache(self, url: str, response: HttpResponse) -> None:
        key = self._cache_key(url)
        meta = {
            "url": url,
            "status_code": response.status_code,
            "headers": response.headers,
            "cached_at": time.time(),
        }
        try:
            with open(self._cache_meta_path(key), "w") as f:
                json.dump(meta, f)
            with open(self._cache_body_path(key), "w", encoding="utf-8") as f:
                f.write(response.body or "")
        except OSError:
            pass
