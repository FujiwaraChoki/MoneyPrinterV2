import re
from typing import Optional

import requests


class XquikClientError(RuntimeError):
    """
    Raised when Xquik research cannot return a valid result page.
    """


class Xquik:
    """
    Thin client for bounded Xquik tweet searches.

    Docs: https://github.com/Xquik-dev/x-twitter-scraper#run-one-request
    """

    SEARCH_URL = "https://xquik.com/api/v1/x/tweets/search"

    def __init__(
        self,
        api_key: str,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("An Xquik API key is required.")

        self._api_key = api_key.strip()
        self._session = session or requests.Session()

    def search_tweets(self, query: str, limit: int) -> list[dict]:
        """
        Search recent public X posts and return bounded prompt-safe fields.

        Args:
            query (str): X search query.
            limit (int): Maximum number of posts to return.

        Returns:
            tweets (list[dict]): Normalized source records.
        """
        normalized_query = " ".join(query.split())
        if not normalized_query:
            return []
        if limit < 1 or limit > 25:
            raise ValueError("Xquik search limit must be between 1 and 25.")

        try:
            response = self._session.get(
                self.SEARCH_URL,
                headers={
                    "Accept": "application/json",
                    "x-api-key": self._api_key,
                },
                params={
                    "q": normalized_query,
                    "queryType": "Latest",
                    "replies": "exclude",
                    "retweets": "exclude",
                    "quotes": "exclude",
                    "limit": limit,
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise XquikClientError("Xquik search request failed.") from exc

        if response.status_code != 200:
            raise XquikClientError(
                f"Xquik search returned HTTP {response.status_code}."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise XquikClientError("Xquik search returned invalid JSON.") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("tweets"), list):
            raise XquikClientError("Xquik search returned an invalid response.")

        sources = []
        for tweet in payload["tweets"][:limit]:
            source = self._normalize_tweet(tweet)
            if source is not None:
                sources.append(source)

        return sources

    def _normalize_tweet(self, tweet: object) -> Optional[dict]:
        if not isinstance(tweet, dict):
            return None

        tweet_id = tweet.get("id")
        text = tweet.get("text")
        if not isinstance(tweet_id, str) or re.fullmatch(r"[0-9]+", tweet_id) is None:
            return None
        if not isinstance(text, str):
            return None

        normalized_text = " ".join(text.split())[:500]
        if not normalized_text:
            return None

        source = {
            "text": normalized_text,
            "url": f"https://x.com/i/web/status/{tweet_id}",
        }

        author = tweet.get("author")
        if isinstance(author, dict):
            username = author.get("username")
            if isinstance(username, str) and re.fullmatch(
                r"[A-Za-z0-9_]{1,15}", username
            ):
                source["author"] = f"@{username}"

        created_at = tweet.get("createdAt")
        if isinstance(created_at, str) and 1 <= len(created_at) <= 40:
            source["created_at"] = created_at

        return source
