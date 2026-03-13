"""Load hierarchy trees from CSV/TSV data files.

Each loader reads a structured data file and builds a SeriesNode tree,
replacing the previously hard-coded hierarchy definitions with the
comprehensive breakdowns in the data/ directory.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from macro_econ.series.node import SeriesNode, SeriesSource

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


# ---------------------------------------------------------------------------
# FRED supplementary mappings (key series only)
# ---------------------------------------------------------------------------

_CPI_FRED: dict[str, str] = {
    "SA0": "CPIAUCSL",
    "SA0L1E": "CPILFESL",
    "SA0E": "CPIENGSL",
    "SAF": "CPIFABSL",
    "SAH": "CPIHOSSL",
    "SAA": "CPIAPPSL",
    "SAT": "CPITRNSL",
    "SAM": "CPIMEDSL",
    "SAR": "CPIRECSL",
    "SAE": "CPIEDUSL",
    "SAG": "CPIOGSSL",
}

_PCE_FRED: dict[str, str] = {
    "pce_total": "PCE",
    "goods": "DGDSRC1M027NBEA",
    "durable_goods": "PCDG",
    "nondurable_goods": "PCND",
    "services": "PCES",
}

_CES_FRED: dict[str, str] = {
    "00-000000": "PAYEMS",
    "05-000000": "USPRIV",
    "10-000000": "USMINE",
    "20-000000": "USCONS",
    "30-000000": "MANEMP",
    "40-000000": "USTPU",
    "50-000000": "USINFO",
    "55-000000": "USFIRE",
    "60-000000": "USSERV",
    "65-000000": "USEHS",
    "70-000000": "USLAH",
    "80-000000": "USOTHER",
    "90-000000": "USGOVT",
    "31-000000": "DMANEMP",
    "32-000000": "NDMANEMP",
}


# ---------------------------------------------------------------------------
# CPI Loader
# ---------------------------------------------------------------------------

def load_cpi_hierarchy(
    path: Optional[Path] = None,
    *,
    max_depth: Optional[int] = None,
) -> SeriesNode:
    """Build a CPI SeriesNode tree from cpi_hierarchy.csv.

    The CSV contains both expenditure items and special aggregates
    (item_type column). Expenditure items form the main tree, special
    aggregates are attached as a separate branch.

    Args:
        path: Override path to the CSV file.
        max_depth: If set, prune the tree at this depth.
    """
    csv_path = path or (_DATA_DIR / "CPI" / "cpi_hierarchy.csv")

    expenditure_rows: list[dict] = []
    special_rows: list[dict] = []

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("item_type") == "special_aggregate":
                special_rows.append(row)
            else:
                expenditure_rows.append(row)

    # Build nodes keyed by item_name
    nodes: dict[str, SeriesNode] = {}
    root: Optional[SeriesNode] = None

    for row in expenditure_rows:
        item_code = row["bls_item_code"]
        level = int(row["indent_level"])

        # Skip section header rows with no valid item code
        if not item_code or "nan" in row.get("bls_series_id_cpi_u_sa", "nan"):
            # Still register in nodes dict so children can link
            header = SeriesNode(
                name=row["item_name"],
                code=f"CPI_HEADER_{level}",
                level=level,
            )
            nodes[row["item_name"]] = header
            continue

        sa_id = row["bls_series_id_cpi_u_sa"]
        nsa_id = row["bls_series_id_cpi_u_nsa"]

        if max_depth is not None and level > max_depth:
            continue

        sources: list[SeriesSource] = [
            SeriesSource("bls", sa_id, {
                "item_code": item_code,
                "seasonal": "S",
                "metric": "sa",
            }),
            SeriesSource("bls", nsa_id, {
                "item_code": item_code,
                "seasonal": "U",
                "metric": "nsa",
            }),
        ]
        # Add FRED source for key series
        fred_id = _CPI_FRED.get(item_code)
        if fred_id:
            sources.append(SeriesSource("fred", fred_id))

        code = f"CPI_{item_code}" if item_code != "SA0" else "CPI"
        node = SeriesNode(
            name=row["item_name"],
            code=code,
            sources=sources,
            level=level,
        )
        nodes[row["item_name"]] = node

        if level == 0 and root is None:
            root = node

    # Link parents
    for row in expenditure_rows:
        level = int(row["indent_level"])
        if max_depth is not None and level > max_depth:
            continue
        parent_name = row["parent_item"]
        if parent_name and parent_name in nodes:
            parent = nodes[parent_name]
            child = nodes[row["item_name"]]
            child.parent = parent
            child.level = parent.level + 1
            parent.children.append(child)

    # Attach special aggregates as a branch
    if root is not None and special_rows:
        special_branch = SeriesNode(
            name="Special Aggregates",
            code="CPI_SPECIAL",
            description="Cross-cutting CPI aggregates",
        )
        for row in special_rows:
            item_code = row["bls_item_code"]
            sa_id = row["bls_series_id_cpi_u_sa"]
            nsa_id = row["bls_series_id_cpi_u_nsa"]

            sources = [
                SeriesSource("bls", sa_id, {
                    "item_code": item_code,
                    "seasonal": "S",
                    "metric": "sa",
                }),
                SeriesSource("bls", nsa_id, {
                    "item_code": item_code,
                    "seasonal": "U",
                    "metric": "nsa",
                }),
            ]
            fred_id = _CPI_FRED.get(item_code)
            if fred_id:
                sources.append(SeriesSource("fred", fred_id))

            special_branch.children.append(SeriesNode(
                name=row["item_name"],
                code=f"CPI_{item_code}",
                sources=sources,
            ))

        root.add_child(special_branch)

    if root is None:
        raise ValueError(f"No root node found in {csv_path}")

    # Fix up levels from the root
    _fix_levels(root, 0)
    return root


# ---------------------------------------------------------------------------
# PCE Loader
# ---------------------------------------------------------------------------

_PCE_METRIC_TABLES: dict[str, str] = {
    "pct_change": "bea_pct_change",
    "contributions": "bea_contributions",
    "quantity_index": "bea_quantity_index",
    "price_index": "bea_price_index",
    "nominal": "bea_nominal",
    "real": "bea_real",
}

_PCE_METRIC_LABELS: dict[str, str] = {
    "pct_change": "Percent Change",
    "contributions": "Contributions to % Change",
    "quantity_index": "Quantity Index",
    "price_index": "Price Index",
    "nominal": "Nominal ($)",
    "real": "Real (Chained 2017$)",
}


def load_pce_hierarchy(
    path: Optional[Path] = None,
    *,
    max_depth: Optional[int] = None,
) -> SeriesNode:
    """Build a PCE SeriesNode tree from pce_hierarchy.tsv.

    Each node carries BEA sources for 6 metric types (percent change,
    contributions, quantity index, price index, nominal, real).

    Args:
        path: Override path to the TSV file.
        max_depth: If set, prune the tree at this depth.
    """
    tsv_path = path or (_DATA_DIR / "PCE" / "pce_hierarchy.tsv")

    rows: list[dict] = []
    with open(tsv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            rows.append(row)

    nodes: dict[str, SeriesNode] = {}
    root: Optional[SeriesNode] = None

    for row in rows:
        key = row["key"]
        level = int(row["level"])
        if max_depth is not None and level > max_depth:
            continue

        sources: list[SeriesSource] = []
        for metric, col in _PCE_METRIC_TABLES.items():
            ref = row.get(col, "")
            if not ref or ":" not in ref:
                continue
            table, line_ref = ref.split(":", 1)
            line_num = int(line_ref[1:])  # "L1" -> 1
            sources.append(SeriesSource(
                "bea",
                table,
                {
                    "table": table,
                    "line_number": line_num,
                    "frequency": "M",
                    "metric": metric,
                },
            ))

        # Add FRED source for key series
        fred_id = _PCE_FRED.get(key)
        if fred_id:
            sources.append(SeriesSource("fred", fred_id, {"metric": "nominal"}))

        code = f"PCE_{key.upper()}" if key != "pce_total" else "PCE"
        node = SeriesNode(
            name=row["name"],
            code=code,
            sources=sources,
            level=level,
        )
        nodes[key] = node

        if level == 0:
            root = node

    # Link parents
    for row in rows:
        level = int(row["level"])
        if max_depth is not None and level > max_depth:
            continue
        parent_key = row.get("parent", "")
        if parent_key and parent_key in nodes:
            parent = nodes[parent_key]
            child = nodes[row["key"]]
            child.parent = parent
            child.level = parent.level + 1
            parent.children.append(child)

    if root is None:
        raise ValueError(f"No root node found in {tsv_path}")

    _fix_levels(root, 0)
    return root


# ---------------------------------------------------------------------------
# CES (Payrolls) Loader
# ---------------------------------------------------------------------------

_CES_METRIC_COLS: dict[str, tuple[str, str]] = {
    # metric -> (SA column, NSA column)
    "employment": ("series_id_SA_employment", "series_id_NSA_employment"),
    "avg_hourly_earnings": ("series_id_SA_avg_hourly_earnings", "series_id_NSA_avg_hourly_earnings"),
    "avg_weekly_hours": ("series_id_SA_avg_weekly_hours", "series_id_NSA_avg_weekly_hours"),
    "avg_weekly_earnings": ("series_id_SA_avg_weekly_earnings", "series_id_NSA_avg_weekly_earnings"),
}

_CES_METRIC_LABELS: dict[str, str] = {
    "employment": "All Employees (Thousands)",
    "avg_hourly_earnings": "Avg Hourly Earnings ($)",
    "avg_weekly_hours": "Avg Weekly Hours",
    "avg_weekly_earnings": "Avg Weekly Earnings ($)",
}


def load_ces_hierarchy(
    path: Optional[Path] = None,
    *,
    max_depth: Optional[int] = None,
) -> SeriesNode:
    """Build a CES SeriesNode tree from the payrolls CSV.

    Each node carries BLS sources for multiple metrics: employment,
    average hourly earnings, average weekly hours, and average weekly
    earnings (both SA and NSA variants).

    Args:
        path: Override path to the CSV file.
        max_depth: If set, prune the tree at this depth.
    """
    csv_path = path or (_DATA_DIR / "Payrolls" / "bls_ces_payrolls_hierarchy_comma_safe.csv")

    rows: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)

    nodes: dict[str, SeriesNode] = {}
    root: Optional[SeriesNode] = None

    for row in rows:
        ces_code = row["ces_industry_code"]
        level = int(row["hierarchy_depth"])
        if max_depth is not None and level > max_depth:
            continue

        sources: list[SeriesSource] = []
        industry_8 = row.get("series_industry_8digit", "")

        for metric, (sa_col, nsa_col) in _CES_METRIC_COLS.items():
            sa_id = row.get(sa_col, "")
            if sa_id:
                sources.append(SeriesSource("bls", sa_id, {
                    "industry_code": industry_8,
                    "seasonal": "S",
                    "metric": metric,
                }))
            nsa_id = row.get(nsa_col, "")
            if nsa_id:
                sources.append(SeriesSource("bls", nsa_id, {
                    "industry_code": industry_8,
                    "seasonal": "U",
                    "metric": metric,
                }))

        # FRED source for key aggregates (employment only)
        fred_id = _CES_FRED.get(ces_code)
        if fred_id:
            sources.append(SeriesSource("fred", fred_id, {"metric": "employment"}))

        code = f"CES_{ces_code.replace('-', '_')}"
        if ces_code == "00-000000":
            code = "NFP"

        node = SeriesNode(
            name=row["industry_title"],
            code=code,
            sources=sources,
            level=level,
        )
        nodes[ces_code] = node

        if level == 0:
            root = node

    # Link parents
    for row in rows:
        level = int(row["hierarchy_depth"])
        if max_depth is not None and level > max_depth:
            continue
        parent_code = row.get("parent_ces_code", "")
        if parent_code and parent_code in nodes:
            parent = nodes[parent_code]
            child = nodes[row["ces_industry_code"]]
            child.parent = parent
            child.level = parent.level + 1
            parent.children.append(child)

    if root is None:
        raise ValueError(f"No root node found in {csv_path}")

    _fix_levels(root, 0)
    return root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fix_levels(node: SeriesNode, level: int) -> None:
    """Recursively set correct levels from root down."""
    node.level = level
    for child in node.children:
        _fix_levels(child, level + 1)


# Metric label registries (importable by viewer)
METRIC_OPTIONS: dict[str, dict[str, str]] = {
    "CPI": {"sa": "Seasonally Adjusted", "nsa": "Not Seasonally Adjusted"},
    "PCE": _PCE_METRIC_LABELS,
    "GDP": {},
    "CES": _CES_METRIC_LABELS,
    "CPS": {},
}
