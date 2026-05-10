"""
crypto_fetcher.py — Fetch OHLC crypto data from the CoinGecko public API.

Uses the /coins/{id}/ohlc endpoint.  No API key is required.
Volume is not provided by this endpoint so the ``volume`` column is NaN.
"""

import pandas as pd
import requests

from .base import BaseFetcher
from .utils import retry, setup_logger
from dotenv import load_dotenv
load_dotenv()

logger = setup_logger(__name__)


class CryptoFetcher(BaseFetcher):
    """Fetch OHLC cryptocurrency data from the CoinGecko public API.

    The CoinGecko ``/coins/{id}/ohlc`` endpoint returns candlestick data as a
    list of ``[timestamp_ms, open, high, low, close]`` arrays.  No authentication
    is required; the free tier allows approximately 30 requests per minute.
    """

    BASE_URL: str = "https://api.coingecko.com/api/v3"
    SOURCE: str = "coingecko"

    @retry(max_attempts=3, delay=2)
    def fetch(self, symbol: str, vs_currency: str = "usd", days: int = 30) -> pd.DataFrame:
        """Fetch OHLC data for a CoinGecko coin ID.

        Parameters
        ----------
        symbol:
            CoinGecko coin ID, e.g. ``"bitcoin"``, ``"ethereum"``, ``"solana"``.
        vs_currency:
            The target currency for prices (default ``"usd"``).
        days:
            Number of past days to retrieve.  CoinGecko accepts 1, 7, 14, 30,
            90, 180, 365, or ``"max"``.

        Returns
        -------
        pd.DataFrame
            Columns: ``[timestamp, open, high, low, close, volume, symbol, source]``
            ``volume`` is ``NaN`` (not provided by this endpoint).
            Sorted by ``timestamp`` ascending.

        Raises
        ------
        ValueError
            If the CoinGecko response is not a list (e.g. an error dict is
            returned instead).
        requests.HTTPError
            If the HTTP request itself fails (including 429 Too Many Requests).
        """
        logger.info(
            "Fetching crypto data for %s vs %s (%d days)", symbol, vs_currency, days
        )

        url = f"{self.BASE_URL}/coins/{symbol}/ohlc"
        params: dict = {"vs_currency": vs_currency, "days": days}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            raise ValueError(
                f"Unexpected CoinGecko response for '{symbol}': expected a list, "
                f"got {type(data).__name__}. Response: {data}"
            )

        if len(data) == 0:
            logger.warning("CoinGecko returned 0 rows for '%s'", symbol)

        records = []
        for row in data:
            timestamp_ms, open_, high, low, close = row
            records.append(
                {
                    "timestamp": pd.to_datetime(timestamp_ms, unit="ms", utc=True),
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": float("nan"),
                    "symbol": symbol,
                    "source": self.SOURCE,
                }
            )

        df = pd.DataFrame(records, columns=["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        self.validate(df)
        logger.info("Fetched %d rows for %s", len(df), symbol)
        return df
