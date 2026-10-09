"""/outcomes: the six annual priorities for a plan year.

The wireframes called the same six rows "outcomes"; they are the six priorities
P01-P06, and the page is now DB-backed and year-scoped (multi-year, 2026-10-08).
Supersedes the earlier "October 16 module" tests: the build memo moved to the
guide, and the content is read from the database, not a fixed data module.

The figures are illustrative until owners confirm them; the page says so.
"""
import re

from app import queries


def _outcomes(logged_in):
    return logged_in("Bill Gaudelli").get("/outcomes").text


def test_it_names_the_plan_year(logged_in):
    """The page is specific about which plan year it shows (multi-year)."""
    body = _outcomes(logged_in)
    assert "The six 2027 priorities" in body, "the year is not named in the title"
    assert "Annual priorities \u00b7 2027" in body


def test_every_priority_shows_milestones_reached_of_planned(logged_in):
    """Progress is milestones, not a KPI value and not an invented composite."""
    body = _outcomes(logged_in)
    assert "milestones planned" in body
    for o in queries.priority_outcomes(2027):
        assert o["Planned"] >= o["Reached"], (
            "%s claims more milestones reached than planned" % o["Code"])
        assert len(o["milestones"]) >= 1, "%s has no milestones" % o["Code"]


def test_the_cards_use_the_scheduling_wording(logged_in):
    body = _outcomes(logged_in)
    assert re.search(r"\d+ of \d+ milestones reached", body), \
        "no 'N of M milestones reached' line"
    assert "no owner named" in body, "the unnamed owner state is missing"


def test_the_page_says_the_figures_are_illustrative(logged_in):
    """A Board-facing page whose numbers are illustrative must say so on the
    page, not only in the source."""
    body = _outcomes(logged_in)
    assert "Illustrative" in body
    assert "not CLL results" in body


def test_no_rollup_figure_appears(logged_in):
    """The brief forbids invented composite scores, so the page must not present a
    combined figure across the six priorities. One card per priority, no more,
    and no aggregate element."""
    body = _outcomes(logged_in)
    cards = re.findall(r'class="oct16-card', body)
    assert len(cards) == 6, "expected one card per priority, found %d" % len(cards)
    for token in ("oct16-total", "oct16-overall", "oct16-summary-figure"):
        assert token not in body, "an aggregate element %r is present" % token


def test_the_milestone_count_matches_the_rows_beneath_it(logged_in):
    """The number must reconcile with the list on the card (browser analysis #12)."""
    import sqlite3

    for o in queries.priority_outcomes(2027):
        met = sum(1 for m in o["milestones"] if m["Status"] == "Met")
        assert o["Reached"] == met, "%s: reached=%d but %d are Met" % (
            o["Code"], o["Reached"], met)
        assert o["Planned"] == len(o["milestones"])


def test_the_page_reads_from_the_database(logged_in, fresh_db):
    """The page is DB-backed: a milestone change is reflected (multi-year)."""
    import sqlite3

    before = _outcomes(logged_in)
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE Milestones SET Status='Met' WHERE Name='B2B strategy launched'")
    conn.commit()
    conn.close()
    after = _outcomes(logged_in)
    assert after != before, "the page did not follow the database"


def test_it_is_behind_the_gate(anon):
    response = anon.get("/outcomes", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("Location") == "/login"


def test_the_legacy_oct16_route_redirects(logged_in):
    r = logged_in("Bill Gaudelli").get("/oct16", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"] == "/outcomes"
