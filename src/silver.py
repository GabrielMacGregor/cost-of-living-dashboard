import logging
from pathlib import Path

import pandas as pd

from src import config

logger = logging.getLogger(__name__)

SILVER_DIR = config.SILVER_DIR

# Numbeo country names → World Bank country names
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
}

# Stack Overflow uses ISO 3166-1 long names; map to World Bank short names
_SO_TO_WB: dict[str, str] = {
    "United States of America": "United States",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Venezuela (Bolivarian Republic of)": "Venezuela, RB",
    "Iran (Islamic Republic of)": "Iran, Islamic Rep.",
    "Republic of Korea": "Korea, Rep.",
    "Democratic People's Republic of Korea": "Korea, Dem. People's Rep.",
    "United Republic of Tanzania": "Tanzania",
    "Viet Nam": "Viet Nam",
    "Syrian Arab Republic": "Syrian Arab Republic",
    "Lao People's Democratic Republic": "Lao PDR",
    "Kyrgyzstan": "Kyrgyz Republic",
    "Slovakia": "Slovak Republic",
    "North Macedonia": "North Macedonia",
    "Congo, the Democratic Republic of the": "Congo, Dem. Rep.",
    "Congo": "Congo, Rep.",
    "Egypt": "Egypt, Arab Rep.",
    "Yemen": "Yemen, Rep.",
    "Gambia": "Gambia, The",
    "Bahamas": "Bahamas, The",
    "Palestine, State of": "West Bank and Gaza",
    "Taiwan, Province of China": "Taiwan, China",
    "Hong Kong": "Hong Kong SAR, China",
    "Macao": "Macao SAR, China",
    "Czech Republic": "Czechia",
    "Russia": "Russian Federation",
    "South Korea": "Korea, Rep.",
    "Ivory Coast": "Côte d'Ivoire",
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

    # Build World Bank lookup: wb_name → {iso3, region}
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

    # Normalise display name to World Bank standard
    df["country"] = df["country"].map(lambda c: _NUMBEO_TO_WB.get(c, c))

    before = len(df)
    df = df.dropna(subset=["iso3", "region"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Silver cost_of_living: dropped %d rows with no iso3/region match", dropped)

    logger.info("Silver cost_of_living: %d countries retained", len(df))
    return df.reset_index(drop=True)


def process_developer_salaries(
    raw_df: pd.DataFrame,
    exchange_rates: dict[str, float],
    outlier_threshold: float = config.SALARY_OUTLIER_THRESHOLD,
) -> tuple[pd.DataFrame, dict]:
    """Clean Stack Overflow survey data and compute median salary in USD by country.

    raw_df must have columns: country, currency, comp_total.
    exchange_rates maps ISO 4217 currency code → units per 1 USD (e.g. {"EUR": 0.92}).
    Salaries above outlier_threshold USD are treated as data errors and removed.

    Returns (result_df, stats) where stats contains quality metrics for the pipeline report.
    """
    df = raw_df.copy()
    df["country"] = df["country"].astype(str).str.strip()
    df["comp_total"] = pd.to_numeric(df["comp_total"], errors="coerce")
    df = df.dropna(subset=["comp_total"])
    rows_in = len(df)

    # Extract ISO 4217 code from strings like "EUR European Euro" or "USD\tUnited States dollar"
    df["currency_code"] = df["currency"].astype(str).str[:3].str.strip()

    # Convert to USD: local_amount / rate = USD amount
    def _to_usd(row) -> float | None:
        code = row["currency_code"]
        rate = exchange_rates.get(code)
        if rate and rate > 0:
            return row["comp_total"] / rate
        return None

    df["salary_usd"] = df.apply(_to_usd, axis=1)
    unknown_currencies = int(df["salary_usd"].isna().sum())
    df = df.dropna(subset=["salary_usd"])

    rows_before_outlier = len(df)
    df = df[df["salary_usd"] <= outlier_threshold]
    outliers_removed = rows_before_outlier - len(df)

    total_dropped = rows_in - len(df)
    if total_dropped:
        logger.warning(
            "Silver developer_salaries: dropped %d rows (unknown currency or outlier)",
            total_dropped,
        )

    # Normalise country names to World Bank standard
    df["country"] = df["country"].map(lambda c: _SO_TO_WB.get(c, c))

    result = (
        df.groupby("country", as_index=False)["salary_usd"]
        .median()
        .rename(columns={"salary_usd": "median_salary_usd"})
    )

    stats = {
        "rows_in": rows_in,
        "unknown_currencies": unknown_currencies,
        "outliers_removed": outliers_removed,
        "countries": len(result),
    }

    logger.info("Silver developer_salaries: %d countries", len(result))
    return result, stats


def save_silver(df: pd.DataFrame, name: str) -> Path:
    """Persist a cleaned DataFrame to the silver layer."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    path = SILVER_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info("Silver: saved %d rows -> %s", len(df), path)
    return path


def load_silver(name: str) -> pd.DataFrame:
    """Load a previously saved silver artifact."""
    path = SILVER_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Silver artifact not found: {path}")
    return pd.read_csv(path)
