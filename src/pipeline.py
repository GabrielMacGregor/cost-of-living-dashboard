import argparse
import logging
from pathlib import Path

import pandas as pd

from src import config
from src.bronze import save_bronze
from src.gold import build_gold_layer, save_gold
from src.ingest_exchange_rates import fetch_exchange_rates
from src.ingest_numbeo import fetch_numbeo_rankings
from src.ingest_stackoverflow import fetch_stackoverflow_salaries
from src.ingest_worldbank import fetch_worldbank_countries
from src.quality import PipelineRunSummary
from src.silver import process_cost_of_living, process_developer_salaries, save_silver

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the cost-of-living medallion pipeline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--year",
        type=int,
        default=config.DEFAULT_YEAR,
        help="Survey year to fetch from Numbeo",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.GOLD_DIR,
        help="Directory for gold layer output",
    )
    parser.add_argument(
        "--salary-outlier-threshold",
        type=float,
        default=config.SALARY_OUTLIER_THRESHOLD,
        dest="salary_outlier_threshold",
        help="Remove salaries (USD) above this value before computing medians",
    )
    return parser.parse_args()


def run_pipeline(
    year: int = config.DEFAULT_YEAR,
    output_dir: Path = config.GOLD_DIR,
    salary_outlier_threshold: float = config.SALARY_OUTLIER_THRESHOLD,
) -> None:
    """Execute the full medallion pipeline: ingest -> bronze -> silver -> gold."""
    logger.info("=== Pipeline start (year=%d) ===", year)
    summary = PipelineRunSummary(year=year)

    # --- Bronze: fetch raw data from each source ---
    logger.info("Step 1/6: Ingesting Numbeo rankings")
    numbeo_raw = fetch_numbeo_rankings(year=year)
    save_bronze(numbeo_raw, "numbeo_rankings")
    summary.record_source("numbeo", rows=len(numbeo_raw))

    logger.info("Step 2/6: Ingesting Stack Overflow survey")
    so_raw = fetch_stackoverflow_salaries()
    save_bronze(so_raw, "stackoverflow_survey")
    summary.record_source("stackoverflow", rows=len(so_raw))

    logger.info("Step 3/6: Ingesting World Bank country metadata")
    wb_raw = fetch_worldbank_countries()
    save_bronze(wb_raw, "worldbank_countries")
    summary.record_source("worldbank", rows=len(wb_raw))

    logger.info("Step 4/6: Ingesting exchange rates")
    exchange_rates = fetch_exchange_rates()
    save_bronze(
        pd.DataFrame(list(exchange_rates.items()), columns=["currency", "rate_per_usd"]),
        "exchange_rates",
    )
    summary.record_source("exchange_rates", rows=len(exchange_rates))

    # --- Silver: clean and normalise each source independently ---
    logger.info("Step 5/6: Building silver layer")

    numbeo_countries_before = set(numbeo_raw["Country"].astype(str))
    cost_silver = process_cost_of_living(numbeo_raw, wb_raw)
    save_silver(cost_silver, "cost_of_living")
    dropped_cost = sorted(numbeo_countries_before - set(cost_silver["country"]))
    summary.record_silver_cost(
        rows_in=len(numbeo_raw),
        rows_out=len(cost_silver),
        dropped_countries=dropped_cost,
    )

    salary_silver, salary_stats = process_developer_salaries(
        so_raw, exchange_rates, outlier_threshold=salary_outlier_threshold
    )
    save_silver(salary_silver, "developer_salaries")
    summary.record_silver_salaries(**salary_stats)

    # --- Gold: merge and compute the final business metric ---
    logger.info("Step 6/6: Building gold layer")
    cost_countries_before = set(cost_silver["country"])
    gold_df = build_gold_layer(cost_silver, salary_silver)
    gold_path = save_gold(gold_df, output_dir=output_dir)

    dropped_gold = sorted(cost_countries_before - set(gold_df["country"]))
    summary.record_gold(countries=len(gold_df), dropped_no_match=dropped_gold)
    summary.output_path = str(gold_path)
    summary.save(output_dir / "pipeline_run_summary.json")

    logger.info("=== Pipeline complete: %d countries in gold layer ===", len(gold_df))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _parse_args()
    run_pipeline(
        year=args.year,
        output_dir=args.output,
        salary_outlier_threshold=args.salary_outlier_threshold,
    )
