"""Offline tests for content-addressed Gold snapshot reconciliation."""

import json

import pandas as pd
import pytest

from src.snapshots import reconcile_gold_snapshot


def _gold():
    return pd.DataFrame({
        "iso3": ["BRA", "DEU"], "country": ["Brazil", "Germany"],
        "region": ["LATAM", "Europe"], "cost_of_living_index": [40.0, 70.0],
        "median_salary_usd": [30000.0, 84000.0], "affordability_index": [750.0, 1200.0],
    })


def test_initial_snapshot(tmp_path):
    stats = reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    assert (stats["status"], stats["inserted"], stats["updated"]) == ("initial", 2, 0)
    root = tmp_path / "2024"
    m = json.loads((root / "latest.json").read_text())
    assert m["survey_year"] == 2024
    assert m["snapshot_id"] == stats["snapshot_id"]
    assert len(list((root / "history").glob("*.csv"))) == 1


def test_idempotent_even_when_order_differs(tmp_path):
    one = reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    manifest = tmp_path / "2024" / "latest.json"
    original_content = manifest.read_bytes()
    two = reconcile_gold_snapshot(_gold().iloc[::-1], 2024, tmp_path)
    assert two["status"] == "unchanged"
    assert two["unchanged"] == 2
    assert two["snapshot_id"] == one["snapshot_id"]
    assert manifest.read_bytes() == original_content
    assert len(list((tmp_path / "2024" / "history").glob("*.csv"))) == 1


def test_insert_update_remove_and_preserve_history(tmp_path):
    first = reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    current = _gold().iloc[[0]].copy()
    current.loc[:, "median_salary_usd"] = [31000.0]
    current.loc[:, "affordability_index"] = [775.0]
    current = pd.concat([current, pd.DataFrame({
        "iso3": ["CAN"], "country": ["Canada"], "region": ["NA"],
        "cost_of_living_index": [55.0], "median_salary_usd": [55000.0],
        "affordability_index": [1000.0],
    })], ignore_index=True)
    second = reconcile_gold_snapshot(current, 2024, tmp_path, max_removed_fraction=None)
    assert (second["inserted"], second["updated"], second["unchanged"], second["removed"]) == (
        1, 1, 0, 1
    )
    assert second["previous_snapshot_id"] == first["snapshot_id"]
    assert len(list((tmp_path / "2024" / "history").glob("*.csv"))) == 2


def test_country_with_new_name_is_update_by_iso3(tmp_path):
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    df = _gold().copy()
    df.loc[df["iso3"] == "BRA", "country"] = "Brasil"
    stats = reconcile_gold_snapshot(df, 2024, tmp_path)
    assert stats["updated"] == 1 and stats["inserted"] == 0


def test_separate_survey_years(tmp_path):
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    stats = reconcile_gold_snapshot(_gold(), 2025, tmp_path)
    assert stats["status"] == "initial"


@pytest.mark.parametrize("mutate", [
    lambda x: x.drop(columns=["iso3"]),
    lambda x: pd.concat([x, x.iloc[:1]], ignore_index=True),
    lambda x: x.assign(cost_of_living_index=[0.0, 70.0]),
    lambda x: x.assign(median_salary_usd=[float("inf"), 84000]),
    lambda x: x.assign(country=[None, "Germany"]),
])
def test_invalid_input_does_not_touch_manifest(tmp_path, mutate):
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    path = tmp_path / "2024" / "latest.json"
    expected = path.read_bytes()
    with pytest.raises(ValueError):
        reconcile_gold_snapshot(mutate(_gold()), 2024, tmp_path)
    assert path.read_bytes() == expected


def test_corrupted_history_fails_closed(tmp_path):
    first = reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    f = tmp_path / "2024" / "history" / f"{first['snapshot_id']}.csv"
    f.write_text("corrupt", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        reconcile_gold_snapshot(_gold(), 2024, tmp_path)


def test_missing_history_fails_closed(tmp_path):
    first = reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    (tmp_path / "2024" / "history" / f"{first['snapshot_id']}.csv").unlink()
    with pytest.raises(ValueError, match="missing or corrupted"):
        reconcile_gold_snapshot(_gold(), 2024, tmp_path)


def test_no_snapshot_when_data_invalid(tmp_path):
    with pytest.raises(ValueError):
        reconcile_gold_snapshot(_gold().assign(iso3=["BRA", "BRA"]), 2024, tmp_path)
    assert not (tmp_path / "2024" / "latest.json").exists()


def test_empty_gold_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="is empty"):
        reconcile_gold_snapshot(_gold().iloc[0:0].copy(), 2024, tmp_path)
    assert not (tmp_path / "2024" / "latest.json").exists()


def test_every_change_appends_an_immutable_manifest(tmp_path):
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)  # unchanged: no new entry
    changed = _gold().assign(median_salary_usd=[31000.0, 84000.0])
    reconcile_gold_snapshot(changed, 2024, tmp_path)
    entries = sorted((tmp_path / "2024" / "log").glob("*.json"))
    assert len(entries) == 2
    first, second = (json.loads(e.read_text()) for e in entries)
    assert first["previous_snapshot_id"] is None
    assert second["previous_snapshot_id"] == first["snapshot_id"]
    assert second["changes"]["updated"] == 1


def test_mass_removal_is_refused_and_leaves_state_untouched(tmp_path):
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    path = tmp_path / "2024" / "latest.json"
    expected = path.read_bytes()
    with pytest.raises(ValueError, match="likely ingestion failure"):
        reconcile_gold_snapshot(_gold().iloc[[0]], 2024, tmp_path)
    assert path.read_bytes() == expected
    assert len(list((tmp_path / "2024" / "log").glob("*.json"))) == 1


def test_mass_removal_guard_can_be_disabled(tmp_path):
    reconcile_gold_snapshot(_gold(), 2024, tmp_path)
    stats = reconcile_gold_snapshot(
        _gold().iloc[[0]], 2024, tmp_path, max_removed_fraction=None
    )
    assert stats["removed"] == 1
