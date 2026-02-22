"""Central configuration: API keys, cache paths, defaults."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
BEA_API_KEY = os.getenv("BEA_API_KEY", "")
BLS_API_KEY = os.getenv("BLS_API_KEY", "")

# Cache TTL defaults (seconds)
DEFAULT_CACHE_TTL = 24 * 60 * 60  # 24 hours

# BLS API constants
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_MAX_SERIES_PER_REQUEST = 50
BLS_MAX_YEARS_PER_REQUEST = 20

# BEA API constants
BEA_API_URL = "https://apps.bea.gov/api/data/"

# NIPA table metric suffixes
NIPA_METRICS = {
    "pct_change_real": "01",
    "quantity_index": "03",
    "price_index": "04",
    "current_dollars": "05",
    "chained_dollars": "06",
    "pct_change_price": "07",
}


def nipa_table_variants(section: int, family: int) -> dict[str, str]:
    """Return {metric_name: table_code} for all standard NIPA metric types."""
    base = f"T{section}{family:02d}"
    return {name: f"{base}{suffix}" for name, suffix in NIPA_METRICS.items()}


def check_api_keys() -> dict[str, bool]:
    """Check which API keys are configured and print a status summary.

    Returns:
        Dict mapping API name to whether a key is present.
    """
    keys = {
        "FRED": bool(FRED_API_KEY),
        "BEA": bool(BEA_API_KEY),
        "BLS": bool(BLS_API_KEY),
    }

    registration_urls = {
        "FRED": "https://fred.stlouisfed.org/docs/api/api_key.html",
        "BEA": "https://apps.bea.gov/API/signup/",
        "BLS": "https://data.bls.gov/registrationEngine/",
    }

    for name, configured in keys.items():
        status = "OK" if configured else "MISSING"
        line = f"  {name:5s} {status}"
        if not configured:
            line += f"  -> Register at {registration_urls[name]}"
        print(line)

    if not keys["BLS"]:
        print("\n  Note: BLS works without a key (v1) but is limited to 25 series/10 years.")

    return keys
