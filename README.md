# Financial Data Pipeline — Ingestion Module

## Overview

The `ingestion` module is responsible for fetching live financial data from external APIs and returning standardised pandas DataFrames for consumption by the `etl/` and `storage/` layers of the pipeline.

It supports three data types:
- **Stock market data** — via Alpha Vantage
- **Forex / currency exchange rates** — via Alpha Vantage
- **Cryptocurrency prices** — via CoinGecko

---

## Project Structure

```
src/ingestion/
├── __init__.py              # Exports all three fetchers
├── base.py                  # Abstract base class (BaseFetcher)
├── config.py                # API keys and symbol configuration
├── utils.py                 # Retry, rate limiting, and logging utilities
├── stock_fetcher.py         # Fetches stock OHLCV data (Alpha Vantage)
├── forex_fetcher.py         # Fetches forex OHLC data (Alpha Vantage)
├── crypto_fetcher.py        # Fetches crypto OHLC data (CoinGecko)
└── tests/
    ├── test_stock_fetcher.py
    ├── test_forex_fetcher.py
    └── test_crypto_fetcher.py
```

---

## APIs Used

| Data Type | API | Docs | Auth |
|-----------|-----|------|------|
| Stocks | Alpha Vantage | https://www.alphavantage.co/documentation/ | API key required |
| Forex | Alpha Vantage | https://www.alphavantage.co/documentation/ | Same API key |
| Crypto | CoinGecko | https://www.coingecko.com/en/api/documentation | No key required |

---

## Setup

### 1. Install dependencies

```bash
pip install requests pandas python-dotenv pytest
```

### 2. Get your Alpha Vantage API key

Sign up for a free key at:
👉 https://www.alphavantage.co/support/#api-key

### 3. Create your `.env` file

Copy the example and fill in your key:

```bash
cp .env.example .env
```

Edit `.env`:
```
ALPHA_VANTAGE_KEY=your_actual_key_here
```

> ⚠️ Never commit `.env` to GitHub. It is listed in `.gitignore`.

---

## Usage

### Import the fetchers

```python
from src.ingestion import StockFetcher, ForexFetcher, CryptoFetcher
```

### Fetch stock data

```python
fetcher = StockFetcher()
df = fetcher.fetch("AAPL")
print(df.tail())
```

### Fetch forex data

```python
fetcher = ForexFetcher()
df = fetcher.fetch(from_symbol="USD", to_symbol="EUR")
# or: df = fetcher.fetch(symbol="USD/EUR")
print(df.tail())
```

### Fetch crypto data

```python
fetcher = CryptoFetcher()
df = fetcher.fetch("bitcoin", vs_currency="usd", days=30)
print(df.tail())
```

---

## Output Schema

Every fetcher returns a pandas DataFrame with the following standardised columns:

| Column | Type | Notes |
|--------|------|-------|
| `timestamp` | datetime (UTC) | Date/time of the data point |
| `open` | float64 | Opening price |
| `high` | float64 | Highest price |
| `low` | float64 | Lowest price |
| `close` | float64 | Closing price |
| `volume` | float64 | Trading volume (NaN if unavailable) |
| `symbol` | str | e.g. `AAPL`, `bitcoin`, `USD/EUR` |
| `source` | str | e.g. `alphavantage`, `coingecko` |

---

## Quick Test

Run this script from the project root to see live output from all three fetchers:

```bash
python quick_test.py
```

Example output:
```
============================================================
  📈 STOCK DATA — AAPL (last 5 days)
============================================================
   timestamp    open    high     low   close      volume symbol       source
  2026-04-02  254.20  256.13  250.65  255.92  31289369.0   AAPL  alphavantage

============================================================
  💱 FOREX DATA — USD/EUR (last 5 days)
============================================================
   timestamp    open    high     low   close  volume  symbol       source
  2026-04-03  0.8666  0.8684  0.8657  0.8681     NaN USD/EUR  alphavantage

============================================================
  🪙 CRYPTO DATA — Bitcoin in USD
============================================================
   timestamp     open     high      low    close  volume   symbol    source
  2026-04-06  69135.0  70065.0  69132.0  69655.0     NaN  bitcoin  coingecko
```

---

## Running Tests

Tests use `pytest` and `unittest.mock` — no real API calls are made.

```bash
pytest src/ingestion/tests/ -v
```

Expected output:
```
44 passed in Xs
```

---

## How This Fits Into the Pipeline

```
External APIs
     │
     ▼
ingestion/        ← This module
     │
     ▼
storage/          ← Saves DataFrames to database/file system
     │
     ▼
etl/              ← Transforms and cleans data
     │
     ▼
warehouse/        ← Stores processed data
     │
     ▼
dashboard/        ← Visualises data
```

The ingestion module only fetches and returns clean DataFrames. It does not handle saving, scheduling, or transformations — those are handled by downstream modules.

---

## Configuration

Edit `src/ingestion/config.py` to change the default symbols and pairs:

```python
STOCK_SYMBOLS  = ["AAPL", "GOOGL", "MSFT", "AMZN"]
CRYPTO_SYMBOLS = ["bitcoin", "ethereum", "solana"]
FOREX_PAIRS    = [("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY")]
```

---

## Rate Limits

| API | Free Tier Limit | Handled By |
|-----|----------------|------------|
| Alpha Vantage | 25 requests/day | `@rate_limit` decorator in `utils.py` |
| CoinGecko | ~30 requests/min | `@retry` decorator in `utils.py` |

---

## Author

Akash — COMP6265 Group 1  
University of Southampton
