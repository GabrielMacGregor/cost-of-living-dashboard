from pathlib import Path
import streamlit as st
import pandas as pd

from src.charts import world_cost_map, salary_by_country_bar, affordability_scatter

st.set_page_config(page_title="Cost of Living vs Developer Salaries", layout="wide")
st.title("Global Cost of Living vs Developer Salaries")

DATA_PATH = Path("data/processed/country_affordability.csv")
EXAMPLE_DATA_PATH = Path("data/processed/example_country_affordability.csv")

if not DATA_PATH.exists():
    if EXAMPLE_DATA_PATH.exists():
        st.info(
            "Showing bundled example data. For real analysis, add raw files in data/raw/ and run `python src/etl.py`."
        )
        df = pd.read_csv(EXAMPLE_DATA_PATH)
    else:
        st.warning(
            "Processed file not found. Run `python src/etl.py` after adding raw files in data/raw/."
        )
        st.stop()
else:
    df = pd.read_csv(DATA_PATH)

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
    st.markdown("1. Countries with high developer salaries do not always provide the best affordability.")
    st.markdown("2. Some mid-salary markets outperform expensive tech hubs on salary-to-cost ratio.")
    st.markdown("3. Regional differences in cost structure materially affect effective purchasing power.")
    st.markdown("4. Affordability can vary significantly even among countries with similar nominal pay.")
