"""PCE (Personal Consumption Expenditures) hierarchy tree.

Loads the full BEA NIPA Table 2.x.x hierarchy from ``data/PCE/pce_hierarchy.tsv``.
The TSV covers 119 components across 5 levels, each mapped to 6 BEA metric
tables (percent change, contributions, quantity index, price index, nominal, real).

Sources per node:
    - BEA table+line for each of the 6 metric types
    - FRED for key headline series (PCE, PCDG, PCND, PCES, etc.)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from macro_econ.series.loaders import load_pce_hierarchy
from macro_econ.series.node import SeriesNode


def build_pce_tree(
    *,
    path: Optional[Path] = None,
    max_depth: Optional[int] = None,
) -> SeriesNode:
    """Build the full PCE hierarchy tree from the data file.

    Args:
        path: Override path to pce_hierarchy.tsv.
        max_depth: Prune the tree at this depth (None = full detail).

    Returns:
        Root SeriesNode for the PCE hierarchy.
    """
    return load_pce_hierarchy(path=path, max_depth=max_depth)
