"""Seasonal adjustment comparison utilities."""

from __future__ import annotations

import pandas as pd


def compare_sa_nsa(
    sa: pd.DataFrame,
    nsa: pd.DataFrame,
    sa_col: str = "value",
    nsa_col: str = "value",
) -> pd.DataFrame:
    """Compare seasonally adjusted and non-seasonally adjusted series.

    Returns:
        DataFrame with columns: sa, nsa, seasonal_factor.
    """
    aligned_sa, aligned_nsa = sa[sa_col].align(nsa[nsa_col], join="inner")
    result = pd.DataFrame({
        "sa": aligned_sa,
        "nsa": aligned_nsa,
        "seasonal_factor": aligned_nsa / aligned_sa,
    })
    return result


def seasonal_factor(
    sa: pd.DataFrame,
    nsa: pd.DataFrame,
    sa_col: str = "value",
    nsa_col: str = "value",
) -> pd.Series:
    """Return the seasonal factor (NSA / SA) for plotting."""
    aligned_sa, aligned_nsa = sa[sa_col].align(nsa[nsa_col], join="inner")
    return aligned_nsa / aligned_sa
