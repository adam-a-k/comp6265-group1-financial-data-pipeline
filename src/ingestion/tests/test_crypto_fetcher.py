"""
tests/test_crypto_fetcher.py — Unit tests for CryptoFetcher.

All tests mock requests.get so no real HTTP calls are made.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ingestion.base import REQUIRED_COLUMNS
from ingestion.crypto_fetcher import CryptoFetcher


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_ohlc_response(num_candles: int = 4) -> list:
    """Build a minimal CoinGecko /coins/{id}/ohlc response.

    Each entry is [timestamp_ms, open, high, low, close].
    """
    base_ts = 1_704_067_200_000  # 2024-01-01 00:00:00 UTC in ms
    interval_ms = 4 * 60 * 60 * 1_000  # 4 hours (typical for 30-day range)
    candles = []
    for i in range(num_candles):
        ts = base_ts + i * interval_ms
        candles.append([ts, 42_000.0 + i, 42_500.0 + i, 41_800.0 + i, 42_200.0 + i])
    return candles


def _mock_response(json_data, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestCryptoFetcherHappyPath:
    def test_returns_dataframe(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=4)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("bitcoin")

        assert isinstance(df, pd.DataFrame)

    def test_correct_columns(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=3)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("ethereum")

        assert list(df.columns) == REQUIRED_COLUMNS

    def test_correct_row_count(self):
        num_candles = 7
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=num_candles)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("bitcoin")

        assert len(df) == num_candles

    def test_volume_is_nan(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=3)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("bitcoin")

        assert df["volume"].isna().all()

    def test_symbol_and_source_columns(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=2)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("solana")

        assert (df["symbol"] == "solana").all()
        assert (df["source"] == "coingecko").all()

    def test_timestamp_converted_from_milliseconds(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=2)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("bitcoin")

        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        # First timestamp in our fixture is 2024-01-01 00:00:00 UTC
        expected_first = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
        assert df["timestamp"].iloc[0] == expected_first

    def test_sorted_ascending_by_timestamp(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=6)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("bitcoin")

        assert df["timestamp"].is_monotonic_increasing

    def test_numeric_columns_are_float64(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=2)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            df = fetcher.fetch("bitcoin")

        for col in ("open", "high", "low", "close"):
            assert df[col].dtype == "float64", f"Column '{col}' dtype is {df[col].dtype}"

    def test_api_called_with_correct_url(self):
        fetcher = CryptoFetcher()
        ohlc_data = _make_ohlc_response(num_candles=2)

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ohlc_data)
            fetcher.fetch("ethereum", vs_currency="eur", days=7)

        call_args = mock_get.call_args
        called_url = call_args[0][0]
        assert "ethereum" in called_url
        assert "ohlc" in called_url

        called_params = call_args[1]["params"]
        assert called_params["vs_currency"] == "eur"
        assert called_params["days"] == 7


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------

class TestCryptoFetcherErrorHandling:
    def test_raises_when_response_is_dict_not_list(self):
        fetcher = CryptoFetcher()
        error_response = {"error": "coin not found"}

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = _mock_response(error_response)
            with pytest.raises(ValueError, match="expected a list"):
                fetcher.fetch("not_a_real_coin")

    def test_http_error_propagates(self):
        """A 429 Too Many Requests should propagate as an HTTPError."""
        import requests as req_lib

        fetcher = CryptoFetcher()
        mock = MagicMock()
        mock.raise_for_status.side_effect = req_lib.HTTPError("429 Too Many Requests")

        with patch("ingestion.crypto_fetcher.requests.get") as mock_get:
            mock_get.return_value = mock
            with pytest.raises(req_lib.HTTPError):
                # retry decorator will retry 3 times; all will raise
                fetcher.fetch("bitcoin")


# ---------------------------------------------------------------------------
# validate() tests
# ---------------------------------------------------------------------------

class TestCryptoFetcherValidate:
    def test_validate_passes_with_all_columns(self):
        fetcher = CryptoFetcher()
        df = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"]
        )
        assert fetcher.validate(df) is True

    def test_validate_raises_when_column_missing(self):
        fetcher = CryptoFetcher()
        # Missing "source"
        df = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume", "symbol"]
        )
        with pytest.raises(ValueError, match="source"):
            fetcher.validate(df)

    def test_validate_raises_listing_all_missing_columns(self):
        fetcher = CryptoFetcher()
        df = pd.DataFrame(columns=["timestamp"])
        with pytest.raises(ValueError, match="missing required columns"):
            fetcher.validate(df)
