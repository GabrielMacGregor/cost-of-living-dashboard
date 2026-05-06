import logging

import requests

from src import config

logger = logging.getLogger(__name__)

ER_API_URL = config.ER_API_URL


def fetch_exchange_rates() -> dict[str, float]:
    """Fetch current USD exchange rates from the Open Exchange Rates API (no key required).

    Returns a dict mapping ISO 4217 currency code → units per 1 USD.
    Example: {"EUR": 0.92, "BRL": 5.1, "INR": 83.2, ...}

    Note: rates reflect the moment the pipeline runs, not the 2024 survey period.
    The raw snapshot is saved to the bronze layer (exchange_rates.csv) for traceability.
    """
    logger.info("Fetching exchange rates from %s", ER_API_URL)
    resp = requests.get(ER_API_URL, timeout=15)
    resp.raise_for_status()

    rates = resp.json().get("rates", {})
    logger.info("Fetched exchange rates for %d currencies", len(rates))
    return rates
