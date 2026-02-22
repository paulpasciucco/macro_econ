"""Color palettes, layout defaults, and recession date constants."""

from __future__ import annotations

# Consistent color palette for economic categories
COLORS = {
    # GDP components
    "PCE": "#1f77b4",
    "Investment": "#ff7f0e",
    "Government": "#2ca02c",
    "Net Exports": "#d62728",
    # CPI categories
    "Food": "#8c564b",
    "Housing": "#e377c2",
    "Apparel": "#7f7f7f",
    "Transportation": "#bcbd22",
    "Medical": "#17becf",
    "Recreation": "#9467bd",
    "Education": "#aec7e8",
    "Other": "#c7c7c7",
    # Employment
    "Goods-Producing": "#ff9896",
    "Service-Providing": "#98df8a",
    "Government (Emp)": "#c5b0d5",
    # General
    "Headline": "#1f77b4",
    "Core": "#ff7f0e",
    "SA": "#1f77b4",
    "NSA": "#ff7f0e",
}

# Default Plotly layout configuration
DEFAULT_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "Arial, sans-serif", "size": 12},
    "margin": {"l": 60, "r": 30, "t": 60, "b": 40},
    "hovermode": "x unified",
    "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
}

# NBER recession dates (start, end) as YYYY-MM-DD strings
# Source: https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
RECESSION_DATES = [
    ("1948-11-01", "1949-10-01"),
    ("1953-07-01", "1954-05-01"),
    ("1957-08-01", "1958-04-01"),
    ("1960-04-01", "1961-02-01"),
    ("1969-12-01", "1970-11-01"),
    ("1973-11-01", "1975-03-01"),
    ("1980-01-01", "1980-07-01"),
    ("1981-07-01", "1982-11-01"),
    ("1990-07-01", "1991-03-01"),
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01"),
]


def format_date_axis(fig: object, freq: str = "M") -> None:
    """Configure x-axis tick format based on data frequency.

    Args:
        fig: Plotly figure object.
        freq: "M" (monthly), "Q" (quarterly), "A" (annual).
    """
    formats = {"M": "%b %Y", "Q": "Q%q %Y", "A": "%Y"}
    fig.update_xaxes(tickformat=formats.get(freq, "%b %Y"))  # type: ignore[union-attr]
