"""Plotly chart builders.

Visual rules follow the dashboard-design skill (.claude/skills/dashboard-design):
dark-surface palette tokens, one hue for single-series bars, emphasis (one colour +
gray) instead of eight categorical hues, hairline solid grid, 2px surface rings on
markers, and titles owned by the page's section headers rather than the figure.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TOP_N_SALARIES = 20
TOP_N_AFFORDABILITY = 20

# ── Tokens (dark mode; see references/dataviz/palette.md) ─────────────────────
SURFACE = "#1a1a19"
TEXT_PRIMARY = "#f0efec"
TEXT_SECONDARY = "#c3c2b7"
TEXT_MUTED = "#898781"
GRID = "#2c2c2a"
AXIS = "#383835"
SERIES_1 = "#3987e5"  # categorical slot 1 (blue)
DEEMPHASIS = "#5b5a56"  # context marks when one series is the story
NO_DATA = "#262624"

# Sequential single-hue ramp (blue 700 -> 300): lowest value recedes into the surface.
_SEQUENTIAL = [
    "#0d366b", "#104281", "#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5", "#6da7ec",
]

_FONT = dict(
    color=TEXT_SECONDARY,
    family="system-ui, -apple-system, 'Segoe UI', sans-serif",
    size=12,
)
_HOVER = dict(bgcolor="#262624", bordercolor=AXIS, font=dict(color=TEXT_PRIMARY, size=13))


_TICK_LABEL = dict(color=TEXT_SECONDARY, size=12)


def _axis(**kwargs) -> dict:
    base = dict(
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=False,
        ticks="",
        tickfont=dict(color=TEXT_MUTED, size=12),
        title_font=dict(color=TEXT_SECONDARY, size=12),
    )
    base.update(kwargs)
    return base


def _layout(**kwargs) -> dict:
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=_FONT,
        title=None,
        hoverlabel=_HOVER,
        **kwargs,
    )


def _bar_height(n_bars: int) -> int:
    """Plot height that includes the x-axis band; keeps bars ~18px thick."""
    return 72 + 28 * n_bars


def _require_columns(df: pd.DataFrame, required: set[str], fn_name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{fn_name}: DataFrame missing columns {sorted(missing)}")


def world_cost_map(df: pd.DataFrame):
    """Choropleth map of cost-of-living index by country (sequential, one hue)."""
    _require_columns(df, {"iso3", "cost_of_living_index", "country"}, "world_cost_map")
    return (
        px.choropleth(
            df,
            locations="iso3",
            color="cost_of_living_index",
            hover_name="country",
            hover_data={"iso3": False, "cost_of_living_index": ":.1f"},
            color_continuous_scale=_SEQUENTIAL,
            labels={"cost_of_living_index": "Cost of living index"},
        )
        .update_layout(
            **_layout(margin={"r": 0, "t": 8, "l": 0, "b": 0}, height=420),
            coloraxis_colorbar=dict(
                title=dict(text="Cost index", font=dict(color=TEXT_SECONDARY, size=12)),
                tickfont=dict(color=TEXT_MUTED, size=12),
                thickness=10,
                len=0.6,
                outlinewidth=0,
            ),
            geo=dict(
                bgcolor="rgba(0,0,0,0)",
                lakecolor=SURFACE,
                landcolor=NO_DATA,
                showland=True,
                showlakes=False,
                showcountries=True,
                countrycolor=SURFACE,
                showframe=False,
                projection_type="natural earth",
            ),
        )
    )


def salary_by_country_bar(df: pd.DataFrame, top_n: int = TOP_N_SALARIES):
    """Horizontal bar chart of top countries by median developer salary."""
    _require_columns(df, {"country", "median_salary_usd"}, "salary_by_country_bar")
    sorted_df = df.sort_values("median_salary_usd", ascending=False).head(top_n)
    sorted_df = sorted_df.sort_values("median_salary_usd", ascending=True)
    return (
        px.bar(
            sorted_df,
            x="median_salary_usd",
            y="country",
            orientation="h",
            labels={"median_salary_usd": "Median salary (USD)", "country": ""},
            color_discrete_sequence=[SERIES_1],
        )
        .update_traces(hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>")
        .update_layout(
            **_layout(
                xaxis=_axis(tickprefix="$", tickformat=","),
                yaxis=_axis(gridcolor="rgba(0,0,0,0)", tickfont=_TICK_LABEL),
                margin={"t": 8, "r": 16, "b": 40, "l": 8},
                bargap=0.35,
                showlegend=False,
                height=_bar_height(len(sorted_df)),
            )
        )
    )


def affordability_scatter(df: pd.DataFrame, highlight_n: int = 10):
    """Scatter of salary vs cost of living; the most affordable countries are emphasised."""
    _require_columns(
        df,
        {"cost_of_living_index", "median_salary_usd", "affordability_index", "region", "country"},
        "affordability_scatter",
    )
    ranked = df.sort_values("affordability_index", ascending=False)
    top = ranked.head(highlight_n)
    rest = ranked.iloc[highlight_n:]
    hover = (
        "<b>%{hovertext}</b><br>%{customdata[0]}<br>"
        "Cost index: %{x:.1f}<br>Salary: $%{y:,.0f}<extra></extra>"
    )

    def _trace(frame: pd.DataFrame, name: str, color: str, **extra) -> go.Scatter:
        return go.Scatter(
            x=frame["cost_of_living_index"],
            y=frame["median_salary_usd"],
            mode=extra.pop("mode", "markers"),
            name=name,
            hovertext=frame["country"],
            customdata=frame[["region"]],
            hovertemplate=hover,
            marker=dict(size=10, color=color, line=dict(width=2, color=SURFACE)),
            **extra,
        )

    label_n = min(5, len(top))
    labels = [c if i < label_n else "" for i, c in enumerate(top["country"])]
    fig = go.Figure(
        [
            _trace(rest, "Other countries", DEEMPHASIS),
            _trace(
                top,
                f"Top {len(top)} most affordable",
                SERIES_1,
                mode="markers+text",
                text=labels,
                textposition="top center",
                textfont=dict(color=TEXT_PRIMARY, size=12),
            ),
        ]
    )
    return fig.update_layout(
        **_layout(
            xaxis=_axis(title="Cost of Living Index"),
            yaxis=_axis(title="Median Salary (USD)", tickprefix="$", tickformat=","),
            margin={"t": 8, "r": 16, "b": 48, "l": 8},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_SECONDARY, size=12),
            ),
            height=420,
        )
    )


def affordability_ranking_bar(df: pd.DataFrame, top_n: int = TOP_N_AFFORDABILITY):
    """Horizontal bar chart of top countries by affordability index (one series, one hue)."""
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
            orientation="h",
            custom_data=["region"],
            labels={"affordability_index": "Affordability index (salary ÷ cost)", "country": ""},
            color_discrete_sequence=[SERIES_1],
        )
        .update_traces(
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Index: %{x:.0f}<extra></extra>"
        )
        .update_layout(
            **_layout(
                xaxis=_axis(),
                yaxis=_axis(gridcolor="rgba(0,0,0,0)", tickfont=_TICK_LABEL),
                margin={"t": 8, "r": 16, "b": 48, "l": 8},
                bargap=0.35,
                showlegend=False,
                height=_bar_height(len(sorted_df)),
            )
        )
    )
