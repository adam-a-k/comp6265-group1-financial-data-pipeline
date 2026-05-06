"""
Tests for src/etl/cleaner.py

Run with:  pytest src/etl/tests/test_cleaner.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../"))

from src.etl.cleaner import clean


# ── Fixtures ──────────────────────────────────────────────────

def make_raw_df(rows=5, source="alphavantage", symbol="AAPL"):
    """Helper: returns a minimal valid raw DataFrame."""
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=rows, freq="D", tz="UTC"),
        "open":   [150.0 + i for i in range(rows)],
        "high":   [155.0 + i for i in range(rows)],
        "low":    [148.0 + i for i in range(rows)],
        "close":  [152.0 + i for i in range(rows)],
        "volume": [1_000_000.0] * rows,
        "symbol": [symbol] * rows,
        "source": [source] * rows,
    })


# ── Happy path ────────────────────────────────────────────────

class TestCleanHappyPath:

    def test_returns_dataframe(self):
        df = clean(make_raw_df())
        assert isinstance(df, pd.DataFrame)

    def test_row_count_unchanged_when_data_is_clean(self):
        raw = make_raw_df(10)
        cleaned = clean(raw)
        assert len(cleaned) == 10

    def test_timestamp_is_datetime(self):
        cleaned = clean(make_raw_df())
        assert pd.api.types.is_datetime64_any_dtype(cleaned["timestamp"])

    def test_price_columns_are_float64(self):
        cleaned = clean(make_raw_df())
        for col in ["open", "high", "low", "close"]:
            assert cleaned[col].dtype == np.float64, f"{col} is not float64"

    def test_index_is_reset(self):
        raw = make_raw_df(5)
        cleaned = clean(raw)
        assert list(cleaned.index) == list(range(len(cleaned)))

    def test_schema_preserved(self):
        raw = make_raw_df()
        cleaned = clean(raw)
        for col in ["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"]:
            assert col in cleaned.columns


# ── Null handling ─────────────────────────────────────────────

class TestCleanNullHandling:

    def test_drops_rows_with_null_close(self):
        raw = make_raw_df(5)
        raw.loc[2, "close"] = np.nan
        cleaned = clean(raw)
        assert len(cleaned) == 4

    def test_drops_rows_with_null_timestamp(self):
        raw = make_raw_df(5)
        raw.loc[0, "timestamp"] = pd.NaT
        cleaned = clean(raw)
        assert len(cleaned) == 4

    def test_drops_rows_with_null_symbol(self):
        raw = make_raw_df(5)
        raw.loc[1, "symbol"] = np.nan
        cleaned = clean(raw)
        assert len(cleaned) == 4

    def test_volume_nulls_are_kept(self):
        """volume is allowed to be NaN (CoinGecko sometimes omits it)"""
        raw = make_raw_df(3)
        raw["volume"] = np.nan
        cleaned = clean(raw)
        assert len(cleaned) == 3


# ── Duplicate handling ────────────────────────────────────────

class TestCleanDuplicates:

    def test_removes_duplicate_symbol_timestamp_rows(self):
        raw = make_raw_df(3)
        raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)  # add duplicate
        assert len(raw) == 4
        cleaned = clean(raw)
        assert len(cleaned) == 3

    def test_same_symbol_different_timestamp_kept(self):
        raw = make_raw_df(5)
        cleaned = clean(raw)
        assert len(cleaned) == 5


# ── Price validation ──────────────────────────────────────────

class TestCleanPriceValidation:

    def test_drops_rows_with_zero_close(self):
        raw = make_raw_df(5)
        raw.loc[3, "close"] = 0.0
        cleaned = clean(raw)
        assert len(cleaned) == 4

    def test_drops_rows_with_negative_price(self):
        raw = make_raw_df(5)
        raw.loc[1, "open"] = -10.0
        cleaned = clean(raw)
        assert len(cleaned) == 4


# ── Error cases ───────────────────────────────────────────────

class TestCleanErrors:

    def test_raises_on_empty_dataframe(self):
        with pytest.raises(ValueError, match="empty"):
            clean(pd.DataFrame())

    def test_raises_on_none(self):
        with pytest.raises(ValueError):
            clean(None)

    def test_raises_on_missing_required_column(self):
        raw = make_raw_df()
        raw = raw.drop(columns=["close"])
        with pytest.raises(ValueError, match="Missing required columns"):
            clean(raw)

    def test_raises_when_all_rows_cleaned_out(self):
        raw = make_raw_df(3)
        raw["close"] = np.nan  # all nulls
        with pytest.raises(ValueError, match="No rows remain"):
            clean(raw)


# ── Multi-source ──────────────────────────────────────────────

class TestCleanMultiSource:

    def test_cleans_coingecko_data(self):
        raw = make_raw_df(5, source="coingecko", symbol="bitcoin")
        cleaned = clean(raw)
        assert len(cleaned) == 5
        assert (cleaned["source"] == "coingecko").all()

    def test_cleans_forex_data(self):
        raw = make_raw_df(5, source="alphavantage", symbol="USD/EUR")
        cleaned = clean(raw)
        assert len(cleaned) == 5
