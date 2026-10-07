"""Dean Priorities read models and rendering (register, 2026-10-07)."""
from app import queries


def test_dean_priorities_grouped(fresh_db):
    rows = queries.dean_priorities()
    assert len(rows) == 11
    assert sum(1 for r in rows if r["fiscal_year"] == 26) == 3
    assert sum(1 for r in rows if r["fiscal_year"] == 27) == 8


def test_percent_scaling(fresh_db):
    by_title = {r["title"]: r for r in queries.dean_priorities()}
    assert by_title["OMS AI"]["percent_complete"] == 50
    assert by_title["Strategy '35 Develop"]["percent_complete"] == 100
    assert by_title["Financial & Labor Optimization"]["percent_complete"] == 0


def test_dean_links_resolve(fresh_db):
    links = queries.major_initiative_dean_links("MI-002")
    assert links
    assert all(l["dean_code"].startswith("D27-") for l in links)


def test_home_shows_dean_section(logged_in):
    html = logged_in("Bill Gaudelli").get("/").text
    assert "Dean Priorities" in html
    assert "FY26" in html and "FY27" in html


def test_major_initiative_shows_description_and_dean_links(logged_in):
    html = logged_in("Bill Gaudelli").get("/major-initiatives/MI-002").text
    assert "Contributes to" in html
