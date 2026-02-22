"""Interactive cross-series viewer for economic data analysis.

Provides a comprehensive widget-based interface for exploring all series
hierarchies (CPI, PCE, GDP, CES, CPS) with:
- Hierarchy visualization (Treemap / Sunburst)
- Single-series drilldown with transforms and date range
- Multi-series heatmap comparison table
- Pre-computed scenario selections
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
from macro_econ.series.node import SeriesNode
from macro_econ.series.pce import build_pce_tree
from macro_econ.viz.styles import DEFAULT_LAYOUT

# ---------------------------------------------------------------------------
# Pre-defined scenario tables for common multi-series analyses
# ---------------------------------------------------------------------------
SCENARIOS: dict[str, dict[str, list[str]]] = {
    "CPI": {
        "Core vs Headline": ["CPI", "CPI_CORE", "CPI_SUPERCORE"],
        "Shelter Components": [
            "CPI_SHELTER", "CPI_OER", "CPI_RENT", "CPI_LODGING",
        ],
        "Food": [
            "CPI_FOOD", "CPI_FOOD_HOME", "CPI_FOOD_AWAY", "CPI_ALCOHOL",
        ],
        "Energy": [
            "CPI_ENERGY", "CPI_MOTOR_FUEL", "CPI_HOUSEHOLD_ENERGY",
            "CPI_ELEC", "CPI_GAS_UTIL",
        ],
        "Transportation": [
            "CPI_TRANSPORT", "CPI_NEW_VEH", "CPI_USED_VEH",
            "CPI_MOTOR_FUEL", "CPI_VEH_INS", "CPI_AIRLINE",
        ],
        "Medical": [
            "CPI_MEDICAL", "CPI_MED_COMM", "CPI_MED_SVC", "CPI_HEALTH_INS",
        ],
        "Major Groups": [
            "CPI_FOOD_BEV", "CPI_HOUSING", "CPI_APPAREL", "CPI_TRANSPORT",
            "CPI_MEDICAL", "CPI_REC", "CPI_EDU_COMM", "CPI_OTHER",
        ],
    },
    "PCE": {
        "Headline vs Core": ["PCE_PI", "PCE_PI_CORE"],
        "Goods vs Services": ["PCE_GOODS", "PCE_SVC"],
        "Durable vs Nondurable": ["PCE_DUR", "PCE_NONDUR"],
        "Services Detail": [
            "PCE_SVC_HOUSING", "PCE_SVC_HEALTH", "PCE_SVC_TRANS",
            "PCE_SVC_REC", "PCE_SVC_FOOD", "PCE_SVC_FIN",
        ],
        "Price Indexes": [
            "PCE_PI", "PCE_PI_CORE", "PCE_PI_GOODS",
            "PCE_PI_DUR", "PCE_PI_NONDUR", "PCE_PI_SVC",
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
        "Major Sectors": ["NFP_GOODS", "NFP_SVC", "NFP_GOVT"],
        "Goods Producing": ["NFP_MINING", "NFP_CONSTR", "NFP_MFG"],
        "Service Providing": [
            "NFP_TTU", "NFP_INFO", "NFP_FIN", "NFP_PBS",
            "NFP_EDHEALTH", "NFP_LEISURE", "NFP_OTH_SVC",
        ],
        "Manufacturing": ["NFP_MFG_DUR", "NFP_MFG_NONDUR"],
        "Earnings & Hours": ["AHE", "AWH", "AHE_PROD", "AWH_PROD"],
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
    """Interactive cross-series viewer for economic data.

    Provides a three-panel control interface with hierarchy visualization,
    single-series drilldown, and multi-series heatmap comparison — all
    rendered in a Jupyter notebook via ipywidgets and Plotly.

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

        # Build all series trees
        self._trees: dict[str, SeriesNode] = {
            "CPI": build_cpi_tree(),
            "PCE": build_pce_tree(),
            "GDP": build_gdp_tree(),
            "CES": build_ces_tree(),
            "CPS": build_cps_tree(),
        }

        # Fetched-data cache: (index_key, node_code) -> DataFrame
        self._data_cache: dict[tuple[str, str], pd.DataFrame] = {}

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
            layout=widgets.Layout(width="160px"),
        )
        self._hierarchy_mode = widgets.Dropdown(
            options=["Treemap", "Sunburst"],
            value="Treemap",
            description="Hierarchy:",
            style={"description_width": "auto"},
            layout=widgets.Layout(width="200px"),
        )
        self._run_hierarchy_btn = widgets.Button(
            description="Show Hierarchy",
            button_style="info",
            icon="sitemap",
            layout=widgets.Layout(width="170px"),
        )
        self._top_bar = widgets.HBox(
            [self._index_select, self._hierarchy_mode, self._run_hierarchy_btn],
            layout=widgets.Layout(
                justify_content="flex-start",
                padding="8px 10px",
                gap="12px",
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
                    "Specific Index Drilldown</div>"
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

        # ---- Middle panel: Multi-Index Table Select ----
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
                    "Multi-Index Table Select</div>"
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

        # ---- Right panel: Controls for Table ----
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
                    "Controls for Table</div>"
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
        self._tabs.set_title(1, "Multi Select Table")
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

    def _fetch_node_data(
        self,
        code: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame | None:
        """Fetch data for a node, trying FRED -> BLS -> BEA in order."""
        idx = self._index_select.value
        tree = self._trees[idx]
        node = tree.find(code)
        if node is None:
            return None

        cache_key = (idx, code)
        if cache_key in self._data_cache:
            df = self._data_cache[cache_key].copy()
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]
            return df

        # Try sources in priority order
        attempts: list[tuple[str, Any]] = [
            ("fred", self._fred),
            ("bls", self._bls),
            ("bea", self._bea),
        ]
        for source_name, client in attempts:
            if client is None:
                continue
            src = node.get_source(source_name)
            if src is None:
                continue
            try:
                if source_name == "bea":
                    df = client.fetch_series(
                        src.series_id,
                        start_date,
                        end_date,
                        table=src.extra.get("table"),
                        line_number=src.extra.get("line_number"),
                        frequency=src.extra.get("frequency", "M"),
                    )
                else:
                    df = client.fetch_series(
                        src.series_id, start_date, end_date,
                    )
                self._data_cache[cache_key] = df
                return df
            except Exception:
                continue

        return None

    # ---- Single Drilldown ----

    def _on_run_drilldown(self, _btn: Any) -> None:
        """Render a line chart for a single series with optional MAs."""
        code = self._drilldown_series.value
        transform = self._drilldown_transform.value
        start_yr = self._drilldown_start.value
        end_yr = self._drilldown_end.value
        avg_periods = _parse_int_list(self._drilldown_avg.value)

        start_date = f"{start_yr}-01-01"
        end_date = f"{end_yr}-12-31"
        # Fetch extra history for transforms that look back
        fetch_start = f"{start_yr - 2}-01-01"

        with self._out_drilldown:
            clear_output(wait=True)

            df = self._fetch_node_data(code, fetch_start, end_date)
            if df is None or df.empty:
                print(f"No data for {code}. Check API client configuration.")
                return

            idx = self._index_select.value
            node = self._trees[idx].find(code)
            name = node.name if node else code
            transform_label = _TRANSFORM_LABELS.get(transform, transform)

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
                title=f"{name} — {transform_label}",
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

    # ---- Multi Select Table ----

    def _on_run_table(self, _btn: Any) -> None:
        """Build a color-coded comparison heatmap table for selected series."""
        selected_codes = list(self._multi_select.value)
        transform = self._table_transform.value
        start_dt = self._table_start.value
        end_dt = self._table_end.value
        avg_periods = _parse_int_list(self._table_avg_periods.value)
        max_cols = self._table_max_cols.value

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

            all_series: dict[str, pd.Series] = {}
            for code in selected_codes:
                node = tree.find(code)
                label = node.name if node else code
                # Fetch extra history so transforms have data
                fetch_start = (
                    f"{int(start_date[:4]) - 2}-01-01" if start_date else None
                )
                df = self._fetch_node_data(code, fetch_start, end_date)
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
                f"{idx} — Multi-Series Comparison ({transform_label})</h3>"
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
                title=f"{idx} — {transform_label}",
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
