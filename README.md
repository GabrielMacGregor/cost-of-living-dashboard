# Global Cost of Living vs Developer Salaries

A storytelling dashboard that compares cost of living and developer salaries across countries to surface affordability insights.

## Project Goal
Transform raw public datasets into clear, recruiter-friendly insights.

## Data Sources
- Numbeo: cost of living by city/country
- Stack Overflow Developer Survey: global developer salary data
- World Bank Open Data: macroeconomic context by country

## Folder Structure
```text
cost-of-living-dashboard/
+-- data/
|   +-- raw/
|   +-- processed/
+-- notebooks/
|   +-- eda.ipynb
+-- src/
|   +-- etl.py
|   +-- charts.py
+-- tests/
|   +-- test_etl.py
+-- .github/workflows/ci.yml
+-- app.py
+-- requirements.txt
+-- Dockerfile
+-- README.md
```

## Dashboard Pages
- Overview: world map with cost-of-living signal
- Salaries: median developer salary by country
- Affordability: index = salary / cost_of_living
- Insights: 3-5 written conclusions in English

## Quickstart
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python src/etl.py
streamlit run app.py
```

If you do not have real raw files yet, the app still runs with bundled example data in
`data/processed/example_country_affordability.csv`.

## Raw Data Contract
Create these two files in `data/raw/` before running ETL:

- `cost_of_living.csv` columns:
  - `country`
  - `cost_of_living_index`
  - `iso3`
  - `region`
- `developer_salaries.csv` columns:
  - `country`
  - `median_salary_usd`

Template files are available:
- `data/raw/cost_of_living_template.csv`
- `data/raw/developer_salaries_template.csv`

## Docker
```bash
docker build -t cost-of-living-dashboard .
docker run -p 8501:8501 cost-of-living-dashboard
```

## Tests
```bash
pytest -q
```

## CI
GitHub Actions runs lint (`ruff`) and tests (`pytest`) on pushes and pull requests to `main`.

## Demo
Add your dashboard GIF here after deployment:

![Demo GIF](docs/demo.gif)

## Key Insights
1. Add 3-5 data-backed insights after your first full ETL run.
2. Keep statements quantitative and easy to scan.
3. Tie conclusions to recruiter-relevant decisions (location, compensation, purchasing power).

## Deployment
Deploy for free with Streamlit Cloud and paste the public URL in this README.

## Streamlit Cloud (Checklist)
1. Push this repo to GitHub.
2. Go to Streamlit Cloud and click "New app".
3. Select repo `GabrielMacGregor/cost-of-living-dashboard`.
4. Set main file path to `app.py`.
5. Deploy and copy the public app URL into this README.
