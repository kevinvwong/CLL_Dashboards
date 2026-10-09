"""Every annual priority page renders from the SHIPPED database.

Found 2026-10-08: the committed cll_initiatives.db is a build artefact of the
schema + seeds, and it was NOT regenerated when the schema gained the multi-year
view. The deployed app read v.PriorityID from a database that only had
PriorityCode and 500'd on every signed-in page. Rebuilding from schema+seeds
(the way test_deploy_rebuild does) did NOT catch it, because those tests never
look at the committed file the archive actually ships.

These tests open the committed database and assert it matches the schema the app
reads, so a schema change without a rebuild fails here rather than in production.
"""
import os
import sqlite3

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(APP, "cll_initiatives.db")


def test_the_committed_db_view_matches_the_app():
    """The shipped db's progress view carries the columns queries.priority_outcomes
    selects (PriorityID, PlanYear)."""
    conn = sqlite3.connect(DB)
    try:
        cols = [d[1] for d in conn.execute(
            "PRAGMA table_info(vw_PriorityMilestoneProgress)")]
    finally:
        conn.close()
    assert "PriorityID" in cols, (
        "the committed db has a stale view (no PriorityID); rebuild it: "
        "python db/build_db.py")
    assert "PlanYear" in cols, "the committed db's view is not year-scoped"


def test_the_committed_db_carries_the_current_plan_year():
    conn = sqlite3.connect(DB)
    try:
        row = conn.execute(
            "SELECT Value FROM AppMeta WHERE Key='current_plan_year'").fetchone()
    finally:
        conn.close()
    assert row is not None, "AppMeta.current_plan_year is missing; rebuild the db"
    assert int(row[0]) == 2027


def test_the_committed_db_milestones_attach_to_the_initiative():
    """Milestones join by TeamInitiativeID, not the reused code.

    They used to join by PriorityID, which put them one level too high in the
    cascade: column F of the register lives on the register ROW, i.e. on the Team
    Initiative, and six of the seeded milestones traced by name to one of its
    clauses while rendering under a Dean priority.
    """
    conn = sqlite3.connect(DB)
    try:
        cols = [d[1] for d in conn.execute("PRAGMA table_info(Milestones)")]
        orphan = conn.execute(
            "SELECT COUNT(*) FROM Milestones m WHERE NOT EXISTS ("
            "  SELECT 1 FROM TeamInitiatives t WHERE t.TeamInitiativeID = m.TeamInitiativeID)"
        ).fetchone()[0]
        n = conn.execute("SELECT COUNT(*) FROM Milestones").fetchone()[0]
    finally:
        conn.close()
    assert "TeamInitiativeID" in cols
    assert "PriorityID" not in cols, "the milestones still key on the priority"
    assert "PriorityCode" not in cols, "the milestones still key on the reused code"
    assert orphan == 0
    # 84 real clauses, not the 18 mock rows this used to assert.
    assert n == 84


def test_a_signed_in_priority_page_renders_against_the_committed_db(logged_in):
    """The end-to-end guard: the page that 500'd now renders."""
    assert logged_in("Bill Gaudelli").get("/outcomes").status_code == 200
