import plotly.express as px
import pandas as pd

TOP_N_SALARIES = 20
TOP_N_AFFORDABILITY = 20


def _require_columns(df: pd.DataFrame, required: set[str], fn_name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{fn_name}: DataFrame missing columns {sorted(missing)}")


def world_cost_map(df: pd.DataFrame):
    """Choropleth map of cost-of-living index by country."""
    _require_columns(df, {"iso3", "cost_of_living_index", "country"}, "world_cost_map")
    return px.choropleth(
        df,
        locations="iso3",
        color="cost_of_living_index",
        hover_name="country",
        title="Global Cost of Living Index",
        color_continuous_scale="OrRd",
    )


def salary_by_country_bar(df: pd.DataFrame):
    """Horizontal bar chart of top countries by median developer salary."""
    _require_columns(df, {"country", "median_salary_usd"}, "salary_by_country_bar")
    sorted_df = df.sort_values("median_salary_usd", ascending=False).head(TOP_N_SALARIES)
    return px.bar(
        sorted_df,
        x="country",
        y="median_salary_usd",
        title=f"Top {TOP_N_SALARIES} Median Developer Salaries",
    )


def affordability_scatter(df: pd.DataFrame):
    """Scatter plot of salary vs cost of living, colored by region."""
    _require_columns(
        df,
        {"cost_of_living_index", "median_salary_usd", "region", "country"},
        "affordability_scatter",
    )
    return px.scatter(
        df,
        x="cost_of_living_index",
        y="median_salary_usd",
        color="region",
        hover_name="country",
        title="Affordability: Salary vs Cost of Living",
    )


def affordability_ranking_bar(df: pd.DataFrame, top_n: int = TOP_N_AFFORDABILITY):
    """Horizontal bar chart of top countries by affordability index."""
    _require_columns(
        df,
        {"country", "affordability_index", "region"},
        "affordability_ranking_bar",
    )
    sorted_df = df.sort_values("affordability_index", ascending=False).head(top_n)
    sorted_df = sorted_df.sort_values("affordability_index", ascending=True)
    return px.bar(
        sorted_df,
        x="affordability_index",
        y="country",
        color="region",
        orientation="h",
        title=f"Top {top_n} Countries by Affordability Index",
        labels={"affordability_index": "Affordability Index", "country": ""},
    )
