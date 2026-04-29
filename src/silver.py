import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SILVER_DIR = Path("data/silver")

# Numbeo uses country names that differ from the World Bank. This map normalises
# the most common mismatches before the join so we retain as many countries as possible.
_NUMBEO_TO_WB: dict[str, str] = {
    "South Korea": "Korea, Rep.",
    "North Korea": "Korea, Dem. People's Rep.",
    "Russia": "Russian Federation",
    "Hong Kong": "Hong Kong SAR, China",
    "Macao": "Macao SAR, China",
    "Taiwan": "Taiwan, China",
    "Venezuela": "Venezuela, RB",
    "Syria": "Syrian Arab Republic",
    "Iran": "Iran, Islamic Rep.",
    "Vietnam": "Viet Nam",
    "Czech Republic": "Czechia",
    "Ivory Coast": "Côte d'Ivoire",
    "Palestine": "West Bank and Gaza",
    "Bolivia": "Bolivia",
    "Tanzania": "Tanzania",
    "Congo": "Congo, Rep.",
    "DR Congo": "Congo, Dem. Rep.",
    "Egypt": "Egypt, Arab Rep.",
    "Yemen": "Yemen, Rep.",
    "Kyrgyzstan": "Kyrgyz Republic",
    "Slovakia": "Slovak Republic",
    "Laos": "Lao PDR",
    "Gambia": "Gambia, The",
    "Bahamas": "Bahamas, The",
    "Macedonia": "North Macedonia",
    "United States": "United States",
}


def process_cost_of_living(raw_df: pd.DataFrame, wb_df: pd.DataFrame) -> pd.DataFrame:
    """Clean Numbeo raw data and enrich each country with iso3 and region.

    raw_df must contain at minimum a 'Country' column and a column whose
    lower-cased name contains 'cost of living index'.
    wb_df must have columns: name, iso3, region (from ingest_worldbank).
    """
    df = raw_df.copy()

    # Normalise column names to snake_case
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    cost_col = next((c for c in df.columns if "cost_of_living_index" in c), None)
    if cost_col is None:
        raise ValueError("Could not find 'cost of living index' column in Numbeo data")

    df = df.rename(columns={"country": "country", cost_col: "cost_of_living_index"})
    df = df[["country", "cost_of_living_index"]].copy()
    df["country"] = df["country"].astype(str).str.strip()
    df["cost_of_living_index"] = pd.to_numeric(df["cost_of_living_index"], errors="coerce")
    df = df.dropna(subset=["cost_of_living_index"])

    # Build World Bank lookup: normalised_name → {iso3, region}
    wb_lookup: dict[str, dict] = {
        row["name"]: {"iso3": row["iso3"], "region": row["region"]}
        for _, row in wb_df.iterrows()
    }

    def _enrich(country_name: str) -> tuple[str | None, str | None]:
        wb_name = _NUMBEO_TO_WB.get(country_name, country_name)
        entry = wb_lookup.get(wb_name)
        if entry:
            return entry["iso3"], entry["region"]
        return None, None

    enriched = df["country"].map(lambda c: _enrich(c))
    df["iso3"] = enriched.map(lambda t: t[0])
    df["region"] = enriched.map(lambda t: t[1])

    before = len(df)
    df = df.dropna(subset=["iso3", "region"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Silver cost_of_living: dropped %d rows with no iso3/region match", dropped)

    logger.info("Silver cost_of_living: %d countries retained", len(df))
    return df.reset_index(drop=True)


def process_developer_salaries(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean Stack Overflow survey data and compute median annual salary by country.

    raw_df must have columns: Country, ConvertedCompYearly.
    Outliers above $1 000 000 USD are removed before computing the median.
    """
    df = raw_df.rename(columns={"Country": "country", "ConvertedCompYearly": "salary_usd"}).copy()
    df["country"] = df["country"].astype(str).str.strip()
    df["salary_usd"] = pd.to_numeric(df["salary_usd"], errors="coerce")
    df = df.dropna(subset=["salary_usd"])
    df = df[df["salary_usd"] <= 1_000_000]

    result = (
        df.groupby("country", as_index=False)["salary_usd"]
        .median()
        .rename(columns={"salary_usd": "median_salary_usd"})
    )

    logger.info("Silver developer_salaries: %d countries", len(result))
    return result


def save_silver(df: pd.DataFrame, name: str) -> Path:
    """Persist a cleaned DataFrame to the silver layer."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    path = SILVER_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info("Silver: saved %d rows → %s", len(df), path)
    return path


def load_silver(name: str) -> pd.DataFrame:
    """Load a previously saved silver artifact."""
    path = SILVER_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Silver artifact not found: {path}")
    return pd.read_csv(path)
