import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class PipelineRunSummary:
    """Collects per-step metrics for a single pipeline run and serializes to JSON."""

    def __init__(self, year: int) -> None:
        self.year = year
        self.run_at: str = datetime.now(timezone.utc).isoformat()
        self.sources: dict = {}
        self.silver: dict = {}
        self.gold: dict = {}
        self.output_path: str = ""

    def record_source(self, name: str, rows: int, url: str = "") -> None:
        self.sources[name] = {"rows": rows, "url": url}

    def record_silver_cost(
        self, rows_in: int, rows_out: int, dropped_countries: list[str]
    ) -> None:
        self.silver["cost_of_living"] = {
            "rows_in": rows_in,
            "rows_out": rows_out,
            "dropped": len(dropped_countries),
            "dropped_countries": dropped_countries,
        }

    def record_silver_salaries(
        self,
        rows_in: int,
        countries: int,
        unknown_currencies: int,
        outliers_removed: int,
    ) -> None:
        self.silver["developer_salaries"] = {
            "rows_in": rows_in,
            "unknown_currencies": unknown_currencies,
            "outliers_removed": outliers_removed,
            "countries": countries,
        }

    def record_gold(self, countries: int, dropped_no_match: list[str]) -> None:
        total = countries + len(dropped_no_match)
        self.gold = {
            "countries": countries,
            "dropped_no_match": dropped_no_match,
            "match_rate_pct": round(100 * countries / total, 1) if total else 0.0,
        }

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "run_at": self.run_at,
            "sources": self.sources,
            "silver": self.silver,
            "gold": self.gold,
            "output_path": self.output_path,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        logger.info("Quality: saved pipeline run summary -> %s", path)
