"""CPI (Consumer Price Index) hierarchy tree.

Sources:
    - BLS CPI-U series (CUSR0000{item_code} for SA, CUUR0000{item_code} for NSA)
    - FRED series for headline and commonly watched items

The BLS series ID format:
    CU[S|U]R0000{item_code}
    - CU = CPI for All Urban Consumers
    - S = seasonally adjusted, U = not seasonally adjusted
    - R = regular monthly periodicity
    - 0000 = U.S. city average
    - item_code = expenditure category
"""

from macro_econ.series.node import SeriesNode, SeriesSource


def _bls(item_code: str, seasonal: str = "S") -> SeriesSource:
    """Create a BLS CPI source from an item code."""
    adj = "S" if seasonal == "S" else "U"
    series_id = f"CU{adj}R0000{item_code}"
    return SeriesSource("bls", series_id, {"item_code": item_code, "seasonal": seasonal})


def _fred(series_id: str) -> SeriesSource:
    return SeriesSource("fred", series_id)


def build_cpi_tree() -> SeriesNode:
    """Build the full CPI-U hierarchy tree.

    Structure follows the BLS expenditure category classification with all
    major groups, sub-groups, and commonly tracked detailed items. Special
    aggregates (Core CPI, energy, etc.) are included as a separate branch.
    """
    return SeriesNode(
        name="CPI-U All Items",
        code="CPI",
        sources=[_bls("SA0"), _fred("CPIAUCSL")],
        description="Consumer Price Index for All Urban Consumers, All Items",
        children=[
            # --- Major Group 1: Food and Beverages ---
            SeriesNode(
                name="Food and Beverages",
                code="CPI_FOOD_BEV",
                sources=[_bls("SAF"), _fred("CPIFABSL")],
                children=[
                    SeriesNode(
                        name="Food",
                        code="CPI_FOOD",
                        sources=[_bls("SAF1")],
                        children=[
                            SeriesNode(
                                name="Food at home",
                                code="CPI_FOOD_HOME",
                                sources=[_bls("SAF11")],
                                children=[
                                    SeriesNode(name="Cereals and bakery products",
                                               code="CPI_CEREAL",
                                               sources=[_bls("SAF111")]),
                                    SeriesNode(name="Meats, poultry, fish, and eggs",
                                               code="CPI_MEATS",
                                               sources=[_bls("SAF112")]),
                                    SeriesNode(name="Dairy and related products",
                                               code="CPI_DAIRY",
                                               sources=[_bls("SAF113")]),
                                    SeriesNode(name="Fruits and vegetables",
                                               code="CPI_FRUIT_VEG",
                                               sources=[_bls("SAF114")]),
                                    SeriesNode(name="Nonalcoholic beverages and beverage materials",
                                               code="CPI_NONALC_BEV",
                                               sources=[_bls("SAF115")]),
                                    SeriesNode(name="Other food at home",
                                               code="CPI_OTH_FOOD",
                                               sources=[_bls("SAF116")]),
                                ],
                            ),
                            SeriesNode(
                                name="Food away from home",
                                code="CPI_FOOD_AWAY",
                                sources=[_bls("SEFV")],
                                children=[
                                    SeriesNode(name="Full service meals and snacks",
                                               code="CPI_FULLSVC",
                                               sources=[_bls("SEFV01")]),
                                    SeriesNode(name="Limited service meals and snacks",
                                               code="CPI_LIMITSVC",
                                               sources=[_bls("SEFV02")]),
                                    SeriesNode(name="Other food away from home",
                                               code="CPI_OTH_FOODAWAY",
                                               sources=[_bls("SEFV03")]),
                                ],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="Alcoholic beverages",
                        code="CPI_ALCOHOL",
                        sources=[_bls("SAF2")],
                    ),
                ],
            ),
            # --- Major Group 2: Housing ---
            SeriesNode(
                name="Housing",
                code="CPI_HOUSING",
                sources=[_bls("SAH"), _fred("CPIHOSSL")],
                children=[
                    SeriesNode(
                        name="Shelter",
                        code="CPI_SHELTER",
                        sources=[_bls("SAH1")],
                        children=[
                            SeriesNode(
                                name="Rent of primary residence",
                                code="CPI_RENT",
                                sources=[_bls("SEHA"), _fred("CUSR0000SEHA")],
                            ),
                            SeriesNode(
                                name="Owners' equivalent rent of residences",
                                code="CPI_OER",
                                sources=[_bls("SEHC"), _fred("CUSR0000SEHC")],
                            ),
                            SeriesNode(
                                name="Lodging away from home",
                                code="CPI_LODGING",
                                sources=[_bls("SEHB")],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="Fuels and utilities",
                        code="CPI_FUELS_UTIL",
                        sources=[_bls("SAH2")],
                        children=[
                            SeriesNode(
                                name="Household energy",
                                code="CPI_HOUSEHOLD_ENERGY",
                                sources=[_bls("SAH21")],
                                children=[
                                    SeriesNode(name="Electricity",
                                               code="CPI_ELEC",
                                               sources=[_bls("SEHF01")]),
                                    SeriesNode(name="Utility (piped) gas service",
                                               code="CPI_GAS_UTIL",
                                               sources=[_bls("SEHF02")]),
                                    SeriesNode(name="Fuel oil and other fuels",
                                               code="CPI_FUEL_OIL",
                                               sources=[_bls("SEHF03")]),
                                ],
                            ),
                            SeriesNode(
                                name="Water and sewer and trash collection services",
                                code="CPI_WATER_SEWER",
                                sources=[_bls("SEHG")],
                            ),
                        ],
                    ),
                    SeriesNode(
                        name="Household furnishings and operations",
                        code="CPI_HH_FURN",
                        sources=[_bls("SAH3")],
                        children=[
                            SeriesNode(name="Household furnishings and supplies",
                                       code="CPI_HH_FURN_SUPPLY",
                                       sources=[_bls("SAH31")]),
                            SeriesNode(name="Household operations",
                                       code="CPI_HH_OPS",
                                       sources=[_bls("SAH32")]),
                        ],
                    ),
                ],
            ),
            # --- Major Group 3: Apparel ---
            SeriesNode(
                name="Apparel",
                code="CPI_APPAREL",
                sources=[_bls("SAA"), _fred("CPIAPPSL")],
                children=[
                    SeriesNode(name="Men's and boys' apparel",
                               code="CPI_MENS",
                               sources=[_bls("SAA1")]),
                    SeriesNode(name="Women's and girls' apparel",
                               code="CPI_WOMENS",
                               sources=[_bls("SAA2")]),
                    SeriesNode(name="Footwear",
                               code="CPI_FOOTWEAR",
                               sources=[_bls("SERA")]),
                    SeriesNode(name="Infants' and toddlers' apparel",
                               code="CPI_INFANT",
                               sources=[_bls("SEAA")]),
                ],
            ),
            # --- Major Group 4: Transportation ---
            SeriesNode(
                name="Transportation",
                code="CPI_TRANSPORT",
                sources=[_bls("SAT"), _fred("CPITRNSL")],
                children=[
                    SeriesNode(
                        name="Private transportation",
                        code="CPI_PRIV_TRANS",
                        sources=[_bls("SAT1")],
                        children=[
                            SeriesNode(name="New vehicles",
                                       code="CPI_NEW_VEH",
                                       sources=[_bls("SETA01"), _fred("CUSR0000SETA01")]),
                            SeriesNode(name="Used cars and trucks",
                                       code="CPI_USED_VEH",
                                       sources=[_bls("SETA02"), _fred("CUSR0000SETA02")]),
                            SeriesNode(name="Motor fuel",
                                       code="CPI_MOTOR_FUEL",
                                       sources=[_bls("SETB"), _fred("CUSR0000SETB")]),
                            SeriesNode(name="Motor vehicle parts and equipment",
                                       code="CPI_VEH_PARTS",
                                       sources=[_bls("SETC")]),
                            SeriesNode(name="Motor vehicle maintenance and repair",
                                       code="CPI_VEH_MAINT",
                                       sources=[_bls("SETD")]),
                            SeriesNode(name="Motor vehicle insurance",
                                       code="CPI_VEH_INS",
                                       sources=[_bls("SETE"), _fred("CUSR0000SETE")]),
                        ],
                    ),
                    SeriesNode(
                        name="Public transportation",
                        code="CPI_PUB_TRANS",
                        sources=[_bls("SAT2")],
                        children=[
                            SeriesNode(name="Airline fares",
                                       code="CPI_AIRLINE",
                                       sources=[_bls("SETG01")]),
                            SeriesNode(name="Other intercity transportation",
                                       code="CPI_OTH_INTERCITY",
                                       sources=[_bls("SETG02")]),
                        ],
                    ),
                ],
            ),
            # --- Major Group 5: Medical Care ---
            SeriesNode(
                name="Medical Care",
                code="CPI_MEDICAL",
                sources=[_bls("SAM"), _fred("CPIMEDSL")],
                children=[
                    SeriesNode(
                        name="Medical care commodities",
                        code="CPI_MED_COMM",
                        sources=[_bls("SAM1")],
                        children=[
                            SeriesNode(name="Prescription drugs",
                                       code="CPI_RX",
                                       sources=[_bls("SEMA01")]),
                            SeriesNode(name="Nonprescription drugs and medical supplies",
                                       code="CPI_OTC",
                                       sources=[_bls("SEMA02")]),
                        ],
                    ),
                    SeriesNode(
                        name="Medical care services",
                        code="CPI_MED_SVC",
                        sources=[_bls("SAM2")],
                        children=[
                            SeriesNode(name="Professional services",
                                       code="CPI_MED_PROF",
                                       sources=[_bls("SEMC")]),
                            SeriesNode(name="Hospital and related services",
                                       code="CPI_HOSPITAL",
                                       sources=[_bls("SEMD")]),
                            SeriesNode(name="Health insurance",
                                       code="CPI_HEALTH_INS",
                                       sources=[_bls("SEME")]),
                        ],
                    ),
                ],
            ),
            # --- Major Group 6: Recreation ---
            SeriesNode(
                name="Recreation",
                code="CPI_REC",
                sources=[_bls("SAR"), _fred("CPIRECSL")],
                children=[
                    SeriesNode(name="Video and audio",
                               code="CPI_VIDEO_AUDIO",
                               sources=[_bls("SERA01")]),
                    SeriesNode(name="Pets, pet products and services",
                               code="CPI_PETS",
                               sources=[_bls("SERA02")]),
                    SeriesNode(name="Sporting goods",
                               code="CPI_SPORTS",
                               sources=[_bls("SERF01")]),
                    SeriesNode(name="Photography",
                               code="CPI_PHOTO",
                               sources=[_bls("SERF02")]),
                    SeriesNode(name="Other recreation",
                               code="CPI_OTH_REC",
                               sources=[_bls("SERG")]),
                ],
            ),
            # --- Major Group 7: Education and Communication ---
            SeriesNode(
                name="Education and Communication",
                code="CPI_EDU_COMM",
                sources=[_bls("SAE"), _fred("CPIEDUSL")],
                children=[
                    SeriesNode(
                        name="Education",
                        code="CPI_EDU",
                        sources=[_bls("SAE1")],
                        children=[
                            SeriesNode(name="Tuition, other school fees, and childcare",
                                       code="CPI_TUITION",
                                       sources=[_bls("SEEA")]),
                        ],
                    ),
                    SeriesNode(
                        name="Communication",
                        code="CPI_COMM",
                        sources=[_bls("SAE2")],
                        children=[
                            SeriesNode(name="Telephone services",
                                       code="CPI_PHONE",
                                       sources=[_bls("SEED")]),
                            SeriesNode(name="Information technology, hardware and services",
                                       code="CPI_IT",
                                       sources=[_bls("SEEE")]),
                        ],
                    ),
                ],
            ),
            # --- Major Group 8: Other Goods and Services ---
            SeriesNode(
                name="Other Goods and Services",
                code="CPI_OTHER",
                sources=[_bls("SAG"), _fred("CPIOGSSL")],
                children=[
                    SeriesNode(name="Tobacco and smoking products",
                               code="CPI_TOBACCO",
                               sources=[_bls("SEGA")]),
                    SeriesNode(name="Personal care",
                               code="CPI_PERSONAL_CARE",
                               sources=[_bls("SAGC")]),
                    SeriesNode(name="Miscellaneous personal services",
                               code="CPI_MISC_SVC",
                               sources=[_bls("SEGD")]),
                ],
            ),
            # --- Special Aggregates ---
            SeriesNode(
                name="Special Aggregates",
                code="CPI_SPECIAL",
                description="Cross-cutting CPI aggregates not part of the expenditure tree",
                children=[
                    SeriesNode(
                        name="All items less food and energy (Core CPI)",
                        code="CPI_CORE",
                        sources=[_bls("SA0L1E"), _fred("CPILFESL")],
                    ),
                    SeriesNode(
                        name="Energy",
                        code="CPI_ENERGY",
                        sources=[_bls("SA0E"), _fred("CPIENGSL")],
                    ),
                    SeriesNode(
                        name="All items less shelter",
                        code="CPI_LESS_SHELTER",
                        sources=[_bls("SA0L2")],
                    ),
                    SeriesNode(
                        name="All items less food",
                        code="CPI_LESS_FOOD",
                        sources=[_bls("SA0L12E")],
                    ),
                    SeriesNode(
                        name="Commodities",
                        code="CPI_COMMODITIES",
                        sources=[_bls("SAC")],
                    ),
                    SeriesNode(
                        name="Commodities less food and energy",
                        code="CPI_CORE_COMMODITIES",
                        sources=[_bls("SACL1E")],
                    ),
                    SeriesNode(
                        name="Services",
                        code="CPI_SERVICES",
                        sources=[_bls("SAS")],
                    ),
                    SeriesNode(
                        name="Services less energy services",
                        code="CPI_SVC_LESS_ENERGY",
                        sources=[_bls("SASL2RS")],
                    ),
                    SeriesNode(
                        name="Services less rent of shelter",
                        code="CPI_SUPERCORE",
                        sources=[_bls("SASLE")],
                        description="Supercore CPI: services excluding shelter",
                    ),
                    SeriesNode(
                        name="All items less food, shelter, and energy",
                        code="CPI_LESS_FOOD_SHELTER_ENERGY",
                        sources=[_bls("SA0L12E3")],
                    ),
                    SeriesNode(
                        name="All items less medical care",
                        code="CPI_LESS_MED",
                        sources=[_bls("SA0L5")],
                    ),
                ],
            ),
        ],
    )
