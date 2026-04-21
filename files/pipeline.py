"""
pipeline.py — Main ETL orchestrator.

Wires together:
  ingestion output → clean → transform → validate → ready for storage

This is the single entry point Ausaf exposes to the rest of the
team. Adam's storage layer calls run_etl() to get a fully
processed DataFrame ready to load into PostgreSQL.

Usage:
    from src.etl.pipeline import run_etl

    # Pass in a raw DataFrame from any of Akash's fetchers
    processed_df = run_etl(raw_df, source_label="alphavantage_stocks")
"""

import pandas as pd
import logging
import sys
import os

from src.etl.cleaner import clean
from src.etl.transformer import transform, normalise_to_usd
from src.etl.validator import validate

# ── Logger setup ─────────────────────────────────────────────
# Import the shared audit logger if it exists, otherwise fall
# back to a basic local logger so ETL works standalone too.
try:
    from src.utils.logger import log_etl_run
    _USE_AUDIT_LOGGER = True
except ImportError:
    _USE_AUDIT_LOGGER = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_etl(
    raw_df: pd.DataFrame,
    source_label: str = "unknown",
    user: str = "pipeline_scheduler",
) -> pd.DataFrame:
    """
    Run the full ETL pipeline on a raw ingestion DataFrame.

    Stages:
      1. clean()          — remove nulls, duplicates, bad types
      2. transform()      — rolling averages, price change, volatility
      3. normalise_to_usd() — add price_currency column
      4. validate()       — data quality gate before storage
      5. audit log        — write entry to etl_audit.log

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw DataFrame from StockFetcher, ForexFetcher, or CryptoFetcher.
    source_label : str
        Human-readable label for this data source (used in logs).
    user : str
        User / process that triggered this ETL run (for audit trail).

    Returns
    -------
    pd.DataFrame
        Fully processed DataFrame ready to be loaded into PostgreSQL.

    Raises
    ------
    ValueError
        If the DataFrame is empty or cleaning removes all rows.
    DataQualityError
        If the final validation step fails.
    """
    logger.info(f"ETL started | source={source_label} | input_rows={len(raw_df)}")

    # ── Stage 1: Clean ────────────────────────────────────────
    logger.info("Stage 1/4 — Cleaning...")
    clean_df = clean(raw_df)
    nulls_dropped = len(raw_df) - len(clean_df)

    # ── Stage 2: Transform ────────────────────────────────────
    logger.info("Stage 2/4 — Transforming...")
    transformed_df = transform(clean_df)

    # ── Stage 3: Normalise ────────────────────────────────────
    logger.info("Stage 3/4 — Normalising currency...")
    normalised_df = normalise_to_usd(transformed_df)

    # ── Stage 4: Validate ─────────────────────────────────────
    logger.info("Stage 4/4 — Validating...")
    validate(normalised_df, stage="pre_load")

    output_rows = len(normalised_df)
    logger.info(
        f"ETL complete | source={source_label} | "
        f"input={len(raw_df)} | output={output_rows}"
    )

    # ── Audit log ─────────────────────────────────────────────
    if _USE_AUDIT_LOGGER:
        log_etl_run(
            stage=source_label,
            source=source_label,
            user=user,
            usage="etl_transform",
            input_rows=len(raw_df),
            output_rows=output_rows,
            nulls_dropped=nulls_dropped,
        )

    return normalised_df


def run_etl_batch(
    fetcher_map: dict,
    user: str = "pipeline_scheduler",
) -> dict:
    """
    Run ETL on multiple raw DataFrames at once.

    Parameters
    ----------
    fetcher_map : dict
        A dict mapping source label → raw DataFrame.
        Example:
            {
                "alphavantage_stocks": stock_df,
                "alphavantage_forex":  forex_df,
                "coingecko_crypto":    crypto_df,
            }
    user : str
        User / process that triggered this run.

    Returns
    -------
    dict
        Same keys, with processed DataFrames as values.
        Failed sources are logged and skipped (not re-raised),
        so one bad source does not kill the whole batch.
    """
    results = {}

    for label, raw_df in fetcher_map.items():
        try:
            results[label] = run_etl(raw_df, source_label=label, user=user)
        except Exception as e:
            logger.error(f"ETL failed for '{label}': {e}")
            results[label] = None

    successful = [k for k, v in results.items() if v is not None]
    failed = [k for k, v in results.items() if v is None]

    logger.info(
        f"Batch ETL complete | success={successful} | failed={failed}"
    )

    return results
