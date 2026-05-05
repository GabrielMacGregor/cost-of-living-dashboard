from pathlib import Path

# Medallion layer paths
BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")

# Pipeline defaults
DEFAULT_YEAR: int = 2024
SALARY_OUTLIER_THRESHOLD: float = 1_000_000
TOP_N_COUNTRIES: int = 20
