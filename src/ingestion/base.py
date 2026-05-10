"""
base.py — Abstract base class for all data fetchers in the ingestion module.

Every fetcher (stock, forex, crypto) must inherit from BaseFetcher and
implement the `fetch` method to return a standardised pandas DataFrame.
"""

from abc import ABC, abstractmethod

import pandas as pd


REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "symbol", "source"]


class BaseFetcher(ABC):
    """Abstract base class that all fetchers must subclass.

    Subclasses must implement :meth:`fetch`, which should return a pandas
    DataFrame that conforms to the standardised OHLCV schema.
    """

    @abstractmethod
    def fetch(self, symbol: str, **kwargs) -> pd.DataFrame:
        """Fetch financial data for *symbol* and return a standardised DataFrame.

        Parameters
        ----------
        symbol:
            The ticker / coin ID / currency code to fetch.
        **kwargs:
            Additional keyword arguments specific to each fetcher subclass.

        Returns
        -------
        pd.DataFrame
            A DataFrame with columns:
            [timestamp, open, high, low, close, volume, symbol, source]
        """

    def validate(self, df: pd.DataFrame) -> bool:
        """Check that *df* contains all required columns.

        Parameters
        ----------
        df:
            The DataFrame to validate.

        Returns
        -------
        bool
            ``True`` if the DataFrame is valid.

        Raises
        ------
        ValueError
            If one or more required columns are missing, listing exactly which
            columns are absent.
        """
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(
                f"DataFrame is missing required columns: {missing}. "
                f"Expected: {REQUIRED_COLUMNS}, got: {list(df.columns)}"
            )
        return True
