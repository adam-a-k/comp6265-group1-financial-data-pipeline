"""
quick_test.py — Run this from your project root to see live output from all three fetchers.

Requirements:
  1. Your .env file must exist with ALPHA_VANTAGE_KEY=your_key_here
  2. Install dependencies:  pip install requests pandas python-dotenv

Run:
  python quick_test.py
"""

import sys
import os

# Load .env file so ALPHA_VANTAGE_KEY is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env loaded\n")
except ImportError:
    print("⚠️  python-dotenv not installed. Run: pip install python-dotenv")
    print("   Falling back to 'demo' key (very limited)\n")

# Make sure Python can find the src/ folder
sys.path.insert(0, os.path.dirname(__file__))

from src.ingestion import StockFetcher, ForexFetcher, CryptoFetcher


def separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ── STOCKS ────────────────────────────────────────────────────
separator("📈 STOCK DATA — AAPL (last 5 days)")
try:
    stock = StockFetcher()
    df = stock.fetch("AAPL", outputsize="compact")
    print(df.tail(5).to_string(index=False))
    print(f"\nTotal rows fetched: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Date range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
except Exception as e:
    print(f"❌ Stock fetch failed: {e}")


# ── FOREX ─────────────────────────────────────────────────────
separator("💱 FOREX DATA — USD/EUR (last 5 days)")
try:
    forex = ForexFetcher()
    df = forex.fetch(from_symbol="USD", to_symbol="EUR")
    print(df.tail(5).to_string(index=False))
    print(f"\nTotal rows fetched: {len(df)}")
    print(f"Date range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
except Exception as e:
    print(f"❌ Forex fetch failed: {e}")


# ── CRYPTO ────────────────────────────────────────────────────
separator("🪙 CRYPTO DATA — Bitcoin in USD (last 5 rows, 30 days)")
try:
    crypto = CryptoFetcher()
    df = crypto.fetch("bitcoin", vs_currency="usd", days=30)
    print(df.tail(5).to_string(index=False))
    print(f"\nTotal rows fetched: {len(df)}")
    print(f"Date range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
except Exception as e:
    print(f"❌ Crypto fetch failed: {e}")


# ── SUMMARY ───────────────────────────────────────────────────
separator("✅ Done")
print("All fetchers return DataFrames with this standard schema:")
print("  timestamp | open | high | low | close | volume | symbol | source")
print("\nThese DataFrames are ready to be passed to the storage/ layer.")
