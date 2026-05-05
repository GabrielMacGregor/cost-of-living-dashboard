"""Tests for PipelineRunSummary (src/quality.py)."""
import json

from src.quality import PipelineRunSummary


def test_summary_has_timestamp():
    summary = PipelineRunSummary(year=2024)
    assert summary.run_at  # non-empty ISO string


def test_to_dict_keys():
    summary = PipelineRunSummary(year=2024)
    assert set(summary.to_dict()) == {"year", "run_at", "sources", "silver", "gold", "output_path"}


def test_record_source():
    summary = PipelineRunSummary(year=2024)
    summary.record_source("numbeo", rows=120, url="https://example.com")
    assert summary.sources["numbeo"] == {"rows": 120, "url": "https://example.com"}


def test_record_silver_cost():
    summary = PipelineRunSummary(year=2024)
    summary.record_silver_cost(rows_in=100, rows_out=90, dropped_countries=["Fakeland", "Neverland"])
    s = summary.silver["cost_of_living"]
    assert s["rows_in"] == 100
    assert s["rows_out"] == 90
    assert s["dropped"] == 2
    assert "Fakeland" in s["dropped_countries"]


def test_record_silver_salaries():
    summary = PipelineRunSummary(year=2024)
    summary.record_silver_salaries(rows_in=5000, countries=80, unknown_currencies=200, outliers_removed=12)
    s = summary.silver["developer_salaries"]
    assert s["rows_in"] == 5000
    assert s["countries"] == 80
    assert s["unknown_currencies"] == 200
    assert s["outliers_removed"] == 12


def test_record_gold_match_rate():
    summary = PipelineRunSummary(year=2024)
    summary.record_gold(countries=90, dropped_no_match=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    assert summary.gold["countries"] == 90
    assert summary.gold["match_rate_pct"] == 90.0  # 90/(90+10)


def test_record_gold_empty_dropped():
    summary = PipelineRunSummary(year=2024)
    summary.record_gold(countries=100, dropped_no_match=[])
    assert summary.gold["match_rate_pct"] == 100.0


def test_record_gold_all_dropped():
    summary = PipelineRunSummary(year=2024)
    summary.record_gold(countries=0, dropped_no_match=["A"])
    assert summary.gold["match_rate_pct"] == 0.0


def test_save_creates_valid_json(tmp_path):
    summary = PipelineRunSummary(year=2024)
    summary.record_source("numbeo", rows=120)
    summary.record_gold(countries=80, dropped_no_match=["TestLand"])
    summary.output_path = "data/gold/country_affordability.csv"

    out = tmp_path / "summary.json"
    summary.save(out)

    assert out.exists()
    data = json.loads(out.read_text())
    assert data["year"] == 2024
    assert data["sources"]["numbeo"]["rows"] == 120
    assert data["gold"]["countries"] == 80
    assert "TestLand" in data["gold"]["dropped_no_match"]
    assert data["output_path"] == "data/gold/country_affordability.csv"


def test_save_creates_parent_dirs(tmp_path):
    summary = PipelineRunSummary(year=2024)
    nested = tmp_path / "a" / "b" / "summary.json"
    summary.save(nested)
    assert nested.exists()
