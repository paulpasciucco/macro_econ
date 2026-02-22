"""Plotly chart builders for economic data visualization."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from macro_econ.viz.styles import DEFAULT_LAYOUT, RECESSION_DATES


def line_chart(
    data: dict[str, pd.DataFrame | pd.Series],
    title: str,
    col: str = "value",
    yaxis_title: str = "",
) -> go.Figure:
    """Multi-series line chart.

    Args:
        data: Dict mapping display labels to DataFrames (with 'value' col) or Series.
        title: Chart title.
        col: Column name to plot from DataFrames.
    """
    fig = go.Figure()
    for label, series_data in data.items():
        if isinstance(series_data, pd.DataFrame):
            y = series_data[col] if col in series_data.columns else series_data.iloc[:, 0]
            x = series_data.index
        else:
            y = series_data
            x = series_data.index
        fig.add_trace(go.Scatter(x=x, y=y, name=label, mode="lines"))

    fig.update_layout(title=title, yaxis_title=yaxis_title, **DEFAULT_LAYOUT)
    return fig


def bar_chart(
    data: dict[str, pd.Series],
    title: str,
    yaxis_title: str = "",
) -> go.Figure:
    """Bar chart for level changes (e.g., monthly payroll changes)."""
    fig = go.Figure()
    for label, series in data.items():
        fig.add_trace(go.Bar(x=series.index, y=series.values, name=label))

    fig.update_layout(title=title, yaxis_title=yaxis_title, barmode="group", **DEFAULT_LAYOUT)
    return fig


def stacked_bar_contributions(
    data: dict[str, pd.Series],
    title: str,
    yaxis_title: str = "Percentage points",
) -> go.Figure:
    """Stacked bar chart for GDP/CPI component contributions."""
    fig = go.Figure()
    for label, series in data.items():
        fig.add_trace(go.Bar(x=series.index, y=series.values, name=label))

    fig.update_layout(title=title, yaxis_title=yaxis_title, barmode="relative", **DEFAULT_LAYOUT)
    return fig


def acf_pacf_plot(
    acf_vals: list | object,
    pacf_vals: list | object,
    title: str = "ACF and PACF",
) -> go.Figure:
    """Side-by-side ACF and PACF bar charts."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=["ACF", "PACF"])

    n_acf = len(acf_vals)
    n_pacf = len(pacf_vals)

    fig.add_trace(
        go.Bar(x=list(range(n_acf)), y=list(acf_vals), name="ACF", showlegend=False),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=list(range(n_pacf)), y=list(pacf_vals), name="PACF", showlegend=False),
        row=1, col=2,
    )

    fig.update_layout(title=title, **DEFAULT_LAYOUT)
    return fig


def stl_plot(stl_result: object, title: str = "STL Decomposition") -> go.Figure:
    """Four-panel STL decomposition plot (observed, trend, seasonal, residual)."""
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        subplot_titles=["Observed", "Trend", "Seasonal", "Residual"],
        vertical_spacing=0.05,
    )

    x = stl_result.observed.index  # type: ignore[union-attr]

    fig.add_trace(
        go.Scatter(x=x, y=stl_result.observed, name="Observed", showlegend=False),  # type: ignore[union-attr]
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=stl_result.trend, name="Trend", showlegend=False),  # type: ignore[union-attr]
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=stl_result.seasonal, name="Seasonal", showlegend=False),  # type: ignore[union-attr]
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=stl_result.resid, name="Residual", showlegend=False),  # type: ignore[union-attr]
        row=4, col=1,
    )

    fig.update_layout(title=title, height=800, **DEFAULT_LAYOUT)
    return fig


def heatmap_table(
    df: pd.DataFrame,
    title: str = "",
    colorscale: str = "RdBu_r",
) -> go.Figure:
    """Color-coded heatmap table (useful for CPI components over time)."""
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=[str(c) for c in df.columns],
        y=list(df.index),
        colorscale=colorscale,
        text=df.values.round(1),
        texttemplate="%{text}",
        hoverongaps=False,
    ))
    fig.update_layout(title=title, height=max(300, len(df) * 30), **DEFAULT_LAYOUT)
    return fig


def recession_shading(fig: go.Figure, opacity: float = 0.1) -> go.Figure:
    """Add NBER recession shading bands to a figure."""
    for start, end in RECESSION_DATES:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="gray", opacity=opacity,
            layer="below", line_width=0,
        )
    return fig
