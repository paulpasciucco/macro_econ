"""Employment hierarchy trees: CES (Establishment Survey) and CPS (Household Survey).

CES hierarchy is loaded from ``data/Payrolls/bls_ces_payrolls_hierarchy_comma_safe.csv``.
Each node carries BLS sources for 4 metric types (employment, avg hourly earnings,
avg weekly hours, avg weekly earnings) in both SA and NSA variants.

CPS (Household Survey) uses FRED series for labor force measures and remains
defined in code since there is no comparable structured data file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from macro_econ.series.loaders import load_ces_hierarchy
from macro_econ.series.node import SeriesNode, SeriesSource


def _fred(series_id: str) -> SeriesSource:
    return SeriesSource("fred", series_id)


def build_ces_tree(
    *,
    path: Optional[Path] = None,
    max_depth: Optional[int] = None,
) -> SeriesNode:
    """Build the CES (Establishment Survey) hierarchy from the data file.

    Args:
        path: Override path to the payrolls CSV.
        max_depth: Prune the tree at this depth (None = full detail).

    Returns:
        Root SeriesNode for the CES/Payrolls hierarchy.
    """
    return load_ces_hierarchy(path=path, max_depth=max_depth)


def build_cps_tree() -> SeriesNode:
    """Build the CPS (Household Survey) hierarchy.

    These series come primarily from FRED since BLS CPS data has different
    series ID structures than CES.
    """
    return SeriesNode(
        name="Household Survey (CPS)",
        code="CPS",
        description="Labor force measures from the Current Population Survey",
        children=[
            # --- Headline Measures ---
            SeriesNode(
                name="Headline Measures",
                code="CPS_HEAD",
                children=[
                    SeriesNode(
                        name="Unemployment Rate",
                        code="UR",
                        sources=[_fred("UNRATE")],
                        description="U-3 measure, percent, SA",
                    ),
                    SeriesNode(
                        name="Civilian Labor Force",
                        code="CLF",
                        sources=[_fred("CLF16OV")],
                        description="Thousands, SA",
                    ),
                    SeriesNode(
                        name="Labor Force Participation Rate",
                        code="LFPR",
                        sources=[_fred("CIVPART")],
                        description="Percent, SA",
                    ),
                    SeriesNode(
                        name="Employment-Population Ratio",
                        code="EPOP",
                        sources=[_fred("EMRATIO")],
                        description="Percent, SA",
                    ),
                    SeriesNode(
                        name="Total Employed",
                        code="EMP",
                        sources=[_fred("CE16OV")],
                        description="Thousands, SA",
                    ),
                    SeriesNode(
                        name="Total Unemployed",
                        code="UNEMP",
                        sources=[_fred("UNEMPLOY")],
                        description="Thousands, SA",
                    ),
                ],
            ),
            # --- Alternative Unemployment Measures ---
            SeriesNode(
                name="Alternative Unemployment Measures",
                code="CPS_ALT_UR",
                description="U-1 through U-6 measures of labor underutilization",
                children=[
                    SeriesNode(name="U-1: Persons unemployed 15 weeks or longer",
                               code="U1", sources=[_fred("U1RATE")]),
                    SeriesNode(name="U-2: Job losers and completed temp jobs",
                               code="U2", sources=[_fred("U2RATE")]),
                    SeriesNode(name="U-3: Total unemployed (official rate)",
                               code="U3", sources=[_fred("UNRATE")]),
                    SeriesNode(name="U-4: Total + discouraged workers",
                               code="U4", sources=[_fred("U4RATE")]),
                    SeriesNode(name="U-5: Total + marginally attached workers",
                               code="U5", sources=[_fred("U5RATE")]),
                    SeriesNode(name="U-6: Total + marginally attached + part-time for economic reasons",
                               code="U6", sources=[_fred("U6RATE")]),
                ],
            ),
            # --- Demographics ---
            SeriesNode(
                name="Demographics",
                code="CPS_DEMO",
                children=[
                    SeriesNode(
                        name="Unemployment by Age",
                        code="CPS_AGE",
                        children=[
                            SeriesNode(name="16-19 years", code="UR_16_19",
                                       sources=[_fred("LNS14000012")]),
                            SeriesNode(name="20-24 years", code="UR_20_24",
                                       sources=[_fred("LNS14000036")]),
                            SeriesNode(name="25-54 years (prime age)", code="UR_25_54",
                                       sources=[_fred("LNS14000060")]),
                            SeriesNode(name="55 years and over", code="UR_55_PLUS",
                                       sources=[_fred("LNS14000024")]),
                        ],
                    ),
                    SeriesNode(
                        name="Unemployment by Gender",
                        code="CPS_GENDER",
                        children=[
                            SeriesNode(name="Men, 20 years and over", code="UR_MEN",
                                       sources=[_fred("LNS14000025")]),
                            SeriesNode(name="Women, 20 years and over", code="UR_WOMEN",
                                       sources=[_fred("LNS14000026")]),
                        ],
                    ),
                    SeriesNode(
                        name="Unemployment by Race",
                        code="CPS_RACE",
                        children=[
                            SeriesNode(name="White", code="UR_WHITE",
                                       sources=[_fred("LNS14000003")]),
                            SeriesNode(name="Black or African American", code="UR_BLACK",
                                       sources=[_fred("LNS14000006")]),
                            SeriesNode(name="Hispanic or Latino", code="UR_HISPANIC",
                                       sources=[_fred("LNS14000009")]),
                            SeriesNode(name="Asian", code="UR_ASIAN",
                                       sources=[_fred("LNS14000032")]),
                        ],
                    ),
                    SeriesNode(
                        name="Prime Age (25-54) Measures",
                        code="CPS_PRIME",
                        children=[
                            SeriesNode(name="LFPR 25-54 years", code="LFPR_25_54",
                                       sources=[_fred("LNS11300060")]),
                            SeriesNode(name="EPOP 25-54 years", code="EPOP_25_54",
                                       sources=[_fred("LNS12300060")]),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_employment_trees(
    *,
    max_depth: Optional[int] = None,
) -> tuple[SeriesNode, SeriesNode]:
    """Build both CES and CPS trees.

    Returns:
        Tuple of (ces_tree, cps_tree).
    """
    return build_ces_tree(max_depth=max_depth), build_cps_tree()
