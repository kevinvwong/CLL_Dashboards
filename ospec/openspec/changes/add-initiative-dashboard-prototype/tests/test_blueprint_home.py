"""Group 2 of blueprint-redesign: the blueprint home.

The home is a hero stage, not a tile grid. These assert the stage's structure,
the priority colour keying, the selected-priority panel, and the signals strip
with its honest no-update state.
"""
import html as _html
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _home(logged_in, query=""):
    return _html.unescape(logged_in("Bill").get("/" + query).text)


# --- 2.1 the hero stage -----------------------------------------------------


def test_the_stage_renders_a_dean_node_and_six_cards(logged_in):
    body = _home(logged_in)
    assert 'class="stage"' in body, "no hero stage"
    assert "dean-node" in body, "no Dean node"
    assert body.count('class="priority-card') == 6, "expected six priority cards"


def test_each_priority_card_is_colour_keyed(logged_in):
    """Each card sets --priority from the priority colour scale."""
    body = _home(logged_in)
    tokens = re.findall(r"--priority:\s*var\((--priority-\d)\)", body)
    assert len(tokens) == 6, tokens
    assert len(set(tokens)) == 6, "two cards share a colour: %s" % tokens


def test_each_card_carries_code_name_and_count(logged_in):
    from app import queries
    body = _home(logged_in)
    for p in queries.blueprint_priorities():
        assert p["Code"] in body, "missing code %s" % p["Code"]
        assert p["Title"] in body, "missing title %s" % p["Title"]
    # Every card shows its count.
    assert body.count('class="count"') >= 6


# --- 2.2 the selected-priority panel ----------------------------------------


def test_a_priority_is_selected_by_default(logged_in):
    """The panel is never empty on first load."""
    body = _home(logged_in)
    assert "Selected priority" in body
    assert 'class="priority-card is-selected"' in body


def test_selecting_a_priority_updates_the_panel(logged_in):
    """Selection is a query parameter, so it works without JavaScript."""
    body = _home(logged_in, "?priority=Pathways")
    assert "Integrated Portfolio &amp; Pathways" in body or \
           "Integrated Portfolio & Pathways" in body
    assert "Selected priority" in body


def test_the_panel_shows_the_description(logged_in):
    from app import priorities
    body = _home(logged_in, "?priority=Data")
    assert priorities.description("Data")[:60] in body


def test_the_panel_lists_its_initiatives(logged_in):
    body = _home(logged_in, "?priority=Data")
    # The panel has the initiatives block, distinct from the signals strip.
    assert "panel-initiatives" in body


def test_an_unknown_priority_falls_back_without_error(logged_in):
    r = logged_in("Bill").get("/?priority=NotARealPriority")
    assert r.status_code == 200
    assert 'class="priority-card is-selected"' in _html.unescape(r.text)


# --- 2.3 the initiative-signals strip ---------------------------------------


def test_signals_show_progress(logged_in):
    body = _home(logged_in)
    assert "initiative-signals" in body
    assert 'role="progressbar"' in body
    assert 'aria-valuenow=' in body


def test_a_signal_with_no_update_is_not_zero(logged_in, fresh_db):
    """A missing update is stated, never a zero bar."""
    import sqlite3
    conn = sqlite3.connect(str(fresh_db))
    try:
        iid = conn.execute("SELECT InitiativeID FROM Initiatives WHERE Code = 'D-A'").fetchone()[0]
        conn.execute("DELETE FROM ProgressUpdates WHERE InitiativeID = ?", (iid,))
        conn.commit()
    finally:
        conn.close()

    body = _home(logged_in)
    assert "No update yet" in body
    assert "progress-empty" in body


def test_no_aggregate_figure_is_shown(logged_in):
    """The design forbids a computed rollup anywhere."""
    body = _home(logged_in)
    assert "aggregate" not in body.lower()
    assert "average" not in body.lower()


# --- 2.4 the reads are named ------------------------------------------------


def test_the_home_reads_are_named_functions():
    """The route reads through named queries, not ad-hoc SQL in the handler."""
    from app import queries
    for fn in ("blueprint_priorities", "initiative_signals", "priority_rows"):
        assert hasattr(queries, fn), "missing read %s" % fn


def test_blueprint_priorities_carry_code_title_colour(logged_in):
    from app import queries
    rows = queries.blueprint_priorities()
    assert len(rows) == 6
    for p in rows:
        assert p["Code"].startswith("P")
        assert p["Title"]
        assert p["ColourToken"].startswith("--priority-")


def test_blueprint_priorities_sort_by_code(logged_in):
    from app import queries
    codes = [p["Code"] for p in queries.blueprint_priorities()]
    assert codes == ["P01", "P02", "P03", "P04", "P05", "P06"]
