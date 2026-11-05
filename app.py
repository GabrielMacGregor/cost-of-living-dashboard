from html import escape

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

# Visual rules: .claude/skills/dashboard-design (dark surface, one system sans,
# 4/8px spacing scale, hairline borders, colour only where it carries meaning).
_CSS = """
<style>
:root {
    --bg:        #0d0d0d;   /* page plane */
    --surface:   #1a1a19;   /* cards and chart surface */
    --border:    rgba(255,255,255,0.10);
    --grid:      #2c2c2a;
    --text:      #f0efec;
    --text-2:    #c3c2b7;
    --muted:     #898781;
    --series-1:  #3987e5;
    --good:      #0ca30c;
    --font: system-ui, -apple-system, "Segoe UI", sans-serif;
    --r: 8px;
}

.stMarkdown, .stMarkdown p, .kpi-card, .table-card, .insight-card, .page-head { font-family: var(--font); }

/* ── Layout ─────────────────────────────────────── */
.main .block-container { padding: 24px 32px 48px; max-width: 1280px; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; border-bottom: 0 !important; }
:focus-visible { outline: 2px solid var(--series-1) !important; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
@media (max-width: 767px) { .main .block-container { padding: 16px 16px 32px; } }

/* ── Page header ─────────────────────────────────── */
.page-head { margin: 0 0 16px; }
.page-head h1 {
    font-family: var(--font) !important; font-size: 1.75rem !important; font-weight: 600 !important;
    color: var(--text) !important; line-height: 1.2 !important; letter-spacing: -0.01em !important;
    margin: 0 0 4px !important; padding: 0 !important;
}
.page-head p { color: var(--text-2); font-size: 0.875rem; line-height: 1.5; margin: 0; max-width: 64ch; }

/* ── Filters row ─────────────────────────────────── */
div[data-testid="stSlider"] label p, div[data-testid="stMultiSelect"] label p {
    font-size: 0.75rem !important; color: var(--text-2) !important;
}

/* ── KPI tiles ───────────────────────────────────── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 8px 0 24px; }
@media (max-width: 1279px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 767px)  { .kpi-grid { grid-template-columns: 1fr; } }
.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); padding: 16px 20px; min-height: 96px; }
.kpi-label { font-size: 0.875rem; color: var(--text-2); margin-bottom: 8px; }
.kpi-value { font-size: 1.75rem; font-weight: 600; color: var(--text); line-height: 1.15; margin-bottom: 4px; letter-spacing: -0.01em; }
.kpi-sub   { font-size: 0.75rem; color: var(--muted); }

/* ── Section header ──────────────────────────────── */
.section-title { font-size: 1.25rem; font-weight: 600; color: var(--text); margin: 32px 0 4px; }
.section-note  { font-size: 0.875rem; color: var(--muted); margin: 0 0 12px; }

/* ── Charts sit on the chart surface ─────────────── */
div[data-testid="stPlotlyChart"] {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); padding: 16px;
}
div[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: var(--r) !important; margin-top: 8px; }
div[data-testid="stExpander"] summary p { font-size: 0.875rem; color: var(--text-2); }

/* ── Tables ──────────────────────────────────────── */
.rankings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 767px) { .rankings-grid { grid-template-columns: 1fr; } }
.table-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); overflow: hidden; }
.table-head { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 0.875rem; font-weight: 600; color: var(--text); }
.table-head span { font-weight: 400; color: var(--text-2); }
table { width: 100%; border-collapse: collapse; }
thead th { font-size: 0.75rem; font-weight: 500; color: var(--muted); padding: 8px 16px; text-align: left; border-bottom: 1px solid var(--grid); }
tbody tr { border-bottom: 1px solid var(--grid); }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: rgba(255,255,255,0.03); }
tbody td { padding: 8px 16px; font-size: 0.875rem; color: var(--text); }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }
.rank-num { color: var(--muted); font-variant-numeric: tabular-nums; width: 40px; }
.idx-cell { display: flex; align-items: center; justify-content: flex-end; gap: 8px; font-variant-numeric: tabular-nums; }
.idx-track { width: 56px; height: 4px; background: var(--grid); border-radius: 2px; overflow: hidden; flex-shrink: 0; }
.idx-fill  { height: 100%; background: var(--series-1); }
.status-ok { color: var(--good); font-size: 0.875rem; }

/* ── Insights ────────────────────────────────────── */
.insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 8px; }
@media (max-width: 767px) { .insights-grid { grid-template-columns: 1fr; } }
.insight-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); padding: 20px 24px; }
.insight-text { font-size: 1rem; color: var(--text-2); line-height: 1.6; }
.insight-text strong { color: var(--text); font-weight: 600; }

/* ── Quality tiles ───────────────────────────────── */
.quality-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 8px 0 24px; }
@media (max-width: 1279px) { .quality-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 767px)  { .quality-grid { grid-template-columns: 1fr; } }
.drop-list { padding: 12px 16px; }
.drop-title { font-size: 0.875rem; font-weight: 600; color: var(--text); margin-bottom: 8px; }
.drop-item  { font-size: 0.875rem; color: var(--text-2); padding: 4px 0; border-bottom: 1px solid var(--grid); }
.drop-none  { font-size: 0.875rem; color: var(--muted); }

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] > div:first-child { padding-top: 24px; }
section[data-testid="stSidebar"] { border-right: 1px solid var(--border) !important; }
.brand-name { font-size: 1rem; font-weight: 600; color: var(--text); line-height: 1.2; }
.brand-sub  { font-size: 0.75rem; color: var(--muted); margin-bottom: 24px; }
.data-meta  { font-size: 0.75rem; color: var(--muted); line-height: 1.6; padding: 12px 16px; border: 1px solid var(--border); border-radius: var(--r); margin-top: 24px; }
.data-meta strong { color: var(--text-2); font-weight: 500; }
a { color: var(--series-1); }
.src-table td { vertical-align: top; }
.src-table td.period { white-space: nowrap; color: var(--text-2); }
.src-note { font-size: 0.875rem; color: var(--text-2); line-height: 1.6; margin: 12px 0 0; }

/* ── Radio → nav items ───────────────────────────── */
div[data-testid="stRadio"] > div:first-child { display: none !important; }
div[data-testid="stRadio"] label > div:first-child { display: none !important; }
div[data-testid="stRadio"] label {
    display: flex !important; align-items: center !important;
    padding: 8px 12px !important; border-radius: 6px !important;
    cursor: pointer !important; margin-bottom: 2px !important; width: 100% !important;
}
div[data-testid="stRadio"] label:hover { background: rgba(255,255,255,0.05) !important; }
div[data-testid="stRadio"] label:has(input:checked) { background: rgba(57,135,229,0.16) !important; }
div[data-testid="stRadio"] label:has(input:checked) p { color: var(--text) !important; font-weight: 600 !important; }
div[data-testid="stRadio"] label p { font-size: 0.875rem !important; margin: 0 !important; color: var(--text-2); }
</style>
"""


def _inject() -> None:
    st.html(_CSS)


def _page_head(title: str, subtitle: str) -> None:
    st.markdown(
        f"""<div class="page-head"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>""",
        unsafe_allow_html=True,
    )


def _tile(label: str, value: str, sub: str) -> str:
    return (
        f'<div class="kpi-card"><div class="kpi-label">{escape(label)}</div>'
        f'<div class="kpi-value">{escape(value)}</div>'
        f'<div class="kpi-sub">{escape(sub)}</div></div>'
    )


def _kpis(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    tiles = [
        _tile("Countries", f"{len(df)}", "In the current selection"),
        _tile(
            "Most affordable",
            str(best["country"]),
            f"Affordability index {best['affordability_index']:,.0f}",
        ),
        _tile(
            "Average salary",
            f"${df['median_salary_usd'].mean():,.0f}",
            "Mean of country medians",
        ),
        _tile(
            "Average cost index",
            f"{df['cost_of_living_index'].mean():.1f}",
            f"Average affordability {df['affordability_index'].mean():,.0f}",
        ),
    ]
    st.markdown(f'<div class="kpi-grid">{"".join(tiles)}</div>', unsafe_allow_html=True)


def _load_data() -> tuple[pd.DataFrame, bool] | None:
    """Return (data, is_example). The quality report must come from the same source."""
    is_example = False
    if config.GOLD_FILE.exists():
        path = config.GOLD_FILE
    elif config.EXAMPLE_GOLD_FILE.exists():
        is_example = True
        path = config.EXAMPLE_GOLD_FILE
    else:
        st.warning("No data found. Run `python -m src.pipeline` to build the gold layer.")
        return None

    try:
        df = pd.read_csv(path)
        if is_example:
            st.info(
                f"Showing bundled example data ({len(df)} countries), and the quality report "
                "describes that example run. Run `python -m src.pipeline` to fetch and "
                "process real data."
            )
        return df, is_example
    except Exception as exc:
        st.error(f"Failed to load data: {exc}")
        return None


def _section(title: str, note: str = "") -> None:
    note_html = f'<p class="section-note">{escape(note)}</p>' if note else ""
    st.markdown(
        f'<div class="section-title">{escape(title)}</div>{note_html}',
        unsafe_allow_html=True,
    )


def _chart(fig, table: pd.DataFrame) -> None:
    """Chart plus its table twin (tooltips never gate a value)."""
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with st.expander("View as table"):
        st.dataframe(table, use_container_width=True, hide_index=True)


def _rankings(df: pd.DataFrame, top_n: int) -> None:
    max_idx = df["affordability_index"].max() or 1

    def _rows(rows_df: pd.DataFrame, rank_start: int) -> str:
        html = ""
        for i, (_, row) in enumerate(rows_df.iterrows()):
            pct = int(row["affordability_index"] / max_idx * 100)
            html += (
                f"<tr>"
                f"<td class='rank-num'>{rank_start + i}</td>"
                f"<td>{escape(str(row['country']))}</td>"
                f"<td class='num'>${row['median_salary_usd']:,.0f}</td>"
                f"<td class='num'><div class='idx-cell'>"
                f"<div class='idx-track'><div class='idx-fill' style='width:{pct}%'></div></div>"
                f"{row['affordability_index']:,.0f}"
                f"</div></td>"
                f"</tr>"
            )
        return html

    # Top and bottom lists never overlap: with few countries, shrink them to fit.
    n = min(top_n, max(len(df) // 2, 1))
    top_df = df.head(n)
    bot_df = df.iloc[n:].tail(n).sort_values("affordability_index")
    bot_start = len(df) - len(bot_df) + 1
    head = "<thead><tr><th>#</th><th>Country</th><th class='num'>Salary</th><th class='num'>Index</th></tr></thead>"

    note = "Affordability index = median salary ÷ cost of living index, a simplified comparison."
    if n < top_n:
        note += f" Showing {n} per list because the selection has {len(df)} countries."
    bottom_card = (
        f"""<div class="table-card">
            <div class="table-head">▼ Least affordable <span>· bottom {len(bot_df)}</span></div>
            <table>{head}<tbody>{_rows(bot_df, bot_start)}</tbody></table>
          </div>"""
        if len(bot_df)
        else ""
    )
    _section("Country rankings", note)
    st.markdown(
        f"""<div class="rankings-grid">
          <div class="table-card">
            <div class="table-head">▲ Most affordable <span>· top {n}</span></div>
            <table>{head}<tbody>{_rows(top_df, 1)}</tbody></table>
          </div>
          {bottom_card}
        </div>""",
        unsafe_allow_html=True,
    )


def _insights(df: pd.DataFrame) -> None:
    best = df.iloc[0]
    worst = df.iloc[-1]
    best_region = df.groupby("region")["affordability_index"].mean().idxmax()
    avg_idx = df["affordability_index"].mean()

    cards = [
        f'<strong>{escape(str(best["country"]))}</strong> leads global affordability '
        f'(index {best["affordability_index"]:,.0f}), while '
        f'<strong>{escape(str(worst["country"]))}</strong> ranks lowest '
        f'({worst["affordability_index"]:,.0f}) — a cost-structure gap, not a salary gap.',
        f'<strong>{escape(str(best_region).strip())}</strong> has the highest average affordability '
        f'in this selection — competitive salaries combined with lower living costs.',
        f'The average affordability index across <strong>{len(df)} countries</strong> is '
        f'<strong>{avg_idx:,.0f}</strong>. Countries above it have above-average salary relative to living costs.',
        'High nominal salaries don\'t always win. Cost structure has a greater impact on '
        '<strong>relative affordability</strong> than raw salary figures. The index is a simplified '
        'comparison, not a full purchasing-power model.',
    ]

    cards_html = "".join(
        f'<div class="insight-card"><div class="insight-text">{text}</div></div>'
        for text in cards
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

    tiles = "".join(
        [
            _tile("Countries in gold layer", f"{gold.get('countries', 0)}", "After joining salary and cost data"),
            _tile("Match rate", f"{gold.get('match_rate_pct', 0):.1f}%", "Countries found in both sources"),
            _tile("Unknown currencies", f"{salaries.get('unknown_currencies', 0)}", "Salary rows without an exchange rate"),
            _tile("Salary outliers removed", f"{salaries.get('outliers_removed', 0)}", "Rows excluded as outliers"),
        ]
    )
    st.markdown(f'<div class="quality-grid">{tiles}</div>', unsafe_allow_html=True)

    _section("Rows per source")
    src_rows = "".join(
        f"<tr><td>{escape(str(name))}</td>"
        f"<td class='num'>{d.get('rows', 0):,}</td>"
        f"<td><span class='status-ok'>✓ Loaded</span></td></tr>"
        for name, d in sources.items()
    )
    st.markdown(
        f"""<div class="table-card">
          <table>
            <thead><tr><th>Source</th><th class='num'>Rows</th><th>Status</th></tr></thead>
            <tbody>{src_rows}</tbody>
          </table>
        </div>""",
        unsafe_allow_html=True,
    )

    def _dropped_list(items: list[str]) -> str:
        if not items:
            return "<div class='drop-none'>None dropped</div>"
        return "".join(f"<div class='drop-item'>{escape(str(c))}</div>" for c in items)

    _section("Dropped countries")
    st.markdown(
        f"""<div class="rankings-grid">
          <div class="table-card drop-list">
            <div class="drop-title">Missing from cost of living data</div>
            {_dropped_list(cost.get("dropped_countries", []))}
          </div>
          <div class="table-card drop-list">
            <div class="drop-title">No match in the gold join</div>
            {_dropped_list(gold.get("dropped_no_match", []))}
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


_SOURCES = [
    (
        "Cost of living index",
        '<a href="https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2024" '
        'target="_blank" rel="noopener noreferrer">Numbeo, Cost of Living Index by Country</a>'
        " (scale relative to New York City = 100)",
        "2024 ranking",
    ),
    (
        "Developer salaries",
        '<a href="https://survey.stackoverflow.co/2024/" target="_blank" '
        'rel="noopener noreferrer">Stack Overflow Developer Survey 2024</a>, annual '
        "compensation as self-reported, via the "
        '<a href="https://github.com/rfordatascience/tidytuesday/tree/main/data/2024/2024-09-03" '
        'target="_blank" rel="noopener noreferrer">TidyTuesday mirror</a> '
        "(data under the Open Database License)",
        "2024 survey",
    ),
    (
        "Country names, ISO3 codes, regions",
        '<a href="https://data.worldbank.org/country" target="_blank" '
        'rel="noopener noreferrer">World Bank Country API</a>',
        "Current list",
    ),
    (
        "Exchange rates to USD",
        '<a href="https://www.exchangerate-api.com" target="_blank" '
        'rel="noopener noreferrer">Rates by Exchange Rate API</a> (open access)',
        "{rates_period}",
    ),
]


def _sources(summary: dict | None) -> None:
    """Where every number comes from, its period, and how the index is built."""
    rates_period = f"Fetched {summary['run_at'][:10]}" if summary and summary.get("run_at") else "Fetched at run time"
    rows = "".join(
        f"<tr><td>{escape(topic)}</td><td>{desc}</td>"
        f"<td class='period'>{escape(period.format(rates_period=rates_period))}</td></tr>"
        for topic, desc, period in _SOURCES
    )
    with st.expander("Sources and method"):
        st.markdown(
            f"""<div class="table-card"><table class="src-table">
              <thead><tr><th>Data</th><th>Source</th><th>Period</th></tr></thead>
              <tbody>{rows}</tbody></table></div>
            <p class="src-note">Affordability index = median developer salary in USD ÷ cost of
            living index. Medians come from self-reported survey answers, with no minimum number
            of respondents per country, and local-currency salaries from the 2024 survey are
            converted at the exchange rates of the run date, so currencies that moved since 2024
            can distort the comparison. It is a simplified comparison, not a full
            purchasing-power model.</p>""",
            unsafe_allow_html=True,
        )


# ── Bootstrap ──────────────────────────────────────────────────────────────────

_inject()
_loaded = _load_data()
if _loaded is None:
    st.stop()
df_raw, _is_example = _loaded

# Same source as the data on screen: never pair real data with the example report.
_summary = load_pipeline_summary(
    config.EXAMPLE_PIPELINE_SUMMARY_FILE if _is_example else config.PIPELINE_SUMMARY_FILE
)

# ── Sidebar: navigation only ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """<div class="brand-name">DevEconomy</div>
        <div class="brand-sub">Developer salary intelligence</div>""",
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Page",
        ["Overview", "Salaries", "Affordability", "Insights", "Data Quality"],
        label_visibility="collapsed",
    )

    if _summary:
        run_at = _summary.get("run_at", "")[:10]
        data_year = _summary.get("year", "—")
        countries = _summary.get("gold", {}).get("countries", "—")
        match_rate = _summary.get("gold", {}).get("match_rate_pct", "—")
        st.markdown(
            f"""<div class="data-meta">
              <strong>{"Example pipeline run" if _is_example else "Last pipeline run"}</strong><br/>{escape(run_at)}<br/>
              Salaries and cost of living: {data_year}<br/>
              Exchange rates: {escape(run_at)}<br/>
              {countries} countries · {match_rate}% match rate
            </div>""",
            unsafe_allow_html=True,
        )

# ── Page header, then one filter row above everything it scopes ────────────────

_HEADERS = {
    "Overview": (
        "Developer salary vs cost of living",
        "Where a developer salary stretches furthest against the local cost of living.",
    ),
    "Salaries": (
        "Developer salaries by country",
        "Median developer salaries normalized to USD for cross-border comparison.",
    ),
    "Affordability": (
        "Where does a salary go furthest?",
        "High nominal salaries don't always win; the affordability index compares salary against living costs.",
    ),
    "Insights": (
        "Key insights",
        "Conclusions about affordability, regional trends and cost structure.",
    ),
    "Data Quality": (
        "Data quality and sources",
        "Pipeline stats, source match rates and diagnostics from the last run.",
    ),
}
_page_head(*_HEADERS[page])

if page != "Data Quality":
    f_region, f_salary, f_top = st.columns([3, 3, 2])
    regions = sorted(df_raw["region"].dropna().unique())
    selected_regions = f_region.multiselect("Region", regions, default=regions)
    sal_min = int(df_raw["median_salary_usd"].min())
    sal_max = int(df_raw["median_salary_usd"].max())
    salary_range = f_salary.slider(
        "Salary range (USD)", sal_min, sal_max, (sal_min, sal_max),
        step=1000, format="$%d",
    )
    top_n = f_top.slider("Ranking size", min_value=3, max_value=20, value=10)

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
        st.warning("No countries match the selected filters. Widen the region or salary range.")
        st.stop()
else:
    top_n = 10
    df = df_raw

# ── Pages ──────────────────────────────────────────────────────────────────────

if page == "Overview":
    _kpis(df)
    _section("Cost of living by country", "Darker blue means a lower cost of living index.")
    _chart(
        world_cost_map(df),
        df[["country", "region", "cost_of_living_index"]]
        .sort_values("cost_of_living_index", ascending=False),
    )
    _rankings(df, top_n)

elif page == "Salaries":
    _kpis(df)
    _section("Median salary by country", "Top 20 countries in the current selection.")
    _chart(
        salary_by_country_bar(df),
        df[["country", "region", "median_salary_usd"]]
        .sort_values("median_salary_usd", ascending=False),
    )

elif page == "Affordability":
    _kpis(df)
    _section("Affordability ranking", f"Top {top_n} countries by salary ÷ cost of living.")
    _chart(
        affordability_ranking_bar(df, top_n=top_n),
        df[["country", "region", "affordability_index"]].head(top_n),
    )
    _section("Salary vs cost of living", f"The {top_n} most affordable countries are highlighted.")
    _chart(
        affordability_scatter(df, highlight_n=top_n),
        df[["country", "region", "cost_of_living_index", "median_salary_usd", "affordability_index"]],
    )

elif page == "Insights":
    _insights(df)

else:  # Data Quality
    _data_quality(_summary)

_sources(_summary)
