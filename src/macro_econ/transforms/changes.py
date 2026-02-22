"""Rate-of-change calculations for economic time series."""

from __future__ import annotations

import pandas as pd


def mom_change(df: pd.DataFrame, col: str = "value") -> pd.Series:
    """Month-over-month percent change."""
    return df[col].pct_change() * 100


def mom_annualized(df: pd.DataFrame, col: str = "value") -> pd.Series:
    """Month-over-month annualized percent change.

    Formula: ((1 + r)^12 - 1) * 100 where r is the monthly decimal change.
    """
    r = df[col].pct_change()
    return ((1 + r) ** 12 - 1) * 100


def qoq_change(df: pd.DataFrame, col: str = "value") -> pd.Series:
    """Quarter-over-quarter percent change."""
    return df[col].pct_change() * 100


def qoq_annualized(df: pd.DataFrame, col: str = "value") -> pd.Series:
    """Quarter-over-quarter annualized percent change (SAAR).

    Formula: ((1 + r)^4 - 1) * 100 where r is the quarterly decimal change.
    """
    r = df[col].pct_change()
    return ((1 + r) ** 4 - 1) * 100


def yoy_change(df: pd.DataFrame, periods: int = 12, col: str = "value") -> pd.Series:
    """Year-over-year percent change.

    Args:
        periods: 12 for monthly data, 4 for quarterly data.
    """
    return df[col].pct_change(periods=periods) * 100


def level_change(df: pd.DataFrame, periods: int = 1, col: str = "value") -> pd.Series:
    """Absolute level change (e.g., payroll gains in thousands)."""
    return df[col].diff(periods=periods)


def annualized_rate_from_index(
    df: pd.DataFrame,
    periods: int = 1,
    annualize_factor: int = 12,
    col: str = "value",
) -> pd.Series:
    """Annualized percent change from a price index.

    Formula: ((P_t / P_{t-n})^(annualize_factor/n) - 1) * 100

    Args:
        periods: Number of periods for the change (e.g., 1 for MoM, 3 for 3m).
        annualize_factor: 12 for monthly data, 4 for quarterly.
    """
    ratio = df[col] / df[col].shift(periods)
    return (ratio ** (annualize_factor / periods) - 1) * 100


def n_month_annualized(
    df: pd.DataFrame,
    n: int = 3,
    col: str = "value",
) -> pd.Series:
    """N-month annualized percent change from an index.

    Common for inflation analysis: 3-month, 6-month annualized rates.
    """
    return annualized_rate_from_index(df, periods=n, annualize_factor=12, col=col)
