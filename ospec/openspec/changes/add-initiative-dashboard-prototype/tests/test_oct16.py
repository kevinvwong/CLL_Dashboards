"""The October 16 deliverable: /oct16.

The wireframes' Option A - the six Dean outcomes by milestones reached. Its own
definition says "Static, clickable pages; no live data feeds", so the content is a
fixed data module rather than a query, and these tests assert that.

The figures are illustrative. The wireframes say of this page "values show format
only, not CLL results", so a test asserts the page says so rather than leaving a
reader to assume they are real.
"""
from app import oct16_data


def test_the_page_renders_the_six_outcomes(logged_in):
    body = logged_in("Bill").get("/oct16").text
    assert "Dean outcomes" in body
    for oid in ("P01", "P02", "P03", "P04", "P05", "P06"):
        assert oid in body or oid.lower() in body, "outcome %s is missing" % oid


def test_every_outcome_shows_milestones_reached_of_planned(logged_in):
    """Progress here is milestones, as the brief specifies - not a KPI value and
    not a percentage of an invented composite."""
    body = logged_in("Bill").get("/oct16").text
    assert "milestones planned" in body
    for o in oct16_data.OUTCOMES:
        assert o["planned"] >= o["reached"], (
            "%s claims more milestones reached than planned" % o["id"]
        )
        assert len(o["milestones"]) >= 1, "%s has no milestones" % o["id"]


def test_the_page_says_the_figures_are_illustrative(logged_in):
    """Not decoration. A Board-facing page whose numbers are illustrative must say
    so on the page, not only in the source."""
    body = logged_in("Bill").get("/oct16").text
    assert "Illustrative" in body
    assert "not CLL results" in body


def test_the_page_names_its_sources(logged_in):
    body = logged_in("Bill").get("/oct16").text
    assert "KPI Atomic Definitions" in body
    assert "wireframes" in body.lower()


def test_no_rollup_figure_appears(logged_in):
    """The brief forbids invented composite scores, so the page must not present a
    combined figure across the six outcomes.

    Asserted on structure, not on words. A word list was the first attempt and it
    was wrong: "average" appears legitimately inside P04's target definition,
    "<=28-day average build", which is the KPI's own wording from the workbook and
    not a rollup. What matters is that no element summarises the six outcomes
    together, which is what this checks.
    """
    import re

    body = logged_in("Bill").get("/oct16").text
    # every outcome is its own card, and there is a card per outcome and no more
    cards = re.findall(r'class="oct16-card', body)
    assert len(cards) == 6, "expected one card per outcome, found %d" % len(cards)
    # the grid contains only those cards
    grid = re.search(r'<ul class="oct16-grid">(.*?)</ul>\s*<section', body, re.S)
    assert grid, "the outcomes grid was not found"
    assert grid.group(1).count("oct16-card") == 6, "something else is in the grid"
    # and no element aggregates them
    for token in ("oct16-total", "oct16-overall", "oct16-summary-figure"):
        assert token not in body, "an aggregate element %r is present" % token


def test_the_page_content_does_not_come_from_the_prototype_tables(logged_in, fresh_db):
    """Static by design: the brief says "no live data feeds".

    Not "needs no database" - the access gate reads the database to decide whether
    the site is up, so removing the file takes the whole app down with it, which is
    correct behaviour and was the first, wrong version of this test. What matters is
    that the *outcome content* is not drawn from the prototype's tables: those hold
    goals and initiatives, and have no outcomes, no teams and no milestones.

    Proven by changing the database out from under the page and asserting the
    content is unchanged.
    """
    import sqlite3

    before = logged_in("Bill").get("/oct16").text
    conn = sqlite3.connect(fresh_db)
    conn.execute("DELETE FROM Initiatives")
    conn.execute("DELETE FROM Goals")
    conn.commit()
    conn.close()

    after = logged_in("Bill").get("/oct16").text
    assert "P01" in after, "the page still renders when the prototype tables are empty"
    # strip the one per-request value that legitimately differs (nothing here), then compare
    assert after == before, "the outcome content changed when the prototype data did"


def test_it_is_behind_the_gate(anon):
    """Board content is not public, even when illustrative."""
    response = anon.get("/oct16", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("Location") == "/login"
