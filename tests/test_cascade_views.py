"""Group 3 of blueprint-redesign: cascade drill-downs and indexes.

Covers the grouping toggle, the relationships display, and the index filters
with their query-string state.
"""
import html as _html
import os

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- 3.1 the cascade drill-down ---------------------------------------------


def test_the_cascade_has_a_section_heading_and_rollup(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/goals/4").text)
    assert "section-heading" in body
    assert "eyebrow" in body
    # The rollup reads total-then-breakdown.
    assert "initiatives" in body and "on track" in body


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


def test_relationships_render_both_directions(logged_in):
    """A D-1 initiative shows what it feeds; a Dean one what feeds it."""
    from app import queries
    rel = queries.relationships_for(["MI-002", "MI-004"])
    assert rel, "no relationships found"
    # MI-004 feeds a Dean initiative.
    assert any(x["Direction"] == "Feeds" for x in rel.get("MI-004", [])), rel.get("MI-004")
    # MI-002 is fed by one.
    assert any(x["Direction"] == "Fed by" for x in rel.get("MI-002", [])), rel.get("MI-002")


def test_relationships_carry_status_and_progress():
    from app import queries
    rel = queries.relationships_for(["MI-004"])
    for x in rel["MI-004"]:
        assert "Status" in x and "PercentComplete" in x


def test_relationships_for_an_empty_list_is_empty():
    from app import queries
    assert queries.relationships_for([]) == {}


def test_a_d1_supporting_two_deans_shows_both():
    """The relationship read does not collapse multiple parents into one."""
    from app import queries
    rel = queries.relationships_for(["MI-004"])
    feeds = [x for x in rel.get("MI-004", []) if x["Direction"] == "Feeds"]
    assert len(feeds) >= 2, "expected MI-004 to feed more than one Dean initiative"


# --- 3.4 the index filters ---------------------------------------------------


def test_the_index_shows_a_filter_bar(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/initiatives").text)
    assert "filter-bar" in body
    for control in ("status", "owner", "goal", "stale"):
        assert ('name="%s"' % control) in body, "no %s filter" % control


def test_a_status_filter_narrows_the_list(logged_in):
    from app import queries
    full = len(queries.all_initiatives())
    body = logged_in("Bill Gaudelli").get("/initiatives?status=at-risk").text
    at_risk = len(queries.all_initiatives({"status": "at-risk"}))
    assert at_risk < full
    # The rendered rows equal the filtered count.
    assert body.count('class="index-row"') == at_risk


def test_an_owner_filter_narrows_the_list(logged_in):
    from app import queries
    body = logged_in("Bill Gaudelli").get("/initiatives?owner=Tim Jacobbe").text
    tim = len(queries.all_initiatives({"owner": "Tim Jacobbe"}))
    assert body.count('class="index-row"') == tim


def test_filters_combine(logged_in):
    from app import queries
    both = len(queries.all_initiatives({"status": "at-risk", "tier": "dean"}))
    body = logged_in("Bill Gaudelli").get("/initiatives?status=at-risk&tier=dean").text
    assert body.count('class="index-row"') == both


def test_an_empty_result_shows_an_empty_state_offering_to_clear(logged_in):
    from app import queries
    # A filter that matches nothing.
    assert queries.all_initiatives({"owner": "NobodyReal"}) == []
    body = _html.unescape(logged_in("Bill Gaudelli").get("/initiatives?owner=NobodyReal").text)
    assert "empty" in body
    assert "Clear" in body


def test_the_filter_controls_reflect_the_applied_value(logged_in):
    body = logged_in("Bill Gaudelli").get("/initiatives?owner=Tim Jacobbe").text
    # The Tim Jacobbe option is selected.
    assert "selected" in body
    assert 'value="Tim Jacobbe"' in body
