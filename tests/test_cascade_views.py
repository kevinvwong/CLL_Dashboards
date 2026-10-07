"""Group 3 of blueprint-redesign: cascade drill-downs and indexes.

Covers the grouping toggle, the relationships display, and the index filters
with their query-string state.
"""
import html as _html
import os
import re

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- 3.1 the cascade drill-down ---------------------------------------------


def test_the_cascade_has_a_section_heading_and_rollup(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/goals/4").text)
    assert "section-heading" in body
    assert "eyebrow" in body
    # The rollup reads total-then-breakdown.
    assert re.search(r"\d+ initiative", body), body[:400]


def test_the_grouping_toggle_offers_three_groupings(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/goals/4").text)
    assert "group-toggle" in body
    for g in ("owner", "tier", "status"):
        assert ("group=%s" % g) in body, "no toggle for %s" % g


@pytest.mark.parametrize("by", ["owner", "tier", "status"])
def test_grouping_renders_label_before_rows(logged_in, by):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/goals/4?group=%s" % by).text)
    assert "list-group-label" in body, "no group labels for %s" % by
    # Every label is followed by its list; no label is left without rows.
    first_label = body.index("list-group-label")
    first_list = body.index("initiative-list")
    assert first_label < first_list, "a label rendered after its rows"


def test_group_rows_only_returns_non_empty_groups():
    from app import queries
    rows = queries.goal_rows(1)
    for by in queries.GROUPINGS:
        for g in queries.group_rows(rows, by):
            assert g["rows"], "an empty group was returned"


def test_an_unknown_grouping_falls_back_without_error(logged_in):
    r = logged_in("Bill Gaudelli").get("/goals/4?group=nonsense")
    assert r.status_code == 200


# --- 3.2 relationships -------------------------------------------------------


def test_relationships_render_the_contributes_to_direction(logged_in):
    """The merged model has ONE direction: a Major Initiative contributes to the
    Dean Priorities it is linked to. The prototype's Feeds/Fed-by pair is gone."""
    from app import queries
    rel = queries.relationships_for(["MI-002", "MI-004"])
    assert rel, "no relationships found"
    for code, rows in rel.items():
        assert all(x["Direction"] == "Contributes to" for x in rows), rows


def test_relationships_for_an_empty_list_is_empty():
    from app import queries
    assert queries.relationships_for([]) == {}


def test_a_major_initiative_contributing_to_two_deans_shows_both(logged_in, fresh_db):
    """The relationship read does not collapse multiple targets into one."""
    import sqlite3

    from app import queries
    conn = sqlite3.connect(fresh_db)
    iid = conn.execute(
        "SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId='MI-004'").fetchone()[0]
    conn.execute("INSERT OR IGNORE INTO MajorInitiativeDeanLinks (MajorInitiativeID, DeanPriorityID) "
                 "VALUES (?, 1), (?, 2)", (iid, iid))
    conn.commit()
    conn.close()
    rel = queries.relationships_for(["MI-004"])
    assert len(rel.get("MI-004", [])) >= 2, "expected MI-004 to contribute to more than one Dean Priority"


# --- 3.4 the index filters ---------------------------------------------------


def test_the_index_shows_a_filter_bar(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/major-initiatives").text)
    assert "mi-table" in body or "filter-bar" in body


def test_a_status_filter_narrows_the_list(logged_in):
    from app import queries
    full = len(queries.all_initiatives())
    at_risk = len(queries.all_initiatives({"status": "at-risk"}))
    assert at_risk < full


# The /initiatives owner-filter index was removed in the 2026-10-07 merge: its
# page is superseded by /major-initiatives, which groups by team and source area
# rather than offering an owner dropdown. The filter tests below pinned that page,
# so they are retired (the underlying all_initiatives filter is still covered by
# test_a_status_filter_narrows_the_list above).
