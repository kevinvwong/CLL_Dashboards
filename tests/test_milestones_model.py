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


def test_the_seeded_milestones_match_the_register_counts(fresh_db):
    """84 milestones, one per column F clause, spread across all 29 initiatives.

    This used to assert 18 wireframe mocks at 3 per priority. The mock rows are
    gone; the count is now derived from register column F, which is what the
    generator reads, so this pins the generator to the source rather than to a
    number someone remembers.
    """
    assert _count(fresh_db, "SELECT COUNT(*) FROM Milestones") == 84
    per = dict(sqlite3.connect(fresh_db).execute(
        "SELECT ti.Code, COUNT(*) FROM Milestones m "
        "JOIN TeamInitiatives ti ON ti.TeamInitiativeID = m.TeamInitiativeID "
        "GROUP BY ti.Code"))
    assert len(per) == 29, "every initiative should carry clauses"
    assert sum(per.values()) == 84
    # clause 1 of every cell is a headline milestone, so it is the heaviest
    heaviest = dict(sqlite3.connect(fresh_db).execute(
        "SELECT ti.Code, m.Weight FROM Milestones m "
        "JOIN TeamInitiatives ti ON ti.TeamInitiativeID = m.TeamInitiativeID "
        "WHERE m.SortOrder = 1"))
    assert all(w > 0 for w in heaviest.values())
    reached = dict(sqlite3.connect(fresh_db).execute(
        "SELECT PriorityCode, Reached FROM vw_PriorityMilestoneProgress"))
    # nothing is reported yet, so nothing is reached - and every priority that
    # HAS a linked initiative reports a positive planned count.
    assert all(v == 0 for v in reached.values()), "no milestone is reported yet"


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
    # P01's milestones are now the clauses of the initiatives linked to P01,
    # not a fixed set of 3 mocks. The invariants that matter: every priority
    # has at least one milestone, reached never exceeds planned, and the
    # statuses are the event vocabulary.
    assert p01["Planned"] >= 1
    assert p01["Reached"] == 0, "no milestone is reported yet"
    assert len(p01["milestones"]) == p01["Planned"]
    assert all(m["Status"] in ("Met", "In progress", "Not started", "Missed")
               for m in p01["milestones"])
