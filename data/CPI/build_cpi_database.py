"""
CPI Relative Importance Database Builder
=========================================
Parses BLS CPI relative importance files (xlsx and txt), builds:
1. A hierarchy table with parent-child relationships and indent levels
2. A time series of relative importance weights (CPI-U and CPI-W)
3. A BLS API series ID mapping for each item

Data sources:
- xlsx files (2020-2025): Modern format with indent levels in column 0
- txt files (1987-2019): Fixed-width text with leading spaces indicating indent
- historicalrelativeimportance19471986_1.xlsx: Wide-format historical data

Output: SQLite database + CSV exports + pickle for fast Python ingestion
"""

import pandas as pd
import numpy as np
import re
import sqlite3
import os
import json
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_DIR = "/mnt/project"
OUTPUT_DIR = "/home/claude"

# ============================================================================
# PART 1: BLS CPI ITEM CODE MAPPING
# ============================================================================
# This is the official BLS item code to item name mapping from Appendix 7
# of the CPI Handbook of Methods. These codes form the series IDs like
# CUUR0000SA0 = CPI-U, Not Seasonally Adjusted, US City Average, All Items

BLS_ITEM_CODES = {
    # ----- Aggregate / Top-Level -----
    "SA0":    "All items",
    "SA0E":   "Energy",
    "SA0L1":  "All items less food",
    "SA0L12": "All items less food and shelter",
    "SA0L1E": "All items less food and energy",
    "SA0L2":  "All items less shelter",
    "SA0L5":  "All items less medical care",
    "SA0LE":  "All items less energy",

    # ----- Commodity/Service Aggregates -----
    "SAC":    "Commodities",
    "SACE":   "Energy commodities",
    "SACL1":  "Commodities less food",
    "SACL11": "Commodities less food and beverages",
    "SACL1E": "Commodities less food and energy commodities",
    "SAD":    "Durables",
    "SAN":    "Nondurables",
    "SAN1D":  "Domestically produced farm food",
    "SANL1":  "Nondurables less food",
    "SANL11": "Nondurables less food and beverages",
    "SANL113":"Nondurables less food, beverages, and apparel",
    "SANL13": "Nondurables less food and apparel",
    "SAS":    "Services",
    "SAS24":  "Utilities and public transportation",
    "SAS2RS": "Rent of shelter",
    "SAS367": "Other services",
    "SAS4":   "Transportation services",
    "SASL2RS":"Services less rent of shelter",
    "SASL5":  "Services less medical care services",
    "SASLE":  "Services less energy services",

    # ----- Major Group: Food and Beverages (SAF) -----
    "SAF":    "Food and beverages",
    "SAF1":   "Food",
    "SAF11":  "Food at home",
    "SAF111": "Cereals and bakery products",
    "SAF112": "Meats, poultry, fish, and eggs",
    "SAF1121":"Meats, poultry, and fish",
    "SAF11211":"Meats",
    "SAF113": "Fruits and vegetables",
    "SAF1131":"Fresh fruits and vegetables",
    "SAF114": "Nonalcoholic beverages and beverage materials",
    "SAF115": "Other food at home",
    "SAF116": "Alcoholic beverages",
    "SEFV":   "Food away from home",
    "SEFV01": "Full service meals and snacks",
    "SEFV02": "Limited service meals and snacks",
    "SEFV03": "Food at employee sites and schools",
    "SEFV04": "Food from vending machines and mobile vendors",
    "SEFV05": "Other food away from home",

    # Food at home detail
    "SEFA":   "Cereals and cereal products",
    "SEFA01": "Flour and prepared flour mixes",
    "SEFA02": "Breakfast cereal",
    "SEFA03": "Rice, pasta, cornmeal",
    "SEFB":   "Bakery products",
    "SEFB01": "Bread",
    "SEFB02": "Fresh biscuits, rolls, muffins",
    "SEFB03": "Cakes, cupcakes, and cookies",
    "SEFB04": "Other bakery products",
    "SEFC":   "Beef and veal",
    "SEFC01": "Uncooked ground beef",
    "SEFC02": "Uncooked beef roasts",
    "SEFC03": "Uncooked beef steaks",
    "SEFC04": "Uncooked other beef and veal",
    "SEFD":   "Pork",
    "SEFD01": "Bacon, breakfast sausage, and related products",
    "SEFD02": "Ham",
    "SEFD03": "Pork chops",
    "SEFD04": "Other pork including roasts, steaks, and ribs",
    "SEFE":   "Other meats",
    "SEFF":   "Poultry",
    "SEFF01": "Chicken",
    "SEFF02": "Other uncooked poultry including turkey",
    "SEFG":   "Fish and seafood",
    "SEFG01": "Fresh fish and seafood",
    "SEFG02": "Processed fish and seafood",
    "SEFH":   "Eggs",
    "SEFJ":   "Dairy and related products",
    "SEFJ01": "Milk",
    "SEFJ02": "Cheese and related products",
    "SEFJ03": "Ice cream and related products",
    "SEFJ04": "Other dairy and related products",
    "SEFK":   "Fresh fruits",
    "SEFK01": "Apples",
    "SEFK02": "Bananas",
    "SEFK03": "Citrus fruits",
    "SEFK04": "Other fresh fruits",
    "SEFL":   "Fresh vegetables",
    "SEFL01": "Potatoes",
    "SEFL02": "Lettuce",
    "SEFL03": "Tomatoes",
    "SEFL04": "Other fresh vegetables",
    "SEFM":   "Processed fruits and vegetables",
    "SEFM01": "Canned fruits and vegetables",
    "SEFM02": "Frozen fruits and vegetables",
    "SEFM03": "Other processed fruits and vegetables including dried",
    "SEFN":   "Juices and nonalcoholic drinks",
    "SEFN01": "Carbonated drinks",
    "SEFN02": "Frozen noncarbonated juices and drinks",
    "SEFN03": "Nonfrozen noncarbonated juices and drinks",
    "SEFP":   "Beverage materials including coffee and tea",
    "SEFP01": "Coffee",
    "SEFP02": "Other beverage materials including tea",
    "SEFR":   "Sugar and sweets",
    "SEFR01": "Sugar and artificial sweeteners",
    "SEFR02": "Candy and chewing gum",
    "SEFR03": "Other sweets",
    "SEFS":   "Fats and oils",
    "SEFS01": "Butter and margarine",
    "SEFS02": "Salad dressing",
    "SEFS03": "Other fats and oils including peanut butter",
    "SEFT":   "Other foods",
    "SEFT01": "Soups",
    "SEFT02": "Frozen and freeze dried prepared foods",
    "SEFT03": "Snacks",
    "SEFT04": "Spices, seasonings, condiments, sauces",
    "SEFT05": "Baby food and formula",
    "SEFT06": "Other miscellaneous foods",
    "SEFW":   "Alcoholic beverages at home",
    "SEFW01": "Beer, ale, and other malt beverages at home",
    "SEFW02": "Distilled spirits at home",
    "SEFW03": "Wine at home",
    "SEFX":   "Alcoholic beverages away from home",

    # ----- Major Group: Housing (SAH) -----
    "SAH":    "Housing",
    "SAH1":   "Shelter",
    "SAH2":   "Fuels and utilities",
    "SAH21":  "Household energy",
    "SAH3":   "Household furnishings and operations",
    "SAH31":  "Household furnishings and supplies",
    "SEHA":   "Rent of primary residence",
    "SEHB":   "Lodging away from home",
    "SEHB01": "Housing at school, excluding board",
    "SEHB02": "Other lodging away from home including hotels and motels",
    "SEHC":   "Owners' equivalent rent of residences",
    "SEHC01": "Owners' equivalent rent of primary residence",
    "SEHD":   "Tenants' and household insurance",
    "SEHE":   "Fuel oil and other fuels",
    "SEHE01": "Fuel oil",
    "SEHE02": "Propane, kerosene, and firewood",
    "SEHF":   "Energy services",
    "SEHF01": "Electricity",
    "SEHF02": "Utility (piped) gas service",
    "SEHG":   "Water and sewer and trash collection services",
    "SEHG01": "Water and sewerage maintenance",
    "SEHG02": "Garbage and trash collection",
    "SEHH":   "Window and floor coverings and other linens",
    "SEHH01": "Floor coverings",
    "SEHH02": "Window coverings",
    "SEHH03": "Other linens",
    "SEHJ":   "Furniture and bedding",
    "SEHJ01": "Bedroom furniture",
    "SEHJ02": "Living room, kitchen, and dining room furniture",
    "SEHJ03": "Other furniture",
    "SEHK":   "Appliances",
    "SEHK01": "Major appliances",
    "SEHK02": "Other appliances",
    "SEHL":   "Other household equipment and furnishings",
    "SEHL01": "Clocks, lamps, and decorator items",
    "SEHL02": "Indoor plants and flowers",
    "SEHL03": "Dishes and flatware",
    "SEHL04": "Nonelectric cookware and tableware",
    "SEHM":   "Tools, hardware, outdoor equipment and supplies",
    "SEHM01": "Tools, hardware and supplies",
    "SEHM02": "Outdoor equipment and supplies",
    "SEHN":   "Housekeeping supplies",
    "SEHN01": "Household cleaning products",
    "SEHN02": "Household paper products",
    "SEHN03": "Miscellaneous household products",
    "SEHP":   "Household operations",
    "SEHP01": "Domestic services",
    "SEHP02": "Gardening and lawn care services",
    "SEHP03": "Moving, storage, freight expense",
    "SEHP04": "Repair of household items",

    # ----- Major Group: Apparel (SAA) -----
    "SAA":    "Apparel",
    "SAA1":   "Men's and boys' apparel",
    "SAA2":   "Women's and girls' apparel",
    "SA311":  "Apparel less footwear",
    "SEAA":   "Men's apparel",
    "SEAA01": "Men's suits, sport coats, and outerwear",
    "SEAA02": "Men's furnishings",
    "SEAA03": "Men's shirts and sweaters",
    "SEAA04": "Men's pants and shorts",
    "SEAB":   "Boys' apparel",
    "SEAC":   "Women's apparel",
    "SEAC01": "Women's outerwear",
    "SEAC02": "Women's dresses",
    "SEAC03": "Women's suits and separates",
    "SEAC04": "Women's underwear, nightwear, sportswear and accessories",
    "SEAD":   "Girls' apparel",
    "SEAE":   "Footwear",
    "SEAE01": "Men's footwear",
    "SEAE02": "Boys' and girls' footwear",
    "SEAE03": "Women's footwear",
    "SEAF":   "Infants' and toddlers' apparel",
    "SEAG":   "Jewelry and watches",
    "SEAG01": "Watches",
    "SEAG02": "Jewelry",

    # ----- Major Group: Transportation (SAT) -----
    "SAT":    "Transportation",
    "SAT1":   "Private transportation",
    "SATCLTB":"Transportation commodities less motor fuel",
    "SETA":   "New and used motor vehicles",
    "SETA01": "New vehicles",
    "SETA02": "Used cars and trucks",
    "SETA03": "Leased cars and trucks",
    "SETA04": "Car and truck rental",
    "SETB":   "Motor fuel",
    "SETB01": "Gasoline (all types)",
    "SETB02": "Other motor fuels",
    "SETC":   "Motor vehicle parts and equipment",
    "SETC01": "Tires",
    "SETC02": "Vehicle accessories other than tires",
    "SETD":   "Motor vehicle maintenance and repair",
    "SETD01": "Motor vehicle body work",
    "SETD02": "Motor vehicle maintenance and servicing",
    "SETD03": "Motor vehicle repair",
    "SETE":   "Motor vehicle insurance",
    "SETF":   "Motor vehicle fees",
    "SETF01": "State motor vehicle registration and license fees",
    "SETF03": "Parking and other fees",
    "SETG":   "Public transportation",
    "SETG01": "Airline fare",
    "SETG02": "Other intercity transportation",
    "SETG03": "Intracity transportation",

    # ----- Major Group: Medical Care (SAM) -----
    "SAM":    "Medical care",
    "SAM1":   "Medical care commodities",
    "SAM2":   "Medical care services",
    "SEMC":   "Professional services",
    "SEMC01": "Physicians' services",
    "SEMC02": "Dental services",
    "SEMC03": "Eyeglasses and eye care",
    "SEMC04": "Services by other medical professionals",
    "SEMD":   "Hospital and related services",
    "SEMD01": "Hospital services",
    "SEMD02": "Nursing homes and adult day services",
    "SEMD03": "Care of invalids and elderly at home",
    "SEME":   "Health insurance",
    "SEMF":   "Medicinal drugs",
    "SEMF01": "Prescription drugs",
    "SEMF02": "Nonprescription drugs",
    "SEMG":   "Medical equipment and supplies",

    # ----- Major Group: Recreation (SAR) -----
    "SAR":    "Recreation",
    "SARC":   "Recreation commodities",
    "SARS":   "Recreation services",
    "SERA":   "Video and audio",
    "SERA01": "Televisions",
    "SERA02": "Cable, satellite, and live streaming television service",
    "SERA03": "Other video equipment",
    "SERA04": "Purchase, subscription, and rental of video",
    "SERA05": "Audio equipment",
    "SERA06": "Recorded music and music subscriptions",
    "SERAC":  "Video and audio products",
    "SERAS":  "Video and audio services",
    "SERB":   "Pets, pet products and services",
    "SERB01": "Pets and pet products",
    "SERB02": "Pet services including veterinary",
    "SERC":   "Sporting goods",
    "SERC01": "Sports vehicles including bicycles",
    "SERC02": "Sports equipment",
    "SERD":   "Photography",
    "SERD01": "Photographic equipment and supplies",
    "SERD02": "Photographers and photo processing",
    "SERE":   "Other recreational goods",
    "SERE01": "Toys",
    "SERE02": "Sewing machines, fabric and supplies",
    "SERE03": "Music instruments and accessories",
    "SERF":   "Other recreation services",
    "SERF01": "Club membership for shopping clubs, fraternal, or other organizations, or participant sports fees",
    "SERF02": "Admissions",
    "SERF03": "Fees for lessons or instructions",
    "SERG":   "Recreational reading materials",
    "SERG01": "Newspapers and magazines",
    "SERG02": "Recreational books",

    # ----- Major Group: Education and Communication (SAE) -----
    "SAE":    "Education and communication",
    "SAE1":   "Education",
    "SAE2":   "Communication",
    "SAE21":  "Information and information processing",
    "SAEC":   "Education and communication commodities",
    "SAES":   "Education and communication services",
    "SEEA":   "Educational books and supplies",
    "SEEB":   "Tuition, other school fees, and childcare",
    "SEEB01": "College tuition and fees",
    "SEEB02": "Elementary and high school tuition and fees",
    "SEEB03": "Child care and nursery school",
    "SEEB04": "Technical and business school tuition and fees",
    "SEEC":   "Postage and delivery services",
    "SEEC01": "Postage",
    "SEEC02": "Delivery services",
    "SEED":   "Residential telephone services",
    "SEED03": "Wireless telephone services",
    "SEED04": "Land-line telephone services",
    "SEEE":   "Information technology, hardware and services",
    "SEEE01": "Personal computers and peripheral equipment",
    "SEEE02": "Computer software and accessories",
    "SEEE03": "Internet services and electronic information providers",
    "SEEE04": "Telephone hardware, calculators, and other consumer information items",
    "SEEEC":  "Information technology commodities",

    # ----- Major Group: Other Goods and Services (SAG) -----
    "SAG":    "Other goods and services",
    "SAG1":   "Personal care",
    "SAGC":   "Other goods",
    "SAGS":   "Other personal services",
    "SEGA":   "Tobacco and smoking products",
    "SEGA01": "Cigarettes",
    "SEGA02": "Tobacco products other than cigarettes",
    "SEGB":   "Personal care products",
    "SEGB01": "Hair, dental, shaving, and miscellaneous personal care products",
    "SEGB02": "Cosmetics, perfume, bath, nail preparations and implements",
    "SEGC":   "Personal care services",
    "SEGC01": "Haircuts and other personal care services",
    "SEGD":   "Miscellaneous personal services",
    "SEGD01": "Legal services",
    "SEGD02": "Funeral expenses",
    "SEGD03": "Laundry and dry cleaning services",
    "SEGD04": "Apparel services other than laundry and dry cleaning",
    "SEGD05": "Financial services",
    "SEGE":   "Miscellaneous personal goods",
}

# Build reverse lookup: normalized item name -> item code
ITEM_NAME_TO_CODE = {}
for code, name in BLS_ITEM_CODES.items():
    normalized = name.strip().lower()
    ITEM_NAME_TO_CODE[normalized] = code


def fuzzy_match_item_code(item_name):
    """Match an item name from the relative importance tables to a BLS item code."""
    if not isinstance(item_name, str):
        return None

    clean = item_name.strip().lower()
    clean = re.sub(r'\.+$', '', clean).strip()
    clean = re.sub(r'\s+', ' ', clean)

    # Direct match
    if clean in ITEM_NAME_TO_CODE:
        return ITEM_NAME_TO_CODE[clean]

    # Try common variations
    variations = [
        clean,
        clean.replace("'", "'"),
        clean.replace("'", "'"),
        clean.replace(" and ", " & "),
        clean.replace(" & ", " and "),
    ]

    for v in variations:
        if v in ITEM_NAME_TO_CODE:
            return ITEM_NAME_TO_CODE[v]

    # Partial matching for known tricky cases
    partial_map = {
        "all items": "SA0",
        "food and beverages": "SAF",
        "food at home": "SAF11",
        "cereals and bakery products": "SAF111",
        "meats, poultry, fish, and eggs": "SAF112",
        "fruits and vegetables": "SAF113",
        "dairy and related products": "SEFJ",
        "dairy products": "SEFJ",
        "nonalcoholic beverages and beverage materials": "SAF114",
        "nonalcoholic beverages": "SAF114",
        "other food at home": "SAF115",
        "food away from home": "SEFV",
        "alcoholic beverages": "SAF116",
        "housing": "SAH",
        "shelter": "SAH1",
        "rent of primary residence": "SEHA",
        "owners' equivalent rent of residences": "SEHC",
        "owners' equivalent rent of primary residence": "SEHC01",
        "tenants' and household insurance": "SEHD",
        "fuels and utilities": "SAH2",
        "household energy": "SAH21",
        "fuel oil and other fuels": "SEHE",
        "fuel oil": "SEHE01",
        "energy services": "SEHF",
        "electricity": "SEHF01",
        "utility (piped) gas service": "SEHF02",
        "water and sewer and trash collection services": "SEHG",
        "household furnishings and operations": "SAH3",
        "household furnishings and supplies": "SAH31",
        "apparel": "SAA",
        "men's and boys' apparel": "SAA1",
        "women's and girls' apparel": "SAA2",
        "footwear": "SEAE",
        "transportation": "SAT",
        "private transportation": "SAT1",
        "new vehicles": "SETA01",
        "used cars and trucks": "SETA02",
        "motor fuel": "SETB",
        "gasoline (all types)": "SETB01",
        "motor vehicle parts and equipment": "SETC",
        "motor vehicle maintenance and repair": "SETD",
        "motor vehicle insurance": "SETE",
        "motor vehicle fees": "SETF",
        "public transportation": "SETG",
        "airline fare": "SETG01",
        "medical care": "SAM",
        "medical care commodities": "SAM1",
        "medical care services": "SAM2",
        "professional services": "SEMC",
        "physicians' services": "SEMC01",
        "dental services": "SEMC02",
        "hospital and related services": "SEMD",
        "hospital services": "SEMD01",
        "health insurance": "SEME",
        "prescription drugs": "SEMF01",
        "nonprescription drugs": "SEMF02",
        "recreation": "SAR",
        "education and communication": "SAE",
        "tuition, other school fees, and childcare": "SEEB",
        "college tuition and fees": "SEEB01",
        "other goods and services": "SAG",
        "tobacco and smoking products": "SEGA",
        "cigarettes": "SEGA01",
        "personal care products": "SEGB",
        "personal care services": "SEGC",
        "energy": "SA0E",
        "all items less food and energy": "SA0L1E",
        "all items less food": "SA0L1",
        "all items less shelter": "SA0L2",
        "all items less energy": "SA0LE",
        "all items less medical care": "SA0L5",
        "commodities": "SAC",
        "services": "SAS",
        "durables": "SAD",
        "nondurables": "SAN",
        "commodities less food": "SACL1",
        "commodities less food and beverages": "SACL11",
        "nondurables less food": "SANL1",
        "nondurables less food and beverages": "SANL11",
        "nondurables less food and apparel": "SANL13",
        "services less rent of shelter": "SASL2RS",
        "services less medical care services": "SASL5",
        "rent of shelter": "SAS2RS",
        "energy commodities": "SACE",
        "services less energy services": "SASLE",
        "commodities less food and energy commodities": "SACL1E",
        "domestically produced farm food": "SAN1D",
        "utilities and public transportation": "SAS24",
        "new and used motor vehicles": "SETA",
        "lodging away from home": "SEHB",
        "medicinal drugs": "SEMF",
        "medical equipment and supplies": "SEMG",
        "video and audio": "SERA",
        "pets, pet products and services": "SERB",
        "sporting goods": "SERC",
        "other recreational goods": "SERE",
        "other recreation services": "SERF",
        "recreational reading materials": "SERG",
        "personal care": "SAG1",
        "miscellaneous personal services": "SEGD",
        "miscellaneous personal goods": "SEGE",
        "information technology, hardware and services": "SEEE",
        "furniture and bedding": "SEHJ",
        "appliances": "SEHK",
        "housekeeping supplies": "SEHN",
        "household operations": "SEHP",
        "postage and delivery services": "SEEC",
        "tools, hardware, outdoor equipment and supplies": "SEHM",
        "nondurables less food, beverages, and apparel": "SANL113",
        "apparel less footwear": "SA311",
        "transportation services": "SAS4",
        "other services": "SAS367",
    }

    if clean in partial_map:
        return partial_map[clean]

    # Try substring match
    for key, code in partial_map.items():
        if clean == key or (len(clean) > 10 and clean in key) or (len(key) > 10 and key in clean):
            return code

    return None


# ============================================================================
# PART 2: PARSE XLSX FILES (2020-2025)
# ============================================================================

def parse_xlsx_file(filepath, year):
    """Parse the modern xlsx format files that have indent levels in column 0."""
    df = pd.read_excel(filepath, sheet_name='Table 1', header=None)

    records = []
    for idx, row in df.iterrows():
        indent = row[0]
        item_name = row[1]
        cpi_u = row[2]
        cpi_w = row[3]

        # Skip header/empty rows
        if pd.isna(item_name) or not isinstance(item_name, str):
            continue
        if item_name.strip() in ('', 'Item and Group', 'Expenditure category'):
            continue
        if 'Percent of all items' in str(item_name):
            continue
        if 'Table' in str(item_name) and 'Weights' in str(item_name):
            continue

        # Get indent level
        if pd.notna(indent):
            try:
                indent_level = int(indent)
            except (ValueError, TypeError):
                continue
        else:
            continue

        # Clean values
        try:
            cpi_u_val = float(cpi_u) if pd.notna(cpi_u) else None
        except (ValueError, TypeError):
            cpi_u_val = None
        try:
            cpi_w_val = float(cpi_w) if pd.notna(cpi_w) else None
        except (ValueError, TypeError):
            cpi_w_val = None

        item_clean = item_name.strip()

        records.append({
            'item_name': item_clean,
            'indent_level': indent_level,
            'cpi_u': cpi_u_val,
            'cpi_w': cpi_w_val,
            'year': year,
        })

    return records


# ============================================================================
# PART 3: PARSE TXT FILES (1987-2019)
# ============================================================================

def parse_txt_file(filepath, year):
    """Parse the fixed-width text format files."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    records = []

    for line in lines:
        # Skip blank/header lines
        stripped = line.strip()
        if not stripped:
            continue
        if any(kw in stripped.lower() for kw in [
            'table', 'relative importance', 'percent of all items',
            'u.s. city average', 'item and group', 'cpi-u', 'cpi-w',
            'expenditure category', 'usrinew', 'usriold', 'this is',
            'cpi item structure', 'item structure', 'available'
        ]):
            continue

        # Parse the line: item name is left, then numbers on the right
        # Items use dots as separators
        # Try to find the numeric values at the end

        match = re.match(
            r'^(\s*)(.*?)\s*\.{2,}\s*([\d.]+)\s+([\d.]+)\s*$',
            line
        )
        if not match:
            # Try without dots
            match = re.match(
                r'^(\s*)(.*?)\s{3,}([\d.]+)\s+([\d.]+)\s*$',
                line
            )
        if not match:
            # Try single value
            match = re.match(
                r'^(\s*)(.*?)\s*\.{2,}\s*([\d.]+)\s*$',
                line
            )
            if match:
                leading_spaces = len(match.group(1))
                item_name = match.group(2).strip()
                item_name = re.sub(r'\.+$', '', item_name).strip()
                try:
                    cpi_u_val = float(match.group(3))
                except ValueError:
                    continue
                cpi_w_val = None

                # Calculate indent level from leading spaces
                indent_level = leading_spaces // 2
                if indent_level > 8:
                    indent_level = 8

                if item_name and cpi_u_val is not None:
                    records.append({
                        'item_name': item_name,
                        'indent_level': indent_level,
                        'cpi_u': cpi_u_val,
                        'cpi_w': cpi_w_val,
                        'year': year,
                    })
                continue
            continue

        leading_spaces = len(match.group(1))
        item_name = match.group(2).strip()
        item_name = re.sub(r'\.+$', '', item_name).strip()

        try:
            cpi_u_val = float(match.group(3))
        except ValueError:
            cpi_u_val = None

        try:
            cpi_w_val = float(match.group(4)) if len(match.groups()) >= 4 else None
        except (ValueError, IndexError):
            cpi_w_val = None

        # Calculate indent level from leading spaces
        indent_level = leading_spaces // 2
        if indent_level > 8:
            indent_level = 8

        if item_name and cpi_u_val is not None:
            records.append({
                'item_name': item_name,
                'indent_level': indent_level,
                'cpi_u': cpi_u_val,
                'cpi_w': cpi_w_val,
                'year': year,
            })

    return records


# ============================================================================
# PART 4: BUILD HIERARCHY WITH PARENT-CHILD RELATIONSHIPS
# ============================================================================

def build_hierarchy(records):
    """Given a list of records with indent levels, assign parent items."""
    # Use a stack to track the current parent at each level
    parent_stack = {}  # indent_level -> item_name

    for i, rec in enumerate(records):
        level = rec['indent_level']
        name = rec['item_name']

        # The parent is the most recent item at level - 1
        if level == 0:
            rec['parent_item'] = None
        else:
            parent_level = level - 1
            while parent_level >= 0:
                if parent_level in parent_stack:
                    rec['parent_item'] = parent_stack[parent_level]
                    break
                parent_level -= 1
            else:
                rec['parent_item'] = None

        parent_stack[level] = name
        # Clear deeper levels
        for k in list(parent_stack.keys()):
            if k > level:
                del parent_stack[k]

    return records


# ============================================================================
# PART 5: MAIN BUILD PROCESS
# ============================================================================

def main():
    print("=" * 70)
    print("CPI RELATIVE IMPORTANCE DATABASE BUILDER")
    print("=" * 70)

    all_records = []

    # --- Parse XLSX files (2020-2025) ---
    xlsx_files = {
        2020: 'cpirelativeimportance.xlsx',  # This is actually 2025 data
        2024: '2024.xlsx',
        2023: '2023.xlsx',
        2022: '2022.xlsx',
        2021: '2021.xlsx',
        2020: '2020.xlsx',
    }

    # First, check what year each xlsx actually is
    print("\n--- Parsing XLSX files ---")
    for filepath_name in ['2020.xlsx', '2021.xlsx', '2022.xlsx', '2023.xlsx',
                          '2024.xlsx', '2025_1.xlsx', 'cpirelativeimportance.xlsx']:
        fpath = os.path.join(PROJECT_DIR, filepath_name)
        if not os.path.exists(fpath):
            continue

        df = pd.read_excel(fpath, sheet_name='Table 1', header=None, nrows=2)
        title = str(df.iloc[0, 1]) if pd.notna(df.iloc[0, 1]) else ""

        # Extract year from title
        year_match = re.search(r'December\s+(\d{4})', title)
        if year_match:
            year = int(year_match.group(1))
        else:
            # Fall back to filename
            year_match = re.search(r'(\d{4})', filepath_name)
            year = int(year_match.group(1)) if year_match else None

        if year:
            print(f"  {filepath_name} -> December {year}")
            records = parse_xlsx_file(fpath, year)
            records = build_hierarchy(records)
            all_records.extend(records)
            print(f"    Parsed {len(records)} items")

    # --- Parse TXT files (1987-2019) ---
    print("\n--- Parsing TXT files ---")
    for year in range(1987, 2020):
        fpath = os.path.join(PROJECT_DIR, f'{year}.txt')
        if not os.path.exists(fpath):
            print(f"  {year}.txt not found, skipping")
            continue

        records = parse_txt_file(fpath, year)
        records = build_hierarchy(records)
        all_records.extend(records)
        print(f"  {year}.txt -> {len(records)} items")

    # --- Create DataFrame ---
    print(f"\n--- Total records: {len(all_records)} ---")
    df = pd.DataFrame(all_records)

    # Match BLS item codes
    print("\n--- Matching BLS item codes ---")
    df['bls_item_code'] = df['item_name'].apply(fuzzy_match_item_code)

    # Build series IDs (CPI-U, Not Seasonally Adjusted, US City Average)
    df['bls_series_id_cpi_u_nsa'] = df['bls_item_code'].apply(
        lambda x: f"CUUR0000{x}" if x else None
    )
    df['bls_series_id_cpi_u_sa'] = df['bls_item_code'].apply(
        lambda x: f"CUSR0000{x}" if x else None
    )
    df['bls_series_id_cpi_w_nsa'] = df['bls_item_code'].apply(
        lambda x: f"CWUR0000{x}" if x else None
    )

    matched = df['bls_item_code'].notna().sum()
    total = len(df)
    unique_items = df['item_name'].nunique()
    unique_matched = df[df['bls_item_code'].notna()]['item_name'].nunique()
    print(f"  Matched {matched}/{total} records ({matched/total*100:.1f}%)")
    print(f"  Unique items: {unique_items}, Matched: {unique_matched}")

    # --- Create hierarchy table (unique items from most recent year) ---
    print("\n--- Building hierarchy table ---")
    latest_year = df['year'].max()
    hierarchy_df = (
        df[df['year'] == latest_year]
        [['item_name', 'indent_level', 'parent_item', 'bls_item_code',
          'bls_series_id_cpi_u_nsa', 'bls_series_id_cpi_u_sa',
          'bls_series_id_cpi_w_nsa']]
        .drop_duplicates(subset=['item_name'])
        .reset_index(drop=True)
    )

    # Determine if each item is a "special aggregate" vs expenditure category
    def classify_item(row):
        code = row['bls_item_code']
        name = row['item_name']
        if code is None or (isinstance(code, float) and np.isnan(code)) or not isinstance(code, str):
            return 'expenditure_item'
        if code.startswith('SA0') and code != 'SA0':
            return 'special_aggregate'
        if code.startswith('SAC') or code.startswith('SAD') or code.startswith('SAN') or code.startswith('SAS'):
            return 'special_aggregate'
        if 'less' in str(name).lower():
            return 'special_aggregate'
        return 'expenditure_item'

    hierarchy_df['item_type'] = hierarchy_df.apply(classify_item, axis=1)

    # --- Create weights time series ---
    print("\n--- Building weights time series ---")
    weights_df = df[['item_name', 'year', 'indent_level', 'cpi_u', 'cpi_w',
                      'bls_item_code', 'bls_series_id_cpi_u_nsa']].copy()

    # Pivot for wide format
    weights_wide_u = weights_df.pivot_table(
        index='item_name',
        columns='year',
        values='cpi_u',
        aggfunc='first'
    ).reset_index()

    weights_wide_w = weights_df.pivot_table(
        index='item_name',
        columns='year',
        values='cpi_w',
        aggfunc='first'
    ).reset_index()

    # --- BLS API Reference Table ---
    print("\n--- Building BLS API reference ---")
    api_ref = []
    for code, name in BLS_ITEM_CODES.items():
        api_ref.append({
            'bls_item_code': code,
            'item_name': name,
            'series_id_cpi_u_nsa': f"CUUR0000{code}",
            'series_id_cpi_u_sa': f"CUSR0000{code}",
            'series_id_cpi_w_nsa': f"CWUR0000{code}",
            'series_id_cpi_w_sa': f"CWSR0000{code}",
            'api_url_v2': f"https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000{code}",
            'data_viewer_url': f"https://data.bls.gov/timeseries/CUUR0000{code}",
        })
    api_ref_df = pd.DataFrame(api_ref)

    # --- Save outputs ---
    print("\n--- Saving outputs ---")

    # 1. SQLite database
    db_path = os.path.join(OUTPUT_DIR, 'cpi_database.sqlite')
    conn = sqlite3.connect(db_path)

    hierarchy_df.to_sql('hierarchy', conn, if_exists='replace', index=False)
    weights_df.to_sql('weights_long', conn, if_exists='replace', index=False)
    api_ref_df.to_sql('bls_api_series', conn, if_exists='replace', index=False)

    conn.close()
    print(f"  SQLite: {db_path}")

    # 2. CSV exports
    hierarchy_df.to_csv(os.path.join(OUTPUT_DIR, 'cpi_hierarchy.csv'), index=False)
    weights_df.to_csv(os.path.join(OUTPUT_DIR, 'cpi_weights_long.csv'), index=False)
    api_ref_df.to_csv(os.path.join(OUTPUT_DIR, 'bls_api_series.csv'), index=False)
    print(f"  CSVs saved")

    # 3. Pickle for fast Python loading
    pickle_data = {
        'hierarchy': hierarchy_df,
        'weights_long': weights_df,
        'weights_wide_cpi_u': weights_wide_u,
        'weights_wide_cpi_w': weights_wide_w,
        'bls_api_series': api_ref_df,
        'bls_item_codes': BLS_ITEM_CODES,
        'metadata': {
            'description': 'CPI Relative Importance Database',
            'source': 'BLS Consumer Price Index',
            'years_covered': sorted(df['year'].unique().tolist()),
            'total_records': len(df),
            'unique_items': df['item_name'].nunique(),
            'build_note': 'BLS API: https://api.bls.gov/publicAPI/v2/timeseries/data/',
        }
    }
    pickle_path = os.path.join(OUTPUT_DIR, 'cpi_database.pkl')
    pd.to_pickle(pickle_data, pickle_path)
    print(f"  Pickle: {pickle_path}")

    # 4. JSON metadata
    metadata = {
        'years_covered': sorted(df['year'].unique().tolist()),
        'total_records': len(df),
        'unique_items': int(df['item_name'].nunique()),
        'items_with_bls_codes': int(unique_matched),
        'bls_api_info': {
            'base_url_v1': 'https://api.bls.gov/publicAPI/v1/timeseries/data/',
            'base_url_v2': 'https://api.bls.gov/publicAPI/v2/timeseries/data/',
            'registration_url': 'https://data.bls.gov/registrationEngine/',
            'series_id_format': 'CU[S/U]R0000[item_code]',
            'note': 'V1: 25 queries/day, 10yr max. V2 (free registration): 500/day, 20yr max.',
            'example_all_items': 'CUUR0000SA0',
            'example_core_cpi': 'CUUR0000SA0L1E',
            'flat_files_url': 'https://download.bls.gov/pub/time.series/cu/',
            'aspect_file_note': 'cu.aspect contains relative importance data via API',
        },
        'database_files': {
            'sqlite': 'cpi_database.sqlite',
            'pickle': 'cpi_database.pkl',
            'csv_hierarchy': 'cpi_hierarchy.csv',
            'csv_weights': 'cpi_weights_long.csv',
            'csv_api_series': 'bls_api_series.csv',
        }
    }
    with open(os.path.join(OUTPUT_DIR, 'cpi_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata JSON saved")

    # --- Print summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Years covered: {min(df['year'])} - {max(df['year'])}")
    print(f"Total records: {len(df):,}")
    print(f"Unique items: {df['item_name'].nunique()}")
    print(f"Items matched to BLS codes: {unique_matched}")
    print(f"\nHierarchy levels (from {latest_year}):")
    for level in sorted(hierarchy_df['indent_level'].unique()):
        count = len(hierarchy_df[hierarchy_df['indent_level'] == level])
        print(f"  Level {level}: {count} items")

    print(f"\nSample hierarchy (top items from {latest_year}):")
    for _, row in hierarchy_df.head(20).iterrows():
        indent = "  " * row['indent_level']
        code = row['bls_item_code'] or '---'
        print(f"  {indent}{row['item_name']} [{code}] (Level {row['indent_level']})")

    print(f"\n\nFiles saved to {OUTPUT_DIR}/")
    print("  - cpi_database.sqlite  (SQLite with 3 tables)")
    print("  - cpi_database.pkl     (Pickle for fast pd.read_pickle())")
    print("  - cpi_hierarchy.csv    (Hierarchy with parent-child)")
    print("  - cpi_weights_long.csv (Weights time series, long format)")
    print("  - bls_api_series.csv   (BLS API series ID reference)")
    print("  - cpi_metadata.json    (Metadata and API info)")


if __name__ == '__main__':
    main()
