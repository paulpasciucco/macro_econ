"""Smoothing functions for economic time series."""

from __future__ import annotations

import pandas as pd


def moving_average(
    df: pd.DataFrame,
    window: int = 3,
    center: bool = False,
    col: str = "value",
) -> pd.Series:
    """Simple moving average.

    Args:
        window: Number of periods (e.g., 3, 6, 12 for monthly data).
        center: If True, center the window.
    """
    return df[col].rolling(window=window, center=center).mean()


def exponential_smoothing(
    df: pd.DataFrame,
    span: int = 12,
    col: str = "value",
) -> pd.Series:
    """Exponentially weighted moving average.

    Args:
        span: Decay in terms of span. Larger span = smoother.
    """
    return df[col].ewm(span=span).mean()
