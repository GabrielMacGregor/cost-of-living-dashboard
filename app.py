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

_FONTS = (
    "<link href='https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800"
    "&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap' rel='stylesheet'/>"
)

_CSS = """
<style>
:root {
    --bg:       #0b0f1a;
    --surface:  #111827;
    --surface2: #1a2235;
    --border:   rgba(255,255,255,0.07);
    --text:     #e8edf5;
    --muted:    #6b7a96;
    --accent:   #3b82f6;
    --green:    #10b981;
    --amber:    #f59e0b;
    --red:      #ef4444;
    --violet:   #8b5cf6;
    --fd: 'Syne', sans-serif;
    --fm: 'DM Mono', monospace;
    --r: 12px;
}

/* ── Layout ─────────────────────────────────────── */
.main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1280px; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: 0 !important;
}

/* ── Hero ────────────────────────────────────────── */
.hero {
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem 2.25rem;
    margin-bottom: 1.75rem;
    overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; top: -80px; right: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 65%);
    pointer-events: none;
}
.hero::after {
    content: ''; position: absolute; bottom: -50px; left: 35%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.hero-badge {
    display: inline-block;
    font-size: 0.68rem; font-family: var(--fm);
    color: var(--accent);
    background: rgba(59,130,246,0.1);
    border: 1px solid rgba(59,130,246,0.22);
    border-radius: 20px;
    padding: 0.22rem 0.75rem;
    margin-bottom: 0.85rem;
    text-transform: uppercase; letter-spacing: 0.07em;
}
.hero h1 {
    font-family: var(--fd) !important;
    font-size: 2rem !important; font-weight: 800 !important;
    color: var(--text) !important;
    line-height: 1.15 !important;
    margin: 0 0 0.55rem 0 !important;
    letter-spacing: -0.025em !important; padding: 0 !important;
}
.hero h1 .hl { color: var(--accent); }
.hero p { color: var(--muted); font-size: 0.92rem; line-height: 1.65; max-width: 52ch; margin: 0; }

/* ── KPI cards ───────────────────────────────────── */
.kpi-grid { display: flex; gap: 1rem; margin-bottom: 1.75rem; flex-wrap: wrap; }
.kpi-card {
    flex: 1; min-width: 140px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r); padding: 1.2rem 1.35rem;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.kpi-card:hover { border-color: rgba(255,255,255,0.14); transform: translateY(-2px); }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }
.c-blue::before  { background: linear-gradient(90deg, var(--accent), transparent); }
.c-green::before { background: linear-gradient(90deg, var(--green),  transparent); }
.c-amber::before { background: linear-gradient(90deg, var(--amber),  transparent); }
.c-violet::before{ background: linear-gradient(90deg, var(--violet), transparent); }
.kpi-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.8rem; }
.kpi-label  { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 500; }
.kpi-icon   { width: 27px; height: 27px; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; }
.c-blue  .kpi-icon { background: rgba(59,130,246,0.12); }
.c-green .kpi-icon { background: rgba(16,185,129,0.12); }
.c-amber .kpi-icon { background: rgba(245,158,11,0.12); }
.c-violet .kpi-icon{ background: rgba(139,92,246,0.12); }
.kpi-value { font-family: var(--fd); font-size: 1.65rem; font-weight: 700; color: var(--text); line-height: 1; margin-bottom: 0.3rem; letter-spacing: -0.02em; }
.kpi-sub   { font-size: 0.71rem; color: var(--muted); display: flex; align-items: center; gap: 0.35rem; }
.tag { font-size: 0.62rem; padding: 0.08rem 0.42rem; border-radius: 4px; font-family: var(--fm); font-weight: 500; }
.c-blue  .tag  { background: rgba(59,130,246,0.15); color: var(--accent); }
.c-green .tag  { background: rgba(16,185,129,0.15); color: var(--green);  }
.c-amber .tag  { background: rgba(245,158,11,0.15); color: var(--amber);  }
.c-violet .tag { background: rgba(139,92,246,0.15); color: var(--violet); }

/* ── Section header ──────────────────────────────── */
.section-header { display: flex; align-items: center; margin: 1.75rem 0 0.9rem; }
.section-title  { font-family: var(--fd); font-size: 0.97rem; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 0.55rem; }
.section-title::before { content: ''; display: inline-block; width: 3px; height: 14px; border-radius: 2px; background: var(--accent); flex-shrink: 0; }

/* ── Rankings ────────────────────────────────────── */
.rankings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.table-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); overflow: hidden; }
.table-head { padding: 0.85rem 1.15rem; border-bottom: 1px solid var(--border); }
.table-head-title { font-size: 0.78rem; font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 0.45rem; }
.badge-top { background: rgba(16,185,129,0.12); color: var(--green); padding: 0.1rem 0.45rem; border-radius: 4px; font-size: 0.62rem; font-family: var(--fm); }
.badge-bot { background: rgba(239,68,68,0.1);  color: var(--red);   padding: 0.1rem 0.45rem; border-radius: 4px; font-size: 0.62rem; font-family: var(--fm); }
.badge-ok  { background: rgba(16,185,129,0.12); color: var(--green); padding: 0.1rem 0.45rem; border-radius: 4px; font-size: 0.62rem; font-family: var(--fm); }
table { width: 100%; border-collapse: collapse; }
thead th { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 500; padding: 0.6rem 1.15rem; text-align: left; border-bottom: 1px solid var(--border); }
tbody tr { border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.12s; }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: rgba(255,255,255,0.025); }
tbody td { padding: 0.62rem 1.15rem; font-size: 0.79rem; }
.rank-num    { font-family: var(--fm); color: var(--muted); font-size: 0.7rem; }
.cname       { font-weight: 500; color: var(--text); }
.salary-val  { font-family: var(--fm); font-size: 0.76rem; color: var(--green); }
.source-name { font-family: var(--fm); color: var(--muted); font-size: 0.77rem; }
.rows-val    { font-family: var(--fm); font-size: 0.76rem; color: var(--green); }
.idx-cell  { display: flex; align-items: center; gap: 0.5rem; font-family: var(--fm); font-size: 0.74rem; color: var(--text); }
.idx-track { width: 52px; height: 4px; background: rgba(255,255,255,0.07); border-radius: 2px; overflow: hidden; flex-shrink: 0; }
.idx-fill  { height: 100%; border-radius: 2px; }
.fill-hi   { background: var(--green); }
.fill-lo   { background: var(--red);   }

/* ── Insight cards ───────────────────────────────── */
.insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem; }
.insight-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r); padding: 1.4rem 1.5rem 1.3rem;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.insight-card:hover { border-color: rgba(59,130,246,0.25); transform: translateY(-2px); }
.insight-card::after {
    content: ''; position: absolute; bottom: -30px; right: -30px;
    width: 100px; height: 100px; border-radius: 50%;
    background: radial-gradient(circle, rgba(59,130,246,0.07), transparent 70%);
    pointer-events: none;
}
.insight-num  { font-family: var(--fd); font-size: 2.8rem; font-weight: 800; color: rgba(255,255,255,0.04); line-height: 1; position: absolute; top: 0.6rem; right: 1rem; }
.insight-icon { font-size: 1.2rem; margin-bottom: 0.7rem; display: block; }
.insight-text { font-size: 0.88rem; color: var(--text); line-height: 1.68; }
.insight-text strong { color: var(--accent); font-weight: 600; }
.hi-text { color: var(--green); font-weight: 600; }
.lo-text { color: var(--red);   font-weight: 600; }

/* ── Quality cards ───────────────────────────────── */
.quality-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.q-card  { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); padding: 1.2rem; text-align: center; }
.q-value { font-family: var(--fd); font-size: 1.55rem; font-weight: 700; margin-bottom: 0.3rem; }
.q-label { font-size: 0.67rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Sidebar brand / labels ──────────────────────── */
section[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
section[data-testid="stSidebar"] { border-right: 1px solid var(--border) !important; }
.sidebar-brand { display: flex; align-items: center; gap: 0.65rem; margin-bottom: 2rem; padding: 0 0.25rem; }
.brand-icon { width: 34px; height: 34px; background: linear-gradient(135deg, var(--accent) 0%, var(--violet) 100%); border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }
.brand-name { font-family: var(--fd); font-size: 0.9rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.brand-sub  { font-size: 0.63rem; color: var(--muted); }
.nav-label  { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); padding: 0 0.25rem; margin-bottom: 0.3rem; display: block; }
.data-meta  { font-size: 0.64rem; color: var(--muted); line-height: 1.7; padding: 0.8rem 0.9rem; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border); margin-top: 1.5rem; }
.data-meta strong { color: var(--text); }

/* ── Radio → nav items ───────────────────────────── */
div[data-testid="stRadio"] > div:first-child { display: none !important; }
div[data-testid="stRadio"] label > div:first-child { display: none !important; }
div[data-testid="stRadio"] label {
    display: flex !important; align-items: center !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 8px !important; border: 1px solid transparent !important;
    cursor: pointer !important; transition: all 0.15s !important;
    margin-bottom: 2px !important; width: 100% !important;
}
div[data-testid="stRadio"] label:hover { background: rgba(255,255,255,0.04) !important; }
div[data-testid="stRadio"] label:has(input:checked) { background: rgba(59,130,246,0.12) !important; border-color: rgba(59,130,246,0.22) !important; }
div[data-testid="stRadio"] label:has(input:checked) p { color: var(--accent) !important; font-weight: 500 !important; }
div[data-testid="stRadio"] label p { font-size: 0.85rem !important; margin: 0 !important; }

/* ── Widget label overrides ──────────────────────── */
div[data-testid="stSlider"] label, div[data-testid="stMultiSelect"] label {
    font-size: 0.7rem !important; color: var(--muted) !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important;
}
</style>
"""


def _inject() -> None:
    st.html(_FONTS + _CSS)


def _hero(badge: str, title_html: str, subtitle: str) -> None:
    st.markdown(
        f"""<div class="hero">
            <div class="hero-badge">{badge}</div>
            <h1>{title_html}</h1>
            <p>{subtitle}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def _kpis(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    st.markdown(
        f"""<div class="kpi-grid">
          <div class="kpi-card c-blue">
            <div class="kpi-header"><span class="kpi-label">Countries</span><div class="kpi-icon">🌍</div></div>
            <div class="kpi-value">{len(df)}</div>
            <div class="kpi-sub"><span class="tag">in selection</span></div>
          </div>
          <div class="kpi-card c-green">
            <div class="kpi-header"><span class="kpi-label">Top Affordability</span><div class="kpi-icon">🏆</div></div>
            <div class="kpi-value">{best['country']}</div>
            <div class="kpi-sub"><span class="tag">idx {best['affordability_index']:.0f}</span> highest score</div>
          </div>
          <div class="kpi-card c-amber">
            <div class="kpi-header"><span class="kpi-label">Avg Salary</span><div class="kpi-icon">💰</div></div>
            <div class="kpi-value">${df['median_salary_usd'].mean():,.0f}</div>
            <div class="kpi-sub"><span class="tag">median</span> across countries</div>
          </div>
          <div class="kpi-card c-violet">
            <div class="kpi-header"><span class="kpi-label">Avg Cost Index</span><div class="kpi-icon">📊</div></div>
            <div class="kpi-value">{df['cost_of_living_index'].mean():.1f}</div>
            <div class="kpi-sub"><span class="tag">aff. avg {df['affordability_index'].mean():.0f}</span></div>
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


def _section(title: str) -> None:
    st.markdown(
        f'<div class="section-header"><div class="section-title">{title}</div></div>',
        unsafe_allow_html=True,
    )


def _rankings(df: pd.DataFrame, top_n: int) -> None:
    max_idx = df["affordability_index"].max() or 1

    def _rows(rows_df: pd.DataFrame, fill_cls: str, rank_start: int) -> str:
        html = ""
        for i, (_, row) in enumerate(rows_df.iterrows()):
            pct = int(row["affordability_index"] / max_idx * 100)
            html += (
                f"<tr>"
                f"<td class='rank-num'>{rank_start + i}</td>"
                f"<td class='cname'>{row['country']}</td>"
                f"<td class='salary-val'>${row['median_salary_usd']:,.0f}</td>"
                f"<td><div class='idx-cell'>"
                f"<div class='idx-track'><div class='idx-fill {fill_cls}' style='width:{pct}%'></div></div>"
                f"{row['affordability_index']:.0f}"
                f"</div></td>"
                f"</tr>"
            )
        return html

    top_df = df.head(top_n)
    bot_df = df.tail(top_n).sort_values("affordability_index")
    bot_start = len(df) - top_n + 1

    _section("Country Rankings")
    st.markdown(
        f"""<div class="rankings-grid">
          <div class="table-card">
            <div class="table-head">
              <div class="table-head-title"><span class="badge-top">▲ TOP {top_n}</span>&nbsp;Highest Affordability</div>
            </div>
            <table><thead><tr><th>#</th><th>Country</th><th>Salary</th><th>Index</th></tr></thead>
            <tbody>{_rows(top_df, "fill-hi", 1)}</tbody></table>
          </div>
          <div class="table-card">
            <div class="table-head">
              <div class="table-head-title"><span class="badge-bot">▼ BOT {top_n}</span>&nbsp;Lowest Affordability</div>
            </div>
            <table><thead><tr><th>#</th><th>Country</th><th>Salary</th><th>Index</th></tr></thead>
            <tbody>{_rows(bot_df, "fill-lo", bot_start)}</tbody></table>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


def _insights(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    worst = df.iloc[-1]
    best_region = df.groupby("region")["affordability_index"].mean().idxmax()
    avg_idx = df["affordability_index"].mean()

    cards = [
        ("🌍", "01",
         f'<span class="hi-text">{best["country"]}</span> leads global affordability '
         f'(index {best["affordability_index"]:.0f}), while '
         f'<span class="lo-text">{worst["country"]}</span> ranks lowest '
         f'({worst["affordability_index"]:.0f}) — a cost-structure gap, not a salary gap.'),
        ("🌎", "02",
         f'<strong>{best_region}</strong> consistently offers the highest average purchasing power '
         f'— competitive salaries combined with significantly lower living costs.'),
        ("📊", "03",
         f'The global average affordability index across <strong>{len(df)} countries</strong> is '
         f'<strong>{avg_idx:.0f}</strong>. Countries above this threshold offer above-average real purchasing power.'),
        ("💡", "04",
         '<span class="lo-text">High nominal salaries</span> don\'t always win. '
         'Cost structure has a greater impact on <strong>effective purchasing power</strong> '
         'than raw salary figures across all regions.'),
    ]

    cards_html = "".join(
        f"""<div class="insight-card">
            <div class="insight-num">{num}</div>
            <span class="insight-icon">{icon}</span>
            <div class="insight-text">{text}</div>
        </div>"""
        for icon, num, text in cards
    )
    st.markdown(f'<div class="insights-grid">{cards_html}</div>', unsafe_allow_html=True)


def _data_quality(summary: dict | None) -> None:
    if summary is None:
        st.info("No pipeline quality report found. Run `python -m src.pipeline` to generate one.")
        return

    gold = summary.get("gold", {})
    sources = summary.get("sources", {})
    salaries = summary.get("silver", {}).get("developer_salaries", {})
    cost = summary.get("silver", {}).get("cost_of_living", {})

    st.caption(f"Last pipeline run: {summary.get('run_at', 'unknown')}")

    metrics = [
        ("#10b981", gold.get("countries", 0), "Gold Countries"),
        ("#3b82f6", f"{gold.get('match_rate_pct', 0):.1f}%", "Match Rate"),
        ("#f59e0b", salaries.get("unknown_currencies", 0), "Unknown Currencies"),
        ("#ef4444", salaries.get("outliers_removed", 0), "Salary Outliers"),
    ]
    cards_html = "".join(
        f'<div class="q-card"><div class="q-value" style="color:{color};">{val}</div>'
        f'<div class="q-label">{label}</div></div>'
        for color, val, label in metrics
    )
    st.markdown(f'<div class="quality-grid">{cards_html}</div>', unsafe_allow_html=True)

    _section("Source Row Counts")
    src_rows = "".join(
        f"<tr><td class='source-name'>{name}</td>"
        f"<td class='rows-val'>{d.get('rows', 0):,}</td>"
        f"<td><span class='badge-ok'>✓ OK</span></td></tr>"
        for name, d in sources.items()
    )
    st.markdown(
        f"""<div class="table-card" style="margin-bottom:1rem;">
          <table>
            <thead><tr><th>Source</th><th>Rows</th><th>Status</th></tr></thead>
            <tbody>{src_rows}</tbody>
          </table>
        </div>""",
        unsafe_allow_html=True,
    )

    def _dropped_list(items: list[str]) -> str:
        if not items:
            return (
                "<span style='color:#10b981;font-family:var(--fm);"
                "font-size:0.8rem;'>none</span>"
            )
        return "".join(
            f"<div style='font-family:var(--fm);font-size:0.77rem;color:var(--muted);"
            f"padding:0.35rem 0;border-bottom:1px solid var(--border);'>{c}</div>"
            for c in items
        )

    _section("Dropped Countries")
    st.markdown(
        f"""<div class="rankings-grid">
          <div class="table-card" style="padding:1rem 1.15rem;">
            <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;
                        letter-spacing:.08em;margin-bottom:.6rem;">Cost of Living</div>
            {_dropped_list(cost.get("dropped_countries", []))}
          </div>
          <div class="table-card" style="padding:1rem 1.15rem;">
            <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;
                        letter-spacing:.08em;margin-bottom:.6rem;">Gold Matches</div>
            {_dropped_list(gold.get("dropped_no_match", []))}
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Bootstrap ──────────────────────────────────────────────────────────────────

_inject()
df_raw = _load_data()
if df_raw is None:
    st.stop()

_summary = load_pipeline_summary(config.PIPELINE_SUMMARY_FILE) or load_pipeline_summary(
    config.GOLD_DIR / "example_pipeline_run_summary.json"
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """<div class="sidebar-brand">
          <div class="brand-icon">🌍</div>
          <div>
            <div class="brand-name">DevEconomy</div>
            <div class="brand-sub">Salary Intelligence</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown('<span class="nav-label">Navigate</span>', unsafe_allow_html=True)
    page = st.radio(
        "",
        ["Overview", "Salaries", "Affordability", "Insights", "Data Quality"],
        label_visibility="collapsed",
    )

    if page != "Data Quality":
        st.markdown(
            '<span class="nav-label" style="margin-top:1.25rem;">Filters</span>',
            unsafe_allow_html=True,
        )
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

    if _summary:
        run_at = _summary.get("run_at", "")[:16]
        countries = _summary.get("gold", {}).get("countries", "—")
        match_rate = _summary.get("gold", {}).get("match_rate_pct", "—")
        st.markdown(
            f"""<div class="data-meta">
              <strong>Last pipeline run</strong><br/>
              <span style="font-family:var(--fm);">{run_at}</span><br/><br/>
              <span style="color:rgba(255,255,255,0.25);">{countries} countries
              · {match_rate}% match rate</span>
            </div>""",
            unsafe_allow_html=True,
        )

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
    _hero(
        "120+ Countries · 2024 Data",
        'Dev <span class="hl">Salary</span> vs Cost of Living',
        "Discover where developers get the most purchasing power for their salary.",
    )
    _kpis(df)
    _section("Global Affordability Map")
    st.plotly_chart(world_cost_map(df), use_container_width=True)
    _rankings(df, top_n)

elif page == "Salaries":
    _hero(
        "USD Normalized · 2024",
        'Developer <span class="hl">Salaries</span> by Country',
        "Median developer salaries normalized to USD for fair cross-border comparison.",
    )
    _kpis(df)
    _section("Salary by Country")
    st.plotly_chart(salary_by_country_bar(df), use_container_width=True)

elif page == "Affordability":
    _hero(
        "Purchasing Power Analysis",
        'Where Does Your <span class="hl">Salary</span> Go Furthest?',
        "High nominal salaries don't always win — the affordability index reveals the real picture.",
    )
    _kpis(df)
    _section("Affordability Ranking")
    st.plotly_chart(affordability_ranking_bar(df, top_n=top_n), use_container_width=True)
    _section("Salary vs Cost of Living")
    st.plotly_chart(affordability_scatter(df), use_container_width=True)

elif page == "Insights":
    _hero(
        "Analysis · 2024 Data",
        'Key <span class="hl">Insights</span> from the Data',
        "Data-backed conclusions about purchasing power, regional trends, and cost structures.",
    )
    _insights(df)

else:  # Data Quality
    _hero(
        "Pipeline · Quality Report",
        'Data <span class="hl">Quality</span> &amp; Sources',
        "Pipeline execution stats, source match rates, and diagnostics from the last run.",
    )
    _data_quality(_summary)
