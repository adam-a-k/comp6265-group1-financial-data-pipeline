"""
transformer.py — Stage 2 of the ETL pipeline.

Takes a cleaned DataFrame from cleaner.py and adds:
  - 7-day rolling average of closing price
  - Daily price change (absolute and percentage)
  - Price volatility (rolling 7-day std dev)
  - USD normalisation flag (crypto already in USD, stocks assumed USD)

Usage:
    from src.etl.transformer import transform
    transformed_df = transform(clean_df)
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply non-trivial transformations to a cleaned DataFrame.

    Transformations applied per symbol group:
      - 7-day rolling average of close price
      - Daily price change (close - previous close)
      - Daily price change percentage
      - 7-day rolling standard deviation (volatility proxy)

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned DataFrame from cleaner.clean().

    Returns
    -------
    pd.DataFrame
        DataFrame with additional computed columns.
    """
    if df is None or df.empty:
        raise ValueError("Input DataFrame is empty or None.")

    df = df.copy()
    df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    results = []

    for symbol, group in df.groupby("symbol", sort=False):
        group = group.copy().sort_values("timestamp")

        # ── 7-day rolling average close ──────────────────────
        group["rolling_avg_7d"] = (
            group["close"]
            .rolling(window=7, min_periods=1)
            .mean()
            .round(6)
        )

        # ── Daily price change ────────────────────────────────
        group["price_change"] = group["close"].diff().round(6)

        # ── Daily % change ────────────────────────────────────
        group["price_change_pct"] = (
            group["close"].pct_change() * 100
        ).round(4)

        # ── 7-day rolling volatility (std dev of close) ───────
        group["volatility_7d"] = (
            group["close"]
            .rolling(window=7, min_periods=2)
            .std()
            .round(6)
        )

        results.append(group)

    transformed_df = pd.concat(results, ignore_index=True)

    logger.info(
        f"transform() | symbols={df['symbol'].nunique()} "
        f"| rows={len(transformed_df)} "
        f"| new_columns=['rolling_avg_7d', 'price_change', 'price_change_pct', 'volatility_7d']"
    )

    return transformed_df


def normalise_to_usd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a normalisation flag indicating the price currency.

    Alpha Vantage stocks and forex are already quoted in their
    natural currency. CoinGecko crypto is fetched in USD.
    This function adds a `price_currency` column for clarity
    and downstream use.

    Parameters
    ----------
    df : pd.DataFrame
        Transformed DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with `price_currency` column added.
    """
    if df is None or df.empty:
        raise ValueError("Input DataFrame is empty or None.")

    df = df.copy()

    def infer_currency(row):
        source = str(row.get("source", "")).lower()
        symbol = str(row.get("symbol", "")).upper()

        if source == "coingecko":
            return "USD"  # CoinGecko always fetched in USD
        elif "/" in symbol:
            # Forex: USD/EUR → price is in EUR
            parts = symbol.split("/")
            return parts[1] if len(parts) == 2 else "UNKNOWN"
        else:
            return "USD"  # Stocks default to USD

    df["price_currency"] = df.apply(infer_currency, axis=1)

    logger.info(
        f"normalise_to_usd() | currencies found: {df['price_currency'].unique().tolist()}"
    )

    return df
