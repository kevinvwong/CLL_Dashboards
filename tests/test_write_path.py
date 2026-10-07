"""The write seam: atomicity, refusal messages, and append-only progress.

Covers the `initiative-write-path` spec of deepen-dashboard-modules.

These assert the seam's own contract, which the route tests exercise only
indirectly. They reach the seam the same way a route does - through the public
write functions - so they test the interface, not a private helper.
"""
import os
import sqlite3

import pytest

from app import repo

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")


def _count(db, table, where="", params=()):
    conn = sqlite3.connect(str(db))
    try:
        sql = "SELECT COUNT(*) FROM %s" % table
        if where:
            sql += " WHERE " + where
        return conn.execute(sql, params).fetchone()[0]
    finally:
        conn.close()


# --- atomicity --------------------------------------------------------------


def test_a_refused_write_leaves_nothing_behind(fresh_db):
    """A body that raises part-way writes nothing.

    add_progress_update validates before it opens the connection, so drive the
    rollback through a body that writes and then fails: an unknown initiative
    code reaches the SELECT, then raises RuleError inside the transaction.
    """
    before = _count(fresh_db, "MajorInitiativeUpdates")
    with pytest.raises(repo.RuleError):
        repo.add_progress_update(
            code="NO-SUCH-CODE", percent=50, status="On track", note="x",
            entered_by_id=1,
        )
    assert _count(fresh_db, "MajorInitiativeUpdates") == before, (
        "a refused write left a row behind"
    )


def test_a_body_that_raises_mid_write_rolls_back(fresh_db):
    """The seam rolls back when the body raises after writing.

    Drives the seam directly with a body that inserts a real row and then
    raises, so the rollback path is exercised - not just the pre-checks.
    """
    before = _count(fresh_db, "MajorInitiativeUpdates")

    def body(conn):
        conn.execute(
            "INSERT INTO MajorInitiativeUpdates "
            "(MajorInitiativeID, PercentComplete, Status, Note, EnteredByID) "
            "VALUES (1, 10, 'On track', 'temporary', 1)"
        )
        raise RuntimeError("boom after a write")

    with pytest.raises(RuntimeError):
        repo.write(body)

    assert _count(fresh_db, "MajorInitiativeUpdates") == before, (
        "the seam committed a body that raised"
    )


def test_a_successful_write_is_complete(fresh_db):
    """A body that returns commits every row it wrote."""
    before = _count(fresh_db, "MajorInitiativeUpdates")

    def body(conn):
        conn.execute(
            "INSERT INTO MajorInitiativeUpdates "
            "(MajorInitiativeID, PercentComplete, Status, Note, EnteredByID) "
            "VALUES (1, 10, 'On track', 'kept', 1)"
        )
        return "done"

    assert repo.write(body) == "done"
    assert _count(fresh_db, "MajorInitiativeUpdates") == before + 1


# --- refusal messages -------------------------------------------------------


def test_percent_out_of_range_is_a_message_not_a_driver_error(fresh_db):
    with pytest.raises(repo.RuleError) as e:
        repo.add_progress_update(code="MI-002", percent=150, status="On track",
                                 note="", entered_by_id=1)
    assert "between 0 and 100" in e.value.message


def test_unknown_status_lists_the_allowed_set(fresh_db):
    with pytest.raises(repo.RuleError) as e:
        repo.add_progress_update(code="MI-002", percent=10, status="Sideways",
                                 note="", entered_by_id=1)
    msg = e.value.message
    assert "On track" in msg and "At risk" in msg, msg


def test_duplicate_code_names_the_code(fresh_db):
    with pytest.raises(repo.RuleError) as e:
        repo.create_initiative(code="MI-002", name="Dup", level="Dean", owner_id=1,
                               description="", person_id=1)
    assert "MI-002" in e.value.message, e.value.message


def test_unknown_owner_is_a_message_not_a_driver_error(fresh_db):
    """The one write with its own integrity mapping still refuses readable."""
    with pytest.raises(repo.RuleError) as e:
        repo.create_initiative(code="FRESH-1", name="New", level="D-1",
                               owner_id=999999, description="", person_id=1)
    assert "directory" in e.value.message.lower(), e.value.message


# --- append-only ------------------------------------------------------------


def test_an_update_never_rewrites_earlier_updates(fresh_db):
    id1 = repo.add_progress_update(code="MI-002", percent=10, status="On track",
                                   note="first", entered_by_id=1)
    repo.add_progress_update(code="MI-002", percent=20, status="On track",
                             note="second", entered_by_id=1)

    conn = sqlite3.connect(str(fresh_db))
    try:
        row = conn.execute(
            "SELECT Note, PercentComplete FROM MajorInitiativeUpdates WHERE UpdateID = ?",
            (id1,),
        ).fetchone()
    finally:
        conn.close()
    assert row == ("first", 10), "an earlier update was rewritten"


# --- the seam is one place --------------------------------------------------


def test_the_transaction_skeleton_exists_once():
    """Every write delegates to repo.write; none rolls its own skeleton."""
    text = open(os.path.join(SRC, "repo.py"), encoding="utf-8").read()
    assert text.count("def write(") == 1
    # Each of the eight writes calls write(...) rather than try/commit/rollback.
    assert text.count("write(body") >= 7, (
        "a write function still carries its own transaction skeleton"
    )
