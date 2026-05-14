from pathlib import Path

# Medallion layer paths
BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")
GOLD_FILE = GOLD_DIR / "country_affordability.csv"
EXAMPLE_GOLD_FILE = GOLD_DIR / "example_country_affordability.csv"
PIPELINE_SUMMARY_FILE = GOLD_DIR / "pipeline_run_summary.json"
EXAMPLE_PIPELINE_SUMMARY_FILE = GOLD_DIR / "example_pipeline_run_summary.json"

# Pipeline defaults
DEFAULT_YEAR: int = 2024
SALARY_OUTLIER_THRESHOLD: float = 1_000_000
TOP_N_COUNTRIES: int = 20

# Data source URLs
NUMBEO_URL = "https://www.numbeo.com/cost-of-living/rankings_by_country.jsp"
SO_SURVEY_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main"
    "/data/2024/2024-09-03/stackoverflow_survey_single_response.csv"
)
WB_URL = "https://api.worldbank.org/v2/country?format=json&per_page=300"
ER_API_URL = "https://open.er-api.com/v6/latest/USD"
