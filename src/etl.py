from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def affordability_index(salary_usd: pd.Series, cost_index: pd.Series) -> pd.Series:
    """Return affordability index as salary divided by cost index."""
    return salary_usd / cost_index.replace({0: pd.NA})


def build_country_dataset(cost_df: pd.DataFrame, salary_df: pd.DataFrame) -> pd.DataFrame:
    """Merge country-level cost-of-living and salary data and compute affordability."""
    merged = cost_df.merge(salary_df, on="country", how="inner")
    merged["affordability_index"] = affordability_index(
        merged["median_salary_usd"], merged["cost_of_living_index"]
    )
    return merged


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
    result.to_csv(PROCESSED_DIR / "country_affordability.csv", index=False)
    return result


if __name__ == "__main__":
    df = run_etl()
    print(f"Generated {len(df)} rows in data/processed/country_affordability.csv")
