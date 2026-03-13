"""CPI (Consumer Price Index) hierarchy tree.

Loads the full BLS CPI-U expenditure hierarchy from ``data/CPI/cpi_hierarchy.csv``.
The CSV covers all 300+ item codes at every indent level, plus special
aggregates (Core CPI, Energy, Supercore, etc.).

Sources per node:
    - BLS CPI-U SA  (``CUSR0000{item_code}``)
    - BLS CPI-U NSA (``CUUR0000{item_code}``)
    - FRED for key headline series
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from macro_econ.series.loaders import load_cpi_hierarchy
from macro_econ.series.node import SeriesNode


def build_cpi_tree(
    *,
    path: Optional[Path] = None,
    max_depth: Optional[int] = None,
) -> SeriesNode:
    """Build the full CPI-U hierarchy tree from the data file.

    Args:
        path: Override path to cpi_hierarchy.csv.
        max_depth: Prune the tree at this depth (None = full detail).

    Returns:
        Root SeriesNode for the CPI hierarchy.
    """
    return load_cpi_hierarchy(path=path, max_depth=max_depth)
