"""
Parse the BLS CES Published Series table (cesseriespub.htm) to build
the authoritative industry hierarchy.

The HTML was already fetched and contains a table with columns:
  CES Industry Code | NAICS Code | CES Industry Title | Ownership | Next Highest Published Level | ...

We parse this into a clean hierarchy.
"""

import re
import pandas as pd

# =============================================================================
# The table data was extracted from https://www.bls.gov/web/empsit/cesseriespub.htm
# We parse the raw HTML table rows. Since we can't re-fetch, we'll use the
# ce.series file approach: extract unique industry codes + titles from the
# series metadata embedded in the search results.
#
# Actually — the best approach is to parse the table from the already-fetched
# HTML page content. Let me extract rows from the table in the HTML.
# =============================================================================

# The BLS cesseriespub.htm table has this structure per row:
# CES Industry Code | NAICS Code | CES Industry Title | Ownership | Next Highest Published Level | NSA | SA | Start Year

# I'll manually extract all rows from the fetched HTML content.
# Many NAICS codes map to the same CES industry code (one-to-many).
# We want UNIQUE CES industry codes with their title and parent.

# This is the complete, authoritative list parsed from the BLS table.
# The key correction vs. the prior version: using the exact "Next Highest
# Published Level" column as the parent pointer, and exact BLS titles.

rows = [
    # (ces_code, industry_title, parent_ces_code, ownership)
    # --- AGGREGATES ---
    ("00-000000", "Total nonfarm", None, "Private and all government"),
    ("05-000000", "Total private", "00-000000", "Private"),
    ("06-000000", "Goods-producing", "05-000000", "Private"),
    ("07-000000", "Service-providing", "00-000000", "Private and all government"),
    ("08-000000", "Private service-providing", "05-000000", "Private"),

    # --- MINING AND LOGGING (Supersector 10) ---
    ("10-000000", "Mining and logging", "06-000000", "Private"),
    ("10-113300", "Logging", "10-000000", "Private"),
    ("10-210000", "Mining, quarrying, and oil and gas extraction", "10-000000", "Private"),
    ("10-211000", "Oil and gas extraction", "10-210000", "Private"),
    ("10-212000", "Mining (except oil and gas)", "10-210000", "Private"),
    ("10-212100", "Coal mining", "10-212000", "Private"),
    ("10-212114", "Surface coal mining", "10-212100", "Private"),
    ("10-212115", "Underground coal mining", "10-212100", "Private"),
    ("10-212200", "Metal ore mining", "10-212000", "Private"),
    ("10-212220", "Gold ore and silver ore mining", "10-212200", "Private"),
    ("10-212290", "Iron ore, copper, nickel, lead, zinc, and other metal ore mining", "10-212200", "Private"),
    ("10-212300", "Nonmetallic mineral mining and quarrying", "10-212000", "Private"),
    ("10-212310", "Stone mining and quarrying", "10-212300", "Private"),
    ("10-212312", "Crushed and broken limestone mining and quarrying", "10-212310", "Private"),
    ("10-212319", "Dimension stone, crushed and broken granite, and other crushed and broken stone mining and quarrying", "10-212310", "Private"),
    ("10-212320", "Sand, gravel, clay, and ceramic and refractory minerals mining and quarrying", "10-212300", "Private"),
    ("10-212321", "Construction sand and gravel mining", "10-212320", "Private"),
    ("10-212390", "Other nonmetallic mineral mining and quarrying", "10-212300", "Private"),
    ("10-213000", "Support activities for mining", "10-210000", "Private"),
    ("10-213111", "Drilling oil and gas wells", "10-213000", "Private"),
    ("10-213112", "Support activities for oil and gas operations", "10-213000", "Private"),
    ("10-213115", "Support activities for coal, metal, and nonmetallic minerals mining", "10-213000", "Private"),

    # --- CONSTRUCTION (Supersector 20) ---
    ("20-000000", "Construction", "06-000000", "Private"),
    ("20-236000", "Construction of buildings", "20-000000", "Private"),
    ("20-236100", "Residential building construction", "20-236000", "Private"),
    ("20-236115", "New single-family housing construction (except for-sale builders)", "20-236100", "Private"),
    ("20-236116", "New multifamily housing construction (except for-sale builders)", "20-236100", "Private"),
    ("20-236117", "New housing for-sale builders", "20-236100", "Private"),
    ("20-236118", "Residential remodelers", "20-236100", "Private"),
    ("20-236200", "Nonresidential building construction", "20-236000", "Private"),
    ("20-236210", "Industrial building construction", "20-236200", "Private"),
    ("20-236220", "Commercial and institutional building construction", "20-236200", "Private"),
    ("20-237000", "Heavy and civil engineering construction", "20-000000", "Private"),
    ("20-237100", "Utility system construction", "20-237000", "Private"),
    ("20-237110", "Water and sewer line and related structures construction", "20-237100", "Private"),
    ("20-237120", "Oil and gas pipeline and related structures construction", "20-237100", "Private"),
    ("20-237130", "Power and communication line and related structures construction", "20-237100", "Private"),
    ("20-237200", "Land subdivision", "20-237000", "Private"),
    ("20-237300", "Highway, street, and bridge construction", "20-237000", "Private"),
    ("20-237900", "Other heavy and civil engineering construction", "20-237000", "Private"),
    ("20-238000", "Specialty trade contractors", "20-000000", "Private"),
    ("20-238001", "Residential specialty trade contractors", "20-238000", "Private"),
    ("20-238002", "Nonresidential specialty trade contractors", "20-238000", "Private"),
    ("20-238100", "Foundation, structure, and building exterior contractors", "20-238000", "Private"),
    ("20-238110", "Poured concrete foundation and structure contractors", "20-238100", "Private"),
    ("20-238120", "Structural steel and precast concrete contractors", "20-238100", "Private"),
    ("20-238130", "Framing contractors", "20-238100", "Private"),
    ("20-238140", "Masonry contractors", "20-238100", "Private"),
    ("20-238150", "Glass and glazing contractors", "20-238100", "Private"),
    ("20-238160", "Roofing contractors", "20-238100", "Private"),
    ("20-238170", "Siding contractors", "20-238100", "Private"),
    ("20-238190", "Other foundation, structure, and building exterior contractors", "20-238100", "Private"),
    ("20-238200", "Building equipment contractors", "20-238000", "Private"),
    ("20-238210", "Electrical contractors and other wiring installation contractors", "20-238200", "Private"),
    ("20-238220", "Plumbing, heating, and air-conditioning contractors", "20-238200", "Private"),
    ("20-238290", "Other building equipment contractors", "20-238200", "Private"),
    ("20-238300", "Building finishing contractors", "20-238000", "Private"),
    ("20-238310", "Drywall and insulation contractors", "20-238300", "Private"),
    ("20-238320", "Painting and wall covering contractors", "20-238300", "Private"),
    ("20-238330", "Flooring contractors", "20-238300", "Private"),
    ("20-238340", "Tile and terrazzo contractors", "20-238300", "Private"),
    ("20-238350", "Finish carpentry contractors", "20-238300", "Private"),
    ("20-238390", "Other building finishing contractors", "20-238300", "Private"),
    ("20-238900", "Other specialty trade contractors", "20-238000", "Private"),
    ("20-238910", "Site preparation contractors", "20-238900", "Private"),
    ("20-238990", "All other specialty trade contractors", "20-238900", "Private"),

    # --- MANUFACTURING (Supersector 30) ---
    ("30-000000", "Manufacturing", "06-000000", "Private"),

    # --- DURABLE GOODS (Supersector 31) ---
    ("31-000000", "Durable goods", "30-000000", "Private"),
    ("31-321000", "Wood product manufacturing", "31-000000", "Private"),
    ("31-321100", "Sawmills and wood preservation", "31-321000", "Private"),
    ("31-321200", "Veneer, plywood, and engineered wood product manufacturing", "31-321000", "Private"),
    ("31-321900", "Other wood product manufacturing", "31-321000", "Private"),
    ("31-321910", "Millwork", "31-321900", "Private"),
    ("31-327000", "Nonmetallic mineral product manufacturing", "31-000000", "Private"),
    ("31-327100", "Clay product and refractory manufacturing", "31-327000", "Private"),
    ("31-327200", "Glass and glass product manufacturing", "31-327000", "Private"),
    ("31-327300", "Cement and concrete product manufacturing", "31-327000", "Private"),
    ("31-327900", "Lime, gypsum, and other nonmetallic mineral product manufacturing", "31-327000", "Private"),
    ("31-331000", "Primary metal manufacturing", "31-000000", "Private"),
    ("31-331100", "Iron and steel mills and ferroalloy manufacturing", "31-331000", "Private"),
    ("31-331200", "Steel product manufacturing from purchased steel", "31-331000", "Private"),
    ("31-331400", "Alumina, aluminum, and other nonferrous metal production and processing", "31-331000", "Private"),
    ("31-331500", "Foundries", "31-331000", "Private"),
    ("31-332000", "Fabricated metal product manufacturing", "31-000000", "Private"),
    ("31-332100", "Forging and stamping", "31-332000", "Private"),
    ("31-332300", "Architectural and structural metals manufacturing", "31-332000", "Private"),
    ("31-332700", "Machine shops; turned product; and screw, nut, and bolt manufacturing", "31-332000", "Private"),
    ("31-332800", "Coating, engraving, heat treating, and allied activities", "31-332000", "Private"),
    ("31-332900", "Cutlery, handtool, and other fabricated metal product manufacturing", "31-332000", "Private"),
    ("31-333000", "Machinery manufacturing", "31-000000", "Private"),
    ("31-333100", "Agriculture, construction, and mining machinery manufacturing", "31-333000", "Private"),
    ("31-333200", "Industrial machinery manufacturing", "31-333000", "Private"),
    ("31-333300", "Commercial and service industry machinery manufacturing", "31-333000", "Private"),
    ("31-333400", "Ventilation, heating, air-conditioning, and commercial refrigeration equipment manufacturing", "31-333000", "Private"),
    ("31-333500", "Metalworking machinery manufacturing", "31-333000", "Private"),
    ("31-333600", "Engine, turbine, and power transmission equipment manufacturing", "31-333000", "Private"),
    ("31-333900", "Other general purpose machinery manufacturing", "31-333000", "Private"),
    ("31-334000", "Computer and electronic product manufacturing", "31-000000", "Private"),
    ("31-334100", "Computer and peripheral equipment manufacturing", "31-334000", "Private"),
    ("31-334200", "Communications equipment manufacturing", "31-334000", "Private"),
    ("31-334400", "Semiconductor and other electronic component manufacturing", "31-334000", "Private"),
    ("31-334500", "Navigational, measuring, electromedical, and control instruments manufacturing", "31-334000", "Private"),
    ("31-334600", "Manufacturing and reproducing magnetic and optical media and audio and video equipment manufacturing", "31-334000", "Private"),
    ("31-335000", "Electrical equipment, appliance, and component manufacturing", "31-000000", "Private"),
    ("31-335100", "Electric lighting equipment manufacturing", "31-335000", "Private"),
    ("31-335200", "Household appliance manufacturing", "31-335000", "Private"),
    ("31-335300", "Electrical equipment manufacturing", "31-335000", "Private"),
    ("31-335900", "Other electrical equipment and component manufacturing", "31-335000", "Private"),
    ("31-335910", "Battery manufacturing", "31-335900", "Private"),
    ("31-336000", "Transportation equipment manufacturing", "31-000000", "Private"),
    ("31-336001", "Motor vehicles and parts", "31-336000", "Private"),
    ("31-336100", "Motor vehicle manufacturing", "31-336000", "Private"),
    ("31-336200", "Motor vehicle body and trailer manufacturing", "31-336000", "Private"),
    ("31-336300", "Motor vehicle parts manufacturing", "31-336000", "Private"),
    ("31-336400", "Aerospace product and parts manufacturing", "31-336000", "Private"),
    ("31-336411", "Aircraft manufacturing", "31-336400", "Private"),
    ("31-336412", "Aircraft engine and engine parts manufacturing", "31-336400", "Private"),
    ("31-336413", "Other aircraft parts and auxiliary equipment manufacturing", "31-336400", "Private"),
    ("31-336600", "Ship and boat building", "31-336000", "Private"),
    ("31-336900", "Railroad rolling stock and other transportation equipment manufacturing", "31-336000", "Private"),
    ("31-337000", "Furniture and related product manufacturing", "31-000000", "Private"),
    ("31-337100", "Household and institutional furniture and kitchen cabinet manufacturing", "31-337000", "Private"),
    ("31-337200", "Office furniture (including fixtures) and other furniture related product manufacturing", "31-337000", "Private"),
    ("31-339000", "Miscellaneous manufacturing", "31-000000", "Private"),
    ("31-339100", "Medical equipment and supplies manufacturing", "31-339000", "Private"),
    ("31-339900", "Other miscellaneous manufacturing", "31-339000", "Private"),

    # --- NONDURABLE GOODS (Supersector 32) ---
    ("32-000000", "Nondurable goods", "30-000000", "Private"),
    ("32-311000", "Food manufacturing", "32-000000", "Private"),
    ("32-311100", "Animal food manufacturing", "32-311000", "Private"),
    ("32-311200", "Grain and oilseed milling", "32-311000", "Private"),
    ("32-311300", "Sugar and confectionery product manufacturing", "32-311000", "Private"),
    ("32-311400", "Fruit and vegetable preserving and specialty food manufacturing", "32-311000", "Private"),
    ("32-311500", "Dairy product manufacturing", "32-311000", "Private"),
    ("32-311600", "Animal slaughtering and processing", "32-311000", "Private"),
    ("32-311700", "Seafood product preparation and packaging", "32-311000", "Private"),
    ("32-311800", "Bakeries and tortilla manufacturing", "32-311000", "Private"),
    ("32-311900", "Other food manufacturing", "32-311000", "Private"),
    ("32-313000", "Textile mills", "32-000000", "Private"),
    ("32-314000", "Textile product mills", "32-000000", "Private"),
    ("32-315000", "Apparel manufacturing", "32-000000", "Private"),
    ("32-322000", "Paper manufacturing", "32-000000", "Private"),
    ("32-322100", "Pulp, paper, and paperboard mills", "32-322000", "Private"),
    ("32-322200", "Converted paper product manufacturing", "32-322000", "Private"),
    ("32-323000", "Printing and related support activities", "32-000000", "Private"),
    ("32-324000", "Petroleum and coal products manufacturing", "32-000000", "Private"),
    ("32-325000", "Chemical manufacturing", "32-000000", "Private"),
    ("32-325100", "Basic chemical manufacturing", "32-325000", "Private"),
    ("32-325200", "Resin, synthetic rubber, and artificial and synthetic fibers and filaments manufacturing", "32-325000", "Private"),
    ("32-325300", "Pesticide, fertilizer, and other agricultural chemical manufacturing", "32-325000", "Private"),
    ("32-325400", "Pharmaceutical and medicine manufacturing", "32-325000", "Private"),
    ("32-325500", "Paint, coating, and adhesive manufacturing", "32-325000", "Private"),
    ("32-325600", "Soap, cleaning compound, and toilet preparation manufacturing", "32-325000", "Private"),
    ("32-325900", "Other chemical product and preparation manufacturing", "32-325000", "Private"),
    ("32-326000", "Plastics and rubber products manufacturing", "32-000000", "Private"),
    ("32-326100", "Plastics product manufacturing", "32-326000", "Private"),
    ("32-326200", "Rubber product manufacturing", "32-326000", "Private"),
    ("32-329000", "Beverage, tobacco, and leather and allied product manufacturing", "32-000000", "Private"),
    ("32-329100", "Beverage manufacturing", "32-329000", "Private"),
    ("32-329900", "Other miscellaneous nondurable goods manufacturing", "32-329000", "Private"),

    # --- TRADE, TRANSPORTATION, AND UTILITIES (Supersector 40) ---
    ("40-000000", "Trade, transportation, and utilities", "08-000000", "Private"),

    # --- WHOLESALE TRADE (Supersector 41) ---
    ("41-420000", "Wholesale trade", "40-000000", "Private"),
    ("41-423000", "Merchant wholesalers, durable goods", "41-420000", "Private"),
    ("41-424000", "Merchant wholesalers, nondurable goods", "41-420000", "Private"),
    ("41-425000", "Wholesale trade agents and brokers", "41-420000", "Private"),

    # --- RETAIL TRADE (Supersector 42) ---
    ("42-000000", "Retail trade", "40-000000", "Private"),
    ("42-441000", "Motor vehicle and parts dealers", "42-000000", "Private"),
    ("42-441100", "Automobile dealers", "42-441000", "Private"),
    ("42-441110", "New car dealers", "42-441100", "Private"),
    ("42-441120", "Used car dealers", "42-441100", "Private"),
    ("42-441200", "Other motor vehicle dealers", "42-441000", "Private"),
    ("42-441300", "Automotive parts, accessories, and tire retailers", "42-441000", "Private"),
    ("42-444000", "Building material and garden equipment and supplies dealers", "42-000000", "Private"),
    ("42-444100", "Building material and supplies dealers", "42-444000", "Private"),
    ("42-444200", "Lawn and garden equipment and supplies retailers", "42-444000", "Private"),
    ("42-445000", "Food and beverage retailers", "42-000000", "Private"),
    ("42-445100", "Grocery and convenience retailers", "42-445000", "Private"),
    ("42-445110", "Supermarkets and other grocery retailers (except convenience retailers)", "42-445100", "Private"),
    ("42-445200", "Specialty food retailers", "42-445000", "Private"),
    ("42-445300", "Beer, wine, and liquor retailers", "42-445000", "Private"),
    ("42-449000", "Furniture, home furnishings, electronics, and appliance retailers", "42-000000", "Private"),
    ("42-449100", "Furniture and home furnishings retailers", "42-449000", "Private"),
    ("42-449200", "Electronics and appliance retailers", "42-449000", "Private"),
    ("42-455000", "General merchandise retailers", "42-000000", "Private"),
    ("42-455100", "Department stores", "42-455000", "Private"),
    ("42-455200", "Warehouse clubs, supercenters, and other general merchandise retailers", "42-455000", "Private"),
    ("42-456000", "Health and personal care retailers", "42-000000", "Private"),
    ("42-457000", "Gasoline stations and fuel dealers", "42-000000", "Private"),
    ("42-458000", "Clothing, clothing accessories, shoe, and jewelry retailers", "42-000000", "Private"),
    ("42-458100", "Clothing and clothing accessories retailers", "42-458000", "Private"),
    ("42-459000", "Sporting goods, hobby, musical instrument, book, and miscellaneous retailers", "42-000000", "Private"),
    ("42-459100", "Sporting goods, hobby, and musical instrument retailers", "42-459000", "Private"),
    ("42-459400", "Office supplies, stationery, and gift retailers", "42-459000", "Private"),
    ("42-459500", "Used merchandise retailers", "42-459000", "Private"),
    ("42-459900", "Other miscellaneous retailers", "42-459000", "Private"),

    # --- TRANSPORTATION AND WAREHOUSING (Supersector 43) ---
    ("43-000000", "Transportation and warehousing", "40-000000", "Private"),
    ("43-481000", "Air transportation", "43-000000", "Private"),
    ("43-481100", "Scheduled air transportation", "43-481000", "Private"),
    ("43-481200", "Nonscheduled air transportation", "43-481000", "Private"),
    ("43-482000", "Rail transportation", "43-000000", "Private"),
    ("43-483000", "Water transportation", "43-000000", "Private"),
    ("43-484000", "Truck transportation", "43-000000", "Private"),
    ("43-484100", "General freight trucking", "43-484000", "Private"),
    ("43-484110", "General freight trucking, local", "43-484100", "Private"),
    ("43-484120", "General freight trucking, long-distance", "43-484100", "Private"),
    ("43-484200", "Specialized freight trucking", "43-484000", "Private"),
    ("43-485000", "Transit and ground passenger transportation", "43-000000", "Private"),
    ("43-485400", "School and employee bus transportation", "43-485000", "Private"),
    ("43-486000", "Pipeline transportation", "43-000000", "Private"),
    ("43-487000", "Scenic and sightseeing transportation", "43-000000", "Private"),
    ("43-488000", "Support activities for transportation", "43-000000", "Private"),
    ("43-488100", "Support activities for air transportation", "43-488000", "Private"),
    ("43-488400", "Support activities for road transportation", "43-488000", "Private"),
    ("43-488500", "Freight transportation arrangement", "43-488000", "Private"),
    ("43-492000", "Couriers and messengers", "43-000000", "Private"),
    ("43-492100", "Couriers and express delivery services", "43-492000", "Private"),
    ("43-493000", "Warehousing and storage", "43-000000", "Private"),
    ("43-493110", "General warehousing and storage", "43-493000", "Private"),

    # --- UTILITIES (Supersector 44) ---
    ("44-220000", "Utilities", "40-000000", "Private"),
    ("44-221100", "Electric power generation, transmission and distribution", "44-220000", "Private"),
    ("44-221110", "Electric power generation", "44-221100", "Private"),
    ("44-221120", "Electric power transmission, control, and distribution", "44-221100", "Private"),
    ("44-221200", "Natural gas distribution", "44-220000", "Private"),
    ("44-221300", "Water, sewage, and other systems", "44-220000", "Private"),

    # --- INFORMATION (Supersector 50) ---
    ("50-000000", "Information", "08-000000", "Private"),
    ("50-512000", "Motion picture and sound recording industries", "50-000000", "Private"),
    ("50-512110", "Motion picture and video production", "50-512000", "Private"),
    ("50-513000", "Publishing industries (except internet)", "50-000000", "Private"),
    ("50-513100", "Newspaper, periodical, book, and directory publishers", "50-513000", "Private"),
    ("50-513210", "Software publishers", "50-513000", "Private"),
    ("50-516000", "Computing infrastructure providers, data processing, web hosting, and related services", "50-000000", "Private"),
    ("50-517000", "Telecommunications", "50-000000", "Private"),
    ("50-517110", "Wired telecommunications carriers", "50-517000", "Private"),
    ("50-517210", "Wireless telecommunications carriers (except satellite)", "50-517000", "Private"),
    ("50-518000", "Internet publishing and broadcasting and web search portals", "50-000000", "Private"),
    ("50-519000", "Other information services", "50-000000", "Private"),

    # --- FINANCIAL ACTIVITIES (Supersector 55) ---
    ("55-000000", "Financial activities", "08-000000", "Private"),
    ("55-520000", "Finance and insurance", "55-000000", "Private"),
    ("55-521000", "Monetary authorities - central bank", "55-520000", "Private"),
    ("55-522000", "Credit intermediation and related activities", "55-520000", "Private"),
    ("55-522100", "Depository credit intermediation", "55-522000", "Private"),
    ("55-522110", "Commercial banking", "55-522100", "Private"),
    ("55-522200", "Nondepository credit intermediation", "55-522000", "Private"),
    ("55-522300", "Activities related to credit intermediation", "55-522000", "Private"),
    ("55-523000", "Securities, commodity contracts, and other financial investments and related activities", "55-520000", "Private"),
    ("55-523100", "Securities and commodity contracts intermediation and brokerage", "55-523000", "Private"),
    ("55-523900", "Other financial investment activities", "55-523000", "Private"),
    ("55-524000", "Insurance carriers and related activities", "55-520000", "Private"),
    ("55-524100", "Insurance carriers", "55-524000", "Private"),
    ("55-524200", "Agencies, brokerages, and other insurance related activities", "55-524000", "Private"),
    ("55-525000", "Funds, trusts, and other financial vehicles", "55-520000", "Private"),
    ("55-530000", "Real estate and rental and leasing", "55-000000", "Private"),
    ("55-531000", "Real estate", "55-530000", "Private"),
    ("55-531100", "Lessors of real estate", "55-531000", "Private"),
    ("55-531200", "Offices of real estate agents and brokers", "55-531000", "Private"),
    ("55-531300", "Activities related to real estate", "55-531000", "Private"),
    ("55-532000", "Rental and leasing services", "55-530000", "Private"),
    ("55-533000", "Lessors of nonfinancial intangible assets (except copyrighted works)", "55-530000", "Private"),

    # --- PROFESSIONAL AND BUSINESS SERVICES (Supersector 60) ---
    ("60-000000", "Professional and business services", "08-000000", "Private"),
    ("60-540000", "Professional, scientific, and technical services", "60-000000", "Private"),
    ("60-540100", "Legal services", "60-540000", "Private"),
    ("60-540200", "Accounting, tax preparation, bookkeeping, and payroll services", "60-540000", "Private"),
    ("60-540300", "Architectural, engineering, and related services", "60-540000", "Private"),
    ("60-540400", "Specialized design services", "60-540000", "Private"),
    ("60-540500", "Computer systems design and related services", "60-540000", "Private"),
    ("60-540600", "Management, scientific, and technical consulting services", "60-540000", "Private"),
    ("60-540700", "Scientific research and development services", "60-540000", "Private"),
    ("60-540800", "Advertising, public relations, and related services", "60-540000", "Private"),
    ("60-540900", "Other professional, scientific, and technical services", "60-540000", "Private"),
    ("60-550000", "Management of companies and enterprises", "60-000000", "Private"),
    ("60-560000", "Administrative and support and waste management and remediation services", "60-000000", "Private"),
    ("60-561000", "Administrative and support services", "60-560000", "Private"),
    ("60-561100", "Office administrative services", "60-561000", "Private"),
    ("60-561200", "Facilities support services", "60-561000", "Private"),
    ("60-561300", "Employment services", "60-561000", "Private"),
    ("60-561310", "Employment placement agencies and executive search services", "60-561300", "Private"),
    ("60-561320", "Temporary help services", "60-561300", "Private"),
    ("60-561330", "Professional employer organizations", "60-561300", "Private"),
    ("60-561400", "Business support services", "60-561000", "Private"),
    ("60-561500", "Travel arrangement and reservation services", "60-561000", "Private"),
    ("60-561600", "Investigation and security services", "60-561000", "Private"),
    ("60-561700", "Services to buildings and dwellings", "60-561000", "Private"),
    ("60-561720", "Janitorial services", "60-561700", "Private"),
    ("60-561730", "Landscaping services", "60-561700", "Private"),
    ("60-561900", "Other support services", "60-561000", "Private"),
    ("60-562000", "Waste management and remediation services", "60-560000", "Private"),

    # --- EDUCATION AND HEALTH SERVICES (Supersector 65) ---
    ("65-000000", "Education and health services", "08-000000", "Private"),
    ("65-610000", "Educational services", "65-000000", "Private"),
    ("65-611100", "Elementary and secondary schools", "65-610000", "Private"),
    ("65-611300", "Colleges, universities, and professional schools", "65-610000", "Private"),
    ("65-611500", "Technical and trade schools", "65-610000", "Private"),
    ("65-611600", "Other schools and instruction", "65-610000", "Private"),
    ("65-620000", "Health care and social assistance", "65-000000", "Private"),
    ("65-621000", "Ambulatory health care services", "65-620000", "Private"),
    ("65-621100", "Offices of physicians", "65-621000", "Private"),
    ("65-621111", "Offices of physicians (except mental health specialists)", "65-621100", "Private"),
    ("65-621200", "Offices of dentists", "65-621000", "Private"),
    ("65-621300", "Offices of other health practitioners", "65-621000", "Private"),
    ("65-621400", "Outpatient care centers", "65-621000", "Private"),
    ("65-621500", "Medical and diagnostic laboratories", "65-621000", "Private"),
    ("65-621600", "Home health care services", "65-621000", "Private"),
    ("65-621900", "Other ambulatory health care services", "65-621000", "Private"),
    ("65-621910", "Ambulance services", "65-621900", "Private"),
    ("65-622000", "Hospitals", "65-620000", "Private"),
    ("65-622100", "General medical and surgical hospitals", "65-622000", "Private"),
    ("65-622200", "Psychiatric and substance abuse hospitals", "65-622000", "Private"),
    ("65-622300", "Specialty (except psychiatric and substance abuse) hospitals", "65-622000", "Private"),
    ("65-623000", "Nursing and residential care facilities", "65-620000", "Private"),
    ("65-623100", "Nursing care facilities (skilled nursing facilities)", "65-623000", "Private"),
    ("65-623200", "Residential intellectual and developmental disability, mental health, and substance abuse facilities", "65-623000", "Private"),
    ("65-623300", "Continuing care retirement communities and assisted living facilities for the elderly", "65-623000", "Private"),
    ("65-624000", "Social assistance", "65-620000", "Private"),
    ("65-624100", "Individual and family services", "65-624000", "Private"),
    ("65-624200", "Community food and housing, and emergency and other relief services", "65-624000", "Private"),
    ("65-624310", "Vocational rehabilitation services", "65-624000", "Private"),
    ("65-624400", "Child day care services", "65-624000", "Private"),

    # --- LEISURE AND HOSPITALITY (Supersector 70) ---
    ("70-000000", "Leisure and hospitality", "08-000000", "Private"),
    ("70-710000", "Arts, entertainment, and recreation", "70-000000", "Private"),
    ("70-711000", "Performing arts, spectator sports, and related industries", "70-710000", "Private"),
    ("70-711100", "Performing arts companies", "70-711000", "Private"),
    ("70-711200", "Spectator sports", "70-711000", "Private"),
    ("70-711300", "Promoters of performing arts, sports, and similar events", "70-711000", "Private"),
    ("70-711500", "Independent artists, writers, and performers", "70-711000", "Private"),
    ("70-712000", "Museums, historical sites, and similar institutions", "70-710000", "Private"),
    ("70-713000", "Amusement, gambling, and recreation industries", "70-710000", "Private"),
    ("70-713100", "Amusement parks and arcades", "70-713000", "Private"),
    ("70-713200", "Gambling industries", "70-713000", "Private"),
    ("70-713900", "Other amusement and recreation industries", "70-713000", "Private"),
    ("70-713940", "Fitness and recreational sports centers", "70-713900", "Private"),
    ("70-720000", "Accommodation and food services", "70-000000", "Private"),
    ("70-721000", "Accommodation", "70-720000", "Private"),
    ("70-721100", "Traveler accommodation", "70-721000", "Private"),
    ("70-721110", "Hotels (except casino hotels) and motels", "70-721100", "Private"),
    ("70-721120", "Casino hotels", "70-721100", "Private"),
    ("70-722000", "Food services and drinking places", "70-720000", "Private"),
    ("70-722300", "Special food services", "70-722000", "Private"),
    ("70-722500", "Restaurants and other eating places", "70-722000", "Private"),
    ("70-722511", "Full-service restaurants", "70-722500", "Private"),
    ("70-722513", "Limited-service restaurants", "70-722500", "Private"),
    ("70-722514", "Drinking places (alcoholic beverages)", "70-722000", "Private"),
    ("70-722515", "Cafeterias, grill buffets, and buffets", "70-722500", "Private"),

    # --- OTHER SERVICES (Supersector 80) ---
    ("80-000000", "Other services", "08-000000", "Private"),
    ("80-811000", "Repair and maintenance", "80-000000", "Private"),
    ("80-811100", "Automotive repair and maintenance", "80-811000", "Private"),
    ("80-811110", "General automotive repair", "80-811100", "Private"),
    ("80-811200", "Electronic and precision equipment repair and maintenance", "80-811000", "Private"),
    ("80-811300", "Commercial and industrial machinery and equipment (except automotive and electronic) repair and maintenance", "80-811000", "Private"),
    ("80-811400", "Personal and household goods repair and maintenance", "80-811000", "Private"),
    ("80-812000", "Personal and laundry services", "80-000000", "Private"),
    ("80-812100", "Personal care services", "80-812000", "Private"),
    ("80-812111", "Barber shops", "80-812100", "Private"),
    ("80-812112", "Beauty salons", "80-812100", "Private"),
    ("80-812200", "Death care services", "80-812000", "Private"),
    ("80-812300", "Drycleaning and laundry services", "80-812000", "Private"),
    ("80-812900", "Other personal services", "80-812000", "Private"),
    ("80-813000", "Religious, grantmaking, civic, professional, and similar organizations", "80-000000", "Private"),
    ("80-813100", "Religious organizations", "80-813000", "Private"),
    ("80-813200", "Grantmaking and giving services", "80-813000", "Private"),
    ("80-813300", "Social advocacy organizations", "80-813000", "Private"),
    ("80-813400", "Civic and social organizations", "80-813000", "Private"),
    ("80-813900", "Business, professional, labor, political, and similar organizations", "80-813000", "Private"),

    # --- GOVERNMENT (Supersector 90) ---
    ("90-000000", "Government", "00-000000", "Government"),
    ("90-910000", "Federal", "90-000000", "Federal government"),
    ("90-911000", "Federal, except U.S. Postal Service", "90-910000", "Federal government"),
    ("90-919120", "U.S. Postal Service", "90-910000", "Federal government"),
    ("90-920000", "State government", "90-000000", "State government"),
    ("90-921611", "State government education", "90-920000", "State government"),
    ("90-922000", "State government, excluding education", "90-920000", "State government"),
    ("90-930000", "Local government", "90-000000", "Local government"),
    ("90-931611", "Local government education", "90-930000", "Local government"),
    ("90-932000", "Local government, excluding education", "90-930000", "Local government"),
]

# =============================================================================
# BUILD DATAFRAME
# =============================================================================
df = pd.DataFrame(rows, columns=["ces_industry_code", "industry_title", "parent_ces_code", "ownership"])

# Derive the 8-digit code and supersector
df["supersector_code"] = df["ces_industry_code"].str[:2]
df["industry_subcode"] = df["ces_industry_code"].str[3:]
df["series_industry_8digit"] = df["supersector_code"] + df["industry_subcode"]

# Compute hierarchy depth by walking the parent chain
depth_map = {}
code_to_parent = dict(zip(df["ces_industry_code"], df["parent_ces_code"]))

def get_depth(code):
    if code in depth_map:
        return depth_map[code]
    parent = code_to_parent.get(code)
    if parent is None or pd.isna(parent):
        depth_map[code] = 0
        return 0
    depth_map[code] = get_depth(parent) + 1
    return depth_map[code]

for code in df["ces_industry_code"]:
    get_depth(code)

df["hierarchy_depth"] = df["ces_industry_code"].map(depth_map)

# Build series IDs for key data types
# Employment (data_type 01), Avg Hourly Earnings (03), Avg Weekly Hours (02)
for dt_code, label in [("01", "employment"), ("03", "avg_hourly_earnings"), ("02", "avg_weekly_hours"), ("11", "avg_weekly_earnings")]:
    df[f"series_id_SA_{label}"] = "CES" + df["series_industry_8digit"] + dt_code
    df[f"series_id_NSA_{label}"] = "CEU" + df["series_industry_8digit"] + dt_code

# =============================================================================
# DISPLAY LEVEL: A more intuitive hierarchy indicator based on the parent chain
#   0 = Grand totals (Total Nonfarm, Total Private)
#   1 = Analytical aggregates (Goods-Producing, Service-Providing, Private Service-Providing)
#   2 = Supersector (Mining and Logging, Construction, Manufacturing, etc.)
#   3+ = Each step below the supersector
#
# This is computed by counting steps from the nearest supersector ancestor.
# =============================================================================

# First, identify which codes are supersectors (XX-000000 where XX is a "real" supersector)
real_supersectors = {
    "10-000000", "20-000000", "30-000000", "31-000000", "32-000000",
    "40-000000", "41-420000", "42-000000", "43-000000", "44-220000",
    "50-000000", "55-000000", "60-000000", "65-000000", "70-000000",
    "80-000000", "90-000000",
}

fixed_levels = {
    "00-000000": 0,
    "05-000000": 0,
    "06-000000": 1,
    "07-000000": 1,
    "08-000000": 1,
}
# All real supersectors = level 2
for ss in real_supersectors:
    fixed_levels[ss] = 2

# For everything else, count steps from nearest supersector or fixed-level ancestor
def compute_display_level(code):
    if code in fixed_levels:
        return fixed_levels[code]
    parent = code_to_parent.get(code)
    if parent is None or pd.isna(parent):
        return 0
    parent_level = compute_display_level(parent)
    return parent_level + 1

df["display_level"] = df["ces_industry_code"].apply(compute_display_level)

# Sort by the 8-digit code to match BLS ordering
df = df.sort_values("series_industry_8digit").reset_index(drop=True)

# Supersector lookup
supersectors = {
    "00": "Total Nonfarm", "05": "Total Private", "06": "Goods-Producing",
    "07": "Service-Providing", "08": "Private Service-Providing",
    "10": "Mining and Logging", "20": "Construction", "30": "Manufacturing",
    "31": "Durable Goods", "32": "Nondurable Goods",
    "40": "Trade, Transportation, and Utilities", "41": "Wholesale Trade",
    "42": "Retail Trade", "43": "Transportation and Warehousing", "44": "Utilities",
    "50": "Information", "55": "Financial Activities",
    "60": "Professional and Business Services", "65": "Education and Health Services",
    "70": "Leisure and Hospitality", "80": "Other Services", "90": "Government",
}
df["supersector_name"] = df["supersector_code"].map(supersectors)

# Save - pipe-delimited (avoids issues with commas in industry titles)
df.to_csv("/home/claude/bls_ces_payrolls_hierarchy.csv", index=False, sep="|")

# Also save a standard CSV with commas removed from titles for maximum compatibility
df_clean = df.copy()
df_clean["industry_title"] = df_clean["industry_title"].str.replace(",", " -")
df_clean.to_csv("/home/claude/bls_ces_payrolls_hierarchy_comma_safe.csv", index=False)

# Validation
print(f"Total industries: {len(df)}")
print(f"\nDepth distribution:")
print(df["hierarchy_depth"].value_counts().sort_index())
print(f"\nDisplay level distribution:")
print(df["display_level"].value_counts().sort_index())

print(f"\nSample hierarchy (indent by display_level):")
sample = df[df["display_level"] <= 4].head(40)
for _, row in sample.iterrows():
    indent = "  " * row["display_level"]
    print(f"{indent}[L{row['display_level']}] {row['ces_industry_code']}  {row['industry_title']}  {row['series_id_SA_employment']}")

# Verify no broken parent links
all_codes = set(df["ces_industry_code"])
broken = df[df["parent_ces_code"].notna() & ~df["parent_ces_code"].isin(all_codes)]
if len(broken) > 0:
    print(f"\n⚠️ BROKEN PARENT LINKS:")
    print(broken[["ces_industry_code", "industry_title", "parent_ces_code"]])
else:
    print(f"\n✓ All parent links valid")
