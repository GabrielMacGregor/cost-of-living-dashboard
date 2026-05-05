import logging

import pandas as pd

from src.bronze import save_bronze
from src.gold import build_gold_layer, save_gold
from src.ingest_exchange_rates import fetch_exchange_rates
from src.ingest_numbeo import fetch_numbeo_rankings
from src.ingest_stackoverflow import fetch_stackoverflow_salaries
from src.ingest_worldbank import fetch_worldbank_countries
from src.silver import process_cost_of_living, process_developer_salaries, save_silver

logger = logging.getLogger(__name__)


def run_pipeline(year: int = 2024) -> None:
    """Execute the full medallion pipeline: ingest → bronze → silver → gold."""
    logger.info("=== Pipeline start (year=%d) ===", year)

    # --- Bronze: fetch raw data from each source ---
    logger.info("Step 1/6: Ingesting Numbeo rankings")
    numbeo_raw = fetch_numbeo_rankings(year=year)
    save_bronze(numbeo_raw, "numbeo_rankings")

    logger.info("Step 2/6: Ingesting Stack Overflow survey")
    so_raw = fetch_stackoverflow_salaries()
    save_bronze(so_raw, "stackoverflow_survey")

    logger.info("Step 3/6: Ingesting World Bank country metadata")
    wb_raw = fetch_worldbank_countries()
    save_bronze(wb_raw, "worldbank_countries")

    logger.info("Step 4/6: Ingesting exchange rates")
    exchange_rates = fetch_exchange_rates()
    save_bronze(
        pd.DataFrame(list(exchange_rates.items()), columns=["currency", "rate_per_usd"]),
        "exchange_rates",
    )

    # --- Silver: clean and normalise each source independently ---
    logger.info("Step 5/6: Building silver layer")
    cost_silver = process_cost_of_living(numbeo_raw, wb_raw)
    save_silver(cost_silver, "cost_of_living")

    salary_silver = process_developer_salaries(so_raw, exchange_rates)
    save_silver(salary_silver, "developer_salaries")

    # --- Gold: merge and compute the final business metric ---
    logger.info("Step 6/6: Building gold layer")
    gold_df = build_gold_layer(cost_silver, salary_silver)
    save_gold(gold_df)

    logger.info("=== Pipeline complete: %d countries in gold layer ===", len(gold_df))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_pipeline()
