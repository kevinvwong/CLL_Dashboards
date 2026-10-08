"""The Milestones model, the outcome state, and dataset provenance.

These pin the model added 2026-10-07 (ADR-0001, ADR-0002): milestones hang off
Priorities, the outcome state lives on Priorities, and the dataset carries a
provenance marker so mock data can never read as confirmed (plan D5).
"""
import sqlite3


def _count(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchone()[0]
    finally:
        conn.close()


def test_the_view_returns_every_priority_even_with_no_milestones(fresh_db):
    """A priority with no milestones must still appear, reading 0 of 0."""
    conn = sqlite3.connect(fresh_db)
    try:
        rows = conn.execute(
            "SELECT PriorityCode, Planned, Reached FROM vw_PriorityMilestoneProgress "
            "ORDER BY PriorityCode").fetchall()
    finally:
        conn.close()
    assert [r[0] for r in rows] == ["P01", "P02", "P03", "P04", "P05", "P06"]
    assert all(r[2] <= r[1] for r in rows), "reached exceeds planned"


def test_the_seeded_milestones_match_the_wireframe_counts(fresh_db):
    """18 milestones, 3 per priority, and the reached counts the wireframe drew.
    Milestones join to Priorities by PriorityID (multi-year fix, 2026-10-08)."""
    assert _count(fresh_db, "SELECT COUNT(*) FROM Milestones") == 18
    per = dict(sqlite3.connect(fresh_db).execute(
        "SELECT p.Code, COUNT(*) FROM Milestones m JOIN Priorities p "
        "ON p.PriorityID = m.PriorityID GROUP BY p.Code"))
    assert per == {"P01": 3, "P02": 3, "P03": 3, "P04": 3, "P05": 3, "P06": 3}
    reached = dict(sqlite3.connect(fresh_db).execute(
        "SELECT PriorityCode, Reached FROM vw_PriorityMilestoneProgress"))
    assert reached == {"P01": 1, "P02": 2, "P03": 1, "P04": 0, "P05": 1, "P06": 1}


def test_milestone_status_vocabulary_is_the_event_set(fresh_db):
    """A milestone is Met/Missed/In progress/Not started - never 'On track'."""
    conn = sqlite3.connect(fresh_db)
    try:
        values = {r[0] for r in conn.execute("SELECT DISTINCT Status FROM Milestones")}
    finally:
        conn.close()
    assert values <= {"Met", "In progress", "Not started", "Missed"}
    assert "On track" not in values and "Complete" not in values


def test_the_priority_state_carries_the_reported_outcome(fresh_db):
    """Every priority reports an outcome state; P03/P04 are the at-risk ones."""
    rows = dict(sqlite3.connect(fresh_db).execute(
        "SELECT Code, Status FROM Priorities"))
    assert rows == {"P01": "On track", "P02": "On track", "P03": "At risk",
                    "P04": "At risk", "P05": "On track", "P06": "On track"}


def test_the_seed_marks_the_dataset_as_mock(fresh_db):
    """The seed is mock, and says so; the importer is what flips it."""
    assert _count(fresh_db, "SELECT COUNT(*) FROM AppMeta WHERE Key='dataset_provenance'") == 1
    val = sqlite3.connect(fresh_db).execute(
        "SELECT Value FROM AppMeta WHERE Key='dataset_provenance'").fetchone()[0]
    assert val == "mock"


def test_queries_read_the_model(fresh_db, monkeypatch):
    from app import queries
    monkeypatch.setenv("DB_PATH", str(fresh_db))
    assert queries.dataset_provenance() == "mock"
    outcomes = queries.priority_outcomes()
    assert [o["Code"] for o in outcomes] == ["P01", "P02", "P03", "P04", "P05", "P06"]
    p01 = outcomes[0]
    assert p01["Reached"] == 1 and p01["Planned"] == 3
    assert len(p01["milestones"]) == 3
    assert p01["milestones"][0]["Status"] == "Met"
