import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

BRONZE_DIR = Path("data/bronze")


def save_bronze(df: pd.DataFrame, name: str) -> Path:
    """Persist a raw ingested DataFrame to the bronze layer without any transformation."""
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    path = BRONZE_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info("Bronze: saved %d rows → %s", len(df), path)
    return path


def load_bronze(name: str) -> pd.DataFrame:
    """Load a previously saved bronze artifact."""
    path = BRONZE_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Bronze artifact not found: {path}")
    return pd.read_csv(path)
