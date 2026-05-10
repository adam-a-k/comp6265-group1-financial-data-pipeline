"""
tests/test_forex_fetcher.py — Unit tests for ForexFetcher.

All tests mock requests.get so no real HTTP calls are made.
"""

import math
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ingestion.base import REQUIRED_COLUMNS
from ingestion.forex_fetcher import ForexFetcher


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_fx_response(from_sym: str = "USD", to_sym: str = "EUR", num_days: int = 3) -> dict:
    """Build a minimal Alpha Vantage FX_DAILY response."""
    dates = pd.date_range(end="2024-01-03", periods=num_days, freq="B")
    time_series = {}
    for i, date in enumerate(dates):
        time_series[date.strftime("%Y-%m-%d")] = {
            "1. open": str(0.91 + i * 0.001),
            "2. high": str(0.92 + i * 0.001),
            "3. low":  str(0.90 + i * 0.001),
            "4. close": str(0.915 + i * 0.001),
        }
    return {
        "Meta Data": {
            "1. Information": "Forex Daily Prices (open, high, low, close)",
            "2. From Symbol": from_sym,
            "3. To Symbol": to_sym,
        },
        "Time Series FX (Daily)": time_series,
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

class TestForexFetcherHappyPath:
    def test_returns_dataframe(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response("USD", "EUR", num_days=3)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")

        assert isinstance(df, pd.DataFrame)

    def test_correct_columns(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response("USD", "GBP", num_days=4)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="GBP")

        assert list(df.columns) == REQUIRED_COLUMNS

    def test_correct_row_count(self):
        num_days = 5
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response(num_days=num_days)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")

        assert len(df) == num_days

    def test_volume_is_nan(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response(num_days=3)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")

        assert df["volume"].isna().all()

    def test_symbol_constructed_correctly(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response("USD", "JPY", num_days=2)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="JPY")

        assert (df["symbol"] == "USD/JPY").all()

    def test_source_is_alphavantage(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response(num_days=2)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")

        assert (df["source"] == "alphavantage").all()

    def test_sorted_ascending_by_timestamp(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response(num_days=5)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")

        assert df["timestamp"].is_monotonic_increasing

    def test_numeric_columns_are_float64(self):
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response(num_days=2)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")

        for col in ("open", "high", "low", "close"):
            assert df[col].dtype == "float64", f"Column '{col}' dtype is {df[col].dtype}"

    def test_symbol_string_parsed_correctly(self):
        """fetch() should accept symbol='USD/EUR' as a convenience."""
        fetcher = ForexFetcher(api_key="test_key")
        fx_data = _make_fx_response("USD", "EUR", num_days=2)

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(fx_data)
            df = fetcher.fetch(symbol="USD/EUR")

        assert (df["symbol"] == "USD/EUR").all()


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------

class TestForexFetcherErrorHandling:
    def test_raises_on_error_message(self):
        fetcher = ForexFetcher(api_key="test_key")
        error_response = {"Error Message": "Invalid API call."}

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(error_response)
            with pytest.raises(ValueError, match="Alpha Vantage API error"):
                fetcher.fetch(from_symbol="USD", to_symbol="INVALID")

    def test_raises_on_note_message(self):
        fetcher = ForexFetcher(api_key="test_key")
        note_response = {"Note": "Thank you for using Alpha Vantage! Rate limit reached."}

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(note_response)
            with pytest.raises(ValueError, match="rate-limit note"):
                fetcher.fetch(from_symbol="USD", to_symbol="EUR")

    def test_raises_when_time_series_key_missing(self):
        fetcher = ForexFetcher(api_key="test_key")
        weird_response = {"Meta Data": {}}

        with patch("ingestion.forex_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(weird_response)
            with pytest.raises(ValueError, match="Unexpected response format"):
                fetcher.fetch(from_symbol="USD", to_symbol="EUR")

    def test_raises_when_no_symbol_info_given(self):
        fetcher = ForexFetcher(api_key="test_key")
        with pytest.raises(ValueError, match="Provide either"):
            # No from/to_symbol, and symbol has no slash
            fetcher.fetch(symbol="USDJPY")


# ---------------------------------------------------------------------------
# validate() tests
# ---------------------------------------------------------------------------

class TestForexFetcherValidate:
    def test_validate_passes_with_all_columns(self):
        fetcher = ForexFetcher(api_key="test_key")
        df = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"]
        )
        assert fetcher.validate(df) is True

    def test_validate_raises_when_column_missing(self):
        fetcher = ForexFetcher(api_key="test_key")
        df = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "symbol", "source"]
            # "volume" missing
        )
        with pytest.raises(ValueError, match="volume"):
            fetcher.validate(df)
