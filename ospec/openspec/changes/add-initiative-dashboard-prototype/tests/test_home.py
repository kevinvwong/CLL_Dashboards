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
            SELECT g.GoalNumber, COUNT(DISTINCT i.InitiativeID) AS n
            FROM Goals g
            LEFT JOIN InitiativeGoals ig ON ig.GoalID = g.GoalID
            LEFT JOIN Initiatives i
                   ON i.InitiativeID = ig.InitiativeID AND i.IsActive = 1
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
            SELECT p.PriorityName, COUNT(DISTINCT i.InitiativeID) AS n
            FROM Priorities p
            LEFT JOIN InitiativePriorities ip ON ip.PriorityID = p.PriorityID
            LEFT JOIN Initiatives i
                   ON i.InitiativeID = ip.InitiativeID AND i.IsActive = 1
            GROUP BY p.PriorityID, p.PriorityName
            """
        ).fetchall()
    finally:
        conn.close()
    return {r[0]: r[1] for r in rows}


def test_home_shows_the_stage_with_goals_and_priorities(logged_in):
    """Replaces the tile-grid assertion (blueprint-redesign group 2).

    The home is now a hero stage, not a tile grid: the Dean node, the six
    priority cards, and the goals panel. The goals and priorities are still
    each reachable, which is what this checked.
    """
    from app import queries

    response = logged_in("Bill").get("/")
    assert response.status_code == 200

    goals = queries.goal_tiles()
    priorities = queries.priority_tiles()
    assert len(goals) == GOAL_COUNT
    assert len(priorities) == PRIORITY_COUNT

    body = response.text
    # The stage and its node.
    assert "stage" in body and "dean-node" in body
    # Six priority cards, each linking to its panel selection.
    for priority in priorities:
        assert f"/?priority={priority['PriorityName']}" in body
    # The goals panel keeps every goal reachable.
    for goal in goals:
        assert f"/goals/{goal['GoalNumber']}" in body
    # And the full cascade for the selected priority stays one link away.
    assert "/priorities/" in body


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

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                    "..", "db"))
    from canonical_goals import GOALS  # noqa: E402

    by_number = {n: short for n, short, _title in GOALS}
    got = {g["GoalNumber"]: g["ShortName"] for g in queries.goal_tiles()}
    assert got == by_number


def test_tile_counts_appear_in_the_rendered_page(logged_in, fresh_db):
    body = logged_in("Bill").get("/").text
    # A goal name and its count appear together in the markup.
    from app import queries

    a_goal = queries.goal_tiles()[0]
    assert a_goal["ShortName"] in body
    assert f">{a_goal['InitiativeCount']}<" in body


def test_home_requires_a_signed_in_person(anon):
    """The gate still applies to the home screen."""
    response = anon.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_nav_and_print_assets_are_present(logged_in):
    body = logged_in("Bill").get("/").text
    assert 'href="/meeting"' in body
    assert 'href="/checks"' in body
    assert 'media="print"' in body
    assert "<dialog" in body
