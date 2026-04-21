"""
src/etl — ETL Pipeline Module

Ausaf — COMP6265 Group 1

Public API:
    run_etl(raw_df, source_label)       → single DataFrame ETL
    run_etl_batch(fetcher_map)          → multiple DataFrames ETL

    clean(df)                           → cleaning only
    transform(df)                       → transformations only
    validate(df)                        → quality checks only
"""

from src.etl.pipeline import run_etl, run_etl_batch
from src.etl.cleaner import clean
from src.etl.transformer import transform, normalise_to_usd
from src.etl.validator import validate, DataQualityError

__all__ = [
    "run_etl",
    "run_etl_batch",
    "clean",
    "transform",
    "normalise_to_usd",
    "validate",
    "DataQualityError",
]
