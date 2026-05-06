import io
import logging

import pandas as pd
import requests

from src import config

logger = logging.getLogger(__name__)

# TidyTuesday mirrors the Stack Overflow 2024 Developer Survey with a stable, public URL.
# Original source: https://survey.stackoverflow.co/2024/
SO_SURVEY_URL = config.SO_SURVEY_URL


def fetch_stackoverflow_salaries(url: str = SO_SURVEY_URL) -> pd.DataFrame:
    """Download the Stack Overflow Developer Survey 2024 and return salary rows.

    Returns a DataFrame with columns: country, currency, comp_total.
    Only respondents who reported compensation are included.
    """
    logger.info("Downloading Stack Overflow survey from %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), usecols=["country", "currency", "comp_total"])
    df = df.dropna(subset=["comp_total"])
    logger.info("Fetched %d salary rows from Stack Overflow survey", len(df))
    return df
