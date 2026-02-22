"""Employment hierarchy trees: CES (Establishment Survey) and CPS (Household Survey).

Sources:
    - BLS CES series: CE[S|U]{industry_code 8}{data_type 2}
    - BLS CPS series via FRED (household survey measures)
    - FRED series for headline numbers

CES data type codes:
    01 = All employees (thousands)
    02 = Average weekly hours
    03 = Average hourly earnings
    06 = Production/nonsupervisory employees
    11 = Average weekly earnings
"""

from macro_econ.series.node import SeriesNode, SeriesSource


def _fred(series_id: str) -> SeriesSource:
    return SeriesSource("fred", series_id)


def _ces(industry_code: str, data_type: str = "01", seasonal: str = "S") -> SeriesSource:
    """Create a BLS CES source.

    Args:
        industry_code: 8-digit supersector + industry code (e.g., "00000000" for total nonfarm).
        data_type: 2-digit data type code.
        seasonal: "S" for seasonally adjusted, "U" for unadjusted.
    """
    adj = "S" if seasonal == "S" else "U"
    series_id = f"CE{adj}{industry_code}{data_type}"
    return SeriesSource(
        "bls",
        series_id,
        {"industry_code": industry_code, "data_type": data_type, "seasonal": seasonal},
    )


def build_ces_tree() -> SeriesNode:
    """Build the CES (Current Employment Statistics / Establishment Survey) hierarchy.

    Structure follows BLS Table B-1: Employees on nonfarm payrolls.
    All series default to data_type=01 (all employees, thousands, SA).
    """
    return SeriesNode(
        name="Total Nonfarm",
        code="NFP",
        sources=[_ces("00000000"), _fred("PAYEMS")],
        description="Total nonfarm payrolls, seasonally adjusted, thousands",
        children=[
            SeriesNode(
                name="Total Private",
                code="NFP_PRIV",
                sources=[_ces("05000000"), _fred("USPRIV")],
                children=[
                    # --- Goods-Producing ---
                    SeriesNode(
                        name="Goods-Producing",
                        code="NFP_GOODS",
                        sources=[_ces("06000000")],
                        children=[
                            SeriesNode(
                                name="Mining and Logging",
                                code="NFP_MINING",
                                sources=[_ces("10000000"), _fred("USMINE")],
                                children=[
                                    SeriesNode(name="Mining (except oil and gas)",
                                               code="NFP_MINING_EX",
                                               sources=[_ces("10212000")]),
                                    SeriesNode(name="Oil and gas extraction",
                                               code="NFP_OIL_GAS",
                                               sources=[_ces("10211000")]),
                                    SeriesNode(name="Logging",
                                               code="NFP_LOGGING",
                                               sources=[_ces("10113000")]),
                                    SeriesNode(name="Support activities for mining",
                                               code="NFP_MINING_SUPPORT",
                                               sources=[_ces("10213000")]),
                                ],
                            ),
                            SeriesNode(
                                name="Construction",
                                code="NFP_CONSTR",
                                sources=[_ces("20000000"), _fred("USCONS")],
                                children=[
                                    SeriesNode(name="Construction of buildings",
                                               code="NFP_CONSTR_BLDG",
                                               sources=[_ces("20236000")]),
                                    SeriesNode(name="Heavy and civil engineering construction",
                                               code="NFP_CONSTR_HEAVY",
                                               sources=[_ces("20237000")]),
                                    SeriesNode(name="Specialty trade contractors",
                                               code="NFP_CONSTR_SPEC",
                                               sources=[_ces("20238000")]),
                                ],
                            ),
                            SeriesNode(
                                name="Manufacturing",
                                code="NFP_MFG",
                                sources=[_ces("30000000"), _fred("MANEMP")],
                                children=[
                                    SeriesNode(
                                        name="Durable Goods",
                                        code="NFP_MFG_DUR",
                                        sources=[_ces("31000000"), _fred("DMANEMP")],
                                        children=[
                                            SeriesNode(name="Wood products",
                                                       code="NFP_MFG_WOOD",
                                                       sources=[_ces("31321000")]),
                                            SeriesNode(name="Primary metals",
                                                       code="NFP_MFG_METALS",
                                                       sources=[_ces("31331000")]),
                                            SeriesNode(name="Fabricated metal products",
                                                       code="NFP_MFG_FABMETAL",
                                                       sources=[_ces("31332000")]),
                                            SeriesNode(name="Machinery",
                                                       code="NFP_MFG_MACH",
                                                       sources=[_ces("31333000")]),
                                            SeriesNode(name="Computer and electronic products",
                                                       code="NFP_MFG_COMP",
                                                       sources=[_ces("31334000")]),
                                            SeriesNode(name="Electrical equipment and appliances",
                                                       code="NFP_MFG_ELEC",
                                                       sources=[_ces("31335000")]),
                                            SeriesNode(name="Transportation equipment",
                                                       code="NFP_MFG_TRANS",
                                                       sources=[_ces("31336000")]),
                                            SeriesNode(name="Furniture and related products",
                                                       code="NFP_MFG_FURN",
                                                       sources=[_ces("31337000")]),
                                            SeriesNode(name="Miscellaneous durable goods mfg",
                                                       code="NFP_MFG_MISC_DUR",
                                                       sources=[_ces("31339000")]),
                                        ],
                                    ),
                                    SeriesNode(
                                        name="Nondurable Goods",
                                        code="NFP_MFG_NONDUR",
                                        sources=[_ces("32000000"), _fred("NDMANEMP")],
                                        children=[
                                            SeriesNode(name="Food manufacturing",
                                                       code="NFP_MFG_FOOD",
                                                       sources=[_ces("32311000")]),
                                            SeriesNode(name="Textile mills and product mills",
                                                       code="NFP_MFG_TEXT",
                                                       sources=[_ces("32313000")]),
                                            SeriesNode(name="Paper and paper products",
                                                       code="NFP_MFG_PAPER",
                                                       sources=[_ces("32322000")]),
                                            SeriesNode(name="Printing and related activities",
                                                       code="NFP_MFG_PRINT",
                                                       sources=[_ces("32323000")]),
                                            SeriesNode(name="Petroleum and coal products",
                                                       code="NFP_MFG_PETRO",
                                                       sources=[_ces("32324000")]),
                                            SeriesNode(name="Chemical products",
                                                       code="NFP_MFG_CHEM",
                                                       sources=[_ces("32325000")]),
                                            SeriesNode(name="Plastics and rubber products",
                                                       code="NFP_MFG_PLASTIC",
                                                       sources=[_ces("32326000")]),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # --- Service-Providing ---
                    SeriesNode(
                        name="Private Service-Providing",
                        code="NFP_SVC",
                        sources=[_ces("07000000")],
                        children=[
                            SeriesNode(
                                name="Trade, Transportation, and Utilities",
                                code="NFP_TTU",
                                sources=[_ces("40000000"), _fred("USTPU")],
                                children=[
                                    SeriesNode(name="Wholesale Trade",
                                               code="NFP_WHOLESALE",
                                               sources=[_ces("41000000")]),
                                    SeriesNode(name="Retail Trade",
                                               code="NFP_RETAIL",
                                               sources=[_ces("42000000"), _fred("USTRADE")]),
                                    SeriesNode(name="Transportation and Warehousing",
                                               code="NFP_TRANS_WARE",
                                               sources=[_ces("43000000")]),
                                    SeriesNode(name="Utilities",
                                               code="NFP_UTILITIES",
                                               sources=[_ces("44000000")]),
                                ],
                            ),
                            SeriesNode(
                                name="Information",
                                code="NFP_INFO",
                                sources=[_ces("50000000"), _fred("USINFO")],
                            ),
                            SeriesNode(
                                name="Financial Activities",
                                code="NFP_FIN",
                                sources=[_ces("55000000"), _fred("USFIRE")],
                                children=[
                                    SeriesNode(name="Finance and Insurance",
                                               code="NFP_FIN_INS",
                                               sources=[_ces("55520000")]),
                                    SeriesNode(name="Real Estate and Rental and Leasing",
                                               code="NFP_REAL_EST",
                                               sources=[_ces("55530000")]),
                                ],
                            ),
                            SeriesNode(
                                name="Professional and Business Services",
                                code="NFP_PBS",
                                sources=[_ces("60000000"), _fred("USSERV")],
                                children=[
                                    SeriesNode(name="Professional, Scientific, and Technical",
                                               code="NFP_PROF_TECH",
                                               sources=[_ces("60541000")]),
                                    SeriesNode(name="Management of Companies",
                                               code="NFP_MGMT",
                                               sources=[_ces("60550000")]),
                                    SeriesNode(name="Administrative and Support",
                                               code="NFP_ADMIN",
                                               sources=[_ces("60561000")]),
                                    SeriesNode(name="Temporary Help Services",
                                               code="NFP_TEMP",
                                               sources=[_ces("60561300")]),
                                ],
                            ),
                            SeriesNode(
                                name="Education and Health Services",
                                code="NFP_EDHEALTH",
                                sources=[_ces("65000000"), _fred("USEHS")],
                                children=[
                                    SeriesNode(name="Educational Services",
                                               code="NFP_EDU",
                                               sources=[_ces("65610000")]),
                                    SeriesNode(name="Health Care and Social Assistance",
                                               code="NFP_HEALTH",
                                               sources=[_ces("65620000")]),
                                ],
                            ),
                            SeriesNode(
                                name="Leisure and Hospitality",
                                code="NFP_LEISURE",
                                sources=[_ces("70000000"), _fred("USLAH")],
                                children=[
                                    SeriesNode(name="Arts, Entertainment, and Recreation",
                                               code="NFP_ARTS",
                                               sources=[_ces("70710000")]),
                                    SeriesNode(name="Accommodation and Food Services",
                                               code="NFP_ACCOM_FOOD",
                                               sources=[_ces("70720000")]),
                                ],
                            ),
                            SeriesNode(
                                name="Other Services",
                                code="NFP_OTH_SVC",
                                sources=[_ces("80000000"), _fred("USSERV")],
                            ),
                        ],
                    ),
                ],
            ),
            # --- Government ---
            SeriesNode(
                name="Government",
                code="NFP_GOVT",
                sources=[_ces("90000000"), _fred("USGOVT")],
                children=[
                    SeriesNode(
                        name="Federal Government",
                        code="NFP_FED",
                        sources=[_ces("90910000"), _fred("CES9091000001")],
                    ),
                    SeriesNode(
                        name="State Government",
                        code="NFP_STATE",
                        sources=[_ces("90920000"), _fred("CES9092000001")],
                    ),
                    SeriesNode(
                        name="Local Government",
                        code="NFP_LOCAL",
                        sources=[_ces("90930000"), _fred("CES9093000001")],
                    ),
                ],
            ),
            # --- Earnings and Hours ---
            SeriesNode(
                name="Earnings and Hours",
                code="NFP_EARN",
                description="Average hourly earnings and weekly hours for total private",
                children=[
                    SeriesNode(
                        name="Average Hourly Earnings (Total Private)",
                        code="AHE",
                        sources=[_ces("05000000", "03"), _fred("CES0500000003")],
                    ),
                    SeriesNode(
                        name="Average Weekly Hours (Total Private)",
                        code="AWH",
                        sources=[_ces("05000000", "02"), _fred("CES0500000002")],
                    ),
                    SeriesNode(
                        name="Average Hourly Earnings (Production/Nonsupervisory)",
                        code="AHE_PROD",
                        sources=[_ces("05000000", "08"), _fred("CES0500000008")],
                    ),
                    SeriesNode(
                        name="Average Weekly Hours (Production/Nonsupervisory)",
                        code="AWH_PROD",
                        sources=[_ces("05000000", "07"), _fred("CES0500000007")],
                    ),
                ],
            ),
        ],
    )


def build_cps_tree() -> SeriesNode:
    """Build the CPS (Current Population Survey / Household Survey) hierarchy.

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
                    SeriesNode(
                        name="U-1: Persons unemployed 15 weeks or longer",
                        code="U1",
                        sources=[_fred("U1RATE")],
                    ),
                    SeriesNode(
                        name="U-2: Job losers and completed temp jobs",
                        code="U2",
                        sources=[_fred("U2RATE")],
                    ),
                    SeriesNode(
                        name="U-3: Total unemployed (official rate)",
                        code="U3",
                        sources=[_fred("UNRATE")],
                    ),
                    SeriesNode(
                        name="U-4: Total + discouraged workers",
                        code="U4",
                        sources=[_fred("U4RATE")],
                    ),
                    SeriesNode(
                        name="U-5: Total + marginally attached workers",
                        code="U5",
                        sources=[_fred("U5RATE")],
                    ),
                    SeriesNode(
                        name="U-6: Total + marginally attached + part-time for economic reasons",
                        code="U6",
                        sources=[_fred("U6RATE")],
                    ),
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
                            SeriesNode(name="16-19 years",
                                       code="UR_16_19",
                                       sources=[_fred("LNS14000012")]),
                            SeriesNode(name="20-24 years",
                                       code="UR_20_24",
                                       sources=[_fred("LNS14000036")]),
                            SeriesNode(name="25-54 years (prime age)",
                                       code="UR_25_54",
                                       sources=[_fred("LNS14000060")]),
                            SeriesNode(name="55 years and over",
                                       code="UR_55_PLUS",
                                       sources=[_fred("LNS14000024")]),
                        ],
                    ),
                    SeriesNode(
                        name="Unemployment by Gender",
                        code="CPS_GENDER",
                        children=[
                            SeriesNode(name="Men, 20 years and over",
                                       code="UR_MEN",
                                       sources=[_fred("LNS14000025")]),
                            SeriesNode(name="Women, 20 years and over",
                                       code="UR_WOMEN",
                                       sources=[_fred("LNS14000026")]),
                        ],
                    ),
                    SeriesNode(
                        name="Unemployment by Race",
                        code="CPS_RACE",
                        children=[
                            SeriesNode(name="White",
                                       code="UR_WHITE",
                                       sources=[_fred("LNS14000003")]),
                            SeriesNode(name="Black or African American",
                                       code="UR_BLACK",
                                       sources=[_fred("LNS14000006")]),
                            SeriesNode(name="Hispanic or Latino",
                                       code="UR_HISPANIC",
                                       sources=[_fred("LNS14000009")]),
                            SeriesNode(name="Asian",
                                       code="UR_ASIAN",
                                       sources=[_fred("LNS14000032")]),
                        ],
                    ),
                    SeriesNode(
                        name="LFPR by Age (Prime Age)",
                        code="CPS_LFPR_AGE",
                        children=[
                            SeriesNode(name="LFPR 25-54 years",
                                       code="LFPR_25_54",
                                       sources=[_fred("LNS11300060")]),
                            SeriesNode(name="EPOP 25-54 years",
                                       code="EPOP_25_54",
                                       sources=[_fred("LNS12300060")]),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_employment_trees() -> tuple[SeriesNode, SeriesNode]:
    """Build both CES and CPS trees.

    Returns:
        Tuple of (ces_tree, cps_tree).
    """
    return build_ces_tree(), build_cps_tree()
