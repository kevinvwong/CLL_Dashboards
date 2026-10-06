"""Group 1 bug fixes from overhaul-ui-ux-navigation.

Each test names the defect it guards, and each was verified to reproduce before
the fix (see the group-1 tasks). The point of this file is that these defects
cannot come back silently.
"""
import os
import re

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(APP, "app", "templates")


def _signed(client, pid=1):
    client.post("/login", data={"passcode": "testpass"}, follow_redirects=False)
    client.post("/whoami", data={"person_id": pid}, follow_redirects=False)
    return client


# --- 1.1 partial vs full responses -----------------------------------------


@pytest.mark.parametrize("path", [
    "/initiatives/ELIZ-1/edit/details",
    "/initiatives/ELIZ-1/edit/tags",
    "/initiatives/ELIZ-1/edit/links",
    "/initiatives/ELIZ-1/update",
])
def test_edit_forms_are_fragments_when_requested_by_htmx(logged_in, path):
    """A partial request must not carry the site layout.

    The defect: edit_details.html extended base.html, so the whole site loaded
    inside the modal. All four forms are opened with hx-get into #card-modal.
    """
    body = logged_in("Kevin").get(path, headers={"HX-Request": "true"}).text
    assert "<html" not in body.lower(), "fragment carried a full document"
    assert "site-nav" not in body, "fragment carried the site navigation"
    assert "<form" in body, "fragment has no form"


@pytest.mark.parametrize("path", [
    "/initiatives/ELIZ-1/edit/details",
    "/initiatives/ELIZ-1/edit/tags",
    "/initiatives/ELIZ-1/edit/links",
    "/initiatives/ELIZ-1/update",
])
def test_edit_forms_are_full_pages_when_loaded_directly(logged_in, path):
    """A direct load must render the full layout, not a bare fragment."""
    body = logged_in("Kevin").get(path).text
    assert "<html" in body.lower(), "direct load did not render a document"
    assert "site-nav" in body, "direct load had no navigation"


# --- 1.2 the close control --------------------------------------------------


def test_standalone_page_has_no_modal_close_control(logged_in):
    """The full page shows "← Back"; a second "×" is a control for a dialog
    that was never opened."""
    body = logged_in("Bill").get("/initiatives/ELIZ-1").text
    assert 'class="card-close"' not in body, "the full page still shows the close control"
    assert "Back" in body, "the full page lost its Back link"


def test_the_fragment_keeps_the_close_control(logged_in):
    """The modal still needs its close button."""
    body = logged_in("Bill").get("/initiatives/ELIZ-1",
                                headers={"HX-Request": "true"}).text
    assert 'class="card-close"' in body


# --- 1.3 no empty-side chrome ----------------------------------------------


def test_empty_sides_render_no_orphan_chrome():
    """Render list.html directly with one side empty.

    The defect: the Dean <ul> and the "D-1" divider rendered unconditionally, so
    a Dean-only or D-1-only slice showed an empty list and a divider pointing at
    nothing. Invisible in the sample data, where every slice has both sides.
    """
    from app.main import templates

    def render(dean_rows, d1_groups):
        tpl = templates.get_template("list.html")
        return tpl.render(request=None, person={"Name": "Bill"}, app_env="test",
                          may_admin=False, heading="X", description=None,
                          entry_kind="goal", entry_key=1, counts=[], rollup="0 initiatives",
                          dean_rows=dean_rows, d1_groups=d1_groups)

    both_empty = render([], [])
    assert "dean-rows" not in both_empty, "empty Dean list still rendered"
    assert 'class="divider"' not in both_empty, "the D-1 divider rendered with no groups"

    d1_only = render([], [{"owner": "Solo", "rows": [
        {"Code": "X-1", "InitiativeName": "n", "Level": "D-1", "Owner": "o",
         "OwnerID": 1, "PercentComplete": 10, "Status": "On track", "IsPrimary": 0}]}])
    assert "dean-rows" not in d1_only, "empty Dean list still rendered beside a D-1 group"
    assert "Solo" in d1_only, "the D-1 group vanished"


def test_both_populated_still_renders_the_divider(logged_in):
    """The normal case must keep the divider between the two tiers."""
    body = logged_in("Bill").get("/goals/1").text
    assert 'class="divider"' in body
    assert body.index('class="divider"') > body.index("dean-rows")


def test_a_group_with_no_rows_renders_no_label():
    """A group header with no rows under it is an orphan label."""
    from app.main import templates

    tpl = templates.get_template("list.html")
    body = tpl.render(request=None, person={"Name": "Bill"}, app_env="test",
                      may_admin=False, heading="X", description=None, entry_kind="goal",
                      entry_key=1, counts=[], rollup="0 initiatives",
                      dean_rows=[], d1_groups=[{"owner": "Nobody", "rows": []}])
    assert "list-group-label" not in body, "an empty group rendered its label"


# --- 1.4 rollup labels ------------------------------------------------------


def test_rollup_label_is_total_then_breakdown():
    """A pure function, so it can be asserted without a page."""
    from app import queries

    counts = [{"Status": "On track", "Count": 10}]
    assert queries.rollup_label(10, counts) == "10 initiatives \u00b7 10 on track"

    mixed = [{"Status": "On track", "Count": 9}, {"Status": "At risk", "Count": 3}]
    label = queries.rollup_label(12, mixed)
    assert label.startswith("12 initiatives")
    assert "9 on track" in label and "3 at risk" in label


def test_rollup_label_omits_zero_counts():
    from app import queries

    label = queries.rollup_label(2, [{"Status": "On track", "Count": 2},
                                     {"Status": "At risk", "Count": 0}])
    assert "0 at risk" not in label
    assert label == "2 initiatives \u00b7 2 on track"


def test_rollup_label_singularises():
    from app import queries

    assert queries.rollup_label(1, [{"Status": "At risk", "Count": 1}]).startswith("1 initiative ")


def test_goal_header_reads_total_not_a_status_word(logged_in):
    """The defect: the header read "On track 10"."""
    body = logged_in("Bill").get("/goals/4").text
    m = re.search(r'class="status-counts">([^<]+)<', body)
    assert m, "no rollup rendered"
    label = m.group(1)
    assert re.match(r"^\d+ initiatives", label), label
    assert label != "On track 10"


# --- 1.5 pluralised day counts ---------------------------------------------


def test_one_day_is_singular(logged_in, fresh_db):
    """The defect: every count read "N days", including "1 days"."""
    import sqlite3
    import datetime as dt

    # ELIZ-1 is owned by Elizabeth (2); age its only update to exactly 1 day.
    yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    conn = sqlite3.connect(str(fresh_db))
    try:
        iid = conn.execute("SELECT InitiativeID FROM Initiatives WHERE Code = 'ELIZ-1'").fetchone()[0]
        conn.execute("DELETE FROM ProgressUpdates WHERE InitiativeID = ?", (iid,))
        conn.execute(
            "INSERT INTO ProgressUpdates (InitiativeID, UpdateDate, PercentComplete, Status, EnteredByID) "
            "VALUES (?, ?, 10, 'On track', 2)", (iid, yesterday))
        conn.commit()
    finally:
        conn.close()

    body = logged_in("Elizabeth").get("/people/2").text
    assert "1 day since last update" in body
    assert "1 days since last update" not in body


def test_many_days_is_plural(logged_in, fresh_db):
    import sqlite3
    import datetime as dt

    old = (dt.date.today() - dt.timedelta(days=15)).isoformat()
    conn = sqlite3.connect(str(fresh_db))
    try:
        iid = conn.execute("SELECT InitiativeID FROM Initiatives WHERE Code = 'MAR-1'").fetchone()[0]
        conn.execute("DELETE FROM ProgressUpdates WHERE InitiativeID = ?", (iid,))
        conn.execute(
            "INSERT INTO ProgressUpdates (InitiativeID, UpdateDate, PercentComplete, Status, EnteredByID) "
            "VALUES (?, ?, 10, 'On track', 4)", (iid, old))
        conn.commit()
    finally:
        conn.close()

    body = logged_in("Bill").get("/people/4").text
    assert "15 days since last update" in body


# --- 1.6 the index routes and the styled error page ------------------------


def test_initiatives_index_returns_html(logged_in):
    """The defect: GET /initiatives returned a 405 JSON body."""
    r = logged_in("Bill").get("/initiatives")
    assert r.status_code == 200, r.status_code
    assert "text/html" in r.headers.get("content-type", "")
    assert "<html" in r.text.lower()


def test_people_index_returns_html(logged_in):
    """The defect: GET /people returned a 404 JSON body."""
    r = logged_in("Bill").get("/people")
    assert r.status_code == 200, r.status_code
    assert "text/html" in r.headers.get("content-type", "")
    assert "<html" in r.text.lower()


def test_unknown_route_renders_a_styled_page_for_a_browser(logged_in):
    r = logged_in("Bill").get("/no-such-page", headers={"accept": "text/html"})
    assert r.status_code == 404
    assert "<html" in r.text.lower(), "raw body instead of a styled page"
    assert "error-page" in r.text
    assert 'href="/"' in r.text, "no way back to Overview"


def test_unknown_route_still_answers_json_for_a_non_browser(logged_in):
    """A script or probe must not be handed a full HTML document."""
    r = logged_in("Bill").get("/no-such-page", headers={"accept": "application/json"})
    assert r.status_code == 404
    assert "application/json" in r.headers.get("content-type", "")


# --- 1.7 accessible names on the home links ---------------------------------
#
# Group 2 of blueprint-redesign replaced the tile grid with a hero stage. The
# requirement is unchanged: a goal or priority link must carry an accessible
# name stating what it is and how many initiatives it holds. The links simply
# moved from `.tile` to the stage's cards and goals panel.


def test_goal_links_have_accessible_names(logged_in):
    body = logged_in("Bill").get("/").text
    names = re.findall(r'aria-label="([^"]+)"', body)
    goal_labels = [n for n in names if "initiative" in n]
    assert goal_labels, "goal links have no aria-label"
    # A label names the goal and its count, not just a bare number.
    assert any(re.match(r"^.+, \d+ initiatives?$", n) for n in goal_labels), goal_labels


def test_priority_cards_have_accessible_names(logged_in):
    import html as _html
    body = _html.unescape(logged_in("Bill").get("/").text)
    names = re.findall(r'aria-label="([^"]+)"', body)
    assert any("Culture & Learning" in n and "initiative" in n for n in names), names
