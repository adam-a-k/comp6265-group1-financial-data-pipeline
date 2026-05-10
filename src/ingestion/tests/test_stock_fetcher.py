"""
tests/test_stock_fetcher.py — Unit tests for StockFetcher.

All tests mock requests.get so no real HTTP calls are made.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ingestion.base import REQUIRED_COLUMNS
from ingestion.stock_fetcher import StockFetcher


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_av_response(symbol: str = "AAPL", num_days: int = 3) -> dict:
    """Build a minimal but realistic Alpha Vantage TIME_SERIES_DAILY response."""
    dates = pd.date_range(end="2024-01-03", periods=num_days, freq="B")
    time_series = {}
    for i, date in enumerate(dates):
        time_series[date.strftime("%Y-%m-%d")] = {
            "1. open": str(170.0 + i),
            "2. high": str(175.0 + i),
            "3. low": str(168.0 + i),
            "4. close": str(172.0 + i),
            "5. volume": str(50_000_000 + i * 1_000_000),
        }
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": symbol,
        },
        "Time Series (Daily)": time_series,
    }


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestStockFetcherHappyPath:
    def test_returns_dataframe(self):
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("AAPL", num_days=3)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("AAPL")

        assert isinstance(df, pd.DataFrame)

    def test_correct_columns(self):
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("MSFT", num_days=5)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("MSFT")

        assert list(df.columns) == REQUIRED_COLUMNS

    def test_correct_row_count(self):
        num_days = 5
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("AAPL", num_days=num_days)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("AAPL")

        assert len(df) == num_days

    def test_numeric_columns_are_float64(self):
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("AAPL", num_days=2)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("AAPL")

        for col in ("open", "high", "low", "close", "volume"):
            assert df[col].dtype == "float64", f"Column '{col}' dtype is {df[col].dtype}"

    def test_sorted_ascending_by_timestamp(self):
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("AAPL", num_days=5)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("AAPL")

        assert df["timestamp"].is_monotonic_increasing

    def test_symbol_and_source_columns(self):
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("GOOGL", num_days=2)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("GOOGL")

        assert (df["symbol"] == "GOOGL").all()
        assert (df["source"] == "alphavantage").all()

    def test_timestamp_is_datetime(self):
        fetcher = StockFetcher(api_key="test_key")
        av_data = _make_av_response("AAPL", num_days=2)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            df = fetcher.fetch("AAPL")

        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_api_called_with_correct_params(self):
        fetcher = StockFetcher(api_key="MY_KEY")
        av_data = _make_av_response("AMZN", num_days=2)

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(av_data)
            fetcher.fetch("AMZN", outputsize="full")

        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
        assert params["function"] == "TIME_SERIES_DAILY"
        assert params["symbol"] == "AMZN"
        assert params["outputsize"] == "full"
        assert params["apikey"] == "MY_KEY"


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------

class TestStockFetcherErrorHandling:
    def test_raises_on_error_message(self):
        fetcher = StockFetcher(api_key="test_key")
        error_response = {"Error Message": "Invalid API call. Please retry or visit..."}

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(error_response)
            with pytest.raises(ValueError, match="Alpha Vantage API error"):
                fetcher.fetch("INVALID")

    def test_raises_on_note_message(self):
        fetcher = StockFetcher(api_key="test_key")
        note_response = {
            "Note": (
                "Thank you for using Alpha Vantage! Our standard API rate limit is "
                "25 requests per day."
            )
        }

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(note_response)
            with pytest.raises(ValueError, match="rate-limit note"):
                fetcher.fetch("AAPL")

    def test_raises_on_information_message(self):
        fetcher = StockFetcher(api_key="test_key")
        info_response = {"Information": "The **demo** API key is for demo purposes only."}

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(info_response)
            with pytest.raises(ValueError, match="information message"):
                fetcher.fetch("AAPL")

    def test_raises_when_time_series_key_missing(self):
        fetcher = StockFetcher(api_key="test_key")
        weird_response = {"Meta Data": {}, "Something Else": {}}

        with patch("ingestion.stock_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(weird_response)
            with pytest.raises(ValueError, match="Unexpected response format"):
                fetcher.fetch("AAPL")


# ---------------------------------------------------------------------------
# validate() tests (via BaseFetcher)
# ---------------------------------------------------------------------------

class TestStockFetcherValidate:
    def test_validate_passes_with_all_columns(self):
        fetcher = StockFetcher(api_key="test_key")
        df = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"]
        )
        assert fetcher.validate(df) is True

    def test_validate_raises_when_column_missing(self):
        fetcher = StockFetcher(api_key="test_key")
        df = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "symbol", "source"]
            # "volume" is missing
        )
        with pytest.raises(ValueError, match="volume"):
            fetcher.validate(df)

    def test_validate_raises_listing_all_missing_columns(self):
        fetcher = StockFetcher(api_key="test_key")
        df = pd.DataFrame(columns=["timestamp", "close"])
        with pytest.raises(ValueError, match="missing required columns"):
            fetcher.validate(df)
