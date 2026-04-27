import plotly.express as px
import pandas as pd


def world_cost_map(df: pd.DataFrame):
    return px.choropleth(
        df,
        locations="iso3",
        color="cost_of_living_index",
        hover_name="country",
        title="Global Cost of Living Index",
        color_continuous_scale="OrRd",
    )


def salary_by_country_bar(df: pd.DataFrame):
    sorted_df = df.sort_values("median_salary_usd", ascending=False).head(20)
    return px.bar(
        sorted_df,
        x="country",
        y="median_salary_usd",
        title="Top 20 Median Developer Salaries",
    )


def affordability_scatter(df: pd.DataFrame):
    return px.scatter(
        df,
        x="cost_of_living_index",
        y="median_salary_usd",
        color="region",
        hover_name="country",
        title="Affordability: Salary vs Cost of Living",
    )
