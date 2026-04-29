"""
config.py — Centralised configuration for the ingestion module.

All secrets are read from environment variables so that no credentials are
ever hard-coded in source.  Use a .env file (see .env.example) together with
python-dotenv, or export variables directly in your shell / CI environment.
"""

import os
from dotenv import load_dotenv
# ---------------------------------------------------------------------------
# API credentials
# ---------------------------------------------------------------------------

#: Alpha Vantage API key.  Defaults to "demo" which is the public demo key
#: with very limited rate limits.  Set ALPHA_VANTAGE_KEY in your environment.
load_dotenv()
ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "demo")

# ---------------------------------------------------------------------------
# Default symbols to track
# ---------------------------------------------------------------------------

#: Equity tickers fetched by StockFetcher.
STOCK_SYMBOLS: list[str] = ["AAPL", "GOOGL", "MSFT", "AMZN"]

#: CoinGecko coin IDs fetched by CryptoFetcher.
CRYPTO_SYMBOLS: list[str] = ["bitcoin", "ethereum", "solana"]

#: Currency pairs fetched by ForexFetcher — each entry is (from, to).
FOREX_PAIRS: list[tuple[str, str]] = [
    ("USD", "EUR"),
    ("USD", "GBP"),
    ("USD", "JPY"),
]
