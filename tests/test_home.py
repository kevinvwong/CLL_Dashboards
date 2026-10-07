"""Task 3.4 check: the home screen.

The strategy-navigation spec requires 5 goal tiles and 6 priority tiles, each
carrying an initiative count.

Re-pointed at the importing form (task 6.3). This file used to hold a
hand-maintained snapshot of the counts, and that snapshot once pinned the
TRANSPOSED goal numbering - it agreed with the wrong data and had to be edited
by hand when the goals were corrected. The expectation is now derived from the
raw tables by a counting query, and compared to the view the tiles read, so:

  * a broken JOIN in the view fails the test (the view count and the raw count
    disagree) - which is the bug the snapshot was there to catch; and
  * a change to the sample data does NOT require editing this file.

The deliberate consequence, recorded because it changes the task's literal
verify wording: a pure seed change no longer fails this test on its own, because
the expectation is derived rather than pinned. That is the point - pinned
expectations are what drifted.
"""
import sqlite3

GOAL_COUNT = 5
PRIORITY_COUNT = 6


def _raw_goal_counts(fresh_db):
    """Distinct active initiatives per goal, counted from the raw tables.

    Independent of vw_GoalInitiatives, so it can disagree with it - which is what
    makes it a check of the view rather than a copy of it.
    """
    conn = sqlite3.connect(fresh_db)
    try:
        rows = conn.execute(
            """
            SELECT g.GoalNumber, COUNT(DISTINCT i.MajorInitiativeID) AS n
            FROM Goals g
            LEFT JOIN MajorInitiativeGoals ig ON ig.GoalID = g.GoalID
            LEFT JOIN MajorInitiatives i
                   ON i.MajorInitiativeID = ig.MajorInitiativeID AND i.IsActive = 1
            GROUP BY g.GoalID, g.GoalNumber
            """
        ).fetchall()
    finally:
        conn.close()
    return {r[0]: r[1] for r in rows}


def _raw_priority_counts(fresh_db):
    conn = sqlite3.connect(fresh_db)
    try:
        rows = conn.execute(
            """
            SELECT p.PriorityName, COUNT(DISTINCT i.MajorInitiativeID) AS n
            FROM Priorities p
            LEFT JOIN MajorInitiativePriorities ip ON ip.PriorityID = p.PriorityID
            LEFT JOIN MajorInitiatives i
                   ON i.MajorInitiativeID = ip.MajorInitiativeID AND i.IsActive = 1
            GROUP BY p.PriorityID, p.PriorityName
            """
        ).fetchall()
    finally:
        conn.close()
    return {r[0]: r[1] for r in rows}


def test_home_shows_the_dashboard_and_keeps_everything_reachable(logged_in):
    """The home is a portfolio dashboard (scope correction), not a tile grid or
    the prototype's stage. The goals, priorities and initiatives stay reachable.

    Replaces the earlier stage assertion: the stage was removed by direction.
    """
    from app import queries

    response = logged_in("Bill Gaudelli").get("/")
    assert response.status_code == 200

    goals = queries.goal_tiles()
    priorities = queries.priority_tiles()
    assert len(goals) == GOAL_COUNT
    assert len(priorities) == PRIORITY_COUNT

    body = response.text
    # The dashboard's parts, not the prototype's stage.
    assert "stat-band" in body
    assert "priority-grid" in body
    assert "dean-node" not in body, "the prototype's stage still renders"
    # Every priority is reachable from its card.
    for priority in priorities:
        assert f"/priorities/{priority['PriorityName']}" in body or \
               priority["PriorityName"] in body
    # The goals are reachable from the dashboard's tables and nav.
    assert "/major-initiatives" in body


def test_goal_tile_counts_match_an_independent_count(logged_in, fresh_db):
    """The view's counts equal a counting query over the raw tables."""
    from app import queries

    got = {g["GoalNumber"]: g["InitiativeCount"] for g in queries.goal_tiles()}
    assert got == _raw_goal_counts(fresh_db)


def test_priority_tile_counts_match_an_independent_count(logged_in, fresh_db):
    from app import queries

    got = {p["PriorityName"]: p["InitiativeCount"] for p in queries.priority_tiles()}
    assert got == _raw_priority_counts(fresh_db)


def test_goal_names_come_from_the_canonical_list(logged_in):
    """The tile names are the canonical goals, not a snapshot in the test.

    Imports the generated canonical source the same way test_goal_correctness
    does, so a goal rename flows through rather than needing a second edit here.
    """
    import os
    import sys

    from app import queries

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
    from canonical_goals import GOALS  # noqa: E402

    by_number = {n: short for n, short, _title in GOALS}
    got = {g["GoalNumber"]: g["ShortName"] for g in queries.goal_tiles()}
    assert got == by_number


def test_a_priority_and_its_count_appear_in_the_rendered_page(logged_in, fresh_db):
    """A priority name and its initiative count render together (scope
    correction: the tiles became full-field cards, so this checks the card)."""
    from app import queries

    body = logged_in("Bill Gaudelli").get("/").text
    p = queries.blueprint_priorities()[0]
    assert p["Title"] in body
    assert f">{p['InitiativeCount']}<" in body or \
           f"{p['InitiativeCount']} initiative" in body


def test_home_requires_a_signed_in_person(anon):
    """The gate still applies to the home screen."""
    response = anon.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_nav_and_print_assets_are_present(logged_in):
    """The primary nav (blueprint-redesign 5.1) plus print and dialog assets.

    Checks is now an ADMIN entry, not primary nav (5.4), and Bill Gaudelli is not an
    admin - so the primary destinations are asserted here and the admin entry
    is asserted in the coverage-checks test.
    """
    body = logged_in("Bill Gaudelli").get("/").text
    for dest in ("/", "/major-initiatives", "/people", "/outcomes"):
        assert ('href="%s"' % dest) in body, "missing nav destination %s" % dest
    assert 'media="print"' in body
    assert "<dialog" in body
