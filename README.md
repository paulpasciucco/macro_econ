# Economic Statistics Viewer

A Python toolkit for exploring U.S. macroeconomic data — **PCE**, **GDP**, **CPI**, and **Employment** — through interactive Jupyter notebooks. It organizes hundreds of government-reported series into navigable hierarchical trees, fetches data from three federal APIs (FRED, BEA, BLS), and provides a library of transformations and statistical tests commonly used in economic analysis.

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and fill in API keys
cp .env.example .env
# Edit .env with your FRED, BEA, and BLS keys (see "API Keys" section below)

# Launch notebooks
uv run jupyter lab
```

Then open any notebook in the `notebooks/` folder to start exploring.

---

## Architecture

The project is organized in five layers, where each layer depends only on the ones below it:

```
┌─────────────────────────────────────────────────────┐
│  Notebooks                                          │
│  Interactive Jupyter notebooks (01–05)               │
├─────────────────────────────────────────────────────┤
│  Visualization                                      │
│  Plotly charts, ipywidgets tree navigators           │
├─────────────────────────────────────────────────────┤
│  Transforms                                         │
│  MoM/QoQ/YoY, smoothing, seasonal, statistics       │
├─────────────────────────────────────────────────────┤
│  API Clients + Cache                                │
│  FRED, BEA, BLS clients → Parquet cache layer        │
├─────────────────────────────────────────────────────┤
│  Series Hierarchies                                 │
│  SeriesNode trees with multi-API source mappings     │
└─────────────────────────────────────────────────────┘
```

**Data flow**: A notebook asks for a series → the appropriate client checks the Parquet cache → on miss, it calls the federal API, caches the result, and returns a normalized DataFrame → the notebook applies transforms and renders Plotly charts.

---

## Series Hierarchies

### Data Model

Every economic series is represented as a `SeriesNode` in a tree. Each node carries one or more `SeriesSource` objects that map it to a concrete API endpoint:

```python
SeriesSource(source="fred", series_id="CPIAUCSL")
SeriesSource(source="bls",  series_id="CUSR0000SA0", extra={"item_code": "SA0", "seasonal": "S"})
SeriesSource(source="bea",  series_id="T20805",      extra={"table": "T20805", "line_number": 1})
```

`SeriesNode` provides tree traversal methods:

| Method | Description |
|---|---|
| `walk()` | Pre-order generator over all nodes |
| `find(code)` | Depth-first search by code |
| `leaves()` | All leaf nodes (actual data series) |
| `path()` | List of codes from root to this node |
| `print_tree()` | Formatted text dump of the full tree |
| `to_dict()` | Nested dict for JSON export |
| `get_source("fred")` | Return the FRED source for this node, or None |

### PCE — Personal Consumption Expenditures

**27 nodes, 21 leaves.** Built by `build_pce_tree()` in `series/pce.py`.

```
PCE [PCE]  (FRED: PCE, PCEC96 · BEA: T20805)
├── Goods [PCE_GOODS]  (FRED: DGDSRC1)
│   ├── Durable Goods [PCE_DUR]  (FRED: PCDG)
│   │   ├── Motor vehicles and parts
│   │   ├── Furnishings and durable household equipment
│   │   ├── Recreational goods and vehicles
│   │   └── Other durable goods
│   └── Nondurable Goods [PCE_NONDUR]  (FRED: PCND)
│       ├── Food and beverages for off-premises consumption
│       ├── Clothing and footwear
│       ├── Gasoline and other energy goods
│       └── Other nondurable goods
├── Services [PCE_SVC]  (FRED: PCES)
│   ├── Housing and utilities
│   ├── Health care
│   ├── Transportation services
│   ├── Recreation services
│   ├── Food services and accommodations
│   ├── Financial services and insurance
│   └── Other services
└── PCE Price Indexes [PCE_PRICE]
    ├── PCE Price Index [PCEPI]  (FRED: PCEPI)
    └── Core PCE Price Index [PCEPILFE]  (FRED: PCEPILFE)
```

BEA tables follow the NIPA naming convention `T{section}{family:02d}{metric}`:
- T20805 / T20806 = monthly current-dollar / chained-dollar PCE
- T20804 = monthly PCE price indexes
- Metric suffixes: 01=% change real, 04=price index, 05=current $, 06=chained $

### GDP — Gross Domestic Product

**29 nodes, 17 leaves.** Built by `build_gdp_tree()` in `series/gdp.py`. Supports `include_pce_detail=True` to attach the full PCE subtree under the consumption component.

```
GDP [GDP]  (FRED: GDP, GDPC1 · BEA: T10105)
├── C: Personal Consumption Expenditures [GDP_PCE]
├── I: Gross Private Domestic Investment [GPDI]  (FRED: GPDI)
│   ├── Fixed Investment [FPI]  (FRED: FPI)
│   │   ├── Nonresidential [PNFI]  (FRED: PNFI)
│   │   │   ├── Structures
│   │   │   ├── Equipment
│   │   │   └── Intellectual Property Products
│   │   └── Residential [PRFI]  (FRED: PRFI)
│   └── Change in Private Inventories [CBI]  (FRED: CBI)
├── G: Government Consumption & Investment [GCE]  (FRED: GCE)
│   ├── Federal
│   │   ├── National Defense
│   │   └── Nondefense
│   └── State and Local
└── NX: Net Exports [NETEXP]  (FRED: NETEXP)
    ├── Exports [EXPGS]  (FRED: EXPGS)
    │   ├── Goods
    │   └── Services
    └── Imports [IMPGS]  (FRED: IMPGS)
        ├── Goods
        └── Services
```

### CPI — Consumer Price Index

**81 nodes, 58 leaves.** Built by `build_cpi_tree()` in `series/cpi.py`. The most detailed hierarchy, mirroring the BLS CPI-U item structure.

```
CPI-U All Items [CPI]  (FRED: CPIAUCSL · BLS: CUSR0000SA0)
├── Food and Beverages [CPI_FOOD]  (item: SAF)
│   ├── Food at home (SAF1) → Cereals, Meats, Dairy, Fruits/veg, ...
│   ├── Food away from home (SEFV)
│   └── Alcoholic beverages (SAF2)
├── Housing [CPI_HOUSING]  (item: SAH)
│   ├── Shelter (SAH1) → Rent of primary, OER, Lodging away
│   ├── Fuels and utilities (SAH2) → Electricity, Gas, Fuel oil
│   └── Household furnishings (SAH3)
├── Apparel [CPI_APPAREL]  (item: SAA)
├── Transportation [CPI_TRANSPORT]  (item: SAT)
│   ├── New vehicles, Used vehicles, Motor fuel, Insurance, Airline fares, ...
├── Medical Care [CPI_MEDICAL]  (item: SAM)
│   ├── Medical commodities (SAM1), Medical services (SAM2)
├── Recreation [CPI_REC]  (item: SAR)
├── Education and Communication [CPI_EDU]  (item: SAE)
├── Other Goods and Services [CPI_OTHER]  (item: SAG)
└── Special Aggregates [CPI_SPECIAL]
    ├── Core CPI (SA0L1E · FRED: CPILFESL)
    ├── Energy (SA0E)
    ├── All items less shelter (SA0L2)
    ├── Commodities (SAC), Services (SAS)
    └── Supercore / Services less rent of shelter (SASLE)
```

**BLS series ID construction**: `CU{S|U}R0000{item_code}` where S=seasonally adjusted, U=not adjusted. For example, CPI-U All Items SA = `CUSR0000SA0`.

### Employment — CES and CPS

Two separate trees, returned as a tuple by `build_employment_trees()` in `series/employment.py`.

**CES (Current Employment Statistics / Establishment Survey)**
62 nodes, 46 leaves. Payroll employment by industry.

```
Total Nonfarm [NFP]  (BLS: CES0000000001 · FRED: PAYEMS)
├── Total Private [PRIVATE]  (BLS: CES0500000001)
│   ├── Goods-Producing [GOODS]
│   │   ├── Mining and Logging, Construction
│   │   └── Manufacturing → Durable / Nondurable goods
│   └── Private Service-Providing [PRIV_SVC]
│       ├── Trade, Transportation, and Utilities
│       ├── Information
│       ├── Financial Activities
│       ├── Professional and Business Services
│       ├── Education and Health Services
│       ├── Leisure and Hospitality
│       └── Other Services
└── Government [GOVT]
    ├── Federal, State, Local
```

CES series ID format: `CE{S|U}{industry_code_8}{data_type_2}` — swap the last 2 digits to get different measures: `01`=all employees, `03`=avg hourly earnings, `06`=production workers.

**CPS (Current Population Survey / Household Survey)**
32 nodes, 24 leaves. Unemployment, labor force, demographics.

```
CPS Headline Measures
├── Unemployment Rate [UNRATE]  (FRED: UNRATE)
├── Labor Force Participation Rate [CIVPART]  (FRED: CIVPART)
├── Employment-Population Ratio [EMRATIO]  (FRED: EMRATIO)
├── Alternative Measures → U-1 through U-6
└── Demographics → By age group, gender, race
```

---

## API Clients

All three clients extend `BaseClient`, which provides:
- A shared `ParquetCacheStore` (check cache before hitting the network)
- Rate limiting (`time.sleep` between requests)
- A normalized return format: `pd.DataFrame` with a `DatetimeIndex` named `date` and a `value` column

### FRED Client (`clients/fred.py`)

Wraps the `fredapi` library. FRED is the primary data source for headline series.

| Method | Description |
|---|---|
| `fetch_series(series_id, start, end)` | Fetch one series → DataFrame |
| `fetch_node(node)` | Fetch using the node's FRED source |
| `get_series_info(series_id)` | Series metadata (title, frequency, units) |
| `search(text)` | Search FRED for series by keyword |

Rate limit: 120 requests/minute. The client sleeps 0.5s between requests by default.

### BEA Client (`clients/bea.py`)

Direct HTTP GET to the BEA NIPA API. Fetches and caches entire tables at once (a single API call returns all line items for a table), then filters to the requested line number.

| Method | Description |
|---|---|
| `fetch_nipa_table(table, frequency, years)` | Fetch a full NIPA table → DataFrame |
| `fetch_series(table, line_number, ...)` | Extract one line from a NIPA table |
| `list_tables()` | List available NIPA tables |

The `TimePeriod` field is parsed from formats like `"2024Q3"`, `"2024M09"`, `"2024"` into proper datetime indexes.

### BLS Client (`clients/bls.py`)

POST requests to the BLS v2 API. Supports batch fetching (up to 50 series per request).

| Method | Description |
|---|---|
| `fetch_series(series_id, start_year, end_year)` | Fetch one series → DataFrame |
| `fetch_multiple(series_ids, start_year, end_year)` | Batch fetch → dict of DataFrames |
| `fetch_node_tree(root, start_year, end_year)` | Fetch all leaf nodes in a tree |

The response parser skips period `M13` (annual average) and constructs dates from `{year}-{period[1:]}-01`.

---

## Caching

The `ParquetCacheStore` (`cache/store.py`) avoids redundant API calls:

- **Storage**: Each cached series is a `.parquet` file + a `.json` sidecar with metadata (source, timestamp, params).
- **Key generation**: `make_key(source, series_id, **params)` produces a SHA-256 hash (truncated to 16 hex chars) of the inputs.
- **TTL**: 24 hours by default. Expired entries are treated as cache misses.
- **Location**: `data/cache/` directory (git-ignored).

| Method | Description |
|---|---|
| `get(key)` | Return cached DataFrame or None if expired/missing |
| `put(key, df, metadata)` | Write DataFrame + JSON sidecar |
| `invalidate(key)` | Delete a specific cache entry |
| `clear_all()` | Wipe the entire cache |
| `list_entries()` | Show all cached keys with metadata |

---

## Transforms

All transform functions accept a DataFrame with a `value` column (the standard output from any client) and return a `pd.Series`.

### Rate-of-Change (`transforms/changes.py`)

| Function | Formula | Typical Use |
|---|---|---|
| `mom_change(df)` | `pct_change() × 100` | Monthly percent change |
| `mom_annualized(df)` | `((1 + r)^12 − 1) × 100` | Annualized monthly rate (e.g., PCE inflation) |
| `qoq_change(df)` | `pct_change() × 100` | Quarterly percent change |
| `qoq_annualized(df)` | `((1 + r)^4 − 1) × 100` | GDP SAAR |
| `yoy_change(df, periods=12)` | `pct_change(12) × 100` | Year-over-year (use `periods=4` for quarterly) |
| `level_change(df, periods=1)` | `diff(1)` | Payroll gains (thousands) |
| `annualized_rate_from_index(df, periods, factor)` | `(P_t/P_{t-n})^(factor/n) − 1) × 100` | Annualized rate from price index |
| `n_month_annualized(df, n=3)` | Calls `annualized_rate_from_index` with n | 3-month / 6-month annualized inflation |

### Level Conversions (`transforms/levels.py`)

| Function | Description |
|---|---|
| `rebase_index(df, base_period)` | Rebase a price index so that `base_period = 100` |
| `real_from_nominal(nominal, deflator)` | Convert current $ to chained $ via `nominal / deflator × 100` |
| `contribution_to_change(component, aggregate)` | Share-weighted contribution to aggregate percent change |

### Smoothing (`transforms/smoothing.py`)

| Function | Description |
|---|---|
| `moving_average(df, window=3, center=False)` | Simple rolling mean (3, 6, or 12 months) |
| `exponential_smoothing(df, span=12)` | Exponentially weighted moving average |

### Seasonal Analysis (`transforms/seasonal.py`)

| Function | Description |
|---|---|
| `compare_sa_nsa(sa, nsa)` | Returns DataFrame with `sa`, `nsa`, and `seasonal_factor` columns |
| `seasonal_factor(sa, nsa)` | Returns `NSA / SA` ratio as a Series |

### Statistical Tests (`transforms/statistics.py`)

| Function | Returns | What it Tests |
|---|---|---|
| `adf_test(series)` | `StationarityResult` | Augmented Dickey-Fuller unit root test. H0: non-stationary. |
| `kpss_test(series)` | `StationarityResult` | KPSS stationarity test. H0: stationary. |
| `compute_acf_pacf(series, nlags=24)` | `(acf, pacf)` arrays | Autocorrelation and partial autocorrelation |
| `ljung_box_test(series, lags=12)` | DataFrame | Ljung-Box test for autocorrelation up to lag k |
| `durbin_watson(series)` | `float` | Serial correlation in residuals (2.0 = none) |
| `stl_decompose(series, period=None)` | STL result object | Seasonal-Trend decomposition (auto-detects period: 12 for monthly, 4 for quarterly) |

The `StationarityResult` dataclass bundles `test_name`, `statistic`, `p_value`, `critical_values`, `is_stationary` (bool), and a human-readable `summary`.

---

## Visualization

### Charts (`viz/charts.py`)

All chart functions return a `plotly.graph_objects.Figure`.

| Function | Description |
|---|---|
| `line_chart(data, title)` | Multi-series line chart. `data` is a `{label: DataFrame}` dict. |
| `bar_chart(data, title)` | Grouped bar chart (e.g., monthly payroll changes) |
| `stacked_bar_contributions(data, title)` | Stacked bar for component contributions (e.g., GDP) |
| `acf_pacf_plot(acf, pacf, title)` | Side-by-side ACF and PACF bar charts |
| `stl_plot(stl_result, title)` | 4-panel STL decomposition (observed, trend, seasonal, residual) |
| `heatmap_table(df, title)` | Color-coded heatmap (e.g., CPI components × months) |
| `recession_shading(fig)` | Adds gray NBER recession bands (1948–2020) to any figure |

### Widgets (`viz/widgets.py`)

Interactive `ipywidgets` for use inside notebooks:

| Widget | Description |
|---|---|
| `build_tree_widget(root, on_select)` | Nested Accordion reflecting the series hierarchy; leaf nodes are clickable buttons |
| `series_selector(nodes)` | Multi-select list for choosing series to compare |
| `transform_selector()` | Dropdown with options: Level, MoM %, MoM Annualized, QoQ Annualized, YoY %, 3/6/12m MA, 3/6m Annualized |
| `date_range_picker()` | Start/end date picker pair |

### Styles (`viz/styles.py`)

- `COLORS` — named color palette for consistent chart styling across reports
- `DEFAULT_LAYOUT` — shared Plotly layout defaults
- `RECESSION_DATES` — list of `(start, end)` tuples for NBER recessions (1948–2020)
- `format_date_axis(fig)` — helper for date axis formatting

---

## Notebooks

| Notebook | Focus | Key Analyses |
|---|---|---|
| **01_overview.ipynb** | Cross-report dashboard | Headline indicators table, multi-line chart across PCE/CPI/GDP/Employment, recession shading |
| **02_pce.ipynb** | Consumer spending | Tree widget navigation, Goods vs Services split, durable/nondurable breakdown, PCE price index (headline vs core), BEA detailed tables, ADF/KPSS stationarity tests |
| **03_gdp.ipynb** | National output | Real vs nominal GDP, C+I+G+NX contribution stacked bars, investment breakdown (structures/equipment/IP), government & trade detail, GDP deflator comparison |
| **04_cpi.ipynb** | Consumer prices | Tree widget, headline vs core CPI, major group heatmap, shelter deep-dive (rent vs OER), energy prices, SA vs NSA comparison, Ljung-Box & Durbin-Watson tests |
| **05_employment.ipynb** | Labor market | Nonfarm payrolls level & monthly changes, sector breakdown, average hourly earnings & hours trends, CPS dashboard, U-1 through U-6, demographic breakdowns |

Each notebook follows the same pattern:
1. Build the series tree and display it
2. Fetch data from FRED (or BEA/BLS for detail)
3. Apply transforms (rate of change, smoothing, etc.)
4. Render interactive Plotly charts with recession shading
5. Run statistical tests where appropriate

---

## Project Structure

```
macro_econ/
├── pyproject.toml                          # uv/hatch project config
├── .python-version                         # Python 3.11
├── .env.example                            # Template for API keys
├── .gitignore
├── README.md
├── src/macro_econ/
│   ├── __init__.py
│   ├── config.py                           # API keys, cache paths, NIPA table helpers
│   ├── series/
│   │   ├── node.py                         # SeriesNode + SeriesSource dataclasses
│   │   ├── pce.py                          # build_pce_tree() → 27 nodes
│   │   ├── gdp.py                          # build_gdp_tree() → 29 nodes
│   │   ├── cpi.py                          # build_cpi_tree() → 81 nodes
│   │   └── employment.py                   # build_employment_trees() → 62 CES + 32 CPS
│   ├── clients/
│   │   ├── base.py                         # Abstract BaseClient (cache, rate limit, normalize)
│   │   ├── fred.py                         # FRED via fredapi
│   │   ├── bea.py                          # BEA NIPA via HTTP GET
│   │   └── bls.py                          # BLS v2 via HTTP POST (batch 50)
│   ├── cache/
│   │   └── store.py                        # ParquetCacheStore + JSON sidecar
│   ├── transforms/
│   │   ├── changes.py                      # MoM, QoQ, YoY, annualized rates
│   │   ├── levels.py                       # Rebase, real from nominal, contributions
│   │   ├── smoothing.py                    # Moving average, exponential smoothing
│   │   ├── seasonal.py                     # SA vs NSA comparison
│   │   └── statistics.py                   # ADF, KPSS, ACF/PACF, Ljung-Box, DW, STL
│   └── viz/
│       ├── charts.py                       # Plotly line/bar/heatmap/ACF/STL charts
│       ├── widgets.py                      # ipywidgets tree navigator, selectors
│       └── styles.py                       # Colors, layout defaults, recession dates
├── notebooks/
│   ├── 01_overview.ipynb
│   ├── 02_pce.ipynb
│   ├── 03_gdp.ipynb
│   ├── 04_cpi.ipynb
│   └── 05_employment.ipynb
├── data/cache/                             # Parquet cache (git-ignored)
└── tests/
    ├── conftest.py                         # Shared fixtures
    ├── test_node.py                        # 17 tests: tree traversal, find, leaves, path
    ├── test_cache.py                       # 9 tests: put/get, TTL expiry, invalidation
    └── test_transforms.py                  # 15 tests: known-value checks for all transforms
```

---

## Testing

```bash
# Run all 41 tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run a specific test file
uv run pytest tests/test_transforms.py
```

Tests are self-contained (no API keys required). They use synthetic data and known-value assertions to verify:
- **test_node.py** (17 tests): Tree construction, `walk()`, `find()`, `leaves()`, `path()`, `add_child()`, `to_dict()`, parent/level linkage
- **test_cache.py** (9 tests): `put`/`get` round-trip, TTL expiry, `invalidate`, `clear_all`, `list_entries`
- **test_transforms.py** (15 tests): `mom_change`, `mom_annualized`, `qoq_annualized`, `yoy_change`, `level_change`, `rebase_index`, `real_from_nominal`, `moving_average`, `exponential_smoothing`, `adf_test`, `kpss_test`, `compute_acf_pacf`, `ljung_box_test`, `durbin_watson`

---

## API Keys

All three APIs are free but require registration:

| API | Registration Link | Env Variable |
|---|---|---|
| **FRED** (Federal Reserve Economic Data) | https://fred.stlouisfed.org/docs/api/api_key.html | `FRED_API_KEY` |
| **BEA** (Bureau of Economic Analysis) | https://apps.bea.gov/API/signup/ | `BEA_API_KEY` |
| **BLS** (Bureau of Labor Statistics) | https://data.bls.gov/registrationEngine/ | `BLS_API_KEY` |

Add your keys to `.env`:

```
FRED_API_KEY=your_key_here
BEA_API_KEY=your_key_here
BLS_API_KEY=your_key_here
```

The BLS API works without a key (v1) but is limited to 25 series per request and 10 years of data. Registration unlocks v2 with 50 series and 20 years per request.
