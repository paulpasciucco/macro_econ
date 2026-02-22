"""Statistical tests for economic time series analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson as dw_stat
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf


@dataclass
class StationarityResult:
    """Result from a stationarity test."""

    test_name: str
    statistic: float
    p_value: float
    critical_values: dict
    is_stationary: bool
    summary: str


def adf_test(series: pd.Series, max_lags: int | None = None) -> StationarityResult:
    """Augmented Dickey-Fuller test for unit root.

    H0: Unit root exists (series is non-stationary).
    Reject H0 if p-value < 0.05.
    """
    result = adfuller(series.dropna(), maxlag=max_lags)
    stat, p_val = float(result[0]), float(result[1])
    crit = {k: float(v) for k, v in result[4].items()}
    is_stat = bool(p_val < 0.05)
    summary = (
        f"ADF statistic={stat:.4f}, p={p_val:.4f}. "
        f"{'Stationary' if is_stat else 'Non-stationary'} at 5% level."
    )
    return StationarityResult("ADF", stat, p_val, crit, is_stat, summary)


def kpss_test(series: pd.Series, regression: str = "c") -> StationarityResult:
    """KPSS test for stationarity.

    H0: Series is stationary.
    Reject H0 if p-value < 0.05 (series is non-stationary).

    Args:
        regression: "c" for level stationarity, "ct" for trend stationarity.
    """
    stat, p_val, _lags, crit = kpss(series.dropna(), regression=regression)
    stat, p_val = float(stat), float(p_val)
    crit = {k: float(v) for k, v in crit.items()}
    is_stat = bool(p_val >= 0.05)
    summary = (
        f"KPSS statistic={stat:.4f}, p={p_val:.4f}. "
        f"{'Stationary' if is_stat else 'Non-stationary'} at 5% level."
    )
    return StationarityResult("KPSS", stat, p_val, crit, is_stat, summary)


def compute_acf_pacf(
    series: pd.Series,
    nlags: int = 24,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute autocorrelation and partial autocorrelation functions.

    Returns:
        Tuple of (acf_values, pacf_values).
    """
    clean = series.dropna()
    acf_vals = acf(clean, nlags=nlags)
    pacf_vals = pacf(clean, nlags=min(nlags, len(clean) // 2 - 1))
    return acf_vals, pacf_vals


def ljung_box_test(
    series: pd.Series,
    lags: int | list[int] = 12,
) -> pd.DataFrame:
    """Ljung-Box test for autocorrelation.

    H0: No autocorrelation up to lag k.

    Returns:
        DataFrame with columns: lb_stat, lb_pvalue.
    """
    result = acorr_ljungbox(series.dropna(), lags=lags, return_df=True)
    return result


def durbin_watson(series: pd.Series) -> float:
    """Durbin-Watson statistic for serial correlation in residuals.

    Values near 2.0 indicate no autocorrelation.
    Values < 2 indicate positive autocorrelation.
    Values > 2 indicate negative autocorrelation.
    """
    return float(dw_stat(series.dropna().values))


def stl_decompose(
    series: pd.Series,
    period: int | None = None,
) -> object:
    """STL (Seasonal and Trend decomposition using Loess) decomposition.

    Args:
        period: Seasonal period. If None, attempts to infer from frequency:
            12 for monthly, 4 for quarterly.

    Returns:
        STL result object with .trend, .seasonal, .resid attributes.
    """
    clean = series.dropna()

    if period is None:
        freq = pd.infer_freq(clean.index)
        if freq and freq.startswith("M"):
            period = 12
        elif freq and freq.startswith("Q"):
            period = 4
        else:
            period = 12

    stl = STL(clean, period=period)
    return stl.fit()
