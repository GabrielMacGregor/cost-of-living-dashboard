from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_FILE = PROCESSED_DIR / "country_affordability.csv"

REQUIRED_COST_COLUMNS = {"country", "cost_of_living_index", "iso3", "region"}
REQUIRED_SALARY_COLUMNS = {"country", "median_salary_usd"}


def affordability_index(salary_usd: pd.Series, cost_index: pd.Series) -> pd.Series:
    """Return affordability index as salary divided by cost index."""
    return salary_usd / cost_index.replace({0: pd.NA})


def _validate_columns(df: pd.DataFrame, required_columns: set[str], dataset_name: str) -> None:
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {sorted(missing)}")


def build_country_dataset(cost_df: pd.DataFrame, salary_df: pd.DataFrame) -> pd.DataFrame:
    """Merge country-level cost-of-living and salary data and compute affordability."""
    _validate_columns(cost_df, REQUIRED_COST_COLUMNS, "cost_of_living.csv")
    _validate_columns(salary_df, REQUIRED_SALARY_COLUMNS, "developer_salaries.csv")

    cost_df = cost_df.copy()
    salary_df = salary_df.copy()
    cost_df["country"] = cost_df["country"].astype(str).str.strip()
    salary_df["country"] = salary_df["country"].astype(str).str.strip()

    merged = cost_df.merge(salary_df, on="country", how="inner")
    merged["affordability_index"] = affordability_index(
        merged["median_salary_usd"], merged["cost_of_living_index"]
    )
    return merged.sort_values("affordability_index", ascending=False).reset_index(drop=True)


def write_example_raw_templates() -> None:
    """Write small template datasets to help first-time setup."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    cost_template = pd.DataFrame(
        [
            {"country": "Brazil", "cost_of_living_index": 42.0, "iso3": "BRA", "region": "Latin America"},
            {"country": "Germany", "cost_of_living_index": 68.0, "iso3": "DEU", "region": "Europe"},
            {"country": "Canada", "cost_of_living_index": 65.0, "iso3": "CAN", "region": "North America"},
        ]
    )
    salary_template = pd.DataFrame(
        [
            {"country": "Brazil", "median_salary_usd": 32000},
            {"country": "Germany", "median_salary_usd": 86000},
            {"country": "Canada", "median_salary_usd": 90000},
        ]
    )

    (RAW_DIR / "cost_of_living_template.csv").write_text(
        cost_template.to_csv(index=False), encoding="utf-8"
    )
    (RAW_DIR / "developer_salaries_template.csv").write_text(
        salary_template.to_csv(index=False), encoding="utf-8"
    )


def run_etl() -> pd.DataFrame:
    """Load raw CSVs and output processed merged dataset."""
    cost_path = RAW_DIR / "cost_of_living.csv"
    salary_path = RAW_DIR / "developer_salaries.csv"

    if not cost_path.exists() or not salary_path.exists():
        raise FileNotFoundError(
            "Missing raw files. Expected data/raw/cost_of_living.csv and "
            "data/raw/developer_salaries.csv"
        )

    cost_df = pd.read_csv(cost_path)
    salary_df = pd.read_csv(salary_path)

    result = build_country_dataset(cost_df, salary_df)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(PROCESSED_FILE, index=False)
    return result


if __name__ == "__main__":
    write_example_raw_templates()
    df = run_etl()
    print(f"Generated {len(df)} rows in {PROCESSED_FILE}")
