"""
forex_fetcher.py — Fetch daily forex OHLC data from Alpha Vantage.

Uses the FX_DAILY endpoint.  Forex has no volume data so the ``volume``
column is populated with ``None`` / NaN.
"""

import pandas as pd
import requests

from .base import BaseFetcher
from .config import ALPHA_VANTAGE_KEY
from .utils import rate_limit, retry, setup_logger
from dotenv import load_dotenv
load_dotenv()

logger = setup_logger(__name__)


class ForexFetcher(BaseFetcher):
    """Fetch daily OHLC forex data from the Alpha Vantage FX_DAILY endpoint.

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
    def fetch(self, symbol: str = "", from_symbol: str = "", to_symbol: str = "") -> pd.DataFrame:
        """Fetch daily OHLC data for a currency pair.

        Either pass ``symbol`` in the form ``"USD/EUR"`` **or** pass
        ``from_symbol`` and ``to_symbol`` separately.

        Parameters
        ----------
        symbol:
            Currency pair string, e.g. ``"USD/EUR"``.  Used when
            ``from_symbol`` / ``to_symbol`` are not both provided.
        from_symbol:
            Base currency code, e.g. ``"USD"``.
        to_symbol:
            Quote currency code, e.g. ``"EUR"``.

        Returns
        -------
        pd.DataFrame
            Columns: ``[timestamp, open, high, low, close, volume, symbol, source]``
            ``volume`` is ``NaN`` (forex has no volume).
            Sorted by ``timestamp`` ascending.

        Raises
        ------
        ValueError
            If the Alpha Vantage response contains an error or note message,
            if the expected time-series key is absent from the response, or
            if neither a slash-delimited ``symbol`` nor both ``from_symbol``
            and ``to_symbol`` are supplied.
        requests.HTTPError
            If the HTTP request itself fails.
        """
        if from_symbol and to_symbol:
            # Explicit codes take precedence.
            pass
        elif "/" in symbol:
            from_symbol, to_symbol = symbol.split("/", 1)
        else:
            raise ValueError(
                "Provide either 'symbol' (e.g. 'USD/EUR') or both "
                "'from_symbol' and 'to_symbol'."
            )

        pair_label = f"{from_symbol}/{to_symbol}"
        logger.info("Fetching forex data for %s", pair_label)

        params = {
            "function": "FX_DAILY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": "compact",
            "apikey": self.api_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        self._check_api_errors(data, pair_label)

        time_series_key = "Time Series FX (Daily)"
        if time_series_key not in data:
            raise ValueError(
                f"Unexpected response format for pair '{pair_label}': "
                f"key '{time_series_key}' not found. Response keys: {list(data.keys())}"
            )

        records = []
        for date_str, ohlc in data[time_series_key].items():
            records.append(
                {
                    "timestamp": pd.to_datetime(date_str, utc=True),
                    "open": float(ohlc["1. open"]),
                    "high": float(ohlc["2. high"]),
                    "low": float(ohlc["3. low"]),
                    "close": float(ohlc["4. close"]),
                    "volume": float("nan"),
                    "symbol": pair_label,
                    "source": self.SOURCE,
                }
            )

        df = pd.DataFrame(records, columns=["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        self.validate(df)
        logger.info("Fetched %d rows for %s", len(df), pair_label)
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_api_errors(data: dict, pair_label: str) -> None:
        """Raise ValueError if the Alpha Vantage JSON contains an error payload."""
        if "Error Message" in data:
            raise ValueError(
                f"Alpha Vantage API error for pair '{pair_label}': {data['Error Message']}"
            )
        if "Note" in data:
            raise ValueError(
                f"Alpha Vantage rate-limit note for pair '{pair_label}': {data['Note']}"
            )
        if "Information" in data:
            raise ValueError(
                f"Alpha Vantage information message for pair '{pair_label}': {data['Information']}"
            )
