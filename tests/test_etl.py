import pandas as pd
import pytest

from src.etl import affordability_index, build_country_dataset, run_etl


# ---------------------------------------------------------------------------
# affordability_index
# ---------------------------------------------------------------------------


def test_affordability_index_basic():
    salary = pd.Series([60000, 120000])
    cost = pd.Series([60, 120])
    result = affordability_index(salary, cost)
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
# build_country_dataset helpers
# ---------------------------------------------------------------------------


def _cost_df(**overrides):
    data = {
        "country": ["Brazil", "Germany"],
        "cost_of_living_index": [40, 70],
        "iso3": ["BRA", "DEU"],
        "region": ["LATAM", "Europe"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _salary_df(**overrides):
    data = {
        "country": ["Brazil", "Germany"],
        "median_salary_usd": [30000, 84000],
    }
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# build_country_dataset — happy path
# ---------------------------------------------------------------------------


def test_build_country_dataset_merges_and_adds_metric():
    out = build_country_dataset(_cost_df(), _salary_df())

    assert "affordability_index" in out.columns
    assert len(out) == 2
    assert out.loc[out["country"] == "Brazil", "affordability_index"].iloc[0] == 750


def test_build_country_dataset_sorted_descending():
    out = build_country_dataset(_cost_df(), _salary_df())
    indices = out["affordability_index"].tolist()
    assert indices == sorted(indices, reverse=True)


# ---------------------------------------------------------------------------
# build_country_dataset — validation
# ---------------------------------------------------------------------------


def test_build_country_dataset_validates_required_columns():
    cost_df = pd.DataFrame(
        {"country": ["Brazil"], "cost_of_living_index": [40], "iso3": ["BRA"]}
    )
    with pytest.raises(ValueError, match="missing required columns"):
        build_country_dataset(cost_df, _salary_df())


# ---------------------------------------------------------------------------
# build_country_dataset — edge cases
# ---------------------------------------------------------------------------


def test_build_country_dataset_strips_whitespace():
    out = build_country_dataset(
        _cost_df(country=["  Brazil  ", " Germany "]),
        _salary_df(country=["Brazil", "Germany"]),
    )
    assert len(out) == 2


def test_build_country_dataset_empty_intersection():
    salary_df = pd.DataFrame({"country": ["Canada"], "median_salary_usd": [90000]})
    out = build_country_dataset(_cost_df(), salary_df)
    assert len(out) == 0


def test_build_country_dataset_drops_zero_cost_rows():
    cost_df = _cost_df(
        country=["Brazil", "Germany", "Canada"],
        cost_of_living_index=[40, 70, 0],
        iso3=["BRA", "DEU", "CAN"],
        region=["LATAM", "Europe", "NA"],
    )
    salary_df = pd.DataFrame(
        {
            "country": ["Brazil", "Germany", "Canada"],
            "median_salary_usd": [30000, 84000, 90000],
        }
    )

    out = build_country_dataset(cost_df, salary_df)
    assert len(out) == 2
    assert "Canada" not in out["country"].values


def test_build_country_dataset_coerces_numeric_strings():
    out = build_country_dataset(
        _cost_df(cost_of_living_index=["40", "70"]),
        _salary_df(median_salary_usd=["30000", "84000"]),
    )
    assert len(out) == 2
    brazil_idx = out.loc[out["country"] == "Brazil", "affordability_index"].iloc[0]
    assert brazil_idx == pytest.approx(750)


def test_build_country_dataset_non_numeric_cost_treated_as_nan():
    cost_df = _cost_df(
        country=["Brazil", "Germany", "Canada"],
        cost_of_living_index=[40, "invalid", 65],
        iso3=["BRA", "DEU", "CAN"],
        region=["LATAM", "Europe", "NA"],
    )
    salary_df = pd.DataFrame(
        {
            "country": ["Brazil", "Germany", "Canada"],
            "median_salary_usd": [30000, 84000, 90000],
        }
    )

    out = build_country_dataset(cost_df, salary_df)
    # Germany has invalid cost_of_living_index → affordability_index is NaN → dropped
    assert "Germany" not in out["country"].values
    assert len(out) == 2


def test_build_country_dataset_nan_salary_row_dropped():
    salary_df = _salary_df(median_salary_usd=[float("nan"), 84000])
    out = build_country_dataset(_cost_df(), salary_df)
    assert "Brazil" not in out["country"].values
    assert len(out) == 1


# ---------------------------------------------------------------------------
# run_etl
# ---------------------------------------------------------------------------


def test_run_etl_missing_files_raises(tmp_path, monkeypatch):
    import src.etl as etl_module

    monkeypatch.setattr(etl_module, "RAW_DIR", tmp_path / "raw")
    with pytest.raises(FileNotFoundError):
        run_etl()
