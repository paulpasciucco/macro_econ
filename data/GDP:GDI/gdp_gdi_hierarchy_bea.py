"""
GDP & GDI Hierarchy — BEA NIPA Edition
=======================================

Complete mapping of GDP (expenditure approach) and GDI (income approach)
component hierarchies using BEA NIPA table/line identifiers and SeriesCodes.

GDP Tables (Table 1.1.x family, all share line numbers):
    - T10101  (Table 1.1.1)  : Percent Change from Preceding Period in Real GDP
    - T10102  (Table 1.1.2)  : Contributions to Percent Change in Real GDP
    - T10103  (Table 1.1.3)  : Real GDP Quantity Indexes
    - T10104  (Table 1.1.4)  : Price Indexes for GDP
    - T10105  (Table 1.1.5)  : Nominal (Current-Dollar) GDP
    - T10106  (Table 1.1.6)  : Real GDP (Chained Dollars)
    - T10107  (Table 1.1.7)  : Percent Change in Prices for GDP
    - T10109  (Table 1.1.9)  : Implicit Price Deflators for GDP
    - T10110  (Table 1.1.10) : Percentage Shares of GDP

GDI Table:
    - T11000  (Table 1.10)   : Gross Domestic Income by Type of Income

GDP + GDI Aggregate Table:
    - T11705  (Table 1.17.5) : GDP, GDI, and Other Major NIPA Aggregates
    - T11706  (Table 1.17.6) : Real GDP, GDI, and Other Aggregates (Chained $)

Usage:
    from gdp_gdi_hierarchy_bea import (
        GDP_HIERARCHY,
        GDI_HIERARCHY,
        GDP_TABLES,
        GDI_TABLES,
        build_gdp_dataframe,
        build_gdi_dataframe,
        build_bea_request,
    )

    # Flat DataFrames
    gdp_df = build_gdp_dataframe()
    gdi_df = build_gdi_dataframe()

    # BEA API request for nominal GDP
    params = build_bea_request("T10105", "Q", [2023, 2024], "YOUR_KEY")

BEA API Registration:
    Get a free API key at https://apps.bea.gov/api/signup/
"""

import pandas as pd
from typing import Optional


# ---------------------------------------------------------------------------
# BEA Table Configuration — GDP (Table 1.1.x family)
# ---------------------------------------------------------------------------
# All GDP 1.1.x tables share the same 26-line structure.
# ---------------------------------------------------------------------------

GDP_TABLES = {
    "pct_change":      {"table_name": "T10101", "display": "Table 1.1.1",  "description": "Percent Change from Preceding Period in Real GDP"},
    "contributions":   {"table_name": "T10102", "display": "Table 1.1.2",  "description": "Contributions to Percent Change in Real GDP"},
    "quantity_index":  {"table_name": "T10103", "display": "Table 1.1.3",  "description": "Real GDP Quantity Indexes"},
    "price_index":     {"table_name": "T10104", "display": "Table 1.1.4",  "description": "Price Indexes for GDP"},
    "nominal":         {"table_name": "T10105", "display": "Table 1.1.5",  "description": "Gross Domestic Product (Current Dollars)"},
    "real":            {"table_name": "T10106", "display": "Table 1.1.6",  "description": "Real GDP (Chained Dollars)"},
    "pct_change_price":{"table_name": "T10107", "display": "Table 1.1.7",  "description": "Percent Change in Prices for GDP"},
    "deflator":        {"table_name": "T10109", "display": "Table 1.1.9",  "description": "Implicit Price Deflators for GDP"},
    "shares":          {"table_name": "T10110", "display": "Table 1.1.10", "description": "Percentage Shares of GDP"},
}

# ---------------------------------------------------------------------------
# BEA Table Configuration — GDI
# ---------------------------------------------------------------------------

GDI_TABLES = {
    "gdi_by_income":     {"table_name": "T11000", "display": "Table 1.10",   "description": "Gross Domestic Income by Type of Income"},
    "gdi_shares":        {"table_name": "T11100", "display": "Table 1.11",   "description": "Percentage Shares of Gross Domestic Income"},
    "national_income":   {"table_name": "T11200", "display": "Table 1.12",   "description": "National Income by Type of Income"},
}

# ---------------------------------------------------------------------------
# BEA Table Configuration — GDP/GDI Aggregates
# ---------------------------------------------------------------------------

AGGREGATE_TABLES = {
    "gdp_gdi_nominal":  {"table_name": "T11705", "display": "Table 1.17.5", "description": "GDP, GDI, and Other Major NIPA Aggregates"},
    "gdp_gdi_real":     {"table_name": "T11706", "display": "Table 1.17.6", "description": "Real GDP, Real GDI, and Other Major NIPA Aggregates (Chained $)"},
    "gdp_gdi_pct":      {"table_name": "T11701", "display": "Table 1.17.1", "description": "Percent Change in Real GDP, Real GDI, and Other Aggregates"},
}


# ---------------------------------------------------------------------------
# GDP Hierarchy — Table 1.1.5 (T10105)
# ---------------------------------------------------------------------------
# Confirmed line numbers and SeriesCodes from BEA API output.
# SeriesCode is the BEA internal code returned in API responses.
# These line numbers are shared across all T101xx tables.
# ---------------------------------------------------------------------------

GDP_HIERARCHY = {

    # === TOTAL GDP ===
    "gdp": {
        "name": "Gross Domestic Product",
        "level": 0,
        "line": 1,
        "series_code": "A191RC",
        "children": ["pce", "gross_private_domestic_investment", "net_exports", "government"],
    },

    # === C: PERSONAL CONSUMPTION EXPENDITURES ===
    "pce": {
        "name": "Personal Consumption Expenditures",
        "level": 1,
        "line": 2,
        "series_code": "DPCERC",
        "children": ["pce_goods", "pce_services"],
        "note": "Links to PCE detail tables (T20401–T20406) for full sub-component breakdown",
    },
    "pce_goods": {
        "name": "Goods",
        "level": 2,
        "line": 3,
        "series_code": "DGDSRC",
        "children": ["pce_durable_goods", "pce_nondurable_goods"],
    },
    "pce_durable_goods": {
        "name": "Durable Goods",
        "level": 3,
        "line": 4,
        "series_code": "DDURRC",
        "children": [],
    },
    "pce_nondurable_goods": {
        "name": "Nondurable Goods",
        "level": 3,
        "line": 5,
        "series_code": "DNDGRC",
        "children": [],
    },
    "pce_services": {
        "name": "Services",
        "level": 2,
        "line": 6,
        "series_code": "DSERRC",
        "children": [],
    },

    # === I: GROSS PRIVATE DOMESTIC INVESTMENT ===
    "gross_private_domestic_investment": {
        "name": "Gross Private Domestic Investment",
        "level": 1,
        "line": 7,
        "series_code": "A006RC",
        "children": ["fixed_investment", "change_in_private_inventories"],
    },
    "fixed_investment": {
        "name": "Fixed Investment",
        "level": 2,
        "line": 8,
        "series_code": "A007RC",
        "children": ["nonresidential", "residential"],
    },
    "nonresidential": {
        "name": "Nonresidential",
        "level": 3,
        "line": 9,
        "series_code": "A008RC",
        "children": ["structures", "equipment", "intellectual_property_products"],
    },
    "structures": {
        "name": "Structures",
        "level": 4,
        "line": 10,
        "series_code": "B009RC",
        "children": [],
    },
    "equipment": {
        "name": "Equipment",
        "level": 4,
        "line": 11,
        "series_code": "Y033RC",
        "children": [],
    },
    "intellectual_property_products": {
        "name": "Intellectual Property Products",
        "level": 4,
        "line": 12,
        "series_code": "Y001RC",
        "children": [],
    },
    "residential": {
        "name": "Residential",
        "level": 3,
        "line": 13,
        "series_code": "A011RC",
        "children": [],
    },
    "change_in_private_inventories": {
        "name": "Change in Private Inventories",
        "level": 2,
        "line": 14,
        "series_code": "A014RC",
        "children": [],
    },

    # === NX: NET EXPORTS ===
    "net_exports": {
        "name": "Net Exports of Goods and Services",
        "level": 1,
        "line": 15,
        "series_code": "A019RC",
        "children": ["exports", "imports"],
    },
    "exports": {
        "name": "Exports",
        "level": 2,
        "line": 16,
        "series_code": "B020RC",
        "children": ["exports_goods", "exports_services"],
    },
    "exports_goods": {
        "name": "Goods (Exports)",
        "level": 3,
        "line": 17,
        "series_code": "A253RC",
        "children": [],
    },
    "exports_services": {
        "name": "Services (Exports)",
        "level": 3,
        "line": 18,
        "series_code": "A646RC",
        "children": [],
    },
    "imports": {
        "name": "Imports",
        "level": 2,
        "line": 19,
        "series_code": "B021RC",
        "children": [],
    },
    "imports_goods": {
        "name": "Goods (Imports)",
        "level": 3,
        "line": 20,
        "series_code": "A255RC",
        "children": [],
    },
    "imports_services": {
        "name": "Services (Imports)",
        "level": 3,
        "line": 21,
        "series_code": "B656RC",
        "children": [],
    },

    # === G: GOVERNMENT ===
    "government": {
        "name": "Government Consumption Expenditures and Gross Investment",
        "level": 1,
        "line": 22,
        "series_code": "A822RC",
        "children": ["federal", "state_and_local"],
    },
    "federal": {
        "name": "Federal",
        "level": 2,
        "line": 23,
        "series_code": "A823RC",
        "children": ["national_defense", "nondefense"],
    },
    "national_defense": {
        "name": "National Defense",
        "level": 3,
        "line": 24,
        "series_code": "A824RC",
        "children": [],
    },
    "nondefense": {
        "name": "Nondefense",
        "level": 3,
        "line": 25,
        "series_code": "A825RC",
        "children": [],
    },
    "state_and_local": {
        "name": "State and Local",
        "level": 2,
        "line": 26,
        "series_code": "A829RC",
        "children": [],
    },
}

# Fix imports parent-child: imports has goods and services children
GDP_HIERARCHY["imports"]["children"] = ["imports_goods", "imports_services"]


# ---------------------------------------------------------------------------
# GDI Hierarchy — Table 1.10 (T11000)
# ---------------------------------------------------------------------------
# GDI = Compensation + Taxes on Production - Subsidies
#      + Net Operating Surplus + Consumption of Fixed Capital
#      + Statistical Discrepancy
#
# NOTE: Line numbers below follow the standard BEA Table 1.10 structure.
# SeriesCodes are the BEA internal codes. Validate against a live API pull
# as BEA occasionally renumbers lines in revised table vintages.
# ---------------------------------------------------------------------------

GDI_HIERARCHY = {

    # === TOTAL GDI ===
    "gdi": {
        "name": "Gross Domestic Income",
        "level": 0,
        "line": 1,
        "series_code": "A261RC",
        "children": [
            "compensation_of_employees",
            "taxes_on_production_and_imports",
            "less_subsidies",
            "net_operating_surplus",
            "consumption_of_fixed_capital",
            "statistical_discrepancy",
        ],
    },

    # === COMPENSATION OF EMPLOYEES ===
    "compensation_of_employees": {
        "name": "Compensation of Employees, Paid",
        "level": 1,
        "line": 2,
        "series_code": "A033RC",
        "children": ["wages_and_salaries", "supplements_to_wages_and_salaries"],
    },
    "wages_and_salaries": {
        "name": "Wages and Salaries",
        "level": 2,
        "line": 3,
        "series_code": "A034RC",
        "children": ["wages_government", "wages_other"],
    },
    "wages_government": {
        "name": "Government",
        "level": 3,
        "line": 4,
        "series_code": "A132RC",
        "children": [],
    },
    "wages_other": {
        "name": "Other",
        "level": 3,
        "line": 5,
        "series_code": "A133RC",
        "children": [],
    },
    "supplements_to_wages_and_salaries": {
        "name": "Supplements to Wages and Salaries",
        "level": 2,
        "line": 6,
        "series_code": "A038RC",
        "children": [
            "employer_contributions_pension_insurance",
            "employer_contributions_government_social_insurance",
        ],
    },
    "employer_contributions_pension_insurance": {
        "name": "Employer Contributions for Employee Pension and Insurance Funds",
        "level": 3,
        "line": 7,
        "series_code": "B040RC",
        "children": [],
    },
    "employer_contributions_government_social_insurance": {
        "name": "Employer Contributions for Government Social Insurance",
        "level": 3,
        "line": 8,
        "series_code": "A039RC",
        "children": [],
    },

    # === TAXES ON PRODUCTION AND IMPORTS ===
    "taxes_on_production_and_imports": {
        "name": "Taxes on Production and Imports",
        "level": 1,
        "line": 9,
        "series_code": "W054RC",
        "children": [],
    },

    # === LESS: SUBSIDIES ===
    "less_subsidies": {
        "name": "Less: Subsidies",
        "level": 1,
        "line": 10,
        "series_code": "A107RC",
        "children": [],
    },

    # === NET OPERATING SURPLUS ===
    "net_operating_surplus": {
        "name": "Net Operating Surplus",
        "level": 1,
        "line": 11,
        "series_code": "A445RC",
        "children": [
            "net_operating_surplus_private",
            "current_surplus_of_government_enterprises",
        ],
    },
    "net_operating_surplus_private": {
        "name": "Private Enterprises",
        "level": 2,
        "line": 12,
        "series_code": "W273RC",
        "children": [
            "proprietors_income",
            "rental_income_of_persons",
            "corporate_profits",
            "net_interest_and_misc_payments",
            "business_current_transfer_payments",
        ],
        "note": "Sub-items below are the income-type decomposition of private NOS",
    },
    "proprietors_income": {
        "name": "Proprietors' Income with IVA and CCAdj",
        "level": 3,
        "line": 13,
        "series_code": "A041RC",
        "children": ["proprietors_income_farm", "proprietors_income_nonfarm"],
    },
    "proprietors_income_farm": {
        "name": "Farm",
        "level": 4,
        "line": 14,
        "series_code": "B042RC",
        "children": [],
    },
    "proprietors_income_nonfarm": {
        "name": "Nonfarm",
        "level": 4,
        "line": 15,
        "series_code": "A043RC",
        "children": [],
    },
    "rental_income_of_persons": {
        "name": "Rental Income of Persons with CCAdj",
        "level": 3,
        "line": 16,
        "series_code": "A048RC",
        "children": [],
    },
    "corporate_profits": {
        "name": "Corporate Profits with IVA and CCAdj",
        "level": 3,
        "line": 17,
        "series_code": "A446RC",
        "children": [
            "corporate_profits_domestic",
            "corporate_profits_rest_of_world",
        ],
    },
    "corporate_profits_domestic": {
        "name": "Domestic Industries",
        "level": 4,
        "line": 18,
        "series_code": "W274RC",
        "children": [
            "corporate_profits_financial",
            "corporate_profits_nonfinancial",
        ],
    },
    "corporate_profits_financial": {
        "name": "Financial",
        "level": 5,
        "line": 19,
        "series_code": "A463RC",
        "children": [],
    },
    "corporate_profits_nonfinancial": {
        "name": "Nonfinancial",
        "level": 5,
        "line": 20,
        "series_code": "A464RC",
        "children": [],
    },
    "corporate_profits_rest_of_world": {
        "name": "Rest of the World",
        "level": 4,
        "line": 21,
        "series_code": "W275RC",
        "children": [],
    },
    "net_interest_and_misc_payments": {
        "name": "Net Interest and Miscellaneous Payments on Assets",
        "level": 3,
        "line": 22,
        "series_code": "W255RC",
        "children": [],
    },
    "business_current_transfer_payments": {
        "name": "Business Current Transfer Payments (Net)",
        "level": 3,
        "line": 23,
        "series_code": "A061RC",
        "children": [],
    },
    "current_surplus_of_government_enterprises": {
        "name": "Current Surplus of Government Enterprises",
        "level": 2,
        "line": 24,
        "series_code": "A108RC",
        "children": [],
    },

    # === CONSUMPTION OF FIXED CAPITAL ===
    "consumption_of_fixed_capital": {
        "name": "Consumption of Fixed Capital",
        "level": 1,
        "line": 25,
        "series_code": "A262RC",
        "children": ["cfc_private", "cfc_government"],
    },
    "cfc_private": {
        "name": "Private",
        "level": 2,
        "line": 26,
        "series_code": "Y702RC",
        "children": [],
    },
    "cfc_government": {
        "name": "Government",
        "level": 2,
        "line": 27,
        "series_code": "A918RC",
        "children": [],
    },

    # === STATISTICAL DISCREPANCY ===
    "statistical_discrepancy": {
        "name": "Statistical Discrepancy",
        "level": 1,
        "line": 28,
        "series_code": "A141RC",
        "children": [],
    },
}


# ---------------------------------------------------------------------------
# GDP/GDI Cross-Reference: Table 1.17.5 (T11705) Major Aggregates
# ---------------------------------------------------------------------------
# This table presents GDP, GDI, and derived aggregates side by side.
# Useful for computing the GDP-GDI average ("GDPplus" concept).
# ---------------------------------------------------------------------------

GDP_GDI_AGGREGATES = {
    "gdp_aggregate": {
        "name": "Gross Domestic Product",
        "table": "T11705",
        "line": 1,
        "series_code": "A191RC",
    },
    "gdi_aggregate": {
        "name": "Gross Domestic Income",
        "table": "T11705",
        "line": 25,
        "series_code": "A261RC",
    },
    "final_sales_domestic_purchasers": {
        "name": "Final Sales to Domestic Purchasers",
        "table": "T11705",
        "line": 21,
        "series_code": "A015RC",
    },
    "gross_domestic_purchases": {
        "name": "Gross Domestic Purchases",
        "table": "T11705",
        "line": 22,
        "series_code": "A018RC",
    },
    "gdp_gdi_average": {
        "name": "Average of GDP and GDI",
        "table": "T11705",
        "line": 27,
        "series_code": "A267RC",
        "note": "Arithmetic mean of GDP and GDI, increasingly used as a more stable measure",
    },
    "statistical_discrepancy_aggregate": {
        "name": "Statistical Discrepancy",
        "table": "T11705",
        "line": 28,
        "series_code": "A141RC",
    },
}


# ---------------------------------------------------------------------------
# BEA API Helpers
# ---------------------------------------------------------------------------

BEA_API_BASE_URL = "https://apps.bea.gov/api/data/"
BEA_FREQUENCY_OPTIONS = ["M", "Q", "A"]  # Monthly, Quarterly, Annual


def build_bea_request(
    table_name: str = "T10105",
    frequency: str = "Q",
    years: Optional[list] = None,
    api_key: str = "YOUR_API_KEY_HERE",
) -> dict:
    """
    Build BEA API request parameters.

    Parameters
    ----------
    table_name : str
        BEA table name (e.g., 'T10105' for nominal GDP, 'T11000' for GDI)
    frequency : str
        'M' (monthly), 'Q' (quarterly), or 'A' (annual).
        Note: GDP tables are typically Q or A only.
    years : list of int, optional
        Years to request. Defaults to [2023, 2024].
    api_key : str
        Your BEA API key.

    Returns
    -------
    dict
        Parameters ready for requests.get(url, params=...).
    """
    if years is None:
        years = [2023, 2024]

    year_str = ",".join(str(y) for y in years)

    params = {
        "UserID": api_key,
        "method": "GetData",
        "DatasetName": "NIPA",
        "TableName": table_name,
        "Frequency": frequency,
        "Year": year_str,
        "ResultFormat": "JSON",
    }

    return params


def parse_bea_response(response_json: dict) -> pd.DataFrame:
    """
    Parse a BEA API JSON response into a clean DataFrame.

    Parameters
    ----------
    response_json : dict
        The parsed JSON from a BEA API response.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with numeric LineNumber and DataValue columns.
    """
    data = response_json.get("BEAAPI", {}).get("Results", {}).get("Data", [])

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "LineNumber" in df.columns:
        df["LineNumber"] = pd.to_numeric(df["LineNumber"], errors="coerce")

    if "DataValue" in df.columns:
        df["DataValue"] = (
            df["DataValue"]
            .str.replace(",", "", regex=False)
            .replace("---", None)
        )
        df["DataValue"] = pd.to_numeric(df["DataValue"], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# DataFrame Builders
# ---------------------------------------------------------------------------

def _build_hierarchy_df(hierarchy: dict, table_family: dict) -> pd.DataFrame:
    """
    Convert a hierarchy dict into a flat DataFrame with BEA table identifiers.

    Parameters
    ----------
    hierarchy : dict
        One of GDP_HIERARCHY or GDI_HIERARCHY.
    table_family : dict
        The corresponding table config (GDP_TABLES or GDI_TABLES).

    Returns
    -------
    pd.DataFrame
    """
    # Build reverse parent lookup
    parent_map = {}
    for parent_key, parent_node in hierarchy.items():
        for child_key in parent_node.get("children", []):
            parent_map[child_key] = parent_key

    rows = []
    for key, node in hierarchy.items():
        row = {
            "key": key,
            "name": node["name"],
            "level": node["level"],
            "line": node["line"],
            "series_code": node.get("series_code"),
            "parent": parent_map.get(key, None),
            "is_leaf": len(node.get("children", [])) == 0,
        }

        # Add a column for each table in the family
        for measure_key, table_info in table_family.items():
            row[f"bea_{measure_key}"] = f"{table_info['table_name']}:L{node['line']}"

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def build_gdp_dataframe() -> pd.DataFrame:
    """Build a flat DataFrame of the GDP hierarchy with BEA table references."""
    return _build_hierarchy_df(GDP_HIERARCHY, GDP_TABLES)


def build_gdi_dataframe() -> pd.DataFrame:
    """Build a flat DataFrame of the GDI hierarchy with BEA table references."""
    return _build_hierarchy_df(GDI_HIERARCHY, GDI_TABLES)


def build_combined_dataframe() -> pd.DataFrame:
    """
    Build a combined DataFrame with both GDP and GDI components,
    tagged by report type.
    """
    gdp_df = build_gdp_dataframe()
    gdp_df["report"] = "GDP"
    gdp_df["primary_table"] = "T10105"

    gdi_df = build_gdi_dataframe()
    gdi_df["report"] = "GDI"
    gdi_df["primary_table"] = "T11000"

    # Keep only the common columns
    common_cols = ["report", "primary_table", "key", "name", "level", "line", "series_code", "parent", "is_leaf"]

    combined = pd.concat(
        [gdp_df[common_cols], gdi_df[common_cols]],
        ignore_index=True,
    )

    return combined


# ---------------------------------------------------------------------------
# Tree Utilities
# ---------------------------------------------------------------------------

def get_children(hierarchy: dict, key: str, recursive: bool = False) -> list:
    """Get child keys from a given hierarchy."""
    if key not in hierarchy:
        raise KeyError(f"Component '{key}' not found")

    direct_children = hierarchy[key].get("children", [])

    if not recursive:
        return direct_children

    all_descendants = []
    stack = list(direct_children)
    while stack:
        child = stack.pop(0)
        all_descendants.append(child)
        grandchildren = hierarchy.get(child, {}).get("children", [])
        stack.extend(grandchildren)

    return all_descendants


def get_path_to_root(hierarchy: dict, key: str) -> list:
    """Get path from a component up to the root."""
    parent_map = {}
    for parent_key, parent_node in hierarchy.items():
        for child_key in parent_node.get("children", []):
            parent_map[child_key] = parent_key

    path = [key]
    current = key
    while current in parent_map:
        current = parent_map[current]
        path.append(current)

    return path


def print_hierarchy_tree(hierarchy: dict, key: str = None, indent: int = 0) -> None:
    """Print a hierarchy as an indented tree."""
    if key is None:
        # Find root (level 0)
        for k, v in hierarchy.items():
            if v["level"] == 0:
                key = k
                break

    node = hierarchy.get(key, {})
    name = node.get("name", key)
    line = node.get("line", "?")
    series = node.get("series_code", "N/A")
    prefix = "  " * indent + ("├── " if indent > 0 else "")

    print(f"{prefix}{name}  [L{line} | {series}]")

    for child_key in node.get("children", []):
        print_hierarchy_tree(hierarchy, child_key, indent + 1)


# ---------------------------------------------------------------------------
# Main: Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 80)
    print("GDP HIERARCHY (Expenditure Approach) — Table 1.1.5 / T10105")
    print("=" * 80)
    print_hierarchy_tree(GDP_HIERARCHY)

    print("\n" + "=" * 80)
    print("GDI HIERARCHY (Income Approach) — Table 1.10 / T11000")
    print("=" * 80)
    print_hierarchy_tree(GDI_HIERARCHY)

    print("\n" + "=" * 80)
    print("GDP TABLES AVAILABLE")
    print("=" * 80)
    for measure, info in GDP_TABLES.items():
        print(f"  {measure:20s}  {info['table_name']}  ({info['display']})  {info['description']}")

    print("\n" + "=" * 80)
    print("GDI TABLES AVAILABLE")
    print("=" * 80)
    for measure, info in GDI_TABLES.items():
        print(f"  {measure:20s}  {info['table_name']}  ({info['display']})  {info['description']}")

    print("\n" + "=" * 80)
    print("COMBINED DATAFRAME")
    print("=" * 80)
    combined = build_combined_dataframe()
    print(combined[["report", "key", "name", "level", "line", "series_code"]].to_string(index=False))

    print(f"\nGDP components: {len(GDP_HIERARCHY)}")
    print(f"GDI components: {len(GDI_HIERARCHY)}")

    print("\n" + "=" * 80)
    print("EXAMPLE BEA API REQUESTS")
    print("=" * 80)
    print("\nNominal GDP (Quarterly, 2023-2024):")
    for k, v in build_bea_request("T10105", "Q", [2023, 2024]).items():
        print(f"  {k}: {v}")

    print("\nGDI by Income (Quarterly, 2023-2024):")
    for k, v in build_bea_request("T11000", "Q", [2023, 2024]).items():
        print(f"  {k}: {v}")

    print("\nGDP/GDI Aggregates (Quarterly, 2023-2024):")
    for k, v in build_bea_request("T11705", "Q", [2023, 2024]).items():
        print(f"  {k}: {v}")
