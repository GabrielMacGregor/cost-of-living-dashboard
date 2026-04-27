from pathlib import Path
import streamlit as st
import pandas as pd

from src.charts import world_cost_map, salary_by_country_bar, affordability_scatter

st.set_page_config(page_title="Cost of Living vs Developer Salaries", layout="wide")
st.title("Global Cost of Living vs Developer Salaries")

DATA_PATH = Path("data/processed/country_affordability.csv")
EXAMPLE_DATA_PATH = Path("data/processed/example_country_affordability.csv")


def _load_data() -> pd.DataFrame | None:
    if DATA_PATH.exists():
        path = DATA_PATH
    elif EXAMPLE_DATA_PATH.exists():
        st.info(
            "Showing bundled example data. For real analysis, add raw files in data/raw/ and run `python src/etl.py`."
        )
        path = EXAMPLE_DATA_PATH
    else:
        st.warning(
            "Processed file not found. Run `python src/etl.py` after adding raw files in data/raw/."
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
        f"for developers on a salary-to-cost basis."
    )
    st.markdown(
        f"3. The global average affordability index across {len(df)} countries is "
        f"**{avg_idx:.0f}** — countries above this threshold offer above-average purchasing power."
    )
    st.markdown(
        "4. Countries with high nominal salaries do not always lead in affordability: "
        "cost structure has a greater impact on effective purchasing power than salary alone."
    )


df = _load_data()
if df is None:
    st.stop()

page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Salaries", "Affordability", "Insights"],
)

if page == "Overview":
    st.subheader("Overview")
    st.plotly_chart(world_cost_map(df), use_container_width=True)

elif page == "Salaries":
    st.subheader("Salaries")
    st.plotly_chart(salary_by_country_bar(df), use_container_width=True)

elif page == "Affordability":
    st.subheader("Affordability")
    st.metric("Average Affordability Index", f"{df['affordability_index'].mean():.2f}")
    st.plotly_chart(affordability_scatter(df), use_container_width=True)

else:
    st.subheader("Insights")
    _render_insights(df)
