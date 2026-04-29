import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

WB_URL = "https://api.worldbank.org/v2/country?format=json&per_page=300"


def fetch_worldbank_countries() -> pd.DataFrame:
    """Fetch country metadata from the World Bank REST API (no key required).

    Returns a DataFrame with columns: name, iso3, region.
    Aggregate entries (e.g. 'World', 'High income') are excluded.
    """
    logger.info("Fetching country metadata from World Bank API")

    resp = requests.get(WB_URL, timeout=30)
    resp.raise_for_status()

    # Response format: [pagination_metadata, [country_objects]]
    countries = resp.json()[1]

    rows = [
        {
            "name": c["name"],
            "iso3": c["id"],
            "region": c["region"]["value"],
        }
        for c in countries
        if c.get("region") and c["region"]["value"] != "Aggregates"
    ]

    df = pd.DataFrame(rows)
    logger.info("Fetched %d countries from World Bank", len(df))
    return df
