import logging
from pathlib import Path

import pandas as pd

from src import config

logger = logging.getLogger(__name__)

GOLD_DIR = config.GOLD_DIR
GOLD_FILE = config.GOLD_FILE

_REQUIRED_COST = {"country", "cost_of_living_index", "iso3", "region"}
_REQUIRED_SALARY = {"country", "median_salary_usd"}


def affordability_index(salary_usd: pd.Series, cost_index: pd.Series) -> pd.Series:
    """Return salary / cost_index. Zero cost produces pd.NA (not inf)."""
    return salary_usd / cost_index.replace({0: pd.NA})


def _validate_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")


def build_gold_layer(cost_df: pd.DataFrame, salary_df: pd.DataFrame) -> pd.DataFrame:
    """Merge silver-quality cost and salary DataFrames and compute affordability.

    Both inputs are expected to be already clean (silver layer output).
    Returns a DataFrame sorted descending by affordability_index.
    """
    _validate_columns(cost_df, _REQUIRED_COST, "cost_of_living")
    _validate_columns(salary_df, _REQUIRED_SALARY, "developer_salaries")

    merged = cost_df.merge(salary_df, on="country", how="inner")
    logger.info("Gold: merged %d countries", len(merged))

    merged["affordability_index"] = affordability_index(
        merged["median_salary_usd"], merged["cost_of_living_index"]
    )

    before = len(merged)
    merged = merged.dropna(subset=["affordability_index"])
    if before - len(merged):
        logger.warning(
            "Gold: dropped %d row(s) with undefined affordability_index", before - len(merged)
        )

    return merged.sort_values("affordability_index", ascending=False).reset_index(drop=True)


def save_gold(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """Persist the gold layer to disk."""
    target_dir = output_dir if output_dir is not None else GOLD_DIR
    target = target_dir / "country_affordability.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
    logger.info("Gold: saved %d rows -> %s", len(df), target)
    return target


def load_gold() -> pd.DataFrame:
    """Load the gold layer from disk."""
    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"Gold layer not found: {GOLD_FILE}")
    return pd.read_csv(GOLD_FILE)
