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


_RATES = {"USD": 1.0, "EUR": 0.92, "BRL": 5.0}


def _so_df(**overrides):
    data = {
        "country": ["Brazil", "Brazil", "Germany", "Germany", "Germany"],
        "currency": ["BRL\tBrazilian real"] * 2 + ["EUR European Euro"] * 3,
        "comp_total": [150000, 170000, 73600, 82800, 79120],
        # BRL: 150000/5 = 30000 USD, 170000/5 = 34000 USD → median 32000
        # EUR: 73600/0.92 = 80000 USD, 82800/0.92 = 90000 USD, 79120/0.92 = 86000 USD → median 86000
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_process_salaries_computes_median():
    out, _ = process_developer_salaries(_so_df(), _RATES)
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == pytest.approx(32000.0)


def test_process_salaries_one_row_per_country():
    out, _ = process_developer_salaries(_so_df(), _RATES)
    assert len(out) == out["country"].nunique()


# ---------------------------------------------------------------------------
# process_developer_salaries — edge cases
# ---------------------------------------------------------------------------


def test_process_salaries_drops_nan():
    df = _so_df()
    df.loc[0, "comp_total"] = float("nan")
    out, _ = process_developer_salaries(df, _RATES)
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == pytest.approx(34000.0)


def test_process_salaries_removes_outliers_above_1m():
    df = _so_df()
    df.loc[0, "comp_total"] = 9_999_999 * 5  # 9.99M USD after BRL conversion
    out, _ = process_developer_salaries(df, _RATES)
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == pytest.approx(34000.0)


def test_process_salaries_drops_unknown_currency():
    df = _so_df()
    df.loc[0, "currency"] = "XYZ Unknown"  # no rate available
    out, _ = process_developer_salaries(df, _RATES)
    # Brazil row with unknown currency is dropped; only the remaining row survives
    brazil = out.loc[out["country"] == "Brazil", "median_salary_usd"].iloc[0]
    assert brazil == pytest.approx(34000.0)


def test_process_salaries_normalises_so_country_names():
    df = pd.DataFrame({
        "country": ["United States of America"],
        "currency": ["USD\tUnited States dollar"],
        "comp_total": [120000.0],
    })
    out, _ = process_developer_salaries(df, _RATES)
    assert "United States" in out["country"].values


def test_process_salaries_handles_empty_country():
    df = _so_df()
    df.loc[0, "country"] = float("nan")
    out, _ = process_developer_salaries(df, _RATES)
    assert "Brazil" in out["country"].values


# ---------------------------------------------------------------------------
# process_developer_salaries — stats dict
# ---------------------------------------------------------------------------


def test_process_salaries_stats_keys():
    _, stats = process_developer_salaries(_so_df(), _RATES)
    assert set(stats) == {"rows_in", "unknown_currencies", "outliers_removed", "countries"}


def test_process_salaries_stats_counts():
    _, stats = process_developer_salaries(_so_df(), _RATES)
    assert stats["rows_in"] == 5
    assert stats["countries"] == 2
    assert stats["unknown_currencies"] == 0
    assert stats["outliers_removed"] == 0


def test_process_salaries_stats_tracks_unknown_currency():
    df = _so_df()
    df.loc[0, "currency"] = "XYZ Unknown"
    _, stats = process_developer_salaries(df, _RATES)
    assert stats["unknown_currencies"] >= 1


def test_process_salaries_stats_tracks_outliers():
    df = _so_df()
    df.loc[0, "comp_total"] = 9_999_999 * 5
    _, stats = process_developer_salaries(df, _RATES)
    assert stats["outliers_removed"] >= 1


def test_process_salaries_custom_outlier_threshold():
    df = _so_df()
    # threshold=29000 removes both Brazil rows (30000 and 34000 USD)
    out, stats = process_developer_salaries(df, _RATES, outlier_threshold=29_000)
    assert "Brazil" not in out["country"].values
    assert stats["outliers_removed"] >= 1
