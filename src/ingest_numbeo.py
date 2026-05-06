import io
import logging

import pandas as pd
import requests

from src import config

logger = logging.getLogger(__name__)

NUMBEO_URL = config.NUMBEO_URL
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; cost-of-living-dashboard/1.0)"}


def fetch_numbeo_rankings(year: int = 2024) -> pd.DataFrame:
    """Scrape Numbeo cost-of-living country rankings table (id='t2').

    Returns the raw table as a DataFrame — no cleaning applied.
    """
    url = f"{NUMBEO_URL}?title={year}"
    logger.info("Fetching Numbeo rankings from %s", url)

    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(io.StringIO(resp.text), attrs={"id": "t2"})
    if not tables:
        raise RuntimeError("Could not find rankings table (id='t2') on Numbeo page")

    df = tables[0]
    logger.info("Fetched %d rows from Numbeo", len(df))
    return df
