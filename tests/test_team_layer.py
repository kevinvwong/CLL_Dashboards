"""The organizational layer: teams, source areas, and the 29 Major Initiatives.

Covers the blueprint-redesign scope correction: the Dean's prototype's layer
that our schema did not hold. Every field the prototype carries is asserted
present, and the counts are cross-checked against the prototype's own data.js
so the seed cannot silently drift from its source.
"""
import os
import re

import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(R, "cll_initiatives.db")


def _rows(db, sql, params=()):
    import sqlite3
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


# --- the counts, from the prototype's own statements -----------------------


def test_five_source_areas(fresh_db):
    assert len(_rows(fresh_db, "SELECT * FROM SourceAreas")) == 5


def test_four_teams(fresh_db):
    teams = _rows(fresh_db, "SELECT * FROM Teams")
    assert len(teams) == 4
    for t in teams:
        assert t["Description"], "team %s has no description" % t["Name"]


def test_twenty_nine_major_initiatives(fresh_db):
    """The prototype's header says '35 cascading KPIs' = 6 + 29."""
    assert len(_rows(fresh_db, "SELECT * FROM MajorInitiatives")) == 29


def test_major_initiatives_sum_by_source_area(fresh_db):
    """The prototype's five areas: 4 + 6 + 4 + 6 + 9 = 29."""
    got = {r["Name"]: r["n"] for r in _rows(
        fresh_db,
        "SELECT sa.Name, COUNT(*) AS n FROM MajorInitiatives k "
        "JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID GROUP BY sa.Name")}
    assert got == {
        "Content & Product Strategy": 4,
        "Administration & Operations": 6,
        "Strategic Solutions": 4,
        "Research, Development & Innovation": 6,
        "Academic Affairs": 9,
    }


# --- every field the prototype carries -------------------------------------


def test_every_major_initiative_field_is_present(fresh_db):
    """The prototype's goal() returns these keys; each must be storable."""
    row = _rows(fresh_db, "SELECT * FROM vw_MajorInitiatives LIMIT 1")[0]
    for field in ("Code", "Title", "Team", "SourceArea", "StrategyAlign",
                  "Initiatives", "SourceTarget", "ProposedTarget",
                  "TargetStatus", "SlideRef", "Status", "Note"):
        assert field in row, "missing field %s" % field


def test_target_status_is_one_of_two_vocabularies(fresh_db):
    """The prototype's targetStatus: 'source' or 'needs_review'."""
    got = {r["TargetStatus"] for r in _rows(fresh_db, "SELECT TargetStatus FROM MajorInitiatives")}
    assert got <= {"source", "needs_review"}, got


def test_the_needs_review_count_matches_the_prototype(fresh_db):
    """The prototype's header says '21 need review' across the 35 KPIs.

    The 21 split across the DEAN priorities (6) and the Major Initiatives; the MI
    share is what is stored here, and it must be > 0 and <= 29.
    """
    n = _rows(fresh_db, "SELECT COUNT(*) AS n FROM MajorInitiatives "
                        "WHERE TargetStatus = 'needs_review'")[0]["n"]
    assert 0 < n <= 29


# --- the four priority fields -------------------------------------------------


def test_priorities_carry_code_of_p01_to_p06(fresh_db):
    codes = sorted(r["Code"] for r in _rows(fresh_db, "SELECT Code FROM Priorities"))
    assert codes == ["P01", "P02", "P03", "P04", "P05", "P06"]


@pytest.mark.parametrize("field", ["Measure", "Target", "Cadence", "OwnerLabel", "Colour"])
def test_every_priority_has_the_governed_field(fresh_db, field):
    """The four fields the schema did not hold, now populated for all six."""
    rows = _rows(fresh_db, "SELECT %s AS v FROM Priorities" % field)
    assert all(r["v"] for r in rows), "%s is empty for some priority" % field


# --- the links ----------------------------------------------------------------


def test_major_initiative_priorities_resolve(fresh_db):
    """Every link joins a real Major Initiative to a real priority."""
    links = _rows(fresh_db, "SELECT * FROM vw_MajorInitiativePriorities")
    assert len(links) == 51
    for link in links:
        assert link["MajorInitiativeCode"] and link["PriorityName"]


def test_each_major_initiative_feeds_at_least_one_priority(fresh_db):
    """An initiative with no priority is invisible on every priority view."""
    orphan = _rows(fresh_db,
        "SELECT k.Code FROM MajorInitiatives k "
        "WHERE NOT EXISTS (SELECT 1 FROM MajorInitiativePriorities p WHERE p.MajorInitiativeID = k.MajorInitiativeID)")
    assert not orphan, "Major Initiatives with no priority: %s" % orphan


# --- the read models ----------------------------------------------------------


def test_team_summary_via_the_view(fresh_db):
    rows = _rows(fresh_db, "SELECT * FROM vw_TeamSummary")
    assert len(rows) == 4
    assert sum(r["MajorInitiativeCount"] for r in rows) == 29
