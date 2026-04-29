"""
stock_fetcher.py — Fetch daily OHLCV stock data from Alpha Vantage.

Uses the TIME_SERIES_DAILY endpoint.  Returns a standardised pandas DataFrame
ready for consumption by the ETL and storage layers.
"""

import pandas as pd
import requests

from .base import BaseFetcher
from .config import ALPHA_VANTAGE_KEY
from .utils import rate_limit, retry, setup_logger
from dotenv import load_dotenv
load_dotenv()
logger = setup_logger(__name__)


class StockFetcher(BaseFetcher):
    """Fetch daily OHLCV equity data from the Alpha Vantage TIME_SERIES_DAILY endpoint.

    Parameters
    ----------
    api_key:
        Alpha Vantage API key.  Defaults to the value of the
        ``ALPHA_VANTAGE_KEY`` environment variable (or ``"demo"`` if unset).
    """

    BASE_URL: str = "https://www.alphavantage.co/query"
    SOURCE: str = "alphavantage"

    def __init__(self, api_key: str = ALPHA_VANTAGE_KEY) -> None:
        self.api_key = api_key

    @retry(max_attempts=3, delay=2)
    @rate_limit(calls_per_minute=25)
    def fetch(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        """Fetch daily OHLCV data for an equity symbol.

        Parameters
        ----------
        symbol:
            Ticker symbol, e.g. ``"AAPL"``.
        outputsize:
            ``"compact"`` returns the last 100 trading days (default).
            ``"full"`` returns up to 20 years of history.

        Returns
        -------
        pd.DataFrame
            Columns: ``[timestamp, open, high, low, close, volume, symbol, source]``
            Sorted by ``timestamp`` ascending.

        Raises
        ------
        ValueError
            If the Alpha Vantage response contains an error or note message,
            or if the expected time-series key is absent from the response.
        requests.HTTPError
            If the HTTP request itself fails.
        """
        logger.info("Fetching stock data for %s (outputsize=%s)", symbol, outputsize)

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        self._check_api_errors(data, symbol)

        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            raise ValueError(
                f"Unexpected response format for symbol '{symbol}': "
                f"key '{time_series_key}' not found. Response keys: {list(data.keys())}"
            )

        records = []
        for date_str, ohlcv in data[time_series_key].items():
            records.append(
                {
                    "timestamp": pd.to_datetime(date_str, utc=True),
                    "open": float(ohlcv["1. open"]),
                    "high": float(ohlcv["2. high"]),
                    "low": float(ohlcv["3. low"]),
                    "close": float(ohlcv["4. close"]),
                    "volume": float(ohlcv["5. volume"]),
                    "symbol": symbol,
                    "source": self.SOURCE,
                }
            )

        df = pd.DataFrame(records, columns=["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        self.validate(df)
        logger.info("Fetched %d rows for %s", len(df), symbol)
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_api_errors(data: dict, symbol: str) -> None:
        """Raise ValueError if the Alpha Vantage JSON contains an error payload.

        Alpha Vantage signals errors via JSON body rather than HTTP status codes.
        Common keys are ``"Error Message"`` and ``"Note"`` (rate-limit warning).
        """
        if "Error Message" in data:
            raise ValueError(
                f"Alpha Vantage API error for symbol '{symbol}': {data['Error Message']}"
            )
        if "Note" in data:
            raise ValueError(
                f"Alpha Vantage rate-limit note for symbol '{symbol}': {data['Note']}"
            )
        if "Information" in data:
            raise ValueError(
                f"Alpha Vantage information message for symbol '{symbol}': {data['Information']}"
            )
