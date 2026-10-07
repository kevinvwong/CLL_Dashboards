"""Search and the meeting enhancements.

The two features the superseded overhaul-ui-ux-navigation change specified and
blueprint-redesign did not ship. Built here so they were not lost when that
change was closed: global search (3.5) and meeting quick ranges, change deltas
and presenter mode (6.1, 6.3, 6.4).
"""
import html as _html
import os
import re

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def _enable_meeting(meeting_on):
    """The meeting is iced by default; these cases verify it is intact."""
    return meeting_on


# --- search (overhaul 3.5) ---------------------------------------------------


def test_search_finds_an_initiative_by_code(logged_in):
    from app import queries
    results = queries.search("MI-003")
    assert results, "no result for a code"
    assert "Data" in results[0]["label"] or results[0]["code"] == "MI-003", results[0]


def test_search_finds_a_person(logged_in):
    from app import queries
    kinds = {r["kind"] for r in queries.search("elizabeth")}
    assert "person" in kinds, kinds


def test_search_spans_all_four_kinds(logged_in):
    from app import queries
    kinds = set()
    for term in ("MI-002", "Bill Gaudelli", "Research", "Data"):
        for r in queries.search(term):
            kinds.add(r["kind"])
    assert {"team-initiative", "person", "goal", "priority"} <= kinds, kinds


def test_search_returns_nothing_for_empty_or_no_match(logged_in):
    from app import queries
    assert queries.search("") == []
    assert queries.search("zzzznotathing") == []


def test_the_search_endpoint_renders_the_fragment_for_the_palette(logged_in):
    """An htmx request from the palette gets the bare fragment to swap in."""
    body = logged_in("Bill Gaudelli").get("/search?q=MI-003",
                                 headers={"HX-Request": "true"}).text
    assert "search-results" in body
    assert "<html" not in body.lower(), "the palette wants a fragment"


def test_a_direct_search_load_is_a_full_page(logged_in):
    """A direct load - what pressing Enter in the palette does - must be a real
    page, not the raw fragment. It previously rendered with no chrome at all
    (Times New Roman, no header), which looked like a crash."""
    body = logged_in("Bill Gaudelli").get("/search?q=faculty").text
    assert "<html" in body.lower()
    assert "site-header" in body, "the direct page has no chrome"


def test_a_single_search_result_redirects_straight_to_it(logged_in):
    """Enter on an unambiguous query should land on the thing, not a list of one."""
    r = logged_in("Bill Gaudelli").get("/search?q=MI-001", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/team-initiatives/MI-001"


def test_search_finds_a_team_initiative_by_its_id(logged_in):
    """The 29 Team Initiatives are core objects; they must be findable."""
    from app import queries
    kinds = {r["kind"] for r in queries.search("MI-001")}
    assert "team-initiative" in kinds, kinds


def test_the_search_palette_is_in_the_layout(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'id="search-palette"' in body
    assert "data-search-open" in body
    # Opened with Cmd/Ctrl+K.
    assert "metaKey" in body and "ctrlKey" in body


# --- meeting quick ranges (overhaul 6.1) ------------------------------------


def test_the_meeting_offers_quick_ranges(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/meeting").text)
    assert "range=7d" in body
    assert "range=14d" in body
    assert "Last meeting" in body


def test_a_range_sets_the_window(logged_in):
    """?range=14d moves the window 14 days back, not 7."""
    from app import queries
    import datetime as dt
    body = logged_in("Bill Gaudelli").get("/meeting?range=14d").text
    expected = queries.default_since(14)
    assert expected in body
    # And the chip is marked active.
    assert re.search(r'range=14d"[^>]*is-active', body) or "is-active" in body


# --- meeting deltas (overhaul 6.3) ------------------------------------------


def test_deltas_show_before_and_after(logged_in, diary):
    from app import queries
    diary('MI-002', 20, 'On track', on='2026-09-20')
    diary('MI-002', 40, 'On track', on='2026-10-05')
    rows = queries.update_deltas("2000-01-01")
    assert rows, "no deltas"
    changed = [d for d in rows if not d["IsFirst"]]
    assert changed, "expected at least one non-first update"
    # A changed row carries both values.
    d = changed[0]
    assert d["PrevPercent"] is not None and d["PercentComplete"] is not None


def test_a_first_update_is_marked_not_invented_as_zero(logged_in):
    from app import queries
    rows = queries.update_deltas("2000-01-01")
    firsts = [d for d in rows if d["IsFirst"]]
    # If any exist, they must be marked, not shown as a 0 -> N change.
    for d in firsts:
        assert d["PrevPercent"] is None


def test_the_meeting_renders_the_delta_arrow(logged_in, diary):
    diary('MI-002', 20, 'On track', on='2026-09-20')
    diary('MI-002', 40, 'On track', on='2026-10-05')
    body = logged_in("Bill Gaudelli").get("/meeting?since=2000-01-01").text
    # The arrow is rendered as text (→), so a delta is visible without colour.
    assert "→" in body or "&rarr;" in body


def test_changes_stay_grouped_by_owner(logged_in, fresh_db, diary):
    diary('MI-002', 20, 'On track', on='2026-10-05')
    """The meeting-view requirement: changes grouped by owner is unchanged."""
    import sqlite3
    conn = sqlite3.connect(str(fresh_db))
    conn.execute("UPDATE TeamInitiativeUpdates SET UpdateDate = date('now')")
    conn.commit()
    conn.close()
    body = logged_in("Bill Gaudelli").get("/meeting?since=2000-01-01").text
    assert 'class="list-group-label"' in body


# --- presenter mode (overhaul 6.4) ------------------------------------------


def test_the_meeting_offers_presenter_mode(logged_in):
    body = logged_in("Bill Gaudelli").get("/meeting").text
    assert "meeting-presenter" in body
    assert "data-presenter-start" in body


def test_presenter_groups_exist_for_arrow_navigation(logged_in, fresh_db):
    import sqlite3
    conn = sqlite3.connect(str(fresh_db))
    conn.execute("UPDATE TeamInitiativeUpdates SET UpdateDate = date('now')")
    conn.commit()
    conn.close()
    body = logged_in("Bill Gaudelli").get("/meeting?since=2000-01-01").text
    assert "presenter-position" in body
    # The arrow keys are wired.
    assert "ArrowRight" in body and "ArrowLeft" in body
    assert "presenting" in body


def test_presenter_mode_is_hidden_for_print(logged_in):
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    # The presenter overlay is excluded from print.
    assert re.search(r"@media print[^}]*\.presenter[^}]*display: none", css, re.S) or \
           ".presenter { display: none; }" in css
