"""
Tests for src/etl/validator.py

Run with:  pytest src/etl/tests/test_validator.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../"))

from src.etl.validator import validate, DataQualityError


# ── Fixtures ──────────────────────────────────────────────────

def make_valid_df(rows=5):
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=rows, freq="D", tz="UTC"),
        "open":   [150.0] * rows,
        "high":   [155.0] * rows,
        "low":    [148.0] * rows,
        "close":  [152.0] * rows,
        "volume": [1_000_000.0] * rows,
        "symbol": ["AAPL"] * rows,
        "source": ["alphavantage"] * rows,
        "rolling_avg_7d":    [151.0] * rows,
        "price_change":      [1.0] * rows,
        "price_change_pct":  [0.66] * rows,
        "volatility_7d":     [1.2] * rows,
        "price_currency":    ["USD"] * rows,
    })


# ── Happy path ────────────────────────────────────────────────

class TestValidateHappyPath:

    def test_returns_true_for_valid_df(self):
        assert validate(make_valid_df()) is True

    def test_accepts_forex_data(self):
        df = make_valid_df()
        df["symbol"] = "USD/EUR"
        df["price_currency"] = "EUR"
        assert validate(df) is True

    def test_accepts_crypto_data(self):
        df = make_valid_df()
        df["symbol"] = "bitcoin"
        df["source"] = "coingecko"
        assert validate(df) is True


# ── Failure cases ─────────────────────────────────────────────

class TestValidateFailures:

    def test_raises_on_empty_dataframe(self):
        with pytest.raises(DataQualityError):
            validate(pd.DataFrame())

    def test_raises_on_none(self):
        with pytest.raises(DataQualityError):
            validate(None)

    def test_raises_on_missing_column(self):
        df = make_valid_df().drop(columns=["close"])
        with pytest.raises(DataQualityError, match="Missing required columns"):
            validate(df)

    def test_raises_on_null_close(self):
        df = make_valid_df()
        df.loc[0, "close"] = np.nan
        with pytest.raises(DataQualityError):
            validate(df)

    def test_raises_on_null_symbol(self):
        df = make_valid_df()
        df.loc[1, "symbol"] = np.nan
        with pytest.raises(DataQualityError):
            validate(df)

    def test_raises_on_negative_price(self):
        df = make_valid_df()
        df.loc[0, "close"] = -1.0
        with pytest.raises(DataQualityError):
            validate(df)

    def test_raises_on_zero_price(self):
        df = make_valid_df()
        df.loc[2, "open"] = 0.0
        with pytest.raises(DataQualityError):
            validate(df)

    def test_raises_on_duplicate_symbol_timestamp(self):
        df = make_valid_df(3)
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        with pytest.raises(DataQualityError):
            validate(df)

    def test_raises_on_empty_symbol_string(self):
        df = make_valid_df()
        df.loc[0, "symbol"] = "   "
        with pytest.raises(DataQualityError):
            validate(df)
