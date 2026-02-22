"""Interactive ipywidgets for Jupyter notebook series selection."""

from __future__ import annotations

from typing import Callable

import ipywidgets as widgets

from macro_econ.series.node import SeriesNode


def build_tree_widget(
    root: SeriesNode,
    on_select: Callable[[SeriesNode], None] | None = None,
    max_depth: int = 4,
) -> widgets.Widget:
    """Build a nested Accordion widget from a SeriesNode tree.

    Args:
        root: Root of the hierarchy tree.
        on_select: Callback when a leaf node is clicked.
        max_depth: Maximum depth to expand (deeper nodes shown as buttons).
    """
    def _build_node(node: SeriesNode, depth: int = 0) -> widgets.Widget:
        if node.is_leaf or depth >= max_depth:
            btn = widgets.Button(
                description=node.name[:40],
                tooltip=f"{node.name} [{node.code}]",
                layout=widgets.Layout(width="auto"),
            )
            if on_select:
                btn.on_click(lambda _b, n=node: on_select(n))
            return btn

        children_widgets = [_build_node(child, depth + 1) for child in node.children]
        accordion = widgets.Accordion(children=children_widgets)
        for i, child in enumerate(node.children):
            accordion.set_title(i, f"{child.name} [{child.code}]")
        accordion.selected_index = None
        return accordion

    return _build_node(root)


def series_selector(
    nodes: list[SeriesNode],
) -> widgets.SelectMultiple:
    """Multi-select widget for choosing series to compare."""
    options = [(f"{n.name} [{n.code}]", n.code) for n in nodes]
    return widgets.SelectMultiple(
        options=options,
        description="Series:",
        layout=widgets.Layout(width="100%", height="200px"),
    )


def transform_selector() -> widgets.Dropdown:
    """Dropdown for selecting data transformation."""
    return widgets.Dropdown(
        options=[
            ("Level", "level"),
            ("MoM %", "mom"),
            ("MoM Annualized %", "mom_ann"),
            ("QoQ Annualized %", "qoq_ann"),
            ("YoY %", "yoy"),
            ("3m MA", "ma3"),
            ("6m MA", "ma6"),
            ("12m MA", "ma12"),
            ("3m Annualized %", "ann3"),
            ("6m Annualized %", "ann6"),
        ],
        value="level",
        description="Transform:",
    )


def date_range_picker(
    start: str = "2000-01-01",
    end: str = "2026-12-31",
) -> widgets.HBox:
    """Two date picker widgets in an HBox."""
    start_picker = widgets.DatePicker(
        description="Start:",
        value=None,
    )
    end_picker = widgets.DatePicker(
        description="End:",
        value=None,
    )
    return widgets.HBox([start_picker, end_picker])
