"""PCE (Personal Consumption Expenditures) hierarchy tree.

Sources:
    - BEA NIPA Tables 2.3.x (by major type, annual/quarterly)
    - BEA NIPA Tables 2.4.x (by type, more detail)
    - BEA NIPA Tables 2.8.x (by major type, monthly)
    - FRED series for headline and major components
"""

from macro_econ.series.node import SeriesNode, SeriesSource


def _fred(series_id: str) -> SeriesSource:
    return SeriesSource("fred", series_id)


def _bea(table: str, line: int, freq: str = "M") -> SeriesSource:
    return SeriesSource("bea", table, {"table": table, "frequency": freq, "line_number": line})


def build_pce_tree() -> SeriesNode:
    """Build the full PCE hierarchy tree.

    Structure follows BEA NIPA Table 2.3.5 / 2.8.5 (PCE by Major Type of Product).
    FRED series IDs are for monthly current-dollar PCE unless noted.
    """
    return SeriesNode(
        name="Personal Consumption Expenditures",
        code="PCE",
        sources=[_fred("PCE"), _fred("PCEC96"), _bea("T20805", 1)],
        description="Total PCE, current dollars (PCE) and chained 2017$ (PCEC96)",
        children=[
            SeriesNode(
                name="Goods",
                code="PCE_GOODS",
                sources=[_fred("DGDSRC1M027NBEA"), _bea("T20805", 2)],
                children=[
                    SeriesNode(
                        name="Durable Goods",
                        code="PCE_DUR",
                        sources=[_fred("PCDG"), _fred("PCDGCC96"), _bea("T20805", 3)],
                        children=[
                            SeriesNode(
                                name="Motor vehicles and parts",
                                code="PCE_DUR_MOTOR",
                                sources=[_fred("DMOTRC1M027NBEA"), _bea("T20805", 4)],
                            ),
                            SeriesNode(
                                name="Furnishings and durable household equipment",
                                code="PCE_DUR_FURN",
                                sources=[_fred("DFDHRC1M027NBEA"), _bea("T20805", 5)],
                            ),
                            SeriesNode(
                                name="Recreational goods and vehicles",
                                code="PCE_DUR_REC",
                                sources=[_fred("DRECRC1M027NBEA"), _bea("T20805", 6)],
                            ),
                            SeriesNode(
                                name="Other durable goods",
                                code="PCE_DUR_OTH",
                                sources=[_fred("DODGRC1M027NBEA"), _bea("T20805", 7)],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="Nondurable Goods",
                        code="PCE_NONDUR",
                        sources=[_fred("PCND"), _fred("PCNDGC96"), _bea("T20805", 8)],
                        children=[
                            SeriesNode(
                                name="Food and beverages purchased for off-premises consumption",
                                code="PCE_NONDUR_FOOD",
                                sources=[_fred("DFXARC1M027NBEA"), _bea("T20805", 9)],
                            ),
                            SeriesNode(
                                name="Clothing and footwear",
                                code="PCE_NONDUR_CLOTH",
                                sources=[_fred("DCAFRC1M027NBEA"), _bea("T20805", 10)],
                            ),
                            SeriesNode(
                                name="Gasoline and other energy goods",
                                code="PCE_NONDUR_GAS",
                                sources=[_fred("DGOERG1M027NBEA"), _bea("T20805", 11)],
                            ),
                            SeriesNode(
                                name="Other nondurable goods",
                                code="PCE_NONDUR_OTH",
                                sources=[_fred("DONHRC1M027NBEA"), _bea("T20805", 12)],
                            ),
                        ],
                    ),
                ],
            ),
            SeriesNode(
                name="Services",
                code="PCE_SVC",
                sources=[_fred("PCES"), _fred("PCESVC96"), _bea("T20805", 13)],
                children=[
                    SeriesNode(
                        name="Housing and utilities",
                        code="PCE_SVC_HOUSING",
                        sources=[_fred("DHUTRG3M086SBEA"), _bea("T20805", 14)],
                    ),
                    SeriesNode(
                        name="Health care",
                        code="PCE_SVC_HEALTH",
                        sources=[_fred("DHLCRC1M027NBEA"), _bea("T20805", 15)],
                    ),
                    SeriesNode(
                        name="Transportation services",
                        code="PCE_SVC_TRANS",
                        sources=[_fred("DTRSRC1M027NBEA"), _bea("T20805", 16)],
                    ),
                    SeriesNode(
                        name="Recreation services",
                        code="PCE_SVC_REC",
                        sources=[_fred("DREQRC1M027NBEA"), _bea("T20805", 17)],
                    ),
                    SeriesNode(
                        name="Food services and accommodations",
                        code="PCE_SVC_FOOD",
                        sources=[_fred("DFSARC1M027NBEA"), _bea("T20805", 18)],
                    ),
                    SeriesNode(
                        name="Financial services and insurance",
                        code="PCE_SVC_FIN",
                        sources=[_fred("DFINRC1M027NBEA"), _bea("T20805", 19)],
                    ),
                    SeriesNode(
                        name="Other services",
                        code="PCE_SVC_OTH",
                        sources=[_fred("DOTHRC1M027NBEA"), _bea("T20805", 20)],
                    ),
                ],
            ),
            # PCE Price Indexes (separate subtree for convenience)
            SeriesNode(
                name="PCE Price Indexes",
                code="PCE_PRICE",
                description="Price indexes from BEA Table 2.8.4",
                children=[
                    SeriesNode(
                        name="PCE Price Index (headline)",
                        code="PCE_PI",
                        sources=[_fred("PCEPI"), _bea("T20804", 1)],
                    ),
                    SeriesNode(
                        name="PCE Price Index excluding food and energy (core)",
                        code="PCE_PI_CORE",
                        sources=[_fred("PCEPILFE"), _bea("T20804", 15)],
                    ),
                    SeriesNode(
                        name="Goods Price Index",
                        code="PCE_PI_GOODS",
                        sources=[_fred("DGDSRG3M086SBEA")],
                    ),
                    SeriesNode(
                        name="Durable Goods Price Index",
                        code="PCE_PI_DUR",
                        sources=[_fred("DDURRG3M086SBEA")],
                    ),
                    SeriesNode(
                        name="Nondurable Goods Price Index",
                        code="PCE_PI_NONDUR",
                        sources=[_fred("DNDGRG3M086SBEA")],
                    ),
                    SeriesNode(
                        name="Services Price Index",
                        code="PCE_PI_SVC",
                        sources=[_fred("DSERRG3M086SBEA")],
                    ),
                ],
            ),
        ],
    )
