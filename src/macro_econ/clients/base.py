"""Abstract base client for API data fetching."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

import pandas as pd

from macro_econ.cache.store import ParquetCacheStore

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Abstract base for all API clients.

    All clients share:
    - A cache store for avoiding redundant API calls
    - A normalized return format: pd.DataFrame with DatetimeIndex and 'value' column
    - Rate limiting via sleep between requests
    """

    def __init__(
        self,
        cache: ParquetCacheStore | None = None,
        rate_limit_delay: float = 0.5,
    ):
        self.cache = cache or ParquetCacheStore()
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Sleep if needed to respect rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    @abstractmethod
    def fetch_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: object,
    ) -> pd.DataFrame:
        """Fetch a single time series.

        Returns:
            DataFrame with DatetimeIndex named 'date' and a 'value' column.
        """
        ...

    @staticmethod
    def _normalize_df(df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        """Ensure DataFrame has DatetimeIndex and 'value' column."""
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        if value_col != "value" and value_col in df.columns:
            df = df.rename(columns={value_col: "value"})
        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df
