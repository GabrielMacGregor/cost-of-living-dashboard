"""Silver layer tests (process_cost_of_living, process_developer_salaries)."""
import pandas as pd
import pytest

from src.silver import process_cost_of_living, process_developer_salaries


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _wb_df():
    return pd.DataFrame(
        {
            "name": ["Brazil", "Germany", "Canada", "Korea, Rep."],
            "iso3": ["BRA", "DEU", "CAN", "KOR"],
            "region": ["Latin America & Caribbean", "Europe & Central Asia",
                       "North America", "East Asia & Pacific"],
        }
    )


def _numbeo_df(**overrides):
    data = {
        "Country": ["Brazil", "Germany", "Canada"],
        "Cost of Living Index": [42.0, 68.0, 65.0],
        "Rent Index": [10.0, 30.0, 28.0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# process_cost_of_living — happy path
# ---------------------------------------------------------------------------


def test_process_cost_keeps_matched_countries():
    out = process_cost_of_living(_numbeo_df(), _wb_df())
    assert set(out["country"]) == {"Brazil", "Germany", "Canada"}


def test_process_cost_adds_iso3_and_region():
    out = process_cost_of_living(_numbeo_df(), _wb_df())
    bra = out.loc[out["country"] == "Brazil"].iloc[0]
    assert bra["iso3"] == "BRA"
    assert bra["region"] == "Latin America & Caribbean"


def test_process_cost_drops_extra_numbeo_columns():
    out = process_cost_of_living(_numbeo_df(), _wb_df())
    assert set(out.columns) == {"country", "cost_of_living_index", "iso3", "region"}


# ---------------------------------------------------------------------------
# process_cost_of_living — edge cases
# ---------------------------------------------------------------------------


def test_process_cost_drops_unmatched_country():
    df = pd.DataFrame(
        {"Country": ["Brazil", "FakeCountryXYZ"], "Cost of Living Index": [42.0, 55.0]}
    )
    out = process_cost_of_living(df, _wb_df())
    assert "FakeCountryXYZ" not in out["country"].values
    assert "Brazil" in out["country"].values


def test_process_cost_applies_name_mapping():
    """'South Korea' in Numbeo maps to 'Korea, Rep.' in World Bank."""
    df = pd.DataFrame({"Country": ["South Korea"], "Cost of Living Index": [68.0]})
    out = process_cost_of_living(df, _wb_df())
    assert len(out) == 1
    assert out.iloc[0]["iso3"] == "KOR"


def test_process_cost_drops_non_numeric_index():
    df = _numbeo_df(**{"Cost of Living Index": ["42.0", "invalid", "65.0"]})
    out = process_cost_of_living(df, _wb_df())
    assert "Germany" not in out["country"].values
    assert len(out) == 2


def test_process_cost_raises_on_missing_cost_column():
    df = pd.DataFrame({"Country": ["Brazil"], "Rent Index": [10.0]})
    with pytest.raises(ValueError, match="cost of living index"):
        process_cost_of_living(df, _wb_df())


# ---------------------------------------------------------------------------
# process_developer_salaries — happy path
# ---------------------------------------------------------------------------


def _so_df(**overrides):
    data = {
        "Country": ["Brazil", "Brazil", "Germany", "Germany", "Germany"],
        "ConvertedCompYearly": [30000, 34000, 80000, 90000, 86000],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_process_salaries_computes_median():
    out = process_developer_salaries(_so_df())
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == 32000.0  # median of [30000, 34000]


def test_process_salaries_one_row_per_country():
    out = process_developer_salaries(_so_df())
    assert len(out) == out["country"].nunique()


# ---------------------------------------------------------------------------
# process_developer_salaries — edge cases
# ---------------------------------------------------------------------------


def test_process_salaries_drops_nan():
    df = _so_df(**{"ConvertedCompYearly": [float("nan"), 34000, 80000, 90000, 86000]})
    out = process_developer_salaries(df)
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == 34000.0


def test_process_salaries_removes_outliers_above_1m():
    df = _so_df(**{"ConvertedCompYearly": [30000, 9_999_999, 80000, 90000, 86000]})
    out = process_developer_salaries(df)
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == 30000.0


def test_process_salaries_handles_empty_country():
    df = _so_df()
    df.loc[0, "Country"] = float("nan")
    out = process_developer_salaries(df)
    # "nan" string should appear as a country or be handled gracefully
    assert "Brazil" in out["country"].values
