"""
news_fetcher.py — Fetch news articles from the NewsAPI /v2/everything endpoint.

Returns a standardised pandas DataFrame ready for consumption by the ETL
and storage layers.
"""

from datetime import datetime, timezone

from .config import NEWS_API_KEY
import pandas as pd
import requests


class NewsFetcher:
    """Fetch news articles from the NewsAPI /v2/everything endpoint."""

    BASE_URL: str = "https://newsapi.org/v2/everything"
    SOURCE: str = "newsapi"

    def __init__(self, api_key: str = NEWS_API_KEY) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        self.api_key = api_key

    def fetch(self, query: str, page_size: int = 20) -> pd.DataFrame:
        """Fetch news articles matching *query*.

        Parameters
        ----------
        query:
            Search query string, e.g. ``"AAPL"`` or ``"bitcoin"``.
        page_size:
            Number of articles to return (default 20, max 100).

        Returns
        -------
        pd.DataFrame
            Columns: ``[source, symbol, timestamp, title, description, url, publisher, fetched_at]``
            ``source`` is always ``"newsapi"``; ``symbol`` is the query string.

        Raises
        ------
        RuntimeError
            On request timeout, HTTP error, or any other network failure.
        """
        try:
            params = {
                "q": query,
                "pageSize": page_size,
                "apiKey": self.api_key,
            }
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            raise RuntimeError(
                f"NewsAPI request timed out for query '{query}': {exc}"
            ) from exc
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"NewsAPI HTTP error for query '{query}': {exc}"
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(
                f"NewsAPI request failed for query '{query}': {exc}"
            ) from exc

        articles = data.get("articles", [])
        fetched_at = datetime.now(timezone.utc)

        if not articles:
            return pd.DataFrame(
                columns=["source", "symbol", "timestamp", "title", "description", "url", "publisher", "fetched_at"]
            )

        records = []
        for article in articles:
            records.append(
                {
                    "source": self.SOURCE,
                    "symbol": query,
                    "timestamp": pd.to_datetime(article.get("publishedAt"), utc=True),
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "publisher": article.get("source", {}).get("name"),
                    "fetched_at": fetched_at,
                }
            )

        return pd.DataFrame(
            records,
            columns=["source", "symbol", "timestamp", "title", "description", "url", "publisher", "fetched_at"],
        )
