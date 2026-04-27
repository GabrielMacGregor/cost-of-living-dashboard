import pandas as pd

from src.etl import affordability_index, build_country_dataset


def test_affordability_index_basic():
    salary = pd.Series([60000, 120000])
    cost = pd.Series([60, 120])
    result = affordability_index(salary, cost)
    assert result.iloc[0] == 1000
    assert result.iloc[1] == 1000


def test_build_country_dataset_merges_and_adds_metric():
    cost_df = pd.DataFrame(
        {
            "country": ["Brazil", "Germany"],
            "cost_of_living_index": [40, 70],
            "iso3": ["BRA", "DEU"],
            "region": ["LATAM", "Europe"],
        }
    )
    salary_df = pd.DataFrame(
        {
            "country": ["Brazil", "Germany"],
            "median_salary_usd": [30000, 84000],
        }
    )

    out = build_country_dataset(cost_df, salary_df)

    assert "affordability_index" in out.columns
    assert len(out) == 2
    assert out.loc[out["country"] == "Brazil", "affordability_index"].iloc[0] == 750
