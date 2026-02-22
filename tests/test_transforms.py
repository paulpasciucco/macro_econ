"""Tests for the transformation engine."""

import numpy as np
import pandas as pd
import pytest

from macro_econ.transforms import (
    adf_test,
    compare_sa_nsa,
    durbin_watson,
    exponential_smoothing,
    kpss_test,
    level_change,
    ljung_box_test,
    mom_annualized,
    mom_change,
    moving_average,
    n_month_annualized,
    qoq_annualized,
    rebase_index,
    stl_decompose,
    yoy_change,
)


@pytest.fixture
def monthly_df():
    """Monthly series: 100, 102, 104.04, 106.1208 (2% monthly growth)."""
    dates = pd.date_range("2024-01-01", periods=4, freq="MS")
    values = [100.0, 102.0, 104.04, 106.1208]
    return pd.DataFrame({"value": values}, index=dates)


@pytest.fixture
def quarterly_df():
    """Quarterly series with known values."""
    dates = pd.date_range("2024-01-01", periods=8, freq="QS")
    values = [100.0, 101.0, 102.01, 103.0301, 104.060401, 105.10100501,
              106.15201506, 107.21353521]
    return pd.DataFrame({"value": values}, index=dates)


@pytest.fixture
def long_monthly_df():
    """24 months of data with trend + noise for statistical tests."""
    np.random.seed(42)
    dates = pd.date_range("2022-01-01", periods=24, freq="MS")
    trend = np.arange(24) * 0.5 + 100
    noise = np.random.normal(0, 0.3, 24)
    return pd.DataFrame({"value": trend + noise}, index=dates)


class TestChanges:
    def test_mom_change(self, monthly_df):
        result = mom_change(monthly_df)
        assert pd.isna(result.iloc[0])
        assert abs(result.iloc[1] - 2.0) < 0.01
        assert abs(result.iloc[2] - 2.0) < 0.01

    def test_mom_annualized(self, monthly_df):
        result = mom_annualized(monthly_df)
        # 2% monthly -> ((1.02)^12 - 1) * 100 = 26.82%
        assert abs(result.iloc[1] - 26.82) < 0.1

    def test_yoy_change(self, quarterly_df):
        result = yoy_change(quarterly_df, periods=4)
        # First 4 should be NaN, then ~4.06%
        assert pd.isna(result.iloc[0])
        assert abs(result.iloc[4] - 4.06) < 0.1

    def test_level_change(self, monthly_df):
        result = level_change(monthly_df)
        assert pd.isna(result.iloc[0])
        assert abs(result.iloc[1] - 2.0) < 0.01

    def test_qoq_annualized(self, quarterly_df):
        result = qoq_annualized(quarterly_df)
        # 1% quarterly -> ((1.01)^4 - 1) * 100 = 4.06%
        assert abs(result.iloc[1] - 4.06) < 0.1

    def test_n_month_annualized(self, monthly_df):
        result = n_month_annualized(monthly_df, n=1)
        # Same as mom_annualized for n=1
        assert abs(result.iloc[1] - 26.82) < 0.1


class TestLevels:
    def test_rebase_index(self, monthly_df):
        result = rebase_index(monthly_df, "2024-02-01")
        assert abs(result.iloc[1] - 100.0) < 0.01
        assert abs(result.iloc[0] - (100 / 102 * 100)) < 0.01


class TestSmoothing:
    def test_moving_average(self, monthly_df):
        result = moving_average(monthly_df, window=2)
        assert pd.isna(result.iloc[0])
        assert abs(result.iloc[1] - 101.0) < 0.01

    def test_exponential_smoothing(self, monthly_df):
        result = exponential_smoothing(monthly_df, span=2)
        assert len(result) == 4
        assert not pd.isna(result.iloc[0])


class TestSeasonal:
    def test_compare_sa_nsa(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="MS")
        sa = pd.DataFrame({"value": [100, 102, 104]}, index=dates)
        nsa = pd.DataFrame({"value": [98, 104, 103]}, index=dates)
        result = compare_sa_nsa(sa, nsa)
        assert "seasonal_factor" in result.columns
        assert abs(result["seasonal_factor"].iloc[0] - 0.98) < 0.01


class TestStatistics:
    def test_adf_test(self, long_monthly_df):
        result = adf_test(long_monthly_df["value"])
        assert result.test_name == "ADF"
        assert isinstance(result.p_value, float)
        assert isinstance(result.is_stationary, bool)

    def test_kpss_test(self, long_monthly_df):
        result = kpss_test(long_monthly_df["value"])
        assert result.test_name == "KPSS"
        assert isinstance(result.p_value, float)

    def test_ljung_box(self, long_monthly_df):
        result = ljung_box_test(long_monthly_df["value"], lags=6)
        assert len(result) == 6
        assert "lb_stat" in result.columns

    def test_durbin_watson(self, long_monthly_df):
        dw = durbin_watson(long_monthly_df["value"])
        assert 0 <= dw <= 4

    def test_stl_decompose(self, long_monthly_df):
        result = stl_decompose(long_monthly_df["value"], period=12)
        assert hasattr(result, "trend")
        assert hasattr(result, "seasonal")
        assert hasattr(result, "resid")
        assert len(result.trend) == 24
