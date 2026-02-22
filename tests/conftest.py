"""Shared test fixtures."""

import pytest

from macro_econ.series.node import SeriesNode, SeriesSource


@pytest.fixture
def sample_tree() -> SeriesNode:
    """Build a sample hierarchy for testing."""
    return SeriesNode(
        name="Root",
        code="ROOT",
        sources=[SeriesSource("fred", "ROOT_SERIES")],
        children=[
            SeriesNode(
                name="Branch A",
                code="A",
                sources=[
                    SeriesSource("fred", "A_FRED"),
                    SeriesSource("bea", "T10105", {"table": "T10105", "line_number": 1}),
                ],
                children=[
                    SeriesNode(
                        name="Leaf A1",
                        code="A1",
                        sources=[SeriesSource("fred", "A1_FRED")],
                    ),
                    SeriesNode(
                        name="Leaf A2",
                        code="A2",
                        sources=[SeriesSource("bls", "CES0000000001")],
                    ),
                ],
            ),
            SeriesNode(
                name="Branch B",
                code="B",
                children=[
                    SeriesNode(
                        name="Sub-branch B1",
                        code="B1",
                        children=[
                            SeriesNode(
                                name="Leaf B1a",
                                code="B1a",
                                sources=[SeriesSource("fred", "B1a_FRED")],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
