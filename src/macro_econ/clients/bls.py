"""BLS (Bureau of Labor Statistics) API v2 client."""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
import requests

from macro_econ.cache.store import make_key
from macro_econ.clients.base import BaseClient
from macro_econ.config import (
    BLS_API_KEY,
    BLS_API_URL,
    BLS_MAX_SERIES_PER_REQUEST,
    BLS_MAX_YEARS_PER_REQUEST,
)
from macro_econ.series.node import SeriesNode

logger = logging.getLogger(__name__)


class BlsClient(BaseClient):
    """Client for fetching data from the BLS Public Data API v2.

    The v2 API requires a registration key and supports:
    - Up to 50 series per request
    - Up to 500 requests per day
    - Up to 20 years of data per request
    """

    def __init__(self, api_key: str | None = None, **kwargs: object):
        super().__init__(rate_limit_delay=0.5, **kwargs)
        self.api_key = api_key or BLS_API_KEY
        if not self.api_key:
            raise ValueError(
                "BLS API key required. Set BLS_API_KEY in .env or pass api_key parameter."
            )

    def _post(self, series_ids: list[str], start_year: int, end_year: int) -> dict:
        """Make a POST request to the BLS API."""
        payload = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": self.api_key,
        }
        self._rate_limit()
        logger.info(
            "BLS API request: %d series, %d-%d", len(series_ids), start_year, end_year
        )
        resp = requests.post(
            BLS_API_URL,
            json=payload,
            headers={"Content-type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "REQUEST_SUCCEEDED":
            msg = data.get("message", ["Unknown error"])
            raise ValueError(f"BLS API error: {msg}")

        return data

    @staticmethod
    def _parse_bls_records(records: list[dict]) -> pd.DataFrame:
        """Parse BLS response records into a DataFrame.

        Skips M13 (annual average). Parses year+period into timestamps.
        """
        rows = []
        for rec in records:
            period = rec.get("period", "")
            if period == "M13":
                continue
            if not period.startswith("M"):
                continue
            year = int(rec["year"])
            month = int(period[1:])
            value = rec.get("value")
            rows.append({
                "date": pd.Timestamp(year, month, 1),
                "value": float(value) if value else None,
            })

        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["value"], index=pd.DatetimeIndex([], name="date"))

        df = df.set_index("date").sort_index()
        df = df.dropna(subset=["value"])
        return df

    def fetch_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: object,
    ) -> pd.DataFrame:
        """Fetch a single BLS series.

        Args:
            series_id: Full BLS series ID (e.g., "CUSR0000SA0").
            start_date: Start date string (parsed to extract year).
            end_date: End date string.

        Returns:
            DataFrame with DatetimeIndex and 'value' column.
        """
        now = datetime.now()
        start_year = int(start_date[:4]) if start_date else now.year - BLS_MAX_YEARS_PER_REQUEST
        end_year = int(end_date[:4]) if end_date else now.year

        cache_key = make_key("bls", series_id, start=start_year, end=end_year)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit: %s", series_id)
            return cached

        data = self._post([series_id], start_year, end_year)
        series_data = data["Results"]["series"][0].get("data", [])
        df = self._parse_bls_records(series_data)

        self.cache.put(cache_key, df, source="bls", series_id=series_id)
        return df

    def fetch_multiple(
        self,
        series_ids: list[str],
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch multiple BLS series in batches of 50.

        Returns:
            Dict mapping series_id -> DataFrame.
        """
        now = datetime.now()
        sy = start_year or (now.year - BLS_MAX_YEARS_PER_REQUEST)
        ey = end_year or now.year

        results: dict[str, pd.DataFrame] = {}

        # Check cache first
        to_fetch: list[str] = []
        for sid in series_ids:
            cache_key = make_key("bls", sid, start=sy, end=ey)
            cached = self.cache.get(cache_key)
            if cached is not None:
                results[sid] = cached
            else:
                to_fetch.append(sid)

        # Fetch remaining in batches
        for i in range(0, len(to_fetch), BLS_MAX_SERIES_PER_REQUEST):
            batch = to_fetch[i : i + BLS_MAX_SERIES_PER_REQUEST]
            data = self._post(batch, sy, ey)

            for series_entry in data["Results"]["series"]:
                sid = series_entry["seriesID"]
                records = series_entry.get("data", [])
                df = self._parse_bls_records(records)
                cache_key = make_key("bls", sid, start=sy, end=ey)
                self.cache.put(cache_key, df, source="bls", series_id=sid)
                results[sid] = df

        return results

    def fetch_node_tree(
        self,
        root: SeriesNode,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch all BLS series for a hierarchy tree.

        Walks the tree, collects all BLS series IDs, and fetches them in batches.

        Returns:
            Dict mapping node code -> DataFrame.
        """
        code_to_sid: dict[str, str] = {}
        for node in root.walk():
            bls_src = node.get_source("bls")
            if bls_src:
                code_to_sid[node.code] = bls_src.series_id

        if not code_to_sid:
            return {}

        sid_to_df = self.fetch_multiple(
            list(code_to_sid.values()),
            start_year=start_year,
            end_year=end_year,
        )

        return {
            code: sid_to_df[sid]
            for code, sid in code_to_sid.items()
            if sid in sid_to_df
        }
