# ETL Pipeline Module

## Overview

The `etl` module takes raw DataFrames from the `ingestion` layer (Akash) and cleans,
transforms, and validates them before passing to the `storage` layer (Adam).

## Structure

```
src/etl/
├── __init__.py              # Public API exports
├── cleaner.py               # Stage 1 — clean raw ingestion data
├── transformer.py           # Stage 2 — rolling averages, price change, volatility
├── validator.py             # Stage 3 — data quality gate before PostgreSQL
├── pipeline.py              # Main entry point — run_etl() wires all stages
└── tests/
    ├── __init__.py
    ├── test_cleaner.py
    ├── test_transformer.py
    └── test_validator.py
```

## Usage

### Single source
```python
from src.etl.pipeline import run_etl

# Pass any raw DataFrame from Akash's fetchers
processed_df = run_etl(raw_df, source_label="alphavantage_stocks")
```

### Multiple sources at once
```python
from src.etl.pipeline import run_etl_batch

results = run_etl_batch({
    "alphavantage_stocks": stock_df,
    "alphavantage_forex":  forex_df,
    "coingecko_crypto":    crypto_df,
})
# results["alphavantage_stocks"] → cleaned + transformed DataFrame
```

## Output Schema

All processed DataFrames have the original 8 columns from ingestion **plus** 5 new ones:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime (UTC) | Normalised to UTC |
| `open` | float64 | Opening price |
| `high` | float64 | Highest price |
| `low` | float64 | Lowest price |
| `close` | float64 | Closing price |
| `volume` | float64 | Trading volume (NaN if unavailable) |
| `symbol` | str | e.g. `AAPL`, `bitcoin`, `USD/EUR` |
| `source` | str | e.g. `alphavantage`, `coingecko` |
| `rolling_avg_7d` | float64 | 7-day rolling average of close price |
| `price_change` | float64 | Daily price change (close diff) |
| `price_change_pct` | float64 | Daily % change |
| `volatility_7d` | float64 | 7-day rolling std dev of close |
| `price_currency` | str | Inferred currency (e.g. `USD`, `EUR`) |

## Running Tests

```bash
pytest src/etl/tests/ -v
```

Expected: **27 passed**

## Governance

The ETL module contributes to the project audit trail via `src/utils/logger.py`:
- Every `run_etl()` call writes to `logs/etl_audit.log`
- Logs: stage, source, user, input rows, output rows, nulls dropped

## Author

Ausaf — COMP6265 Group 1  
University of Southampton
