import pandas as pd
import plotly.express as px

TOP_N_SALARIES = 20
TOP_N_AFFORDABILITY = 20

_COLORWAY = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f43f5e", "#a3e635"]
_BG = "#111827"
_FONT = dict(color="#e8edf5", family="DM Sans, sans-serif", size=12)
_GRID = "rgba(255,255,255,0.06)"


def _layout(**kwargs) -> dict:
    return dict(
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=_FONT,
        colorway=_COLORWAY,
        **kwargs,
    )


def _require_columns(df: pd.DataFrame, required: set[str], fn_name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{fn_name}: DataFrame missing columns {sorted(missing)}")


def world_cost_map(df: pd.DataFrame):
    """Choropleth map of cost-of-living index by country."""
    _require_columns(df, {"iso3", "cost_of_living_index", "country"}, "world_cost_map")
    return (
        px.choropleth(
            df,
            locations="iso3",
            color="cost_of_living_index",
            hover_name="country",
            hover_data={"iso3": False, "cost_of_living_index": ":.1f"},
            title="Cost of Living Index by Country",
            color_continuous_scale=[[0, "#1a2235"], [0.5, "#3b82f6"], [1, "#10b981"]],
        )
        .update_layout(
            **_layout(margin={"r": 0, "t": 48, "l": 0, "b": 0}),
            coloraxis_colorbar={"title": "Index", "tickfont": {"color": "#6b7a96"}},
            geo=dict(
                bgcolor=_BG,
                lakecolor=_BG,
                landcolor="#1a2235",
                showland=True,
                showlakes=False,
                showcountries=True,
                countrycolor="#1e293b",
            ),
        )
    )


def salary_by_country_bar(df: pd.DataFrame):
    """Horizontal bar chart of top countries by median developer salary."""
    _require_columns(df, {"country", "median_salary_usd"}, "salary_by_country_bar")
    sorted_df = df.sort_values("median_salary_usd", ascending=False).head(TOP_N_SALARIES)
    sorted_df = sorted_df.sort_values("median_salary_usd", ascending=True)
    return (
        px.bar(
            sorted_df,
            x="median_salary_usd",
            y="country",
            orientation="h",
            title=f"Top {TOP_N_SALARIES} Countries · Median Developer Salary",
            labels={"median_salary_usd": "Median Salary (USD)", "country": ""},
            color_discrete_sequence=["#3b82f6"],
        )
        .update_traces(hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>")
        .update_layout(
            **_layout(
                xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID, tickprefix="$", tickformat=","),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                margin={"t": 56, "r": 20, "b": 40, "l": 20},
            )
        )
    )


def affordability_scatter(df: pd.DataFrame):
    """Scatter plot of salary vs cost of living, colored by region."""
    _require_columns(
        df,
        {"cost_of_living_index", "median_salary_usd", "region", "country"},
        "affordability_scatter",
    )
    return (
        px.scatter(
            df,
            x="cost_of_living_index",
            y="median_salary_usd",
            color="region",
            hover_name="country",
            title="Salary vs Cost of Living by Country",
            labels={
                "cost_of_living_index": "Cost of Living Index",
                "median_salary_usd": "Median Salary (USD)",
            },
            color_discrete_sequence=_COLORWAY,
        )
        .update_traces(
            marker_size=9,
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Cost index: %{x:.1f}<br>"
                "Salary: $%{y:,.0f}<extra></extra>"
            ),
        )
        .update_layout(
            **_layout(
                xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID),
                yaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID, tickprefix="$", tickformat=","),
                margin={"t": 56, "r": 20, "b": 40, "l": 20},
                legend_title="Region",
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=_GRID),
            )
        )
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
    return (
        px.bar(
            sorted_df,
            x="affordability_index",
            y="country",
            color="region",
            orientation="h",
            title=f"Top {top_n} Countries by Affordability Index",
            labels={"affordability_index": "Affordability Index (salary ÷ cost)", "country": ""},
            color_discrete_sequence=_COLORWAY,
        )
        .update_traces(hovertemplate="<b>%{y}</b><br>Index: %{x:.0f}<extra></extra>")
        .update_layout(
            **_layout(
                xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                margin={"t": 56, "r": 20, "b": 40, "l": 20},
                legend_title="Region",
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=_GRID),
            )
        )
    )
