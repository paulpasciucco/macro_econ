# Economic Statistics Viewer

Interactive Jupyter notebooks for exploring PCE, CPI, GDP, and Employment data from FRED, BEA, and BLS.

## Setup

```bash
# Install dependencies
uv sync

# Copy and fill in API keys
cp .env.example .env
# Edit .env with your keys

# Launch notebooks
uv run jupyter lab
```

## API Keys

- **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html
- **BEA**: https://apps.bea.gov/API/signup/
- **BLS**: https://data.bls.gov/registrationEngine/
