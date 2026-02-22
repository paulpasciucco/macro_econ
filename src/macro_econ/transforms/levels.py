"""Level conversions for economic time series."""

from __future__ import annotations

import pandas as pd


def rebase_index(
    df: pd.DataFrame,
    base_period: str | pd.Timestamp,
    col: str = "value",
) -> pd.Series:
    """Rebase a price index so that base_period = 100.

    Args:
        base_period: The date at which the index should equal 100.
    """
    base_ts = pd.Timestamp(base_period)
    if base_ts not in df.index:
        closest = df.index[df.index.get_indexer([base_ts], method="nearest")[0]]
        base_ts = closest
    base_value = df.loc[base_ts, col]
    return (df[col] / base_value) * 100


def real_from_nominal(
    nominal: pd.DataFrame,
    deflator: pd.DataFrame,
    nominal_col: str = "value",
    deflator_col: str = "value",
) -> pd.Series:
    """Convert current dollars to real (chained) dollars using a price deflator.

    Formula: real = nominal / deflator * 100
    """
    aligned_nom, aligned_def = nominal[nominal_col].align(deflator[deflator_col], join="inner")
    return aligned_nom / aligned_def * 100


def contribution_to_change(
    component: pd.DataFrame,
    aggregate: pd.DataFrame,
    component_col: str = "value",
    aggregate_col: str = "value",
) -> pd.Series:
    """Calculate a component's contribution to the aggregate's percent change.

    Uses the share-weighted approach:
    contribution = (component_change / aggregate_previous) * 100

    This is a simplified version. BEA uses Fisher index-based contributions
    which are more precise but require both price and quantity data.
    """
    comp_change = component[component_col].diff()
    agg_previous = aggregate[aggregate_col].shift(1)
    aligned_change, aligned_prev = comp_change.align(agg_previous, join="inner")
    return aligned_change / aligned_prev * 100
