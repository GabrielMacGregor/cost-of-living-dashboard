"""Smoke tests for the Streamlit app (no network, uses bundled example data)."""

import re

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app():
    return AppTest.from_file("app.py", default_timeout=60).run()


def test_every_page_renders_without_exceptions(app):
    for page in ["Overview", "Salaries", "Affordability", "Insights", "Data Quality"]:
        app.radio[0].set_value(page).run()
        assert not app.exception, page


def test_rankings_never_repeat_countries_or_go_negative_with_few_results(app):
    low = app.slider[0].min
    app.slider[0].set_value((low, low + 8000)).run()
    app.slider[1].set_value(10).run()
    html = " ".join(m.value for m in app.markdown)
    ranks = [int(r) for r in re.findall(r"class='rank-num'>(-?\d+)<", html)]
    names = re.findall(r"<td>([^<]+)</td><td class='num'>\$", html)
    assert ranks and min(ranks) >= 1
    assert len(names) == len(set(names))


def test_sources_panel_and_data_periods_are_shown(app):
    html = " ".join(m.value for m in app.markdown)
    needles = (
        "numbeo.com", "survey.stackoverflow.co/2024", "worldbank.org", "exchangerate-api.com",
    )
    for needle in needles:
        assert needle in html
    assert "Salaries and cost of living:" in html
    assert "Exchange rates:" in html
