"""Unified interactive viewer for economic data analysis.

Provides a single consolidated widget-based interface for exploring all
series hierarchies (CPI, PCE, GDP, CES, CPS) with:
- Metric-aware data fetching (e.g. CES employment vs earnings, PCE nominal vs price index)
- Hierarchy visualization (Treemap / Sunburst) driven by CSV/TSV data files
- Single-series drilldown with transforms, date range, and moving averages
- Multi-series heatmap comparison table with pre-built scenarios
"""

from __future__ import annotations

from datetime import date
from typing import Any

import ipywidgets as widgets
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from IPython.display import HTML, clear_output, display

from macro_econ.series.cpi import build_cpi_tree
from macro_econ.series.employment import build_ces_tree, build_cps_tree
from macro_econ.series.gdp import build_gdp_tree
from macro_econ.series.loaders import METRIC_OPTIONS
from macro_econ.series.node import SeriesNode
from macro_econ.series.pce import build_pce_tree
from macro_econ.viz.styles import DEFAULT_LAYOUT

# ---------------------------------------------------------------------------
# Pre-defined scenario tables for common multi-series analyses
# ---------------------------------------------------------------------------
SCENARIOS: dict[str, dict[str, list[str]]] = {
    "CPI": {
        "Core vs Headline": ["CPI", "CPI_SA0L1E", "CPI_SASLE"],
        "Shelter Components": [
            "CPI_SAH1", "CPI_SEHC", "CPI_SEHA", "CPI_SEHB",
        ],
        "Food": [
            "CPI_SAF1", "CPI_SAF11", "CPI_SEFV", "CPI_SAF2",
        ],
        "Energy": [
            "CPI_SA0E", "CPI_SETB", "CPI_SAH21",
            "CPI_SEHF01", "CPI_SEHF02",
        ],
        "Transportation": [
            "CPI_SAT", "CPI_SETA01", "CPI_SETA02",
            "CPI_SETB", "CPI_SETE", "CPI_SETG01",
        ],
        "Medical": [
            "CPI_SAM", "CPI_SAM1", "CPI_SAM2", "CPI_SEME",
        ],
        "Major Groups": [
            "CPI_SAF", "CPI_SAH", "CPI_SAA", "CPI_SAT",
            "CPI_SAM", "CPI_SAR", "CPI_SAE", "CPI_SAG",
        ],
    },
    "PCE": {
        "Goods vs Services": ["PCE", "PCE_GOODS", "PCE_SERVICES"],
        "Durable vs Nondurable": ["PCE_DURABLE_GOODS", "PCE_NONDURABLE_GOODS"],
        "Services Detail": [
            "PCE_HOUSING_AND_UTILITIES", "PCE_HEALTH_CARE",
            "PCE_TRANSPORTATION_SERVICES", "PCE_RECREATION_SERVICES",
            "PCE_FOOD_SERVICES_AND_ACCOMMODATIONS", "PCE_FINANCIAL_SERVICES_AND_INSURANCE",
        ],
        "Motor Vehicles": [
            "PCE_MOTOR_VEHICLES_AND_PARTS", "PCE_NEW_MOTOR_VEHICLES",
            "PCE_NET_USED_MOTOR_VEHICLES", "PCE_MOTOR_VEHICLE_PARTS_AND_ACCESSORIES",
        ],
    },
    "GDP": {
        "Main Components (C+I+G+NX)": ["GDP_C", "GDP_I", "GDP_NX", "GDP_G"],
        "Investment Detail": [
            "GDP_I_FIXED", "GDP_I_NONRES", "GDP_I_RES", "GDP_I_INV",
        ],
        "Nonresidential": ["GDP_I_STRUCT", "GDP_I_EQUIP", "GDP_I_IP"],
        "Government": [
            "GDP_G_FED", "GDP_G_DEF", "GDP_G_NONDEF", "GDP_G_SL",
        ],
        "Trade": [
            "GDP_X", "GDP_M", "GDP_X_GOODS", "GDP_X_SVC",
            "GDP_M_GOODS", "GDP_M_SVC",
        ],
        "Price Measures": ["GDP_DEFL", "GDP_CHAIN_PI"],
    },
    "CES": {
        "Major Sectors": ["CES_05_000000", "CES_06_000000", "CES_08_000000", "CES_90_000000"],
        "Goods Producing": ["CES_10_000000", "CES_20_000000", "CES_30_000000"],
        "Service Providing": [
            "CES_40_000000", "CES_50_000000", "CES_55_000000", "CES_60_000000",
            "CES_65_000000", "CES_70_000000", "CES_80_000000",
        ],
        "Manufacturing": ["CES_31_000000", "CES_32_000000"],
    },
    "CPS": {
        "Headline": ["UR", "LFPR", "EPOP"],
        "Alternative Unemployment (U1-U6)": [
            "U1", "U2", "U3", "U4", "U5", "U6",
        ],
        "By Age": ["UR_16_19", "UR_20_24", "UR_25_54", "UR_55_PLUS"],
        "By Gender": ["UR_MEN", "UR_WOMEN"],
        "By Race": ["UR_WHITE", "UR_BLACK", "UR_HISPANIC", "UR_ASIAN"],
        "Prime Age": ["UR_25_54", "LFPR_25_54", "EPOP_25_54"],
    },
}

# Transform options: (display label, code)
TRANSFORMS = [
    ("Level", "level"),
    ("MoM %", "mom"),
    ("MoM Annualized %", "mom_ann"),
    ("QoQ %", "qoq"),
    ("QoQ Annualized %", "qoq_ann"),
    ("YoY %", "yoy"),
    ("3m Annualized %", "ann3"),
    ("6m Annualized %", "ann6"),
    ("Level Change", "diff"),
]

_TRANSFORM_LABELS: dict[str, str] = {v: k for k, v in TRANSFORMS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_transform(df: pd.DataFrame, transform: str) -> pd.Series:
    """Apply a named transform to a DataFrame with 'value' column."""
    from macro_econ.transforms.changes import (
        level_change,
        mom_annualized,
        mom_change,
        n_month_annualized,
        qoq_annualized,
        qoq_change,
        yoy_change,
    )

    col = "value"
    dispatch = {
        "level": lambda: df[col],
        "mom": lambda: mom_change(df, col),
        "mom_ann": lambda: mom_annualized(df, col),
        "qoq": lambda: qoq_change(df, col),
        "qoq_ann": lambda: qoq_annualized(df, col),
        "yoy": lambda: yoy_change(df, col, periods=12),
        "ann3": lambda: n_month_annualized(df, n=3, col=col),
        "ann6": lambda: n_month_annualized(df, n=6, col=col),
        "diff": lambda: level_change(df, col=col),
    }
    fn = dispatch.get(transform, lambda: df[col])
    return fn()


def _leaf_count(node: SeriesNode) -> int:
    """Count leaf nodes under a tree node."""
    if node.is_leaf:
        return 1
    return sum(_leaf_count(c) for c in node.children)


def _build_tree_data(
    root: SeriesNode,
) -> tuple[list[str], list[str], list[str], list[int]]:
    """Build parallel lists for a Plotly treemap from a SeriesNode tree."""
    ids: list[str] = []
    labels: list[str] = []
    parents: list[str] = []
    values: list[int] = []

    for node in root.walk():
        path = "/".join(node.path())
        ids.append(path)
        labels.append(node.name)
        if node.parent is not None:
            parents.append("/".join(node.parent.path()))
        else:
            parents.append("")
        values.append(_leaf_count(node))

    return ids, labels, parents, values


def _color_cell(val: float, abs_max: float) -> str:
    """Return CSS for a diverging blue-white-red cell color."""
    if pd.isna(val):
        return "background-color: #f5f5f5; color: #aaa"
    if abs_max == 0:
        return "background-color: #ffffff; color: #333"
    ratio = max(-1.0, min(1.0, val / abs_max))
    if ratio > 0:
        r = 255
        g = int(255 * (1 - ratio * 0.55))
        b = int(255 * (1 - ratio * 0.65))
    elif ratio < 0:
        a = abs(ratio)
        r = int(255 * (1 - a * 0.65))
        g = int(255 * (1 - a * 0.45))
        b = 255
    else:
        r, g, b = 255, 255, 255
    return f"background-color: rgb({r},{g},{b}); color: #333"


def _parse_int_list(text: str) -> list[int]:
    """Parse a comma-separated string of integers."""
    result: list[int] = []
    for tok in text.split(","):
        tok = tok.strip()
        if tok:
            try:
                result.append(int(tok))
            except ValueError:
                pass
    return result


# ---------------------------------------------------------------------------
# CSS for styled table output
# ---------------------------------------------------------------------------
_TABLE_CSS = """
<style>
.macro-viewer-table th {
    background-color: #2c3e50 !important;
    color: white !important;
    text-align: center !important;
    padding: 6px 8px !important;
    font-size: 11px !important;
    border: 1px solid #34495e !important;
    white-space: nowrap;
}
.macro-viewer-table th.row_heading {
    background-color: #34495e !important;
    color: white !important;
    text-align: left !important;
    font-weight: bold !important;
    min-width: 180px !important;
}
.macro-viewer-table td {
    text-align: center !important;
    font-size: 11px !important;
    padding: 4px 6px !important;
    border: 1px solid #eee !important;
    white-space: nowrap;
}
.macro-viewer-table {
    border-collapse: collapse !important;
    width: 100% !important;
}
</style>
"""


# ---------------------------------------------------------------------------
# MacroViewer
# ---------------------------------------------------------------------------

class MacroViewer:
    """Unified interactive viewer for economic data.

    A single consolidated interface combining hierarchy visualization,
    single-series drilldown, and multi-series heatmap comparison. Supports
    metric selection for indices that carry multiple data dimensions (e.g.,
    CES employment vs. earnings, PCE nominal vs. price index).

    Args:
        fred: FredClient instance (optional).
        bls: BlsClient instance (optional).
        bea: BeaClient instance (optional).
        start_date: Default start date for data fetching.

    Usage::

        from macro_econ.clients import FredClient
        from macro_econ.viz.viewer import MacroViewer

        viewer = MacroViewer(fred=FredClient())
        viewer.display()
    """

    def __init__(
        self,
        fred: Any | None = None,
        bls: Any | None = None,
        bea: Any | None = None,
        start_date: str = "2018-01-01",
    ):
        self._fred = fred
        self._bls = bls
        self._bea = bea
        self._default_start = start_date

        # Build all series trees (data-file-driven where available)
        self._trees: dict[str, SeriesNode] = {
            "CPI": build_cpi_tree(),
            "PCE": build_pce_tree(),
            "GDP": build_gdp_tree(),
            "CES": build_ces_tree(),
            "CPS": build_cps_tree(),
        }

        # Fetched-data cache: (index_key, node_code, metric) -> DataFrame
        self._data_cache: dict[tuple[str, str, str], pd.DataFrame] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all widget panels and wire up callbacks."""

        # ---- Top bar ----
        self._index_select = widgets.Dropdown(
            options=list(self._trees.keys()),
            value="CPI",
            description="Index:",
            style={"description_width": "auto"},
            layout=widgets.Layout(width="140px"),
        )
        self._metric_select = widgets.Dropdown(
            options=[("Default", "")],
            value="",
            description="Metric:",
            style={"description_width": "auto"},
            layout=widgets.Layout(width="250px"),
        )
        self._hierarchy_mode = widgets.Dropdown(
            options=["Treemap", "Sunburst"],
            value="Treemap",
            description="Hierarchy:",
            style={"description_width": "auto"},
            layout=widgets.Layout(width="190px"),
        )
        self._run_hierarchy_btn = widgets.Button(
            description="Show Hierarchy",
            button_style="info",
            icon="sitemap",
            layout=widgets.Layout(width="160px"),
        )
        self._top_bar = widgets.HBox(
            [
                self._index_select,
                self._metric_select,
                self._hierarchy_mode,
                self._run_hierarchy_btn,
            ],
            layout=widgets.Layout(
                justify_content="flex-start",
                padding="8px 10px",
                gap="10px",
                border="1px solid #ccc",
                margin="0 0 6px 0",
            ),
        )

        # ---- Left panel: Single Drilldown ----
        self._drilldown_series = widgets.Dropdown(
            options=[],
            description="Series:",
            style={"description_width": "50px"},
            layout=widgets.Layout(width="100%"),
        )
        self._drilldown_transform = widgets.Dropdown(
            options=TRANSFORMS,
            value="level",
            description="Type:",
            style={"description_width": "50px"},
            layout=widgets.Layout(width="100%"),
        )
        self._drilldown_start = widgets.IntText(
            value=2010,
            description="Start Yr:",
            style={"description_width": "60px"},
            layout=widgets.Layout(width="100%"),
        )
        self._drilldown_end = widgets.IntText(
            value=2026,
            description="End Yr:",
            style={"description_width": "60px"},
            layout=widgets.Layout(width="100%"),
        )
        self._drilldown_avg = widgets.Text(
            value="3, 6, 12",
            description="Avg Periods:",
            style={"description_width": "80px"},
            layout=widgets.Layout(width="100%"),
            placeholder="e.g. 3, 6, 12",
        )
        self._run_drilldown_btn = widgets.Button(
            description="Run Drilldown",
            button_style="primary",
            icon="line-chart",
            layout=widgets.Layout(width="100%"),
        )
        self._left_panel = widgets.VBox(
            [
                widgets.HTML(
                    "<div style='font-weight:bold; padding:2px 0 6px 0; "
                    "border-bottom:1px solid #ccc; margin-bottom:6px'>"
                    "Single Series Drilldown</div>"
                ),
                self._drilldown_series,
                self._drilldown_transform,
                widgets.HBox([self._drilldown_start, self._drilldown_end]),
                self._drilldown_avg,
                self._run_drilldown_btn,
            ],
            layout=widgets.Layout(
                width="28%",
                padding="8px",
                border="1px solid #ccc",
                margin="0 4px 0 0",
            ),
        )

        # ---- Middle panel: Multi-Series Select ----
        self._scenario_select = widgets.Dropdown(
            options=[],
            description="Scenario:",
            style={"description_width": "65px"},
            layout=widgets.Layout(width="100%"),
        )
        self._load_scenario_btn = widgets.Button(
            description="Load Scenario",
            button_style="",
            icon="download",
            layout=widgets.Layout(width="100%"),
        )
        self._multi_select = widgets.SelectMultiple(
            options=[],
            description="",
            layout=widgets.Layout(width="100%", height="220px"),
        )
        self._middle_panel = widgets.VBox(
            [
                widgets.HTML(
                    "<div style='font-weight:bold; padding:2px 0 6px 0; "
                    "border-bottom:1px solid #ccc; margin-bottom:6px'>"
                    "Multi-Series Select</div>"
                ),
                self._scenario_select,
                self._load_scenario_btn,
                widgets.HTML(
                    "<small style='color:#666'>Ctrl+Click for multiple</small>"
                ),
                self._multi_select,
            ],
            layout=widgets.Layout(
                width="36%",
                padding="8px",
                border="1px solid #ccc",
                margin="0 4px",
            ),
        )

        # ---- Right panel: Table Controls ----
        self._table_transform = widgets.Dropdown(
            options=TRANSFORMS,
            value="mom",
            description="Type:",
            style={"description_width": "50px"},
            layout=widgets.Layout(width="100%"),
        )
        self._table_start = widgets.DatePicker(
            description="Start:",
            value=date(2022, 1, 1),
            style={"description_width": "50px"},
            layout=widgets.Layout(width="100%"),
        )
        self._table_end = widgets.DatePicker(
            description="End:",
            value=date.today(),
            style={"description_width": "50px"},
            layout=widgets.Layout(width="100%"),
        )
        self._table_avg_periods = widgets.Text(
            value="3, 6, 12",
            description="Averages:",
            style={"description_width": "65px"},
            layout=widgets.Layout(width="100%"),
            placeholder="e.g. 3, 6, 12",
        )
        self._table_max_cols = widgets.IntSlider(
            value=18,
            min=6,
            max=36,
            step=1,
            description="Columns:",
            style={"description_width": "65px"},
            layout=widgets.Layout(width="100%"),
        )
        self._run_table_btn = widgets.Button(
            description="Run Table",
            button_style="primary",
            icon="table",
            layout=widgets.Layout(width="100%"),
        )
        self._right_panel = widgets.VBox(
            [
                widgets.HTML(
                    "<div style='font-weight:bold; padding:2px 0 6px 0; "
                    "border-bottom:1px solid #ccc; margin-bottom:6px'>"
                    "Table Controls</div>"
                ),
                self._table_transform,
                self._table_start,
                self._table_end,
                self._table_avg_periods,
                self._table_max_cols,
                self._run_table_btn,
            ],
            layout=widgets.Layout(
                width="36%",
                padding="8px",
                border="1px solid #ccc",
                margin="0 0 0 4px",
            ),
        )

        # ---- Controls row ----
        self._controls_row = widgets.HBox(
            [self._left_panel, self._middle_panel, self._right_panel],
            layout=widgets.Layout(margin="0 0 6px 0"),
        )

        # ---- Output tabs ----
        self._out_drilldown = widgets.Output()
        self._out_table = widgets.Output()
        self._out_hierarchy = widgets.Output()
        self._tabs = widgets.Tab(
            children=[self._out_drilldown, self._out_table, self._out_hierarchy],
        )
        self._tabs.set_title(0, "Single Drilldown")
        self._tabs.set_title(1, "Multi-Series Table")
        self._tabs.set_title(2, "Index Hierarchy")

        # ---- Main container ----
        self._container = widgets.VBox(
            [self._top_bar, self._controls_row, self._tabs],
            layout=widgets.Layout(width="100%"),
        )

        # ---- Wire callbacks ----
        self._index_select.observe(self._on_index_change, names="value")
        self._run_hierarchy_btn.on_click(self._on_run_hierarchy)
        self._load_scenario_btn.on_click(self._on_load_scenario)
        self._run_drilldown_btn.on_click(self._on_run_drilldown)
        self._run_table_btn.on_click(self._on_run_table)

        # Initialise dropdown options for the default index
        self._on_index_change(None)

    # ------------------------------------------------------------------
    # Reactive callbacks
    # ------------------------------------------------------------------

    def _on_index_change(self, _change: Any) -> None:
        """Refresh panel options when the selected index changes."""
        idx = self._index_select.value
        tree = self._trees[idx]

        # Update metric dropdown
        metric_opts = METRIC_OPTIONS.get(idx, {})
        if metric_opts:
            self._metric_select.options = [("Default", "")] + [
                (label, code) for code, label in metric_opts.items()
            ]
            self._metric_select.value = ""
            self._metric_select.layout.display = ""
        else:
            self._metric_select.options = [("Default", "")]
            self._metric_select.value = ""
            self._metric_select.layout.display = "none"

        # Drilldown: all nodes that have at least one data source
        options = [
            (f"{n.name} [{n.code}]", n.code)
            for n in tree.walk()
            if n.sources
        ]
        self._drilldown_series.options = options
        if options:
            self._drilldown_series.value = options[0][1]

        # Multi-select: branch nodes with sources first, then leaves
        branch_opts = [
            (f"\u25b6 {n.name} [{n.code}]", n.code)
            for n in tree.walk()
            if not n.is_leaf and n.sources
        ]
        leaf_opts = [
            (f"  {n.name} [{n.code}]", n.code)
            for n in tree.leaves()
        ]
        self._multi_select.options = branch_opts + leaf_opts

        # Scenarios
        scenarios = SCENARIOS.get(idx, {})
        self._scenario_select.options = list(scenarios.keys()) or ["(none)"]

    def _on_load_scenario(self, _btn: Any) -> None:
        """Pre-select series codes from a chosen scenario."""
        idx = self._index_select.value
        scenario_name = self._scenario_select.value
        codes = SCENARIOS.get(idx, {}).get(scenario_name, [])
        if not codes:
            return
        available = {v for _, v in self._multi_select.options}
        self._multi_select.value = tuple(c for c in codes if c in available)

    # ---- Hierarchy ----

    def _on_run_hierarchy(self, _btn: Any) -> None:
        """Render a treemap or sunburst of the selected hierarchy."""
        idx = self._index_select.value
        tree = self._trees[idx]
        mode = self._hierarchy_mode.value
        ids, labels, parents, values = _build_tree_data(tree)

        with self._out_hierarchy:
            clear_output(wait=True)
            if mode == "Treemap":
                trace = go.Treemap(
                    ids=ids,
                    labels=labels,
                    parents=parents,
                    values=values,
                    branchvalues="total",
                    textinfo="label",
                    hovertemplate="<b>%{label}</b><extra></extra>",
                    marker=dict(
                        colorscale="Blues",
                        line=dict(width=1, color="white"),
                    ),
                )
            else:
                trace = go.Sunburst(
                    ids=ids,
                    labels=labels,
                    parents=parents,
                    values=values,
                    branchvalues="total",
                    hovertemplate="<b>%{label}</b><extra></extra>",
                )

            fig = go.Figure(trace)
            fig.update_layout(
                title=f"{tree.name} — {mode} Hierarchy",
                height=650,
                margin=dict(l=10, r=10, t=50, b=10),
            )
            fig.show()

        self._tabs.selected_index = 2

    # ---- Data fetching ----

    def _get_metric_source(self, node: SeriesNode, metric: str) -> Any | None:
        """Find the best source for a node given the selected metric.

        When a metric is specified, prefer sources tagged with that metric.
        Falls back to any available source when no metric match is found.
        """
        if metric:
            for src in node.sources:
                if src.extra.get("metric") == metric:
                    return src
        # Fall back: prefer FRED, then any source
        for src in node.sources:
            if src.source == "fred":
                return src
        return node.sources[0] if node.sources else None

    def _fetch_node_data(
        self,
        code: str,
        start_date: str | None = None,
        end_date: str | None = None,
        metric: str = "",
    ) -> pd.DataFrame | None:
        """Fetch data for a node, respecting the selected metric.

        Uses metric-tagged sources when available, falling back to the
        FRED -> BLS -> BEA priority chain.
        """
        idx = self._index_select.value
        tree = self._trees[idx]
        node = tree.find(code)
        if node is None:
            return None

        cache_key = (idx, code, metric)
        if cache_key in self._data_cache:
            df = self._data_cache[cache_key].copy()
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            return df

        # Get the best source for the requested metric
        src = self._get_metric_source(node, metric)
        if src is None:
            return None

        # Try the matched source first
        df = self._try_fetch(src, start_date, end_date)
        if df is not None:
            self._data_cache[cache_key] = df
            return df

        # Fallback: try all sources in priority order
        attempts: list[tuple[str, Any]] = [
            ("fred", self._fred),
            ("bls", self._bls),
            ("bea", self._bea),
        ]
        for source_name, client in attempts:
            if client is None:
                continue
            for s in node.sources:
                if s.source != source_name:
                    continue
                if metric and s.extra.get("metric") and s.extra["metric"] != metric:
                    continue
                df = self._try_fetch_with_client(client, s, start_date, end_date)
                if df is not None:
                    self._data_cache[cache_key] = df
                    return df

        return None

    def _try_fetch(
        self,
        src: Any,
        start_date: str | None,
        end_date: str | None,
    ) -> pd.DataFrame | None:
        """Try fetching from the appropriate client for a source."""
        client_map = {
            "fred": self._fred,
            "bls": self._bls,
            "bea": self._bea,
        }
        client = client_map.get(src.source)
        if client is None:
            return None
        return self._try_fetch_with_client(client, src, start_date, end_date)

    def _try_fetch_with_client(
        self,
        client: Any,
        src: Any,
        start_date: str | None,
        end_date: str | None,
    ) -> pd.DataFrame | None:
        """Execute a fetch against a specific client and source."""
        try:
            if src.source == "bea":
                return client.fetch_series(
                    src.series_id,
                    start_date,
                    end_date,
                    table=src.extra.get("table"),
                    line_number=src.extra.get("line_number"),
                    frequency=src.extra.get("frequency", "M"),
                )
            else:
                return client.fetch_series(src.series_id, start_date, end_date)
        except Exception:
            return None

    # ---- Single Drilldown ----

    def _on_run_drilldown(self, _btn: Any) -> None:
        """Render a line chart for a single series with optional MAs."""
        code = self._drilldown_series.value
        transform = self._drilldown_transform.value
        start_yr = self._drilldown_start.value
        end_yr = self._drilldown_end.value
        avg_periods = _parse_int_list(self._drilldown_avg.value)
        metric = self._metric_select.value

        start_date = f"{start_yr}-01-01"
        end_date = f"{end_yr}-12-31"
        fetch_start = f"{start_yr - 2}-01-01"

        with self._out_drilldown:
            clear_output(wait=True)

            df = self._fetch_node_data(code, fetch_start, end_date, metric=metric)
            if df is None or df.empty:
                print(f"No data for {code}. Check API client configuration.")
                return

            idx = self._index_select.value
            node = self._trees[idx].find(code)
            name = node.name if node else code
            transform_label = _TRANSFORM_LABELS.get(transform, transform)

            # Add metric label to title when relevant
            metric_labels = METRIC_OPTIONS.get(idx, {})
            metric_suffix = f" ({metric_labels[metric]})" if metric and metric in metric_labels else ""

            series = _apply_transform(df, transform)
            series = series[series.index >= pd.Timestamp(start_date)]

            # Line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=series.index,
                y=series.values,
                name=name,
                mode="lines",
                line=dict(color="#1f77b4", width=2),
            ))

            ma_colors = ["#ff7f0e", "#2ca02c", "#d62728"]
            for i, n in enumerate(avg_periods[:3]):
                ma = series.rolling(window=n, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=ma.index,
                    y=ma.values,
                    name=f"{n}-period MA",
                    mode="lines",
                    line=dict(color=ma_colors[i % 3], dash="dash"),
                ))

            fig.update_layout(
                title=f"{name}{metric_suffix} — {transform_label}",
                yaxis_title=transform_label,
                height=450,
                **DEFAULT_LAYOUT,
            )
            fig.show()

            # Recent values table
            recent = series.dropna().tail(24).to_frame(name=name).round(2)
            display(HTML(f"<h4>Last {len(recent)} Observations ({transform_label})</h4>"))
            styled = (
                recent
                .style
                .format("{:.2f}")
                .set_properties(**{
                    "text-align": "center",
                    "font-size": "12px",
                    "padding": "3px 8px",
                })
            )
            display(styled)

        self._tabs.selected_index = 0

    # ---- Multi-Series Table ----

    def _on_run_table(self, _btn: Any) -> None:
        """Build a color-coded comparison heatmap table for selected series."""
        selected_codes = list(self._multi_select.value)
        transform = self._table_transform.value
        start_dt = self._table_start.value
        end_dt = self._table_end.value
        avg_periods = _parse_int_list(self._table_avg_periods.value)
        max_cols = self._table_max_cols.value
        metric = self._metric_select.value

        if not selected_codes:
            with self._out_table:
                clear_output(wait=True)
                print("Select at least one series in the multi-select list.")
            return

        start_date = start_dt.isoformat() if start_dt else self._default_start
        end_date = end_dt.isoformat() if end_dt else None
        transform_label = _TRANSFORM_LABELS.get(transform, transform)

        with self._out_table:
            clear_output(wait=True)
            print(f"Fetching {len(selected_codes)} series ...")

            idx = self._index_select.value
            tree = self._trees[idx]
            metric_labels = METRIC_OPTIONS.get(idx, {})
            metric_suffix = f" ({metric_labels[metric]})" if metric and metric in metric_labels else ""

            all_series: dict[str, pd.Series] = {}
            for code in selected_codes:
                node = tree.find(code)
                label = node.name if node else code
                fetch_start = (
                    f"{int(start_date[:4]) - 2}-01-01" if start_date else None
                )
                df = self._fetch_node_data(code, fetch_start, end_date, metric=metric)
                if df is not None and not df.empty:
                    s = _apply_transform(df, transform)
                    if start_date:
                        s = s[s.index >= pd.Timestamp(start_date)]
                    if end_date:
                        s = s[s.index <= pd.Timestamp(end_date)]
                    all_series[label] = s

            if not all_series:
                clear_output(wait=True)
                print(
                    "No data fetched. Ensure at least one API client is "
                    "configured (fred=, bls=, bea=)."
                )
                return

            # Build rows=series, cols=dates DataFrame
            combined = pd.DataFrame(all_series).T
            combined.columns = pd.to_datetime(combined.columns)
            combined = combined.sort_index(axis=1)

            # Trim to last N columns
            if combined.shape[1] > max_cols:
                combined = combined.iloc[:, -max_cols:]

            # Format column headers
            combined.columns = [c.strftime("%b %Y") for c in combined.columns]

            # Prepend average columns
            for n in sorted(avg_periods, reverse=True):
                if combined.shape[1] >= n:
                    combined.insert(
                        0,
                        f"{n}mo\nAvg",
                        combined.iloc[:, -min(n, combined.shape[1]):].mean(axis=1),
                    )

            clear_output(wait=True)
            display(HTML(_TABLE_CSS))
            display(HTML(
                f"<h3 style='margin:0 0 8px 0'>"
                f"{idx}{metric_suffix} — Multi-Series Comparison ({transform_label})</h3>"
            ))

            # Color-code numeric cells
            numeric_vals = combined.select_dtypes(include=[np.number])
            if numeric_vals.empty:
                display(combined.round(2))
            else:
                vmin = numeric_vals.min().min()
                vmax = numeric_vals.max().max()
                abs_max = (
                    max(abs(vmin), abs(vmax))
                    if pd.notna(vmin) and pd.notna(vmax)
                    else 1.0
                )

                styled = (
                    combined
                    .round(2)
                    .style
                    .map(lambda v: _color_cell(v, abs_max))
                    .format("{:.2f}", na_rep="—")
                    .set_table_attributes('class="macro-viewer-table"')
                )
                display(styled)

            # Plotly heatmap
            display(HTML("<h4 style='margin:12px 0 4px 0'>Heatmap View</h4>"))
            fig = go.Figure(data=go.Heatmap(
                z=combined.values,
                x=list(combined.columns),
                y=list(combined.index),
                colorscale="RdBu_r",
                zmid=0,
                text=combined.round(1).values,
                texttemplate="%{text}",
                hoverongaps=False,
            ))
            fig.update_layout(
                title=f"{idx}{metric_suffix} — {transform_label}",
                height=max(300, len(combined) * 40),
                margin=dict(l=220, r=30, t=60, b=40),
                yaxis=dict(autorange="reversed"),
            )
            fig.show()

        self._tabs.selected_index = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display(self) -> None:
        """Display the viewer in the current notebook cell."""
        display(self._container)
