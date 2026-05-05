"""Chart helper tests."""

import pandas as pd
import pytest

from src.charts import affordability_scatter, salary_by_country_bar, world_cost_map


def _chart_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": ["Brazil", "Germany", "Canada"],
            "iso3": ["BRA", "DEU", "CAN"],
            "region": ["Latin America", "Europe", "North America"],
            "cost_of_living_index": [42.0, 68.0, 65.0],
            "median_salary_usd": [32000.0, 86000.0, 90000.0],
            "affordability_index": [761.9, 1264.7, 1384.6],
        }
    )


def test_world_cost_map_uses_iso3_locations():
    fig = world_cost_map(_chart_df())
    assert fig.data[0].locations.tolist() == ["BRA", "DEU", "CAN"]
    assert fig.layout.title.text == "Global Cost of Living Index"


def test_salary_bar_sorts_by_salary_descending():
    fig = salary_by_country_bar(_chart_df())
    assert fig.data[0].x.tolist() == ["Canada", "Germany", "Brazil"]
    assert fig.data[0].y.tolist() == [90000.0, 86000.0, 32000.0]


def test_affordability_scatter_uses_cost_and_salary_axes():
    fig = affordability_scatter(_chart_df())
    assert fig.layout.xaxis.title.text == "cost_of_living_index"
    assert fig.layout.yaxis.title.text == "median_salary_usd"


def test_chart_helpers_validate_required_columns():
    with pytest.raises(ValueError, match="missing columns"):
        world_cost_map(pd.DataFrame({"country": ["Brazil"]}))
