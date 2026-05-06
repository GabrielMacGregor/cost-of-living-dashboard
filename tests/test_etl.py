"""Gold layer tests (affordability_index, build_gold_layer)."""
import pandas as pd
import pytest

from src.gold import affordability_index, build_gold_layer, load_gold

# ---------------------------------------------------------------------------
# affordability_index
# ---------------------------------------------------------------------------


def test_affordability_index_basic():
    result = affordability_index(pd.Series([60000, 120000]), pd.Series([60, 120]))
    assert result.iloc[0] == 1000
    assert result.iloc[1] == 1000


def test_affordability_index_zero_cost_returns_na():
    result = affordability_index(pd.Series([60000]), pd.Series([0]))
    assert pd.isna(result.iloc[0])


def test_affordability_index_nan_salary_propagates():
    result = affordability_index(pd.Series([float("nan"), 60000]), pd.Series([60, 60]))
    assert pd.isna(result.iloc[0])
    assert result.iloc[1] == 1000


# ---------------------------------------------------------------------------
# build_gold_layer helpers
# ---------------------------------------------------------------------------


def _cost_df(**overrides):
    data = {
        "country": ["Brazil", "Germany"],
        "cost_of_living_index": [40.0, 70.0],
        "iso3": ["BRA", "DEU"],
        "region": ["LATAM", "Europe"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _salary_df(**overrides):
    data = {"country": ["Brazil", "Germany"], "median_salary_usd": [30000.0, 84000.0]}
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# build_gold_layer — happy path
# ---------------------------------------------------------------------------


def test_build_gold_layer_merges_and_adds_metric():
    out = build_gold_layer(_cost_df(), _salary_df())
    assert "affordability_index" in out.columns
    assert len(out) == 2
    assert out.loc[out["country"] == "Brazil", "affordability_index"].iloc[0] == 750


def test_build_gold_layer_sorted_descending():
    out = build_gold_layer(_cost_df(), _salary_df())
    indices = out["affordability_index"].tolist()
    assert indices == sorted(indices, reverse=True)


# ---------------------------------------------------------------------------
# build_gold_layer — validation
# ---------------------------------------------------------------------------


def test_build_gold_layer_validates_required_columns():
    bad_cost = pd.DataFrame(
        {"country": ["Brazil"], "cost_of_living_index": [40.0], "iso3": ["BRA"]}
    )
    with pytest.raises(ValueError, match="missing required columns"):
        build_gold_layer(bad_cost, _salary_df())


# ---------------------------------------------------------------------------
# build_gold_layer — edge cases
# ---------------------------------------------------------------------------


def test_build_gold_layer_empty_intersection():
    salary_df = pd.DataFrame({"country": ["Canada"], "median_salary_usd": [90000.0]})
    out = build_gold_layer(_cost_df(), salary_df)
    assert len(out) == 0


def test_build_gold_layer_drops_zero_cost_rows():
    cost_df = _cost_df(
        country=["Brazil", "Germany", "Canada"],
        cost_of_living_index=[40.0, 70.0, 0.0],
        iso3=["BRA", "DEU", "CAN"],
        region=["LATAM", "Europe", "NA"],
    )
    salary_df = pd.DataFrame(
        {
            "country": ["Brazil", "Germany", "Canada"],
            "median_salary_usd": [30000.0, 84000.0, 90000.0],
        }
    )
    out = build_gold_layer(cost_df, salary_df)
    assert len(out) == 2
    assert "Canada" not in out["country"].values


# ---------------------------------------------------------------------------
# load_gold
# ---------------------------------------------------------------------------


def test_load_gold_missing_file_raises(monkeypatch):
    from pathlib import Path

    import src.gold as gold_module

    monkeypatch.setattr(gold_module, "GOLD_FILE", Path("__nonexistent_gold_file__.csv"))
    with pytest.raises(FileNotFoundError):
        load_gold()
