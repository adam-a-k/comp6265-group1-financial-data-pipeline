"""
cleaner.py — Stage 1 of the ETL pipeline.

Takes raw DataFrames from Akash's ingestion layer and:
  - Validates required fields are present
  - Standardises column types
  - Drops nulls / duplicates
  - Ensures prices are positive
  - Returns a clean DataFrame ready for transformation

Usage:
    from src.etl.cleaner import clean
    clean_df = clean(raw_df)
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "symbol", "source"}
PRICE_COLUMNS = ["open", "high", "low", "close"]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw ingestion DataFrame.

    Steps:
      1. Validate required columns exist
      2. Parse / normalise timestamp to UTC datetime
      3. Cast price columns to float64
      4. Drop rows with null values in required fields
      5. Drop duplicate (symbol, timestamp) rows
      6. Assert prices are positive
      7. Reset index

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from StockFetcher, ForexFetcher, or CryptoFetcher.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with the same schema.

    Raises
    ------
    ValueError
        If required columns are missing or no rows remain after cleaning.
    """
    if df is None or df.empty:
        raise ValueError("Input DataFrame is empty or None.")

    # ── 1. Validate required columns ─────────────────────────
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Input DataFrame is missing required columns: {missing}")

    df = df.copy()
    input_rows = len(df)

    # ── 2. Normalise timestamp ────────────────────────────────
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    # ── 3. Cast price columns to float64 ─────────────────────
    for col in PRICE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    # ── 4. Drop nulls in critical fields ─────────────────────
    critical = ["timestamp", "close", "symbol", "source"]
    before_null_drop = len(df)
    df = df.dropna(subset=critical)
    nulls_dropped = before_null_drop - len(df)

    # ── 5. Drop duplicate (symbol, timestamp) rows ───────────
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["symbol", "timestamp"])
    dupes_dropped = before_dedup - len(df)

    # ── 6. Assert prices are positive ────────────────────────
    for col in PRICE_COLUMNS:
        if col in df.columns:
            invalid = df[col] <= 0
            if invalid.any():
                logger.warning(
                    f"Dropping {invalid.sum()} rows with non-positive {col} values."
                )
                df = df[~invalid]

    output_rows = len(df)

    if output_rows == 0:
        raise ValueError("No rows remain after cleaning — check input data quality.")

    logger.info(
        f"clean() | input={input_rows} | output={output_rows} "
        f"| nulls_dropped={nulls_dropped} | dupes_dropped={dupes_dropped}"
    )

    # ── 7. Reset index ────────────────────────────────────────
    df = df.reset_index(drop=True)

    return df
