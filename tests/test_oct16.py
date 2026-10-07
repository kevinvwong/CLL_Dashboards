"""The October 16 deliverable: /oct16.

The wireframes' Option A - the six Dean outcomes by milestones reached. Its own
definition says "Static, clickable pages; no live data feeds", so the content is a
fixed data module rather than a query, and these tests assert that.

The figures are illustrative. The wireframes say of this page "values show format
only, not CLL results", so a test asserts the page says so rather than leaving a
reader to assume they are real.
"""
from app import oct16_data


def test_it_follows_the_wireframe_layout(logged_in):
    """The page is Option A of the wireframes, so its own furniture must match the
    drawing: eyebrow, title, explainer, the scope block, the data-requirements
    table and the trade-offs. An earlier version showed only the six cards and was
    therefore not the wireframe."""
    body = logged_in("Bill Gaudelli").get("/oct16").text
    assert "OCTOBER 16" in body, "the eyebrow is missing"
    assert "Blueprint outcomes" in body, "the wireframe's own title is missing"
    assert "until its KPIs have data" in body, "the explainer is missing"
    assert "Scope and scale of this choice" in body, "the scope block is missing"
    assert "Data requirements: the complete list" in body, "the data table is missing"
    assert "Trade-offs" in body, "the trade-offs are missing"


def test_the_page_presents_itself_as_chosen_not_as_a_candidate(logged_in):
    """Option A was chosen 2026-10-07.

    The wireframes offered A and B as candidates, so their labels read "OPTION A"
    and "What the Dean is choosing". Now that the choice is made, the page must
    not read as a candidate the Dean still has to pick between - and the eyebrow
    must not be a bare letter the reader has to decode.
    """
    import html as _html

    body = logged_in("Bill Gaudelli").get("/oct16").text
    readable = _html.unescape(body)
    assert "THE DEAN'S DASHBOARD" in readable, "the eyebrow still reads as a candidate"
    assert "OPTION A" not in readable, "a stale candidate label survives"
    assert "is choosing" not in readable, "the page still describes the choice as pending"


def test_the_college_dashboard_milestone_is_not_claimed_as_delivered(logged_in):
    """Choosing the option starts the build; it does not deliver it.

    P05's third milestone is this dashboard itself. It read "This decision" while
    the option was pending. Marking it "Met" once chosen would claim a delivery
    that has not happened, since the deliverable is presented 2026-10-16 - so it
    is In progress.
    """
    p05 = next(o for o in oct16_data.OUTCOMES if o["id"] == "P05")
    statuses = dict(p05["milestones"])
    assert statuses["College dashboard"] == "In progress", (
        "the dashboard must not be marked Met before it is delivered"
    )


def test_the_cards_use_the_wireframes_wording(logged_in):
    """The drawing says "N of M milestones reached" and carries an
    "Owner: ... · updated ..." line. Both are reproduced.

    The count is asserted as a pattern, not as the literal "of 4". The wireframe
    drew "1 of 4" but listed only three milestones; carrying its 4 made the number
    disagree with the rows beneath it. The count is now derived from the list, so
    the card's M equals the milestones it shows (see test_oct16_module.py).

    The owner position is one of three distinguishable states rather than a bare
    "[name]" placeholder - see test_confirmed_data.py. The wireframe's bracket
    convention is kept for the unnamed case.
    """
    import re
    body = logged_in("Bill Gaudelli").get("/oct16").text
    assert re.search(r"\d+ of \d+ milestones reached", body), \
        "no 'N of M milestones reached' line"
    assert "no owner named" in body, "the unnamed owner state is missing"
    # The unnamed state now reads as a sentence ("... — to be named by Oct 12"),
    # not as an unfilled "updated [date]" slot. The string is still present and
    # distinguishable; test_confirmed_data.py pins the three states.


def test_the_data_requirements_table_has_every_row(logged_in):
    """19 rows, matching the workbook's Option A Data sheet. Reproduced rather than
    summarised so the page and the workbook cannot drift apart."""
    import html as _html

    assert len(oct16_data.DATA_REQUIREMENTS) == 19
    readable = _html.unescape(logged_in("Bill Gaudelli").get("/oct16").text)
    for r in oct16_data.DATA_REQUIREMENTS:
        assert r["id"] in readable, "data row %s is missing from the table" % r["id"]
        assert r["element"] in readable, "the element text for %s is missing" % r["id"]


def test_the_scope_block_matches_the_wireframes_figures(logged_in):
    body = logged_in("Bill Gaudelli").get("/oct16").text
    for _, value, _ in oct16_data.SCOPE:
        assert value in body, "scope figure %r is missing" % value
    assert "8 of 16" in body, "the in-hand figure is missing"
    assert "20\u201330" in body, "the items-to-collect figure is missing"


def test_both_sides_of_the_trade_offs_are_shown(logged_in):
    """A page listing only the advantages would not be one the Dean could decide
    from. The wireframes list three pros and two cons."""
    pros = [t for g, t in oct16_data.TRADE_OFFS if g]
    cons = [t for g, t in oct16_data.TRADE_OFFS if not g]
    assert len(pros) == 3 and len(cons) == 2, "the trade-off list changed shape"
    body = logged_in("Bill Gaudelli").get("/oct16").text
    # Compare on rendered text, not raw HTML: an apostrophe renders as &#39;, so a
    # raw substring check reports "missing" for text that is present. Unescape
    # first, then compare.
    import html as _html

    readable = _html.unescape(body)
    for text in pros + cons:
        assert text in readable, "trade-off %r is missing" % text[:40]
    assert "Does not match the 2026 priorities presented in May" in readable, (
        "the sharpest caveat must not be dropped"
    )


def test_every_outcome_shows_milestones_reached_of_planned(logged_in):
    """Progress here is milestones, as the brief specifies - not a KPI value and
    not a percentage of an invented composite."""
    body = logged_in("Bill Gaudelli").get("/oct16").text
    assert "milestones planned" in body
    for o in oct16_data.OUTCOMES:
        assert o["planned"] >= o["reached"], (
            "%s claims more milestones reached than planned" % o["id"]
        )
        assert len(o["milestones"]) >= 1, "%s has no milestones" % o["id"]


def test_the_page_says_the_figures_are_illustrative(logged_in):
    """Not decoration. A Board-facing page whose numbers are illustrative must say
    so on the page, not only in the source."""
    body = logged_in("Bill Gaudelli").get("/oct16").text
    assert "Illustrative" in body
    assert "not CLL results" in body


def test_the_page_names_its_sources(logged_in):
    body = logged_in("Bill Gaudelli").get("/oct16").text
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

    body = logged_in("Bill Gaudelli").get("/oct16").text
    # every outcome is its own card, and there is a card per outcome and no more
    cards = re.findall(r'class="oct16-card', body)
    assert len(cards) == 6, "expected one card per outcome, found %d" % len(cards)
    # the grid contains only those cards. Each card holds a NESTED
    # <ul class="oct16-milestones">, so a lazy ".*?</ul>" stops at the first
    # milestone list. Match from the grid's open to the memo that now follows it.
    grid = re.search(r'<ul class="oct16-grid">(.*?)<details', body, re.S)
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

    before = logged_in("Bill Gaudelli").get("/oct16").text
    conn = sqlite3.connect(fresh_db)
    conn.execute("DELETE FROM Initiatives")
    conn.execute("DELETE FROM Goals")
    conn.commit()
    conn.close()

    after = logged_in("Bill Gaudelli").get("/oct16").text
    assert "P01" in after, "the page still renders when the prototype tables are empty"
    # strip the one per-request value that legitimately differs (nothing here), then compare
    assert after == before, "the outcome content changed when the prototype data did"


def test_it_is_behind_the_gate(anon):
    """Board content is not public, even when illustrative."""
    response = anon.get("/oct16", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("Location") == "/login"


def test_the_milestone_count_matches_the_rows_beneath_it(logged_in):
    """The number must reconcile with the list on the card.

    The defect (browser analysis #12): P01 said "1 of 4" but listed three
    milestones; P05 said "2 of 4 reached" with only one MET among the three it
    showed. The count is now derived from the list, so this cannot drift.
    """
    from app import oct16_data
    for o in oct16_data.OUTCOMES:
        met = sum(1 for _, s in o["milestones"] if s == "Met")
        assert o["reached"] == met, "%s: reached=%d but %d are Met" % (
            o["id"], o["reached"], met)
        assert o["planned"] == len(o["milestones"]), (
            "%s: planned=%d but %d milestones are listed" % (
                o["id"], o["planned"], len(o["milestones"])))
