"""
ingestion — Financial data ingestion module for comp6265-group1-financial-data-pipeline.

Public API
----------
from ingestion import StockFetcher, ForexFetcher, CryptoFetcher
"""

from .crypto_fetcher import CryptoFetcher
from .forex_fetcher import ForexFetcher
from .stock_fetcher import StockFetcher
from .news_fetcher import NewsFetcher

__all__ = ["StockFetcher", "ForexFetcher", "CryptoFetcher", "NewsFetcher"]
