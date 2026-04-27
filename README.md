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
¦   +-- raw/
¦   +-- processed/
+-- notebooks/
¦   +-- eda.ipynb
+-- src/
¦   +-- etl.py
¦   +-- charts.py
+-- tests/
¦   +-- test_etl.py
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
