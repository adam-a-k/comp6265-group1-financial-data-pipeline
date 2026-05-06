"""
Tests for src/etl/transformer.py

Run with:  pytest src/etl/tests/test_transformer.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../"))

from src.etl.transformer import transform, normalise_to_usd


# ── Fixtures ──────────────────────────────────────────────────

def make_clean_df(rows=10, symbol="AAPL", source="alphavantage"):
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=rows, freq="D", tz="UTC"),
        "open":   [100.0 + i for i in range(rows)],
        "high":   [105.0 + i for i in range(rows)],
        "low":    [98.0  + i for i in range(rows)],
        "close":  [102.0 + i for i in range(rows)],
        "volume": [500_000.0] * rows,
        "symbol": [symbol] * rows,
        "source": [source] * rows,
    })


# ── Happy path ────────────────────────────────────────────────

class TestTransformHappyPath:

    def test_returns_dataframe(self):
        df = transform(make_clean_df())
        assert isinstance(df, pd.DataFrame)

    def test_row_count_unchanged(self):
        df = make_clean_df(10)
        result = transform(df)
        assert len(result) == 10

    def test_adds_rolling_avg_column(self):
        result = transform(make_clean_df())
        assert "rolling_avg_7d" in result.columns

    def test_adds_price_change_column(self):
        result = transform(make_clean_df())
        assert "price_change" in result.columns

    def test_adds_price_change_pct_column(self):
        result = transform(make_clean_df())
        assert "price_change_pct" in result.columns

    def test_adds_volatility_column(self):
        result = transform(make_clean_df())
        assert "volatility_7d" in result.columns


# ── Rolling average correctness ───────────────────────────────

class TestRollingAverage:

    def test_rolling_avg_7d_first_row_equals_close(self):
        """With min_periods=1 the first row's rolling avg = close itself."""
        df = make_clean_df(10)
        result = transform(df)
        assert result.iloc[0]["rolling_avg_7d"] == pytest.approx(
            result.iloc[0]["close"], rel=1e-4
        )

    def test_rolling_avg_7d_is_mean_of_last_7(self):
        df = make_clean_df(10)
        result = transform(df)
        expected = df["close"].iloc[3:10].mean()
        assert result.iloc[9]["rolling_avg_7d"] == pytest.approx(expected, rel=1e-4)

    def test_rolling_avg_is_not_null_for_any_row(self):
        result = transform(make_clean_df(10))
        assert result["rolling_avg_7d"].isna().sum() == 0


# ── Price change correctness ──────────────────────────────────

class TestPriceChange:

    def test_first_row_price_change_is_null(self):
        """First row has no previous row to diff against."""
        result = transform(make_clean_df(5))
        assert pd.isna(result.iloc[0]["price_change"])

    def test_price_change_is_correct(self):
        df = make_clean_df(5)
        result = transform(df)
        # close goes 102, 103, 104... so diff = 1.0 for each step
        assert result.iloc[1]["price_change"] == pytest.approx(1.0, rel=1e-4)

    def test_first_row_pct_change_is_null(self):
        result = transform(make_clean_df(5))
        assert pd.isna(result.iloc[0]["price_change_pct"])


# ── Multi-symbol ──────────────────────────────────────────────

class TestTransformMultiSymbol:

    def test_handles_multiple_symbols(self):
        df1 = make_clean_df(10, symbol="AAPL")
        df2 = make_clean_df(10, symbol="MSFT")
        combined = pd.concat([df1, df2], ignore_index=True)
        result = transform(combined)
        assert len(result) == 20
        assert set(result["symbol"].unique()) == {"AAPL", "MSFT"}

    def test_rolling_avg_does_not_bleed_across_symbols(self):
        """Rolling avg for MSFT must not include AAPL rows."""
        df1 = make_clean_df(7, symbol="AAPL")
        df2 = make_clean_df(7, symbol="MSFT")
        df2["close"] = 9999.0  # very different prices
        combined = pd.concat([df1, df2], ignore_index=True)
        result = transform(combined)

        aapl_avg = result[result["symbol"] == "AAPL"]["rolling_avg_7d"].max()
        assert aapl_avg < 200  # must not have been contaminated by MSFT's 9999


# ── Error cases ───────────────────────────────────────────────

class TestTransformErrors:

    def test_raises_on_empty_dataframe(self):
        with pytest.raises(ValueError, match="empty"):
            transform(pd.DataFrame())

    def test_raises_on_none(self):
        with pytest.raises(ValueError):
            transform(None)


# ── normalise_to_usd ─────────────────────────────────────────

class TestNormaliseToUSD:

    def test_adds_price_currency_column(self):
        result = normalise_to_usd(make_clean_df())
        assert "price_currency" in result.columns

    def test_stock_currency_is_usd(self):
        df = make_clean_df(3, symbol="AAPL", source="alphavantage")
        result = normalise_to_usd(df)
        assert (result["price_currency"] == "USD").all()

    def test_crypto_currency_is_usd(self):
        df = make_clean_df(3, symbol="bitcoin", source="coingecko")
        result = normalise_to_usd(df)
        assert (result["price_currency"] == "USD").all()

    def test_forex_usd_eur_currency_is_eur(self):
        df = make_clean_df(3, symbol="USD/EUR", source="alphavantage")
        result = normalise_to_usd(df)
        assert (result["price_currency"] == "EUR").all()
