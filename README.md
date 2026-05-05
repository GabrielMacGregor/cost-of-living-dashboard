# Global Cost of Living vs Developer Salaries

A storytelling dashboard that compares cost of living and developer salaries across countries to surface affordability insights.

## Project Goal

Transform raw public datasets into clear, recruiter-friendly insights about where developers get the most purchasing power for their salaries.

## Data Sources

All data is fetched automatically — no manual downloads needed.

| Source | What it provides | API |
|---|---|---|
| [Numbeo](https://www.numbeo.com/cost-of-living/) | Cost of living index by country | HTML scrape (no key) |
| [Stack Overflow Survey 2024](https://survey.stackoverflow.co/2024/) | Developer compensation in local currency | TidyTuesday mirror |
| [World Bank Open Data](https://data.worldbank.org/) | Country metadata: iso3, region | REST API (no key) |
| [Open Exchange Rates](https://open.er-api.com/) | USD exchange rates for currency conversion | Free tier (no key) |

## Architecture

This project follows the **medallion architecture**:

```
Ingest → Bronze (raw) → Silver (cleaned per source) → Gold (merged + metrics)
```

```text
cost-of-living-dashboard/
├── data/
│   ├── bronze/          # raw ingested data (auto-generated, git-ignored)
│   ├── silver/          # cleaned per-source data (auto-generated, git-ignored)
│   └── gold/            # final merged dataset (auto-generated, git-ignored)
├── notebooks/
│   └── eda.ipynb
├── src/
│   ├── pipeline.py          # orchestrates all 6 steps
│   ├── bronze.py            # save/load bronze layer
│   ├── silver.py            # clean Numbeo + SO data, enrich with World Bank
│   ├── gold.py              # merge silver layers, compute affordability index
│   ├── ingest_numbeo.py     # fetch Numbeo rankings
│   ├── ingest_stackoverflow.py  # fetch SO survey
│   ├── ingest_worldbank.py  # fetch World Bank country metadata
│   ├── ingest_exchange_rates.py  # fetch USD exchange rates
│   └── charts.py            # Plotly chart helpers
├── tests/
│   ├── test_etl.py          # gold layer unit tests
│   └── test_silver.py       # silver layer unit tests
├── .github/workflows/ci.yml
├── app.py
├── requirements.txt
└── Dockerfile
```

## Quickstart

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Fetch data from all sources and build the gold layer (~2 min, requires internet)
python -m src.pipeline

# Launch the dashboard
streamlit run app.py
```

The dashboard also runs without executing the pipeline — it falls back to bundled example data.

## Dashboard Pages

- **Overview**: world map with cost-of-living signal
- **Salaries**: top 20 median developer salaries by country
- **Affordability**: scatter plot of salary vs cost of living, colored by region
- **Insights**: data-backed written conclusions

## Affordability Index

```
affordability_index = median_salary_usd / cost_of_living_index
```

Higher is better — it captures how far a developer's salary goes relative to local costs.

## Docker

```bash
docker build -t cost-of-living-dashboard .
docker run -p 8501:8501 cost-of-living-dashboard
```

> The Docker image does not run the pipeline automatically. Either run `python -m src.pipeline` before building, or mount a pre-built `data/gold/` volume.

## Tests

```bash
pytest -q
```

## CI

GitHub Actions runs lint (`ruff`) and tests (`pytest`) on every push and pull request to `main`.

## Deployment

Deploy for free with [Streamlit Cloud](https://streamlit.io/cloud):

1. Push this repo to GitHub.
2. Go to Streamlit Cloud and click **New app**.
3. Select repo `GabrielMacGregor/cost-of-living-dashboard`.
4. Set main file path to `app.py`.
5. Deploy and paste the public URL here.

**Live demo**: _add URL after deployment_
