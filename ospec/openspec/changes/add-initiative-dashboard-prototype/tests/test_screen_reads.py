"""Screen-shaped reads: one read per screen, and no-update vs zero.

Covers the `screen-reads` spec of deepen-dashboard-modules.

The distinction this file guards is the one the confirmed-data spec cares about:
a missing update is NOT "0% complete". It was previously expressed three different
ways across three screens; these tests pin one behaviour at the read.
"""
import os

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, "app")


# --- one read per screen ----------------------------------------------------


def test_tag_edit_options_returns_lists_and_chosen(fresh_db):
    from app import queries

    iid = _initiative_id(fresh_db, "ELIZ-1")
    options = queries.tag_edit_options(iid)

    assert set(options) == {"goals", "priorities", "chosen_goals", "chosen_priorities"}
    assert options["goals"], "no goal options"
    # Two independent taxonomies: goals and priorities are separate lists.
    assert {g["GoalNumber"] for g in options["goals"]}
    assert {p["PriorityName"] for p in options["priorities"]}
    # The chosen sets are sets of ids.
    assert all(isinstance(x, int) for x in options["chosen_goals"])


def test_link_edit_options_returns_deans_and_chosen(fresh_db):
    from app import queries

    iid = _initiative_id(fresh_db, "ELIZ-1")
    options = queries.link_edit_options(iid)

    assert set(options) == {"deans", "chosen"}
    assert options["deans"], "no Dean targets"
    assert all(d["Code"].startswith("D-") for d in options["deans"])


def test_the_six_pass_through_readers_are_gone():
    """They must not survive beside their replacements."""
    from app import queries

    for name in ("all_goals", "all_priorities", "active_dean_initiatives",
                 "current_goal_tags", "current_priority_tags", "current_links"):
        assert not hasattr(queries, name), (
            "%s still exists beside its screen-shaped replacement" % name
        )


def test_the_card_reads_tags_once(fresh_db):
    """The card's tags come from the card read, not a second reader.

    initiative_card already returns goal_tags and priority_tags; the edit
    screen's read returns the same underlying tables. There is no third path.
    """
    from app import queries

    card = queries.initiative_card("ELIZ-1")
    assert "goal_tags" in card and "priority_tags" in card


# --- no update is not zero --------------------------------------------------


def test_no_update_is_distinct_from_zero_percent(fresh_db):
    """The read reports that an update is absent, separately from its value.

    An initiative with no progress update must not render as "0%". HasUpdate is
    the flag the templates use to tell the two apart.
    """
    import sqlite3

    from app import queries

    iid = _initiative_id(fresh_db, "ELIZ-1")
    # Delete every update for this initiative, so it has none.
    conn = sqlite3.connect(fresh_db)
    try:
        conn.execute("DELETE FROM ProgressUpdates WHERE InitiativeID = ?", (iid,))
        conn.commit()
    finally:
        conn.close()

    owner_id = _person_id(fresh_db, "Elizabeth")
    card = queries.person_card(owner_id)
    row = next(r for r in card["initiatives"] if r["Code"] == "ELIZ-1")

    assert row["HasUpdate"] is False, "an initiative with no update should say so"
    assert row["NeedsUpdate"] is True


def test_zero_percent_with_an_update_is_present_not_missing(fresh_db):
    """A recorded 0% is present, and is not the same as no update at all."""
    import sqlite3

    from app import queries

    iid = _initiative_id(fresh_db, "ELIZ-1")
    conn = sqlite3.connect(fresh_db)
    try:
        conn.execute("DELETE FROM ProgressUpdates WHERE InitiativeID = ?", (iid,))
        conn.execute(
            "INSERT INTO ProgressUpdates (InitiativeID, PercentComplete, Status, Note, EnteredByID) "
            "VALUES (?, 0, 'Not started', 'just beginning', ?)",
            (iid, _person_id(fresh_db, "Elizabeth")),
        )
        conn.commit()
    finally:
        conn.close()

    card = queries.person_card(_person_id(fresh_db, "Elizabeth"))
    row = next(r for r in card["initiatives"] if r["Code"] == "ELIZ-1")
    assert row["HasUpdate"] is True, "a recorded 0% is still an update"
    # A freshly recorded update is not stale.
    assert row["NeedsUpdate"] is False


def _initiative_id(fresh_db, code):
    return _rows(fresh_db, "SELECT InitiativeID FROM Initiatives WHERE Code = ?",
                 (code,))[0]["InitiativeID"]


def _person_id(fresh_db, name):
    return _rows(fresh_db, "SELECT PersonID FROM People WHERE Name = ?", (name,))[0]["PersonID"]


def _rows(db, sql, params=()):
    import sqlite3

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()
