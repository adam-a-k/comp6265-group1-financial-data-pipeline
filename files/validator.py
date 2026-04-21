"""
validator.py — Data quality gate before storage.

Runs a series of checks on the transformed DataFrame before
it is passed to Adam's PostgreSQL storage layer. Any failures
are logged and raised so the pipeline halts rather than
loading bad data.

Usage:
    from src.etl.validator import validate
    validate(transformed_df)   # raises DataQualityError on failure
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Raised when a data quality check fails."""
    pass


def validate(df: pd.DataFrame, stage: str = "pre_load") -> bool:
    """
    Run data quality checks on a transformed DataFrame.

    Checks performed:
      1. DataFrame is not empty
      2. Required columns are present
      3. No nulls in critical fields (timestamp, close, symbol)
      4. All price values are positive
      5. No duplicate (symbol, timestamp) rows
      6. Timestamps are timezone-aware
      7. symbol and source columns are non-empty strings

    Parameters
    ----------
    df : pd.DataFrame
        Transformed DataFrame to validate.
    stage : str
        Label for logging (e.g. "pre_load", "post_clean").

    Returns
    -------
    bool
        True if all checks pass.

    Raises
    ------
    DataQualityError
        If any check fails.
    """
    errors = []

    # ── 1. Not empty ─────────────────────────────────────────
    if df is None or df.empty:
        raise DataQualityError("DataFrame is empty — nothing to load.")

    # ── 2. Required columns present ──────────────────────────
    required = {"timestamp", "open", "high", "low", "close", "symbol", "source"}
    missing = required - set(df.columns)
    if missing:
        errors.append(f"Missing required columns: {missing}")

    if errors:
        raise DataQualityError(" | ".join(errors))

    # ── 3. No nulls in critical fields ───────────────────────
    critical = ["timestamp", "close", "symbol", "source"]
    for col in critical:
        null_count = df[col].isna().sum()
        if null_count > 0:
            errors.append(f"Column '{col}' has {null_count} null value(s)")

    # ── 4. All price values positive ─────────────────────────
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            non_positive = (df[col] <= 0).sum()
            if non_positive > 0:
                errors.append(
                    f"Column '{col}' has {non_positive} non-positive value(s)"
                )

    # ── 5. No duplicate (symbol, timestamp) rows ─────────────
    dupe_count = df.duplicated(subset=["symbol", "timestamp"]).sum()
    if dupe_count > 0:
        errors.append(f"Found {dupe_count} duplicate (symbol, timestamp) row(s)")

    # ── 6. Timestamps are timezone-aware ─────────────────────
    if hasattr(df["timestamp"].dtype, "tz") and df["timestamp"].dtype.tz is None:
        errors.append("Timestamps are not timezone-aware (expected UTC)")

    # ── 7. symbol and source are non-empty strings ───────────
    if (df["symbol"].str.strip() == "").any():
        errors.append("Column 'symbol' contains empty string(s)")
    if (df["source"].str.strip() == "").any():
        errors.append("Column 'source' contains empty string(s)")

    if errors:
        error_msg = f"[{stage}] Data quality checks FAILED:\n  " + "\n  ".join(errors)
        logger.error(error_msg)
        raise DataQualityError(error_msg)

    logger.info(
        f"validate() | stage={stage} | rows={len(df)} "
        f"| symbols={df['symbol'].nunique()} | ALL CHECKS PASSED"
    )

    return True
