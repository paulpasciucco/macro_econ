"""FRED API client using the fredapi library."""

from __future__ import annotations

import logging

import pandas as pd
from fredapi import Fred

from macro_econ.cache.store import make_key
from macro_econ.clients.base import BaseClient
from macro_econ.config import FRED_API_KEY
from macro_econ.series.node import SeriesNode

logger = logging.getLogger(__name__)


class FredClient(BaseClient):
    """Client for fetching data from FRED (Federal Reserve Economic Data).

    Uses the fredapi library as a wrapper around the FRED web service.
    """

    def __init__(self, api_key: str | None = None, **kwargs: object):
        super().__init__(rate_limit_delay=0.5, **kwargs)
        key = api_key or FRED_API_KEY
        if not key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY in .env or pass api_key parameter."
            )
        self._fred = Fred(api_key=key)

    def fetch_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: object,
    ) -> pd.DataFrame:
        """Fetch a single FRED series.

        Returns:
            DataFrame with DatetimeIndex and 'value' column.
        """
        cache_key = make_key("fred", series_id, start=start_date, end=end_date)

        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit: %s", series_id)
            return cached

        logger.info("Fetching from FRED: %s", series_id)
        self._rate_limit()

        raw = self._fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date,
        )

        df = raw.to_frame(name="value")
        df = self._normalize_df(df)
        df = df.dropna(subset=["value"])

        self.cache.put(cache_key, df, source="fred", series_id=series_id)
        return df

    def fetch_node(
        self,
        node: SeriesNode,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """Fetch data for a SeriesNode using its FRED source."""
        src = node.get_source("fred")
        if src is None:
            raise ValueError(f"Node '{node.code}' has no FRED source.")
        return self.fetch_series(src.series_id, start_date, end_date)

    def get_series_info(self, series_id: str) -> pd.Series:
        """Return metadata for a FRED series."""
        return self._fred.get_series_info(series_id)

    def search(self, query: str, limit: int = 20) -> pd.DataFrame:
        """Search for FRED series by keyword."""
        return self._fred.search(query, limit=limit)
