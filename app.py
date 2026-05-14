import pandas as pd
import streamlit as st

from src import config
from src.charts import (
    affordability_ranking_bar,
    affordability_scatter,
    salary_by_country_bar,
    world_cost_map,
)
from src.quality import load_pipeline_summary

st.set_page_config(
    page_title="Dev Salary vs Cost of Living",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = """
<style>
/* ── Layout ─────────────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero banner ─────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #0d2b5e 0%, #1a5fa8 100%);
    padding: 2rem 2.5rem;
    border-radius: 14px;
    margin-bottom: 1.75rem;
}
.hero h1 {
    color: #ffffff !important;
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    margin: 0 0 0.4rem 0 !important;
    line-height: 1.2 !important;
    padding: 0 !important;
}
.hero p { color: rgba(255,255,255,0.72); margin: 0; font-size: 0.95rem; }

/* ── KPI cards ───────────────────────────────────── */
.kpi-grid { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
    flex: 1;
    min-width: 130px;
    background: #ffffff;
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    border-top: 3px solid #0052cc;
}
.kpi-label {
    font-size: 0.7rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.3rem;
}
.kpi-value { font-size: 1.55rem; font-weight: 700; color: #0f172a; line-height: 1.1; }
.kpi-sub { font-size: 0.77rem; color: #0052cc; margin-top: 0.2rem; }

/* ── Section heading ─────────────────────────────── */
.section-heading {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 0.75rem 0;
}

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
.sidebar-brand {
    display: block;
    font-size: 1.05rem;
    font-weight: 700;
    color: #0d2b5e;
    margin-bottom: 1.25rem;
}
.sidebar-section {
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9ca3af;
    margin: 1.1rem 0 0.4rem 0;
}

/* ── Insight cards ───────────────────────────────── */
.insight-card {
    background: #eff6ff;
    border-left: 4px solid #0052cc;
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.75rem;
    color: #0f172a;
    font-size: 0.95rem;
    line-height: 1.55;
}

/* ── Quality badge ───────────────────────────────── */
.q-badge {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 0.9rem 1rem;
    text-align: center;
}
.q-value { font-size: 1.55rem; font-weight: 700; color: #15803d; }
.q-label { font-size: 0.72rem; color: #6b7280; margin-top: 0.15rem; }
</style>
"""


def _inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def _hero(subtitle: str = "") -> None:
    default = "Discover where developers get the most purchasing power for their salary."
    st.markdown(
        f"""<div class="hero">
            <h1>🌍 Dev Salary vs Cost of Living</h1>
            <p>{subtitle or default}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def _kpis(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    st.markdown(
        f"""<div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Countries</div>
            <div class="kpi-value">{len(df)}</div>
            <div class="kpi-sub">in selection</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Top Affordability</div>
            <div class="kpi-value">{best['country']}</div>
            <div class="kpi-sub">index {best['affordability_index']:.0f}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Avg Salary</div>
            <div class="kpi-value">${df['median_salary_usd'].mean():,.0f}</div>
            <div class="kpi-sub">median across countries</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Avg Cost Index</div>
            <div class="kpi-value">{df['cost_of_living_index'].mean():.1f}</div>
            <div class="kpi-sub">affordability avg {df['affordability_index'].mean():.0f}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


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
        st.warning("No data found. Run `python -m src.pipeline` to build the gold layer.")
        return None

    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Failed to load data: {exc}")
        return None


def _rankings(df: pd.DataFrame, top_n: int) -> None:
    st.markdown('<div class="section-heading">Country Rankings</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    cols = ["country", "region", "median_salary_usd", "cost_of_living_index", "affordability_index"]
    with left:
        st.caption(f"Top {top_n} · highest affordability")
        st.dataframe(df.head(top_n)[cols], use_container_width=True, hide_index=True)
    with right:
        st.caption(f"Bottom {top_n} · lowest affordability")
        st.dataframe(
            df.tail(top_n).sort_values("affordability_index")[cols],
            use_container_width=True,
            hide_index=True,
        )


def _insights(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    worst = df.iloc[-1]
    best_region = df.groupby("region")["affordability_index"].mean().idxmax()
    avg_idx = df["affordability_index"].mean()

    items = [
        f"<strong>{best['country']}</strong> leads in affordability (index {best['affordability_index']:.0f}), "
        f"while <strong>{worst['country']}</strong> ranks lowest ({worst['affordability_index']:.0f}).",
        f"The <strong>{best_region}</strong> region offers the highest average purchasing power "
        "on a salary-to-cost basis.",
        f"The global average affordability index across <strong>{len(df)} countries</strong> is "
        f"<strong>{avg_idx:.0f}</strong> — countries above this threshold offer above-average purchasing power.",
        "Countries with high nominal salaries do not always lead in affordability: cost structure has a "
        "greater impact on effective purchasing power than salary alone.",
    ]
    for item in items:
        st.markdown(f'<div class="insight-card">{item}</div>', unsafe_allow_html=True)


def _data_quality() -> None:
    summary = load_pipeline_summary(config.PIPELINE_SUMMARY_FILE)
    if summary is None:
        st.info("No pipeline quality report found. Run `python -m src.pipeline` to generate one.")
        return

    gold = summary.get("gold", {})
    sources = summary.get("sources", {})
    salaries = summary.get("silver", {}).get("developer_salaries", {})
    cost = summary.get("silver", {}).get("cost_of_living", {})

    st.caption(f"Last pipeline run: {summary.get('run_at', 'unknown')}")

    q_cols = st.columns(4)
    for col, (label, value) in zip(
        q_cols,
        [
            ("Gold countries", gold.get("countries", 0)),
            ("Match rate", f"{gold.get('match_rate_pct', 0):.1f}%"),
            ("Unknown currencies", salaries.get("unknown_currencies", 0)),
            ("Salary outliers", salaries.get("outliers_removed", 0)),
        ],
    ):
        col.markdown(
            f'<div class="q-badge"><div class="q-value">{value}</div>'
            f'<div class="q-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-heading">Source Row Counts</div>', unsafe_allow_html=True)
    source_rows = [{"source": n, "rows": d.get("rows", 0)} for n, d in sources.items()]
    st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown(
            '<div class="section-heading">Dropped Cost Countries</div>', unsafe_allow_html=True
        )
        st.write(cost.get("dropped_countries", []))
    with right:
        st.markdown(
            '<div class="section-heading">Dropped Gold Matches</div>', unsafe_allow_html=True
        )
        st.write(gold.get("dropped_no_match", []))


# ── Bootstrap ──────────────────────────────────────────────────────────────────

_inject_css()

df_raw = _load_data()
if df_raw is None:
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<span class="sidebar-brand">🌍 Cost of Living</span>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Navigate</div>', unsafe_allow_html=True)
    page = st.radio(
        "page",
        ["Overview", "Salaries", "Affordability", "Insights", "Data Quality"],
        label_visibility="collapsed",
    )

    if page != "Data Quality":
        st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)
        top_n = st.slider("Ranking size", min_value=3, max_value=20, value=10)

        regions = sorted(df_raw["region"].dropna().unique())
        selected_regions = st.multiselect("Region", regions, default=regions)

        sal_min = int(df_raw["median_salary_usd"].min())
        sal_max = int(df_raw["median_salary_usd"].max())
        salary_range = st.slider(
            "Salary range (USD)", sal_min, sal_max, (sal_min, sal_max),
            step=1000, format="$%d",
        )
    else:
        top_n = 10

# ── Filter ─────────────────────────────────────────────────────────────────────

if page != "Data Quality":
    df = (
        df_raw[
            df_raw["region"].isin(selected_regions)
            & df_raw["median_salary_usd"].between(*salary_range)
        ]
        .copy()
        .sort_values("affordability_index", ascending=False)
        .reset_index(drop=True)
    )
    if df.empty:
        st.warning("No countries match the selected filters.")
        st.stop()
else:
    df = df_raw

# ── Pages ──────────────────────────────────────────────────────────────────────

if page == "Overview":
    _hero()
    _kpis(df)
    st.plotly_chart(world_cost_map(df), use_container_width=True)
    _rankings(df, top_n)

elif page == "Salaries":
    _hero("Top countries by median developer salary in USD.")
    _kpis(df)
    st.plotly_chart(salary_by_country_bar(df), use_container_width=True)

elif page == "Affordability":
    _hero("Where does a developer's salary go furthest?")
    _kpis(df)
    st.plotly_chart(affordability_ranking_bar(df, top_n=top_n), use_container_width=True)
    st.plotly_chart(affordability_scatter(df), use_container_width=True)

elif page == "Insights":
    _hero("Data-backed conclusions from the analysis.")
    _insights(df)

else:  # Data Quality
    _hero("Pipeline quality metrics and data source statistics.")
    _data_quality()
