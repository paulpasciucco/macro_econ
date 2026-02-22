"""BEA (Bureau of Economic Analysis) API client for NIPA tables."""

from __future__ import annotations

import logging
import re

import pandas as pd
import requests

from macro_econ.cache.store import make_key
from macro_econ.clients.base import BaseClient
from macro_econ.config import BEA_API_KEY, BEA_API_URL

logger = logging.getLogger(__name__)


class BeaClient(BaseClient):
    """Client for fetching data from the BEA NIPA tables.

    Each NIPA API call returns an entire table, so caching is done at the
    table level rather than per-series.
    """

    def __init__(self, api_key: str | None = None, **kwargs: object):
        super().__init__(rate_limit_delay=0.6, **kwargs)
        self.api_key = api_key or BEA_API_KEY
        if not self.api_key:
            raise ValueError(
                "BEA API key required. Set BEA_API_KEY in .env or pass api_key parameter."
            )

    def _request(self, params: dict) -> dict:
        """Make a GET request to the BEA API."""
        params = {
            "UserID": self.api_key,
            "ResultFormat": "JSON",
            **params,
        }
        self._rate_limit()
        logger.info("BEA API request: %s", {k: v for k, v in params.items() if k != "UserID"})
        resp = requests.get(BEA_API_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if "BEAAPI" not in data:
            raise ValueError(f"Unexpected BEA response: {data}")

        results = data["BEAAPI"]["Results"]
        if isinstance(results, dict) and "Error" in results:
            raise ValueError(f"BEA API error: {results['Error']}")

        return data

    @staticmethod
    def _parse_time_period(tp: str) -> pd.Timestamp:
        """Parse BEA TimePeriod strings like '2024Q3', '2024M09', '2024'."""
        if re.match(r"^\d{4}Q\d$", tp):
            year, q = int(tp[:4]), int(tp[-1])
            month = (q - 1) * 3 + 1
            return pd.Timestamp(year, month, 1)
        elif re.match(r"^\d{4}M\d{2}$", tp):
            year, month = int(tp[:4]), int(tp[5:])
            return pd.Timestamp(year, month, 1)
        elif re.match(r"^\d{4}$", tp):
            return pd.Timestamp(int(tp), 1, 1)
        else:
            raise ValueError(f"Cannot parse BEA TimePeriod: {tp}")

    def fetch_nipa_table(
        self,
        table_name: str,
        frequency: str = "Q",
        year: str = "ALL",
    ) -> pd.DataFrame:
        """Fetch an entire NIPA table.

        Args:
            table_name: e.g., "T10105", "T20305"
            frequency: "A" (annual), "Q" (quarterly), "M" (monthly)
            year: Specific year(s) or "ALL"

        Returns:
            DataFrame with columns: LineNumber, LineDescription, TimePeriod,
            DataValue, date (parsed timestamp).
        """
        cache_key = make_key("bea_table", table_name, frequency=frequency, year=year)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit: BEA table %s", table_name)
            return cached

        data = self._request({
            "Method": "GetData",
            "datasetname": "NIPA",
            "TableName": table_name,
            "Frequency": frequency,
            "Year": year,
        })

        records = data["BEAAPI"]["Results"]["Data"]
        df = pd.DataFrame(records)

        # Parse time periods
        df["date"] = df["TimePeriod"].apply(self._parse_time_period)
        df["DataValue"] = pd.to_numeric(
            df["DataValue"].str.replace(",", ""), errors="coerce"
        )
        df["LineNumber"] = pd.to_numeric(df["LineNumber"], errors="coerce")

        self.cache.put(cache_key, df, source="bea", table=table_name,
                       frequency=frequency, year=year)
        return df

    def fetch_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        *,
        table: str | None = None,
        line_number: int | None = None,
        frequency: str = "Q",
        **kwargs: object,
    ) -> pd.DataFrame:
        """Fetch a single series from a NIPA table.

        Args:
            series_id: The table name (used as primary identifier for BEA).
            table: Override table name.
            line_number: Line number within the table.
            frequency: A/Q/M.

        Returns:
            DataFrame with DatetimeIndex and 'value' column.
        """
        tbl = table or series_id
        if line_number is None:
            raise ValueError("line_number is required for BEA series extraction.")

        full_table = self.fetch_nipa_table(tbl, frequency)

        mask = full_table["LineNumber"] == line_number
        if start_date:
            mask &= full_table["date"] >= pd.Timestamp(start_date)
        if end_date:
            mask &= full_table["date"] <= pd.Timestamp(end_date)

        subset = full_table[mask][["date", "DataValue"]].copy()
        subset = subset.rename(columns={"DataValue": "value"})
        subset = subset.set_index("date").sort_index()
        return self._normalize_df(subset)

    def list_tables(self) -> pd.DataFrame:
        """List available NIPA tables."""
        data = self._request({
            "Method": "GetParameterValues",
            "datasetname": "NIPA",
            "ParameterName": "TableName",
        })
        records = data["BEAAPI"]["Results"]["ParamValue"]
        return pd.DataFrame(records)
