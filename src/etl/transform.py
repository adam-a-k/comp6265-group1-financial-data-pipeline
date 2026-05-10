"""
ETL Transform Module — Ausaf, Adam
Cleans and transforms raw financial data from Akash's ingestion layer.
Outputs clean DataFrames ready for Adam's PostgreSQL loader.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from src.utils.logger import log_etl_run

logger = logging.getLogger(__name__)

#Mappings because of inconsistencies between source schema and data transformation
STOCK_MAPPING  = {"close": "price"}
CRYPTO_MAPPING = {"close": "price"}
FOREX_MAPPING  = {"close": "price"}

def map_to_canonical(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(columns=mapping)

# ─────────────────────────────────────────────
# DATA QUALITY CHECKS
# ─────────────────────────────────────────────

def validate_raw_data(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Stage 1 quality check — runs at ingestion boundary.
    Ensures required fields exist and are not null.
    Raises ValueError if the data is fundamentally unusable.
    """
    required_columns = {"symbol", "price", "timestamp"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"[{source}] Missing required columns: {missing}")

    null_counts = df[list(required_columns)].isnull().sum()
    if null_counts.any():
        raise ValueError(
            f"[{source}] Null values found in required fields:\n{null_counts[null_counts > 0]}"
        )

    return df


def validate_business_rules(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Stage 2 quality check — runs during transformation.
    Enforces business rules: prices must be positive numbers.
    Drops rows that violate rules rather than raising (with logging).
    """
    initial_count = len(df)

    # Price must be a positive number
    df = df[pd.to_numeric(df["price"], errors="coerce") > 0].copy()

    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"[{source}] Dropped {dropped} rows with non-positive prices.")

    return df


def validate_before_load(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Stage 3 quality check — runs before handing off to Adam's loader.
    Removes duplicate rows based on symbol + timestamp combination.
    """
    initial_count = len(df)
    df = df.drop_duplicates(subset=["symbol", "timestamp"]).copy()
    duplicates_removed = initial_count - len(df)

    if duplicates_removed > 0:
        logger.warning(f"[{source}] Removed {duplicates_removed} duplicate rows before load.")

    return df


# ─────────────────────────────────────────────
# CLEANING HELPERS
# ─────────────────────────────────────────────

def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercases and strips whitespace from all column names."""
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    return df


def parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Parses the timestamp column to a consistent UTC datetime format."""
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    return df


def cast_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures price and volume columns are numeric types."""
    numeric_cols = ["price", "open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def handle_nulls(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Drops rows where critical columns are null.
    Returns the cleaned DataFrame and count of rows dropped.
    """
    before = len(df)
    df = df.dropna(subset=["symbol", "price", "timestamp"])
    nulls_dropped = before - len(df)
    return df, nulls_dropped


# ─────────────────────────────────────────────
# NON-TRIVIAL TRANSFORMATION: ROLLING AVERAGE
# ─────────────────────────────────────────────

def add_rolling_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """
    Calculates a rolling average price per symbol over `window` periods.
    This is the primary analytical transformation in the ETL layer.

    The result is stored in a new column: rolling_avg_{window}d
    Requires data to be sorted by timestamp within each symbol group.
    """
    df = df.sort_values(["symbol", "timestamp"])
    col_name = f"rolling_avg_{window}d"
    df[col_name] = (
        df.groupby("symbol")["price"]
        .transform(lambda x: x.rolling(window=window, min_periods=1).mean())
    )
    return df


def add_price_change_pct(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates percentage price change per symbol relative to the previous record.
    Adds a price_change_pct column.
    """
    df = df.sort_values(["symbol", "timestamp"])
    df["price_change_pct"] = (
        df.groupby("symbol")["price"]
        .pct_change()
        .mul(100)
        .round(4)
    )
    return df


# ─────────────────────────────────────────────
# MAIN TRANSFORM PIPELINES
# ─────────────────────────────────────────────

def transform_stocks(raw_df: pd.DataFrame, user: str = "pipeline_scheduler") -> pd.DataFrame:
    """
    Full ETL pipeline for stock data.
    Input:  raw DataFrame from Akash's stock fetcher
    Output: clean, enriched DataFrame ready for Adam's PostgreSQL loader
    """
    source = "stocks"
    input_rows = len(raw_df)

    # Stage 1: validate structure, map
    raw_df = map_to_canonical(raw_df, STOCK_MAPPING)
    raw_df = validate_raw_data(raw_df, source)

    # Clean
    df = standardise_columns(raw_df.copy())
    df = parse_timestamps(df)
    df = cast_price_columns(df)
    df, nulls_dropped = handle_nulls(df)

    # Stage 2: validate business rules
    df = validate_business_rules(df, source)

    # Transform
    df = add_rolling_average(df, window=7)
    df = add_price_change_pct(df)

    # Stage 3: validate before load
    df = validate_before_load(df, source)

    output_rows = len(df)

    log_etl_run(
        stage="transform_stocks",
        source=source,
        user=user,
        input_rows=input_rows,
        output_rows=output_rows,
        nulls_dropped=nulls_dropped,
    )

    return df


def transform_crypto(raw_df: pd.DataFrame, user: str = "pipeline_scheduler") -> pd.DataFrame:
    """
    Full ETL pipeline for cryptocurrency data.
    Input:  raw DataFrame from Akash's crypto fetcher
    Output: clean, enriched DataFrame ready for Adam's PostgreSQL loader
    """
    source = "crypto"
    input_rows = len(raw_df)

    #Do Mapping then validate
    raw_df = map_to_canonical(raw_df, CRYPTO_MAPPING)
    raw_df = validate_raw_data(raw_df, source)

    df = standardise_columns(raw_df.copy())
    df = parse_timestamps(df)
    df = cast_price_columns(df)
    df, nulls_dropped = handle_nulls(df)

    df = validate_business_rules(df, source)

    df = add_rolling_average(df, window=7)
    df = add_price_change_pct(df)

    df = validate_before_load(df, source)

    output_rows = len(df)

    log_etl_run(
        stage="transform_crypto",
        source=source,
        user=user,
        input_rows=input_rows,
        output_rows=output_rows,
        nulls_dropped=nulls_dropped,
    )

    return df


def transform_forex(raw_df: pd.DataFrame, user: str = "pipeline_scheduler") -> pd.DataFrame:
    """
    Full ETL pipeline for forex data.
    Input:  raw DataFrame from Akash's forex fetcher
    Output: clean, enriched DataFrame ready for Adam's PostgreSQL loader
    """
    source = "forex"
    input_rows = len(raw_df)

    #Do mapping then validate
    raw_df = map_to_canonical(raw_df, FOREX_MAPPING)
    raw_df = validate_raw_data(raw_df, source)

    df = standardise_columns(raw_df.copy())
    df = parse_timestamps(df)
    df = cast_price_columns(df)
    df, nulls_dropped = handle_nulls(df)

    df = validate_business_rules(df, source)

    df = add_rolling_average(df, window=7)
    df = add_price_change_pct(df)

    df = validate_before_load(df, source)

    output_rows = len(df)

    log_etl_run(
        stage="transform_forex",
        source=source,
        user=user,
        input_rows=input_rows,
        output_rows=output_rows,
        nulls_dropped=nulls_dropped,
    )

    return df
