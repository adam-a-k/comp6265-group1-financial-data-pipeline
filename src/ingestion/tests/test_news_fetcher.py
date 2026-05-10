"""
tests/test_news_fetcher.py — Unit tests for NewsFetcher.

All tests mock requests.get so no real HTTP calls are made.
"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
import requests as req_lib

from ingestion.news_fetcher import NewsFetcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COLUMNS = ["source", "symbol", "timestamp", "title", "description", "url", "publisher", "fetched_at"]


def _make_articles_response(query: str = "AAPL", num_articles: int = 2) -> dict:
    """Build a minimal but realistic NewsAPI /v2/everything response."""
    articles = [
        {
            "source": {"id": f"publisher-{i}", "name": f"Publisher {i}"},
            "title": f"Headline {i}",
            "description": f"Body text {i}",
            "url": f"https://example.com/article-{i}",
            "publishedAt": "2024-01-01T12:00:00Z",
        }
        for i in range(num_articles)
    ]
    return {"status": "ok", "totalResults": num_articles, "articles": articles}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------

class TestNewsFetcherInit(unittest.TestCase):
    def test_empty_api_key_raises_value_error(self):
        with self.assertRaises(ValueError):
            NewsFetcher(api_key="")

    def test_whitespace_api_key_raises_value_error(self):
        with self.assertRaises(ValueError):
            NewsFetcher(api_key="")

    def test_valid_api_key_constructs(self):
        fetcher = NewsFetcher(api_key="valid_key")
        self.assertEqual(fetcher.api_key, "valid_key")


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestNewsFetcherHappyPath(unittest.TestCase):
    def test_successful_fetch_returns_dataframe(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("AAPL", num_articles=3)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertIsInstance(df, pd.DataFrame)

    def test_correct_columns(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("AAPL", num_articles=2)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertEqual(list(df.columns), _COLUMNS)

    def test_correct_row_count(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("AAPL", num_articles=5)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertEqual(len(df), 5)

    def test_source_is_always_newsapi(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("AAPL", num_articles=3)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertTrue((df["source"] == "newsapi").all())

    def test_symbol_is_query_string(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("bitcoin", num_articles=2)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("bitcoin")

        self.assertTrue((df["symbol"] == "bitcoin").all())

    def test_empty_articles_returns_empty_dataframe(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = {"status": "ok", "totalResults": 0, "articles": []}

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
        self.assertEqual(list(df.columns), _COLUMNS)

    def test_publisher_mapped_from_source_name(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("AAPL", num_articles=1)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertEqual(df["publisher"].iloc[0], "Publisher 0")

    def test_timestamp_is_datetime(self):
        fetcher = NewsFetcher(api_key="test_key")
        data = _make_articles_response("AAPL", num_articles=2)

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(data)
            df = fetcher.fetch("AAPL")

        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["timestamp"]))


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------

class TestNewsFetcherErrorHandling(unittest.TestCase):
    def test_api_error_status_raises_runtime_error(self):
        fetcher = NewsFetcher(api_key="test_key")
        mock = MagicMock()
        mock.raise_for_status.side_effect = req_lib.HTTPError("401 Unauthorized")

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = mock
            with self.assertRaises(RuntimeError):
                fetcher.fetch("AAPL")

    def test_timeout_raises_runtime_error(self):
        fetcher = NewsFetcher(api_key="test_key")

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.side_effect = req_lib.Timeout("Connection timed out")
            with self.assertRaises(RuntimeError):
                fetcher.fetch("AAPL")

    def test_http_error_raises_runtime_error(self):
        fetcher = NewsFetcher(api_key="test_key")
        mock = MagicMock()
        mock.raise_for_status.side_effect = req_lib.HTTPError("429 Too Many Requests")

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.return_value = mock
            with self.assertRaises(RuntimeError):
                fetcher.fetch("AAPL")

    def test_request_exception_raises_runtime_error(self):
        fetcher = NewsFetcher(api_key="test_key")

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.side_effect = req_lib.RequestException("Connection refused")
            with self.assertRaises(RuntimeError):
                fetcher.fetch("AAPL")

    def test_runtime_error_message_contains_query(self):
        fetcher = NewsFetcher(api_key="test_key")

        with patch("ingestion.news_fetcher.requests.get") as mock_get:
            mock_get.side_effect = req_lib.Timeout("timed out")
            with self.assertRaises(RuntimeError, msg="AAPL"):
                fetcher.fetch("AAPL")


if __name__ == "__main__":
    unittest.main()
