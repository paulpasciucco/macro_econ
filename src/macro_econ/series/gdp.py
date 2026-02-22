"""GDP hierarchy tree.

Sources:
    - BEA NIPA Tables 1.1.x (GDP and its components)
    - FRED series for headline and major components
    - Cross-references PCE hierarchy from pce.py
"""

from macro_econ.series.node import SeriesNode, SeriesSource
from macro_econ.series.pce import build_pce_tree


def _fred(series_id: str) -> SeriesSource:
    return SeriesSource("fred", series_id)


def _bea(table: str, line: int, freq: str = "Q") -> SeriesSource:
    return SeriesSource("bea", table, {"table": table, "frequency": freq, "line_number": line})


def build_gdp_tree(include_pce_detail: bool = False) -> SeriesNode:
    """Build the full GDP hierarchy tree.

    Structure follows BEA NIPA Table 1.1.5 / 1.1.6 (GDP).

    Args:
        include_pce_detail: If True, attach the full PCE sub-tree under the
            Consumption node. If False, use a collapsed PCE node.
    """
    if include_pce_detail:
        pce_node = build_pce_tree()
    else:
        pce_node = SeriesNode(
            name="Personal Consumption Expenditures",
            code="GDP_C",
            sources=[_fred("PCE"), _fred("PCEC96"), _bea("T10105", 2)],
            children=[
                SeriesNode(
                    name="Goods",
                    code="GDP_C_GOODS",
                    sources=[_fred("DGDSRC1M027NBEA")],
                    children=[
                        SeriesNode(name="Durable Goods", code="GDP_C_DUR",
                                   sources=[_fred("PCDG")]),
                        SeriesNode(name="Nondurable Goods", code="GDP_C_NONDUR",
                                   sources=[_fred("PCND")]),
                    ],
                ),
                SeriesNode(
                    name="Services",
                    code="GDP_C_SVC",
                    sources=[_fred("PCES")],
                ),
            ],
        )

    return SeriesNode(
        name="Gross Domestic Product",
        code="GDP",
        sources=[_fred("GDP"), _fred("GDPC1"), _bea("T10105", 1)],
        description="GDP current dollars (GDP) and chained 2017$ (GDPC1)",
        children=[
            pce_node,
            # Investment
            SeriesNode(
                name="Gross Private Domestic Investment",
                code="GDP_I",
                sources=[_fred("GPDI"), _bea("T10105", 7)],
                children=[
                    SeriesNode(
                        name="Fixed Investment",
                        code="GDP_I_FIXED",
                        sources=[_fred("FPI"), _bea("T10105", 8)],
                        children=[
                            SeriesNode(
                                name="Nonresidential",
                                code="GDP_I_NONRES",
                                sources=[_fred("PNFI"), _bea("T10105", 9)],
                                children=[
                                    SeriesNode(
                                        name="Structures",
                                        code="GDP_I_STRUCT",
                                        sources=[_fred("B009RC1Q027SBEA"),
                                                 _bea("T10105", 10)],
                                    ),
                                    SeriesNode(
                                        name="Equipment",
                                        code="GDP_I_EQUIP",
                                        sources=[_fred("Y033RC1Q027SBEA"),
                                                 _bea("T10105", 11)],
                                    ),
                                    SeriesNode(
                                        name="Intellectual Property Products",
                                        code="GDP_I_IP",
                                        sources=[_fred("Y001RC1Q027SBEA"),
                                                 _bea("T10105", 12)],
                                    ),
                                ],
                            ),
                            SeriesNode(
                                name="Residential",
                                code="GDP_I_RES",
                                sources=[_fred("PRFI"), _bea("T10105", 13)],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="Change in Private Inventories",
                        code="GDP_I_INV",
                        sources=[_fred("CBI"), _bea("T10105", 14)],
                    ),
                ],
            ),
            # Net Exports
            SeriesNode(
                name="Net Exports of Goods and Services",
                code="GDP_NX",
                sources=[_fred("NETEXP"), _bea("T10105", 15)],
                children=[
                    SeriesNode(
                        name="Exports",
                        code="GDP_X",
                        sources=[_fred("EXPGS"), _bea("T10105", 16)],
                        children=[
                            SeriesNode(
                                name="Goods",
                                code="GDP_X_GOODS",
                                sources=[_fred("EXPGSC1")],
                            ),
                            SeriesNode(
                                name="Services",
                                code="GDP_X_SVC",
                                sources=[_fred("EXPGSSC1")],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="Imports",
                        code="GDP_M",
                        sources=[_fred("IMPGS"), _bea("T10105", 19)],
                        children=[
                            SeriesNode(
                                name="Goods",
                                code="GDP_M_GOODS",
                                sources=[_fred("IMPGSC1")],
                            ),
                            SeriesNode(
                                name="Services",
                                code="GDP_M_SVC",
                                sources=[_fred("IMPGSSC1")],
                            ),
                        ],
                    ),
                ],
            ),
            # Government
            SeriesNode(
                name="Government Consumption Expenditures and Gross Investment",
                code="GDP_G",
                sources=[_fred("GCE"), _bea("T10105", 22)],
                children=[
                    SeriesNode(
                        name="Federal",
                        code="GDP_G_FED",
                        sources=[_fred("FGCE"), _bea("T10105", 23)],
                        children=[
                            SeriesNode(
                                name="National Defense",
                                code="GDP_G_DEF",
                                sources=[_fred("FDEFX"), _bea("T10105", 24)],
                            ),
                            SeriesNode(
                                name="Nondefense",
                                code="GDP_G_NONDEF",
                                sources=[_fred("FNDEFX"), _bea("T10105", 25)],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="State and Local",
                        code="GDP_G_SL",
                        sources=[_fred("SLCE"), _bea("T10105", 26)],
                    ),
                ],
            ),
            # GDP Price Indexes
            SeriesNode(
                name="GDP Price Measures",
                code="GDP_PRICE",
                description="GDP deflator and related price measures",
                children=[
                    SeriesNode(
                        name="GDP Implicit Price Deflator",
                        code="GDP_DEFL",
                        sources=[_fred("GDPDEF"), _bea("T10107", 1)],
                    ),
                    SeriesNode(
                        name="GDP Chain-type Price Index",
                        code="GDP_CHAIN_PI",
                        sources=[_fred("A191RG3Q086SBEA")],
                    ),
                ],
            ),
        ],
    )
