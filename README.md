# Global Cost of Living vs Developer Salaries

[![CI](https://github.com/GabrielMacGregor/cost-of-living-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/GabrielMacGregor/cost-of-living-dashboard/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

**[Live Demo →](https://cost-of-living-dashboard-e2mvrkamdujmsavrxvoihk.streamlit.app/)**

![Dashboard screenshot](docs/screenshot.png)
<!-- Add a screenshot after first deploy: grab a PNG of the dashboard and save it to docs/screenshot.png -->

A data product that compares developer salaries and cost of living across 120+ countries to surface affordability insights. Built with a fully automated medallion pipeline (bronze → silver → gold) and deployed as an interactive Streamlit dashboard.

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
│   ├── config.py            # central paths, URLs, and pipeline defaults
│   ├── bronze.py            # save/load bronze layer
│   ├── silver.py            # clean Numbeo + SO data, enrich with World Bank
│   ├── gold.py              # merge silver layers, compute affordability index
│   ├── quality.py           # pipeline quality report generation
│   ├── ingest_numbeo.py     # fetch Numbeo rankings
│   ├── ingest_stackoverflow.py  # fetch SO survey
│   ├── ingest_worldbank.py  # fetch World Bank country metadata
│   ├── ingest_exchange_rates.py  # fetch USD exchange rates
│   └── charts.py            # Plotly chart helpers
├── tests/
│   ├── test_etl.py          # gold layer unit tests
│   ├── test_silver.py       # silver layer unit tests
│   ├── test_pipeline.py     # pipeline orchestration and CLI tests
│   ├── test_quality.py      # quality report tests
│   └── test_charts.py       # chart helper tests
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

### Pipeline CLI

```bash
python -m src.pipeline \
  --year 2024 \
  --output data/gold \
  --salary-outlier-threshold 1000000
```

The pipeline writes:

- `data/bronze/*.csv`: raw source snapshots
- `data/silver/*.csv`: cleaned per-source datasets
- `data/gold/country_affordability.csv`: final dashboard dataset
- `data/gold/pipeline_run_summary.json`: quality and lineage report

## Dashboard Pages

- **Overview**: world map with cost-of-living signal
- **Salaries**: top 20 median developer salaries by country
- **Affordability**: scatter plot of salary vs cost of living, colored by region
- **Insights**: data-backed written conclusions
- **Data Quality**: latest pipeline run metrics, source row counts, and dropped-match details

## Affordability Index

```
affordability_index = median_salary_usd / cost_of_living_index
```

Higher is better — it captures how far a developer's salary goes relative to local costs.

## Methodology & Limitations

The pipeline builds a country-level affordability dataset from four public sources:

- Numbeo provides the country cost-of-living index.
- Stack Overflow Survey 2024 provides developer compensation in local currency.
- Open Exchange Rates converts compensation to USD.
- World Bank metadata standardizes country names, ISO3 codes, and regions.

Developer salaries are grouped by country using the median compensation after conversion to USD.
Rows with missing compensation, unknown currencies, unmatched countries, or salaries above
USD 1,000,000 are excluded as incomplete or likely outlier records.

Important limitations:

- Exchange rates are fetched at pipeline runtime, so results can shift between runs.
- Numbeo and Stack Overflow are not fully representative samples of every country.
- The index compares salary to a broad cost-of-living score; it does not model taxes, benefits,
  seniority mix, rent separately, family size, or local purchasing patterns.
- Countries only appear in the gold layer when both cost-of-living and salary data can be matched.

## Data Quality Report

Each full pipeline run creates `data/gold/pipeline_run_summary.json` with:

- run timestamp and selected year;
- raw row counts by source;
- silver-layer row counts and country coverage;
- unknown currency counts;
- removed salary outliers;
- countries dropped because no cross-source match was available;
- gold-layer match rate.

The dashboard reads this file in the **Data Quality** page when available. This makes the ETL
output auditable without opening intermediate CSV files manually.

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

**Live demo**: https://cost-of-living-dashboard-e2mvrkamdujmsavrxvoihk.streamlit.app/
