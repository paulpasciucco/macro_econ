"""
PCE (Personal Consumption Expenditures) Hierarchy — BEA NIPA Edition
=====================================================================

Complete mapping of the PCE component hierarchy using BEA NIPA table
and line number identifiers. This gives full coverage across all
components and all measure types (nominal, real, price index, percent
change, contributions).

BEA NIPA Tables (all share the same line-number structure):
    - T20401  (Table 2.4.1)  : Percent Change from Preceding Period
    - T20403  (Table 2.4.3)  : Quantity Indexes
    - T20404  (Table 2.4.4)  : Price Indexes
    - T20405  (Table 2.4.5)  : Nominal (Current-Dollar) Levels
    - T20406  (Table 2.4.6)  : Real (Chained 2017 Dollar) Levels

Usage:
    from pce_hierarchy_bea import (
        PCE_HIERARCHY,
        build_hierarchy_dataframe,
        build_bea_request,
        get_children,
        get_path_to_root,
        print_hierarchy_tree,
    )

    # Flat DataFrame of all components
    df = build_hierarchy_dataframe()

    # Build a BEA API request for nominal PCE (monthly, 2023-2024)
    params = build_bea_request(
        table="nominal",
        frequency="M",
        years=[2023, 2024],
        api_key="YOUR_KEY",
    )

BEA API Registration:
    Get a free API key at https://apps.bea.gov/api/signup/
"""

import pandas as pd
from typing import Optional


# ---------------------------------------------------------------------------
# BEA Table Configuration
# ---------------------------------------------------------------------------
# All PCE tables share the same line-number scheme. To pull a specific
# component for a specific measure, you need: TableName + LineNumber.
# ---------------------------------------------------------------------------

BEA_TABLES = {
    "pct_change":    {"table_name": "T20401", "display": "Table 2.4.1", "description": "Percent Change from Preceding Period in Real PCE"},
    "contributions": {"table_name": "T20402", "display": "Table 2.4.2", "description": "Contributions to Percent Change in Real PCE"},
    "quantity_index": {"table_name": "T20403", "display": "Table 2.4.3", "description": "Real PCE Quantity Indexes"},
    "price_index":   {"table_name": "T20404", "display": "Table 2.4.4", "description": "Price Indexes for PCE"},
    "nominal":       {"table_name": "T20405", "display": "Table 2.4.5", "description": "PCE, Current-Dollar"},
    "real":          {"table_name": "T20406", "display": "Table 2.4.6", "description": "PCE, Chained (2017) Dollars"},
}

BEA_API_BASE_URL = "https://apps.bea.gov/api/data/"
BEA_FREQUENCY_OPTIONS = ["M", "Q", "A"]  # Monthly, Quarterly, Annual


# ---------------------------------------------------------------------------
# PCE Hierarchy Definition
# ---------------------------------------------------------------------------
# Each node contains:
#   - name:      Human-readable BEA component name
#   - level:     Depth in the hierarchy (0 = total PCE)
#   - line:      BEA NIPA line number (shared across all 2.4.x tables)
#   - children:  List of child component keys
#
# Line numbers are from the BEA NIPA Table 2.4.5U structure.
# These same line numbers apply to Tables 2.4.1 through 2.4.6.
# ---------------------------------------------------------------------------

PCE_HIERARCHY = {

    # =======================================================================
    # TOTAL PCE
    # =======================================================================
    "pce_total": {
        "name": "Personal Consumption Expenditures",
        "level": 0,
        "line": 1,
        "children": ["goods", "services"],
    },

    # =======================================================================
    # GOODS
    # =======================================================================
    "goods": {
        "name": "Goods",
        "level": 1,
        "line": 2,
        "children": ["durable_goods", "nondurable_goods"],
    },

    # --- DURABLE GOODS ---
    "durable_goods": {
        "name": "Durable Goods",
        "level": 2,
        "line": 3,
        "children": [
            "motor_vehicles_and_parts",
            "furnishings_and_durable_household_equipment",
            "recreational_goods_and_vehicles",
            "other_durable_goods",
        ],
    },

    # Motor Vehicles and Parts
    "motor_vehicles_and_parts": {
        "name": "Motor Vehicles and Parts",
        "level": 3,
        "line": 4,
        "children": [
            "new_motor_vehicles",
            "net_used_motor_vehicles",
            "motor_vehicle_parts_and_accessories",
        ],
    },
    "new_motor_vehicles": {
        "name": "New Motor Vehicles",
        "level": 4,
        "line": 5,
        "children": [],
    },
    "net_used_motor_vehicles": {
        "name": "Net Purchases of Used Motor Vehicles",
        "level": 4,
        "line": 6,
        "children": [],
    },
    "motor_vehicle_parts_and_accessories": {
        "name": "Motor Vehicle Parts and Accessories",
        "level": 4,
        "line": 7,
        "children": [],
    },

    # Furnishings and Durable Household Equipment
    "furnishings_and_durable_household_equipment": {
        "name": "Furnishings and Durable Household Equipment",
        "level": 3,
        "line": 8,
        "children": [
            "furniture_and_furnishings",
            "household_appliances",
            "glassware_tableware_household_utensils",
            "tools_hardware_outdoor",
        ],
    },
    "furniture_and_furnishings": {
        "name": "Furniture and Furnishings",
        "level": 4,
        "line": 9,
        "children": [],
    },
    "household_appliances": {
        "name": "Household Appliances",
        "level": 4,
        "line": 10,
        "children": [],
    },
    "glassware_tableware_household_utensils": {
        "name": "Glassware, Tableware, and Household Utensils",
        "level": 4,
        "line": 11,
        "children": [],
    },
    "tools_hardware_outdoor": {
        "name": "Tools and Equipment for House and Garden",
        "level": 4,
        "line": 12,
        "children": [],
    },

    # Recreational Goods and Vehicles
    "recreational_goods_and_vehicles": {
        "name": "Recreational Goods and Vehicles",
        "level": 3,
        "line": 13,
        "children": [
            "video_audio_photographic_info_processing",
            "sporting_equipment_supplies_guns",
            "sports_recreational_vehicles",
            "recreational_books",
            "musical_instruments",
        ],
    },
    "video_audio_photographic_info_processing": {
        "name": "Video, Audio, Photographic, and Information Processing Equipment and Media",
        "level": 4,
        "line": 14,
        "children": [],
    },
    "sporting_equipment_supplies_guns": {
        "name": "Sporting Equipment, Supplies, Guns, and Ammunition",
        "level": 4,
        "line": 15,
        "children": [],
    },
    "sports_recreational_vehicles": {
        "name": "Sports and Recreational Vehicles",
        "level": 4,
        "line": 16,
        "children": [],
    },
    "recreational_books": {
        "name": "Recreational Books",
        "level": 4,
        "line": 17,
        "children": [],
    },
    "musical_instruments": {
        "name": "Musical Instruments",
        "level": 4,
        "line": 18,
        "children": [],
    },

    # Other Durable Goods
    "other_durable_goods": {
        "name": "Other Durable Goods",
        "level": 3,
        "line": 19,
        "children": [
            "jewelry_and_watches",
            "therapeutic_appliances",
            "educational_books",
            "luggage_and_similar",
            "telephone_and_fax_equipment",
        ],
    },
    "jewelry_and_watches": {
        "name": "Jewelry and Watches",
        "level": 4,
        "line": 20,
        "children": [],
    },
    "therapeutic_appliances": {
        "name": "Therapeutic Appliances and Equipment",
        "level": 4,
        "line": 21,
        "children": [],
    },
    "educational_books": {
        "name": "Educational Books",
        "level": 4,
        "line": 22,
        "children": [],
    },
    "luggage_and_similar": {
        "name": "Luggage and Similar Personal Items",
        "level": 4,
        "line": 23,
        "children": [],
    },
    "telephone_and_fax_equipment": {
        "name": "Telephone and Facsimile Equipment",
        "level": 4,
        "line": 24,
        "children": [],
    },

    # --- NONDURABLE GOODS ---
    "nondurable_goods": {
        "name": "Nondurable Goods",
        "level": 2,
        "line": 25,
        "children": [
            "food_and_beverages_off_premises",
            "clothing_and_footwear",
            "gasoline_and_other_energy_goods",
            "other_nondurable_goods",
        ],
    },

    # Food and Beverages (Off-Premises)
    "food_and_beverages_off_premises": {
        "name": "Food and Beverages Purchased for Off-Premises Consumption",
        "level": 3,
        "line": 26,
        "children": [
            "food_nonalcoholic_off_premises",
            "alcohol_off_premises",
        ],
    },
    "food_nonalcoholic_off_premises": {
        "name": "Food and Nonalcoholic Beverages Purchased for Off-Premises Consumption",
        "level": 4,
        "line": 27,
        "children": [],
    },
    "alcohol_off_premises": {
        "name": "Alcoholic Beverages Purchased for Off-Premises Consumption",
        "level": 4,
        "line": 28,
        "children": [],
    },

    # Clothing and Footwear
    "clothing_and_footwear": {
        "name": "Clothing and Footwear",
        "level": 3,
        "line": 29,
        "children": ["garments", "footwear"],
    },
    "garments": {
        "name": "Garments",
        "level": 4,
        "line": 30,
        "children": ["women_and_girls_clothing", "men_and_boys_clothing", "children_and_infant_clothing", "other_clothing"],
    },
    "women_and_girls_clothing": {
        "name": "Women's and Girls' Clothing",
        "level": 5,
        "line": 31,
        "children": [],
    },
    "men_and_boys_clothing": {
        "name": "Men's and Boys' Clothing",
        "level": 5,
        "line": 32,
        "children": [],
    },
    "children_and_infant_clothing": {
        "name": "Children's and Infants' Clothing",
        "level": 5,
        "line": 33,
        "children": [],
    },
    "other_clothing": {
        "name": "Other Clothing",
        "level": 5,
        "line": 34,
        "children": [],
    },
    "footwear": {
        "name": "Footwear",
        "level": 4,
        "line": 35,
        "children": [],
    },

    # Gasoline and Other Energy Goods
    "gasoline_and_other_energy_goods": {
        "name": "Gasoline and Other Energy Goods",
        "level": 3,
        "line": 36,
        "children": [
            "motor_vehicle_fuels_lubricants",
            "fuel_oil_other_fuels",
        ],
    },
    "motor_vehicle_fuels_lubricants": {
        "name": "Motor Vehicle Fuels, Lubricants, and Fluids",
        "level": 4,
        "line": 37,
        "children": [],
    },
    "fuel_oil_other_fuels": {
        "name": "Fuel Oil and Other Fuels",
        "level": 4,
        "line": 38,
        "children": [],
    },

    # Other Nondurable Goods
    "other_nondurable_goods": {
        "name": "Other Nondurable Goods",
        "level": 3,
        "line": 39,
        "children": [
            "pharmaceutical_products",
            "recreational_items",
            "household_supplies",
            "personal_care_products",
            "tobacco",
            "magazines_newspapers_stationery",
            "net_foreign_travel_goods",
        ],
    },
    "pharmaceutical_products": {
        "name": "Pharmaceutical and Other Medical Products",
        "level": 4,
        "line": 40,
        "children": [],
    },
    "recreational_items": {
        "name": "Recreational Items",
        "level": 4,
        "line": 41,
        "children": [],
    },
    "household_supplies": {
        "name": "Household Supplies",
        "level": 4,
        "line": 42,
        "children": [],
    },
    "personal_care_products": {
        "name": "Personal Care Products",
        "level": 4,
        "line": 43,
        "children": [],
    },
    "tobacco": {
        "name": "Tobacco",
        "level": 4,
        "line": 44,
        "children": [],
    },
    "magazines_newspapers_stationery": {
        "name": "Magazines, Newspapers, and Stationery",
        "level": 4,
        "line": 45,
        "children": [],
    },
    "net_foreign_travel_goods": {
        "name": "Net Foreign Travel (Goods)",
        "level": 4,
        "line": 46,
        "children": ["expenditures_by_us_residents_abroad_goods", "less_expenditures_by_foreign_residents_goods"],
    },
    "expenditures_by_us_residents_abroad_goods": {
        "name": "Less: Expenditures Abroad by U.S. Residents (Goods)",
        "level": 5,
        "line": 47,
        "children": [],
    },
    "less_expenditures_by_foreign_residents_goods": {
        "name": "Less: Expenditures in U.S. by Foreign Residents (Goods)",
        "level": 5,
        "line": 48,
        "children": [],
    },

    # =======================================================================
    # SERVICES
    # =======================================================================
    "services": {
        "name": "Services",
        "level": 1,
        "line": 49,
        "children": [
            "household_consumption_expenditures_services",
            "final_consumption_expenditures_nonprofit",
        ],
    },

    # Household Consumption Expenditures (Services)
    "household_consumption_expenditures_services": {
        "name": "Household Consumption Expenditures (Services)",
        "level": 2,
        "line": 50,
        "children": [
            "housing_and_utilities",
            "health_care",
            "transportation_services",
            "recreation_services",
            "food_services_and_accommodations",
            "financial_services_and_insurance",
            "other_services",
        ],
    },

    # Housing and Utilities
    "housing_and_utilities": {
        "name": "Housing and Utilities",
        "level": 3,
        "line": 51,
        "children": ["housing", "utilities"],
    },
    "housing": {
        "name": "Housing",
        "level": 4,
        "line": 52,
        "children": [
            "rental_of_tenant_occupied",
            "imputed_rental_of_owner_occupied",
            "rental_value_farm_dwellings",
            "group_housing",
        ],
    },
    "rental_of_tenant_occupied": {
        "name": "Rental of Tenant-Occupied Nonfarm Housing",
        "level": 5,
        "line": 53,
        "children": [],
    },
    "imputed_rental_of_owner_occupied": {
        "name": "Imputed Rental of Owner-Occupied Nonfarm Housing",
        "level": 5,
        "line": 54,
        "children": [],
    },
    "rental_value_farm_dwellings": {
        "name": "Rental Value of Farm Dwellings",
        "level": 5,
        "line": 55,
        "children": [],
    },
    "group_housing": {
        "name": "Group Housing",
        "level": 5,
        "line": 56,
        "children": [],
    },
    "utilities": {
        "name": "Household Utilities",
        "level": 4,
        "line": 57,
        "children": [
            "water_supply_sanitation",
            "electricity",
            "natural_gas",
            "telephone_and_internet_services",
        ],
    },
    "water_supply_sanitation": {
        "name": "Water Supply and Sanitation",
        "level": 5,
        "line": 58,
        "children": [],
    },
    "electricity": {
        "name": "Electricity",
        "level": 5,
        "line": 59,
        "children": [],
    },
    "natural_gas": {
        "name": "Natural Gas",
        "level": 5,
        "line": 60,
        "children": [],
    },
    "telephone_and_internet_services": {
        "name": "Telecommunication Services",
        "level": 5,
        "line": 61,
        "children": [],
    },

    # Health Care
    "health_care": {
        "name": "Health Care",
        "level": 3,
        "line": 62,
        "children": [
            "outpatient_services",
            "hospital_and_nursing_home_services",
            "health_insurance",
        ],
    },
    "outpatient_services": {
        "name": "Outpatient Services",
        "level": 4,
        "line": 63,
        "children": [
            "physician_services",
            "dental_services",
            "paramedical_services",
        ],
    },
    "physician_services": {
        "name": "Physician Services",
        "level": 5,
        "line": 64,
        "children": [],
    },
    "dental_services": {
        "name": "Dental Services",
        "level": 5,
        "line": 65,
        "children": [],
    },
    "paramedical_services": {
        "name": "Paramedical Services",
        "level": 5,
        "line": 66,
        "children": [],
    },
    "hospital_and_nursing_home_services": {
        "name": "Hospital and Nursing Home Services",
        "level": 4,
        "line": 67,
        "children": ["hospitals", "nursing_homes"],
    },
    "hospitals": {
        "name": "Hospitals",
        "level": 5,
        "line": 68,
        "children": [],
    },
    "nursing_homes": {
        "name": "Nursing Homes",
        "level": 5,
        "line": 69,
        "children": [],
    },
    "health_insurance": {
        "name": "Health Insurance",
        "level": 4,
        "line": 70,
        "children": [],
    },

    # Transportation Services
    "transportation_services": {
        "name": "Transportation Services",
        "level": 3,
        "line": 71,
        "children": [
            "motor_vehicle_maintenance_and_repair",
            "other_motor_vehicle_services",
            "public_transportation",
        ],
    },
    "motor_vehicle_maintenance_and_repair": {
        "name": "Motor Vehicle Maintenance and Repair",
        "level": 4,
        "line": 72,
        "children": [],
    },
    "other_motor_vehicle_services": {
        "name": "Other Motor Vehicle Services",
        "level": 4,
        "line": 73,
        "children": [],
    },
    "public_transportation": {
        "name": "Public Transportation",
        "level": 4,
        "line": 74,
        "children": ["ground_transportation", "air_transportation", "water_transportation"],
    },
    "ground_transportation": {
        "name": "Ground Transportation",
        "level": 5,
        "line": 75,
        "children": [],
    },
    "air_transportation": {
        "name": "Air Transportation",
        "level": 5,
        "line": 76,
        "children": [],
    },
    "water_transportation": {
        "name": "Water Transportation",
        "level": 5,
        "line": 77,
        "children": [],
    },

    # Recreation Services
    "recreation_services": {
        "name": "Recreation Services",
        "level": 3,
        "line": 78,
        "children": [
            "membership_clubs_participant_sports",
            "amusements",
            "audio_video_photo_info_processing_services",
            "gambling",
            "other_recreational_services",
        ],
    },
    "membership_clubs_participant_sports": {
        "name": "Membership Clubs, Sports Centers, Parks, Theaters, and Museums",
        "level": 4,
        "line": 79,
        "children": [],
    },
    "amusements": {
        "name": "Audio-Video, Photographic, and Information Processing Equipment Services",
        "level": 4,
        "line": 80,
        "children": [],
    },
    "audio_video_photo_info_processing_services": {
        "name": "Cable, Satellite, and Other Live Television Services",
        "level": 4,
        "line": 81,
        "children": [],
    },
    "gambling": {
        "name": "Gambling",
        "level": 4,
        "line": 82,
        "children": [],
    },
    "other_recreational_services": {
        "name": "Other Recreational Services",
        "level": 4,
        "line": 83,
        "children": [],
    },

    # Food Services and Accommodations
    "food_services_and_accommodations": {
        "name": "Food Services and Accommodations",
        "level": 3,
        "line": 84,
        "children": [
            "food_services",
            "accommodations",
        ],
    },
    "food_services": {
        "name": "Food Services",
        "level": 4,
        "line": 85,
        "children": ["purchased_meals_and_beverages", "food_furnished_to_employees"],
    },
    "purchased_meals_and_beverages": {
        "name": "Purchased Meals and Beverages",
        "level": 5,
        "line": 86,
        "children": [],
    },
    "food_furnished_to_employees": {
        "name": "Food Furnished to Employees (Including Military)",
        "level": 5,
        "line": 87,
        "children": [],
    },
    "accommodations": {
        "name": "Accommodations",
        "level": 4,
        "line": 88,
        "children": [],
    },

    # Financial Services and Insurance
    "financial_services_and_insurance": {
        "name": "Financial Services and Insurance",
        "level": 3,
        "line": 89,
        "children": [
            "financial_services",
            "insurance",
        ],
    },
    "financial_services": {
        "name": "Financial Services",
        "level": 4,
        "line": 90,
        "children": [],
    },
    "insurance": {
        "name": "Insurance",
        "level": 4,
        "line": 91,
        "children": ["life_insurance", "net_household_insurance", "net_health_insurance", "net_motor_vehicle_insurance"],
    },
    "life_insurance": {
        "name": "Life Insurance",
        "level": 5,
        "line": 92,
        "children": [],
    },
    "net_household_insurance": {
        "name": "Net Household Insurance",
        "level": 5,
        "line": 93,
        "children": [],
    },
    "net_health_insurance": {
        "name": "Net Health Insurance",
        "level": 5,
        "line": 94,
        "children": [],
    },
    "net_motor_vehicle_insurance": {
        "name": "Net Motor Vehicle and Other Transportation Insurance",
        "level": 5,
        "line": 95,
        "children": [],
    },

    # Other Services
    "other_services": {
        "name": "Other Services",
        "level": 3,
        "line": 96,
        "children": [
            "communication_services",
            "education_services",
            "professional_and_other_services",
            "personal_care_and_clothing_services",
            "social_services_and_religious_activities",
            "household_maintenance",
            "net_foreign_travel_services",
        ],
    },
    "communication_services": {
        "name": "Communication",
        "level": 4,
        "line": 97,
        "children": ["postal_and_delivery", "internet_access"],
    },
    "postal_and_delivery": {
        "name": "Postal and Delivery Services",
        "level": 5,
        "line": 98,
        "children": [],
    },
    "internet_access": {
        "name": "Internet Access",
        "level": 5,
        "line": 99,
        "children": [],
    },
    "education_services": {
        "name": "Education Services",
        "level": 4,
        "line": 100,
        "children": ["higher_education", "nursery_elementary_secondary", "commercial_vocational_schools"],
    },
    "higher_education": {
        "name": "Higher Education",
        "level": 5,
        "line": 101,
        "children": [],
    },
    "nursery_elementary_secondary": {
        "name": "Nursery, Elementary, and Secondary Schools",
        "level": 5,
        "line": 102,
        "children": [],
    },
    "commercial_vocational_schools": {
        "name": "Commercial and Vocational Schools",
        "level": 5,
        "line": 103,
        "children": [],
    },
    "professional_and_other_services": {
        "name": "Professional and Other Services",
        "level": 4,
        "line": 104,
        "children": ["legal_services", "accounting_and_tax_prep", "miscellaneous_professional_services"],
    },
    "legal_services": {
        "name": "Legal Services",
        "level": 5,
        "line": 105,
        "children": [],
    },
    "accounting_and_tax_prep": {
        "name": "Accounting and Tax Return Preparation Services",
        "level": 5,
        "line": 106,
        "children": [],
    },
    "miscellaneous_professional_services": {
        "name": "Miscellaneous Professional Services",
        "level": 5,
        "line": 107,
        "children": [],
    },
    "personal_care_and_clothing_services": {
        "name": "Personal Care and Clothing Services",
        "level": 4,
        "line": 108,
        "children": [],
    },
    "social_services_and_religious_activities": {
        "name": "Social Services and Religious Activities",
        "level": 4,
        "line": 109,
        "children": ["child_care", "social_assistance", "religious_and_welfare_activities"],
    },
    "child_care": {
        "name": "Child Care",
        "level": 5,
        "line": 110,
        "children": [],
    },
    "social_assistance": {
        "name": "Social Assistance",
        "level": 5,
        "line": 111,
        "children": [],
    },
    "religious_and_welfare_activities": {
        "name": "Religious and Welfare Activities",
        "level": 5,
        "line": 112,
        "children": [],
    },
    "household_maintenance": {
        "name": "Household Maintenance",
        "level": 4,
        "line": 113,
        "children": [],
    },
    "net_foreign_travel_services": {
        "name": "Net Foreign Travel (Services)",
        "level": 4,
        "line": 114,
        "children": [
            "expenditures_by_us_residents_abroad_services",
            "less_expenditures_by_foreign_residents_services",
        ],
    },
    "expenditures_by_us_residents_abroad_services": {
        "name": "Expenditures Abroad by U.S. Residents (Services)",
        "level": 5,
        "line": 115,
        "children": [],
    },
    "less_expenditures_by_foreign_residents_services": {
        "name": "Less: Expenditures in U.S. by Foreign Residents (Services)",
        "level": 5,
        "line": 116,
        "children": [],
    },

    # Final Consumption Expenditures of NPISHs
    "final_consumption_expenditures_nonprofit": {
        "name": "Final Consumption Expenditures of Nonprofit Institutions Serving Households (NPISHs)",
        "level": 2,
        "line": 117,
        "children": [
            "gross_output_of_nonprofits",
            "less_receipts_from_sales_nonprofits",
        ],
    },
    "gross_output_of_nonprofits": {
        "name": "Gross Output of Nonprofit Institutions",
        "level": 3,
        "line": 118,
        "children": [],
    },
    "less_receipts_from_sales_nonprofits": {
        "name": "Less: Receipts from Sales of Goods and Services by Nonprofit Institutions",
        "level": 3,
        "line": 119,
        "children": [],
    },
}


# ---------------------------------------------------------------------------
# Key Derived / Analytical Series
# ---------------------------------------------------------------------------
# These are commonly used aggregations for inflation analysis that either
# correspond to specific BEA series or need to be computed from components.
# ---------------------------------------------------------------------------

PCE_ANALYTICAL_AGGREGATES = {
    "pce_core_ex_food_energy": {
        "name": "PCE Excluding Food and Energy (Core PCE)",
        "description": "Headline minus food and energy components",
        "note": "Not a single BEA line. Compute by subtracting food + energy from total.",
        "subtract_lines": {
            "food": [26, 85],       # Food off-premises + Food services
            "energy": [36, 59, 60, 38],  # Gas/energy goods + electricity + natural gas + fuel oil
        },
    },
    "pce_supercore": {
        "name": "PCE Services Excluding Housing (Supercore)",
        "description": "Core services measure that strips out sticky housing component",
        "note": "Compute from services (line 49) minus housing (line 52).",
        "base_line": 49,
        "subtract_lines": [52],
    },
    "pce_goods_core": {
        "name": "Core Goods (Goods Ex Food and Energy)",
        "description": "Goods minus food off-premises and gasoline/energy goods",
        "base_line": 2,
        "subtract_lines": [26, 36],
    },
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def build_hierarchy_dataframe() -> pd.DataFrame:
    """
    Convert PCE_HIERARCHY into a flat pandas DataFrame.

    Returns a DataFrame with one row per component, including:
        key, name, level, line, parent, is_leaf, num_children,
        and pre-built identifiers for each BEA table.
    """
    # Build reverse parent lookup
    parent_map = {}
    for parent_key, parent_node in PCE_HIERARCHY.items():
        for child_key in parent_node.get("children", []):
            parent_map[child_key] = parent_key

    rows = []
    for key, node in PCE_HIERARCHY.items():
        row = {
            "key": key,
            "name": node["name"],
            "level": node["level"],
            "line": node["line"],
            "parent": parent_map.get(key, None),
            "is_leaf": len(node.get("children", [])) == 0,
            "num_children": len(node.get("children", [])),
        }

        # Add a column for each BEA table showing the table + line combo
        for measure_key, table_info in BEA_TABLES.items():
            row[f"bea_{measure_key}"] = f"{table_info['table_name']}:L{node['line']}"

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def build_bea_request(
    table: str = "nominal",
    frequency: str = "M",
    years: Optional[list] = None,
    api_key: str = "YOUR_API_KEY_HERE",
) -> dict:
    """
    Build a BEA API request parameters dict.

    Parameters
    ----------
    table : str
        One of: 'nominal', 'real', 'price_index', 'pct_change',
        'quantity_index', 'contributions'
    frequency : str
        'M' (monthly), 'Q' (quarterly), or 'A' (annual)
    years : list of int, optional
        Years to request. Defaults to [2023, 2024].
    api_key : str
        Your BEA API key.

    Returns
    -------
    dict
        Parameters ready for requests.get(url, params=...).

    Example
    -------
    >>> params = build_bea_request("price_index", "M", [2023, 2024], "MY_KEY")
    >>> import requests
    >>> response = requests.get("https://apps.bea.gov/api/data/", params=params)
    """
    if table not in BEA_TABLES:
        raise ValueError(
            f"table must be one of {list(BEA_TABLES.keys())}, got '{table}'"
        )

    if frequency not in BEA_FREQUENCY_OPTIONS:
        raise ValueError(
            f"frequency must be one of {BEA_FREQUENCY_OPTIONS}, got '{frequency}'"
        )

    if years is None:
        years = [2023, 2024]

    year_str = ",".join(str(y) for y in years)
    table_name = BEA_TABLES[table]["table_name"]

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
        Columns: TimePeriod, LineNumber, LineDescription, DataValue, etc.
    """
    data = response_json.get("BEAAPI", {}).get("Results", {}).get("Data", [])

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Clean up data types
    if "LineNumber" in df.columns:
        df["LineNumber"] = pd.to_numeric(df["LineNumber"], errors="coerce")

    if "DataValue" in df.columns:
        # BEA uses commas in numbers and occasionally "---" for missing
        df["DataValue"] = (
            df["DataValue"]
            .str.replace(",", "", regex=False)
            .replace("---", None)
        )
        df["DataValue"] = pd.to_numeric(df["DataValue"], errors="coerce")

    return df


def merge_bea_with_hierarchy(bea_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge a parsed BEA DataFrame with the PCE hierarchy metadata.

    Parameters
    ----------
    bea_df : pd.DataFrame
        Output from parse_bea_response(), must have a 'LineNumber' column.

    Returns
    -------
    pd.DataFrame
        The BEA data enriched with hierarchy key, level, and parent info.
    """
    hierarchy_df = build_hierarchy_dataframe()

    merged = bea_df.merge(
        hierarchy_df[["key", "name", "level", "line", "parent", "is_leaf"]],
        left_on="LineNumber",
        right_on="line",
        how="left",
        suffixes=("_bea", "_hierarchy"),
    )

    return merged


def get_lines_for_level(level: int) -> list:
    """
    Get all BEA line numbers at a specific hierarchy level.

    Parameters
    ----------
    level : int
        Hierarchy level (0=total, 1=goods/services, 2=durables/nondurables, etc.)

    Returns
    -------
    list of int
        BEA line numbers at that level.
    """
    lines = []
    for key, node in PCE_HIERARCHY.items():
        if node["level"] == level:
            lines.append(node["line"])
    return sorted(lines)


def get_children(key: str, recursive: bool = False) -> list:
    """
    Get child component keys for a given PCE component.

    Parameters
    ----------
    key : str
        The component key (e.g., 'durable_goods')
    recursive : bool
        If True, return all descendants (not just direct children)

    Returns
    -------
    list of str
        Child component keys.
    """
    if key not in PCE_HIERARCHY:
        raise KeyError(f"Component '{key}' not found in PCE_HIERARCHY")

    direct_children = PCE_HIERARCHY[key].get("children", [])

    if not recursive:
        return direct_children

    all_descendants = []
    stack = list(direct_children)
    while stack:
        child = stack.pop(0)
        all_descendants.append(child)
        grandchildren = PCE_HIERARCHY.get(child, {}).get("children", [])
        stack.extend(grandchildren)

    return all_descendants


def get_path_to_root(key: str) -> list:
    """
    Get the path from a component up to the PCE total root.

    Parameters
    ----------
    key : str
        A component key (e.g., 'air_transportation')

    Returns
    -------
    list of str
        Keys from the given component up to 'pce_total'.
    """
    parent_map = {}
    for parent_key, parent_node in PCE_HIERARCHY.items():
        for child_key in parent_node.get("children", []):
            parent_map[child_key] = parent_key

    path = [key]
    current = key
    while current in parent_map:
        current = parent_map[current]
        path.append(current)

    return path


def get_line_lookup() -> dict:
    """
    Build a line_number -> key lookup dict.

    Returns
    -------
    dict
        Mapping of BEA line number (int) to hierarchy key (str).
    """
    return {node["line"]: key for key, node in PCE_HIERARCHY.items()}


def print_hierarchy_tree(key: str = "pce_total", indent: int = 0) -> None:
    """
    Print the PCE hierarchy as an indented tree.

    Parameters
    ----------
    key : str
        Starting node key (default: 'pce_total')
    indent : int
        Current indentation level (for recursion)
    """
    node = PCE_HIERARCHY.get(key, {})
    name = node.get("name", key)
    line = node.get("line", "?")
    prefix = "  " * indent + ("├── " if indent > 0 else "")

    print(f"{prefix}{name}  [Line {line}]")

    for child_key in node.get("children", []):
        print_hierarchy_tree(child_key, indent + 1)


# ---------------------------------------------------------------------------
# Main: Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 80)
    print("PCE HIERARCHY TREE (BEA Line Numbers)")
    print("=" * 80)
    print_hierarchy_tree()

    print("\n" + "=" * 80)
    print("BEA TABLES AVAILABLE")
    print("=" * 80)
    for measure, info in BEA_TABLES.items():
        print(f"  {measure:20s}  {info['table_name']}  ({info['display']})  {info['description']}")

    print("\n" + "=" * 80)
    print("HIERARCHY DATAFRAME (first 20 rows)")
    print("=" * 80)
    df = build_hierarchy_dataframe()
    cols = ["key", "name", "level", "line", "parent", "bea_nominal", "bea_price_index"]
    print(df[cols].head(20).to_string(index=False))

    print("\n" + "=" * 80)
    print("EXAMPLE BEA API REQUEST (Monthly Price Index, 2023-2024)")
    print("=" * 80)
    params = build_bea_request("price_index", "M", [2023, 2024])
    for k, v in params.items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 80)
    print("ALL LEVEL-3 COMPONENTS (for mid-level decomposition)")
    print("=" * 80)
    level_3_lines = get_lines_for_level(3)
    for line_num in level_3_lines:
        line_lookup = get_line_lookup()
        key = line_lookup.get(line_num, "unknown")
        name = PCE_HIERARCHY.get(key, {}).get("name", "unknown")
        print(f"  Line {line_num:3d}  {name}")

    print("\n" + "=" * 80)
    print("PATH TO ROOT: air_transportation")
    print("=" * 80)
    path = get_path_to_root("air_transportation")
    path_names = [f"{PCE_HIERARCHY[k]['name']} (L{PCE_HIERARCHY[k]['line']})" for k in path]
    print(" → ".join(path_names))

    print(f"\nTotal components in hierarchy: {len(PCE_HIERARCHY)}")
