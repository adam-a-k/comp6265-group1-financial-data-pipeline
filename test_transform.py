"""
Unit Tests — ETL Transform Module
Ausaf's test suite covering all transformation and validation logic.
Run with: pytest tests/etl/test_transform.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from unittest.mock import patch

from src.etl.transform import (
    validate_raw_data,
    validate_business_rules,
    validate_before_load,
    standardise_columns,
    parse_timestamps,
    cast_price_columns,
    handle_nulls,
    add_rolling_average,
    add_price_change_pct,
    transform_stocks,
    transform_crypto,
    transform_forex,
)


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def valid_stock_df():
    return pd.DataFrame({
        "symbol": ["AAPL", "AAPL", "AAPL", "MSFT", "MSFT"],
        "price": [150.0, 152.0, 149.5, 300.0, 305.0],
        "timestamp": [
            "2024-01-01", "2024-01-02", "2024-01-03",
            "2024-01-01", "2024-01-02"
        ],
        "volume": [1000, 1200, 900, 800, 850],
    })


@pytest.fixture
def valid_crypto_df():
    return pd.DataFrame({
        "symbol": ["bitcoin", "bitcoin", "ethereum"],
        "price": [45000.0, 46000.0, 3000.0],
        "timestamp": ["2024-01-01", "2024-01-02", "2024-01-01"],
    })


@pytest.fixture
def valid_forex_df():
    return pd.DataFrame({
        "symbol": ["USD/EUR", "USD/EUR", "USD/GBP"],
        "price": [0.92, 0.91, 0.78],
        "timestamp": ["2024-01-01", "2024-01-02", "2024-01-01"],
    })


# ─────────────────────────────────────────────
# VALIDATE RAW DATA TESTS
# ─────────────────────────────────────────────

class TestValidateRawData:

    def test_passes_with_valid_data(self, valid_stock_df):
        result = validate_raw_data(valid_stock_df, "stocks")
        assert result is not None
        assert len(result) == len(valid_stock_df)

    def test_raises_on_missing_column(self):
        bad_df = pd.DataFrame({"symbol": ["AAPL"], "price": [150.0]})  # no timestamp
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_raw_data(bad_df, "stocks")

    def test_raises_on_null_in_required_field(self):
        bad_df = pd.DataFrame({
            "symbol": ["AAPL", None],
            "price": [150.0, 151.0],
            "timestamp": ["2024-01-01", "2024-01-02"],
        })
        with pytest.raises(ValueError, match="Null values found"):
            validate_raw_data(bad_df, "stocks")

    def test_raises_on_null_price(self):
        bad_df = pd.DataFrame({
            "symbol": ["AAPL"],
            "price": [None],
            "timestamp": ["2024-01-01"],
        })
        with pytest.raises(ValueError, match="Null values found"):
            validate_raw_data(bad_df, "stocks")


# ─────────────────────────────────────────────
# VALIDATE BUSINESS RULES TESTS
# ─────────────────────────────────────────────

class TestValidateBusinessRules:

    def test_passes_with_positive_prices(self, valid_stock_df):
        result = validate_business_rules(valid_stock_df, "stocks")
        assert len(result) == len(valid_stock_df)

    def test_drops_zero_price_rows(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "AAPL"],
            "price": [0.0, 150.0],
            "timestamp": ["2024-01-01", "2024-01-02"],
        })
        result = validate_business_rules(df, "stocks")
        assert len(result) == 1
        assert result.iloc[0]["price"] == 150.0

    def test_drops_negative_price_rows(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "price": [-10.0, 300.0],
            "timestamp": ["2024-01-01", "2024-01-01"],
        })
        result = validate_business_rules(df, "stocks")
        assert len(result) == 1

    def test_drops_non_numeric_price_rows(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "price": ["N/A", 300.0],
            "timestamp": ["2024-01-01", "2024-01-01"],
        })
        result = validate_business_rules(df, "stocks")
        assert len(result) == 1


# ─────────────────────────────────────────────
# VALIDATE BEFORE LOAD TESTS
# ─────────────────────────────────────────────

class TestValidateBeforeLoad:

    def test_removes_duplicates(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "AAPL"],
            "price": [150.0, 150.0],
            "timestamp": ["2024-01-01", "2024-01-01"],
        })
        result = validate_before_load(df, "stocks")
        assert len(result) == 1

    def test_keeps_same_symbol_different_timestamp(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "AAPL"],
            "price": [150.0, 152.0],
            "timestamp": ["2024-01-01", "2024-01-02"],
        })
        result = validate_before_load(df, "stocks")
        assert len(result) == 2


# ─────────────────────────────────────────────
# CLEANING HELPER TESTS
# ─────────────────────────────────────────────

class TestStandardiseColumns:

    def test_lowercases_column_names(self):
        df = pd.DataFrame({"Symbol": [1], "Price": [2], "Timestamp": [3]})
        result = standardise_columns(df)
        assert list(result.columns) == ["symbol", "price", "timestamp"]

    def test_replaces_spaces_with_underscores(self):
        df = pd.DataFrame({"Market Cap": [1], "Open Price": [2]})
        result = standardise_columns(df)
        assert "market_cap" in result.columns
        assert "open_price" in result.columns


class TestParseTimestamps:

    def test_converts_string_to_datetime(self, valid_stock_df):
        result = parse_timestamps(valid_stock_df)
        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])

    def test_drops_rows_with_unparseable_timestamps(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "price": [150.0, 300.0],
            "timestamp": ["not-a-date", "2024-01-01"],
        })
        result = parse_timestamps(df)
        assert len(result) == 1


class TestHandleNulls:

    def test_drops_rows_with_null_symbol(self):
        df = pd.DataFrame({
            "symbol": [None, "AAPL"],
            "price": [150.0, 151.0],
            "timestamp": ["2024-01-01", "2024-01-02"],
        })
        result, dropped = handle_nulls(df)
        assert len(result) == 1
        assert dropped == 1

    def test_returns_zero_dropped_when_no_nulls(self, valid_stock_df):
        result, dropped = handle_nulls(valid_stock_df)
        assert dropped == 0
        assert len(result) == len(valid_stock_df)


# ─────────────────────────────────────────────
# TRANSFORMATION TESTS
# ─────────────────────────────────────────────

class TestRollingAverage:

    def test_creates_rolling_avg_column(self, valid_stock_df):
        result = add_rolling_average(valid_stock_df, window=7)
        assert "rolling_avg_7d" in result.columns

    def test_rolling_avg_is_numeric(self, valid_stock_df):
        result = add_rolling_average(valid_stock_df, window=7)
        assert pd.api.types.is_float_dtype(result["rolling_avg_7d"])

    def test_rolling_avg_per_symbol(self, valid_stock_df):
        result = add_rolling_average(valid_stock_df, window=7)
        # AAPL has 3 rows; the avg of first row should just be that row's price
        aapl = result[result["symbol"] == "AAPL"].sort_values("timestamp")
        assert aapl.iloc[0]["rolling_avg_7d"] == aapl.iloc[0]["price"]

    def test_custom_window(self, valid_stock_df):
        result = add_rolling_average(valid_stock_df, window=3)
        assert "rolling_avg_3d" in result.columns

    def test_no_nulls_in_rolling_avg(self, valid_stock_df):
        result = add_rolling_average(valid_stock_df, window=7)
        assert result["rolling_avg_7d"].isnull().sum() == 0


class TestPriceChangePct:

    def test_creates_price_change_pct_column(self, valid_stock_df):
        result = add_price_change_pct(valid_stock_df)
        assert "price_change_pct" in result.columns

    def test_first_row_per_symbol_is_nan(self, valid_stock_df):
        result = add_price_change_pct(valid_stock_df)
        aapl = result[result["symbol"] == "AAPL"].sort_values("timestamp")
        assert pd.isna(aapl.iloc[0]["price_change_pct"])

    def test_correct_percentage_calculation(self):
        df = pd.DataFrame({
            "symbol": ["AAPL", "AAPL"],
            "price": [100.0, 110.0],
            "timestamp": ["2024-01-01", "2024-01-02"],
        })
        result = add_price_change_pct(df)
        result = result.sort_values("timestamp")
        assert abs(result.iloc[1]["price_change_pct"] - 10.0) < 0.01


# ─────────────────────────────────────────────
# FULL PIPELINE TESTS
# ─────────────────────────────────────────────

class TestTransformStocks:

    @patch("src.etl.transform.log_etl_run")
    def test_returns_dataframe(self, mock_log, valid_stock_df):
        result = transform_stocks(valid_stock_df)
        assert isinstance(result, pd.DataFrame)

    @patch("src.etl.transform.log_etl_run")
    def test_log_etl_run_called(self, mock_log, valid_stock_df):
        transform_stocks(valid_stock_df)
        mock_log.assert_called_once()

    @patch("src.etl.transform.log_etl_run")
    def test_output_has_rolling_avg(self, mock_log, valid_stock_df):
        result = transform_stocks(valid_stock_df)
        assert "rolling_avg_7d" in result.columns

    @patch("src.etl.transform.log_etl_run")
    def test_output_has_price_change(self, mock_log, valid_stock_df):
        result = transform_stocks(valid_stock_df)
        assert "price_change_pct" in result.columns


class TestTransformCrypto:

    @patch("src.etl.transform.log_etl_run")
    def test_returns_dataframe(self, mock_log, valid_crypto_df):
        result = transform_crypto(valid_crypto_df)
        assert isinstance(result, pd.DataFrame)

    @patch("src.etl.transform.log_etl_run")
    def test_output_has_rolling_avg(self, mock_log, valid_crypto_df):
        result = transform_crypto(valid_crypto_df)
        assert "rolling_avg_7d" in result.columns


class TestTransformForex:

    @patch("src.etl.transform.log_etl_run")
    def test_returns_dataframe(self, mock_log, valid_forex_df):
        result = transform_forex(valid_forex_df)
        assert isinstance(result, pd.DataFrame)

    @patch("src.etl.transform.log_etl_run")
    def test_output_has_rolling_avg(self, mock_log, valid_forex_df):
        result = transform_forex(valid_forex_df)
        assert "rolling_avg_7d" in result.columns
