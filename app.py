import pandas as pd
import streamlit as st

from src import config
from src.charts import affordability_ranking_bar, affordability_scatter, salary_by_country_bar, world_cost_map
from src.quality import load_pipeline_summary

st.set_page_config(page_title="Cost of Living vs Developer Salaries", layout="wide")
st.title("Global Cost of Living vs Developer Salaries")


def _load_data() -> pd.DataFrame | None:
    if config.GOLD_FILE.exists():
        path = config.GOLD_FILE
    elif config.EXAMPLE_GOLD_FILE.exists():
        st.info(
            "Showing bundled example data. "
            "Run `python -m src.pipeline` to fetch and process real data."
        )
        path = config.EXAMPLE_GOLD_FILE
    else:
        st.warning(
            "No data found. Run `python -m src.pipeline` to build the gold layer."
        )
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Failed to load data: {exc}")
        return None


def _render_insights(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    worst = df.iloc[-1]
    best_region = df.groupby("region")["affordability_index"].mean().idxmax()
    avg_idx = df["affordability_index"].mean()

    st.markdown(
        f"1. **{best['country']}** leads in affordability "
        f"(index: {best['affordability_index']:.0f}), while **{worst['country']}** "
        f"ranks lowest ({worst['affordability_index']:.0f})."
    )
    st.markdown(
        f"2. The **{best_region}** region offers the highest average purchasing power "
        "for developers on a salary-to-cost basis."
    )
    st.markdown(
        f"3. The global average affordability index across {len(df)} countries is "
        f"**{avg_idx:.0f}** — countries above this threshold offer above-average purchasing power."
    )
    st.markdown(
        "4. Countries with high nominal salaries do not always lead in affordability: "
        "cost structure has a greater impact on effective purchasing power than salary alone."
    )


def _filter_data(df: pd.DataFrame) -> pd.DataFrame:
    regions = sorted(df["region"].dropna().unique())
    selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

    salary_min, salary_max = st.sidebar.slider(
        "Median salary range",
        min_value=int(df["median_salary_usd"].min()),
        max_value=int(df["median_salary_usd"].max()),
        value=(int(df["median_salary_usd"].min()), int(df["median_salary_usd"].max())),
        step=1000,
        format="$%d",
    )

    filtered = df[
        df["region"].isin(selected_regions)
        & df["median_salary_usd"].between(salary_min, salary_max)
    ].copy()

    if filtered.empty:
        st.warning("No countries match the selected filters.")
        st.stop()

    return filtered.sort_values("affordability_index", ascending=False).reset_index(drop=True)


def _render_kpis(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    avg_affordability = df["affordability_index"].mean()
    avg_salary = df["median_salary_usd"].mean()
    avg_cost = df["cost_of_living_index"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Countries", f"{len(df)}")
    col2.metric("Top affordability", f"{best['country']}", f"{best['affordability_index']:.0f}")
    col3.metric("Avg salary", f"${avg_salary:,.0f}")
    col4.metric("Avg cost index", f"{avg_cost:.1f}", f"Affordability avg {avg_affordability:.0f}")


def _render_rankings(df: pd.DataFrame, top_n: int) -> None:
    ranking_cols = st.columns(2)
    display_cols = ["country", "region", "median_salary_usd", "cost_of_living_index", "affordability_index"]

    with ranking_cols[0]:
        st.subheader(f"Top {top_n} Affordability")
        st.dataframe(
            df.head(top_n)[display_cols],
            use_container_width=True,
            hide_index=True,
        )

    with ranking_cols[1]:
        st.subheader(f"Bottom {top_n} Affordability")
        st.dataframe(
            df.tail(top_n).sort_values("affordability_index")[display_cols],
            use_container_width=True,
            hide_index=True,
        )


def _render_data_quality() -> None:
    summary = load_pipeline_summary(config.PIPELINE_SUMMARY_FILE)
    if summary is None:
        st.info("No pipeline quality report found. Run `python -m src.pipeline` to generate one.")
        return

    gold = summary.get("gold", {})
    sources = summary.get("sources", {})
    salaries = summary.get("silver", {}).get("developer_salaries", {})
    cost = summary.get("silver", {}).get("cost_of_living", {})

    st.subheader("Data Quality")
    st.caption(f"Last pipeline run: {summary.get('run_at', 'unknown')}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gold countries", gold.get("countries", 0))
    col2.metric("Match rate", f"{gold.get('match_rate_pct', 0):.1f}%")
    col3.metric("Unknown currencies", salaries.get("unknown_currencies", 0))
    col4.metric("Salary outliers", salaries.get("outliers_removed", 0))

    st.subheader("Source Rows")
    source_rows = [
        {"source": name, "rows": details.get("rows", 0)}
        for name, details in sources.items()
    ]
    st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

    dropped_cols = st.columns(2)
    with dropped_cols[0]:
        st.subheader("Dropped Cost Countries")
        st.write(cost.get("dropped_countries", []))
    with dropped_cols[1]:
        st.subheader("Dropped Gold Matches")
        st.write(gold.get("dropped_no_match", []))


df = _load_data()
if df is None:
    st.stop()

page = st.sidebar.radio(
    "Navigate", ["Overview", "Salaries", "Affordability", "Insights", "Data Quality"]
)
top_n = st.sidebar.slider("Ranking size", min_value=3, max_value=20, value=5)

if page == "Data Quality":
    _render_data_quality()
    st.stop()

df = _filter_data(df)
_render_kpis(df)

if page == "Overview":
    st.subheader("Overview")
    st.plotly_chart(world_cost_map(df), use_container_width=True)
    _render_rankings(df, top_n)

elif page == "Salaries":
    st.subheader("Salaries")
    st.plotly_chart(salary_by_country_bar(df), use_container_width=True)

elif page == "Affordability":
    st.subheader("Affordability")
    st.plotly_chart(affordability_ranking_bar(df, top_n=top_n), use_container_width=True)
    st.plotly_chart(affordability_scatter(df), use_container_width=True)

else:
    st.subheader("Insights")
    _render_insights(df)
