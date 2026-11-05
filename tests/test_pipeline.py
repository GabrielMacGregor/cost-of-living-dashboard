"""Pipeline orchestration and CLI tests."""
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src import config
from src.pipeline import _parse_args, run_pipeline

# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def test_parse_args_defaults():
    with patch("sys.argv", ["pipeline"]):
        args = _parse_args()
    assert args.year == config.DEFAULT_YEAR
    assert args.output == config.GOLD_DIR
    assert args.salary_outlier_threshold == config.SALARY_OUTLIER_THRESHOLD


def test_parse_args_custom_year():
    with patch("sys.argv", ["pipeline", "--year", "2023"]):
        args = _parse_args()
    assert args.year == 2023


def test_parse_args_custom_output():
    with patch("sys.argv", ["pipeline", "--output", "custom/output"]):
        args = _parse_args()
    assert args.output == Path("custom/output")


def test_parse_args_custom_threshold():
    with patch("sys.argv", ["pipeline", "--salary-outlier-threshold", "500000"]):
        args = _parse_args()
    assert args.salary_outlier_threshold == 500_000.0


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


def test_run_pipeline_orchestrates_medallion_steps(monkeypatch):
    calls: list[tuple[str, str | None, int | None]] = []

    numbeo_raw = pd.DataFrame({"Country": ["Brazil"], "Cost of Living Index": [42.0]})
    so_raw = pd.DataFrame(
        {
            "country": ["Brazil"],
            "currency": ["BRL\tBrazilian real"],
            "comp_total": [160000.0],
        }
    )
    wb_raw = pd.DataFrame(
        {
            "name": ["Brazil"],
            "iso3": ["BRA"],
            "region": ["Latin America & Caribbean"],
        }
    )
    exchange_rates = {"BRL": 5.0}

    def fake_fetch_numbeo_rankings(year: int):
        calls.append(("fetch_numbeo", None, year))
        return numbeo_raw

    def fake_save_bronze(df: pd.DataFrame, name: str):
        calls.append(("save_bronze", name, len(df)))

    def fake_save_silver(df: pd.DataFrame, name: str):
        calls.append(("save_silver", name, len(df)))

    def fake_save_gold(df: pd.DataFrame, output_dir=None):
        calls.append(("save_gold", None, len(df)))
        return Path("data/gold/country_affordability.csv")

    monkeypatch.setattr("src.pipeline.fetch_numbeo_rankings", fake_fetch_numbeo_rankings)
    monkeypatch.setattr("src.pipeline.fetch_stackoverflow_salaries", lambda: so_raw)
    monkeypatch.setattr("src.pipeline.fetch_worldbank_countries", lambda: wb_raw)
    monkeypatch.setattr("src.pipeline.fetch_exchange_rates", lambda: exchange_rates)
    monkeypatch.setattr("src.pipeline.save_bronze", fake_save_bronze)
    monkeypatch.setattr("src.pipeline.save_silver", fake_save_silver)
    monkeypatch.setattr("src.pipeline.save_gold", fake_save_gold)
    monkeypatch.setattr("src.pipeline.PipelineRunSummary.save", lambda self, path: None)

    run_pipeline(year=2024)

    assert ("fetch_numbeo", None, 2024) in calls
    assert ("save_bronze", "numbeo_rankings", 1) in calls
    assert ("save_bronze", "stackoverflow_survey", 1) in calls
    assert ("save_bronze", "worldbank_countries", 1) in calls
    assert ("save_bronze", "exchange_rates", 1) in calls
    assert ("save_silver", "cost_of_living", 1) in calls
    assert ("save_silver", "developer_salaries", 1) in calls
    assert ("save_gold", None, 1) in calls


def test_parse_args_enable_snapshot_tracking():
    with patch("sys.argv", ["pipeline", "--track-snapshots"]):
        args = _parse_args()
    assert args.track_snapshots is True


def test_pipeline_snapshot_tracking_is_opt_in(monkeypatch, tmp_path):
    """The optional audit must receive the final Gold layer, without changing its schema."""
    cost = pd.DataFrame({"Country": ["Brazil"], "Cost of Living Index": [42.0]})
    salaries = pd.DataFrame({
        "country": ["Brazil"], "currency": ["BRL\tBrazilian real"], "comp_total": [160000.0]
    })
    worldbank = pd.DataFrame({
        "name": ["Brazil"], "iso3": ["BRA"], "region": ["Latin America & Caribbean"]
    })
    monkeypatch.setattr("src.pipeline.fetch_numbeo_rankings", lambda year: cost)
    monkeypatch.setattr("src.pipeline.fetch_stackoverflow_salaries", lambda: salaries)
    monkeypatch.setattr("src.pipeline.fetch_worldbank_countries", lambda: worldbank)
    monkeypatch.setattr("src.pipeline.fetch_exchange_rates", lambda: {"BRL": 5.0})
    monkeypatch.setattr("src.pipeline.save_bronze", lambda df, name: None)
    monkeypatch.setattr("src.pipeline.save_silver", lambda df, name: None)
    monkeypatch.setattr(
        "src.pipeline.save_gold", lambda df, output_dir=None: tmp_path / "country_affordability.csv"
    )
    received = []
    expected = {
        "status": "initial", "inserted": 1, "updated": 0, "unchanged": 0,
        "removed": 0, "snapshot_id": "demo", "previous_snapshot_id": None,
    }

    def snapshot_record(df, year, snapshot_root):
        received.append((df.copy(), year, snapshot_root))
        return expected

    monkeypatch.setattr("src.pipeline.reconcile_gold_snapshot", snapshot_record)
    summaries = []
    monkeypatch.setattr(
        "src.pipeline.PipelineRunSummary.save",
        lambda self, path: summaries.append(self.to_dict()),
    )

    run_pipeline(year=2024, output_dir=tmp_path, track_snapshots=False)
    assert received == []
    assert "snapshot" not in summaries[-1]

    run_pipeline(year=2024, output_dir=tmp_path, track_snapshots=True)
    assert len(received) == 1
    assert received[0][1] == 2024
    assert received[0][2] == tmp_path.parent / "snapshots"
    assert received[0][0].iloc[0]["iso3"] == "BRA"
    assert summaries[-1]["snapshot"] == expected


def test_snapshot_error_does_not_block_gold(monkeypatch, tmp_path):
    cost = pd.DataFrame({"Country": ["Brazil"], "Cost of Living Index": [42.0]})
    salaries = pd.DataFrame({
        "country": ["Brazil"], "currency": ["BRL\tBrazilian real"], "comp_total": [160000.0]
    })
    worldbank = pd.DataFrame({
        "name": ["Brazil"], "iso3": ["BRA"], "region": ["Latin America & Caribbean"]
    })
    monkeypatch.setattr("src.pipeline.fetch_numbeo_rankings", lambda year: cost)
    monkeypatch.setattr("src.pipeline.fetch_stackoverflow_salaries", lambda: salaries)
    monkeypatch.setattr("src.pipeline.fetch_worldbank_countries", lambda: worldbank)
    monkeypatch.setattr("src.pipeline.fetch_exchange_rates", lambda: {"BRL": 5.0})
    monkeypatch.setattr("src.pipeline.save_bronze", lambda df, name: None)
    monkeypatch.setattr("src.pipeline.save_silver", lambda df, name: None)
    saved = []
    monkeypatch.setattr(
        "src.pipeline.save_gold",
        lambda df, output_dir=None: saved.append(df) or tmp_path / "country_affordability.csv",
    )

    def boom(df, year, snapshot_root):
        raise ValueError("Previous snapshot is missing or corrupted: boom")

    monkeypatch.setattr("src.pipeline.reconcile_gold_snapshot", boom)
    summaries = []
    monkeypatch.setattr(
        "src.pipeline.PipelineRunSummary.save",
        lambda self, path: summaries.append(self.to_dict()),
    )

    run_pipeline(year=2024, output_dir=tmp_path, track_snapshots=True)

    assert len(saved) == 1
    assert summaries[-1]["snapshot"]["status"] == "error"
    assert "corrupted" in summaries[-1]["snapshot"]["error"]
