"""Multi-year: the six priorities recur, and every annual view is scoped to a year.

Covers the (PlanYear, Code) identity (2026-10-08): a 2028 'P01' is storable beside
the 2027 one, milestones belong to one year's priority row, and /outcomes is the
canonical page for the six, scoped to a plan year with a control that appears
only once a second year exists.
"""
import os
import sqlite3

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _add_2028(db):
    """A 2028 plan with the same P01 code and its own milestone."""
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO Priorities (PriorityName, PlanYear, Code, FullTitle) "
        "VALUES ('Identity', 2028, 'P01', 'One Shared Identity (2028)')")
    pid = conn.execute(
        "SELECT PriorityID FROM Priorities WHERE Code='P01' AND PlanYear=2028").fetchone()[0]
    conn.execute(
        "INSERT INTO Milestones (PriorityID, Name, Status, SortOrder) VALUES (?,?,?,1)",
        (pid, "A 2028 milestone", "Met"))
    conn.commit()
    conn.close()


def test_current_plan_year_comes_from_appmeta(fresh_db):
    from app import queries
    assert queries.current_plan_year() == 2027
    assert queries.plan_years() == [2027]


def test_outcomes_are_scoped_to_a_plan_year(fresh_db):
    from app import queries
    outcomes = queries.priority_outcomes(2027)
    assert [o["Code"] for o in outcomes] == ["P01", "P02", "P03", "P04", "P05", "P06"]
    assert all(o["PlanYear"] == 2027 for o in outcomes)
    # A year with no priorities returns nothing, not another year's rows.
    assert queries.priority_outcomes(2028) == []


def test_a_second_year_renders_with_its_own_milestones(fresh_db, logged_in):
    _add_2028(fresh_db)
    body = logged_in("Bill Gaudelli").get("/outcomes?year=2028").text
    assert "The six 2028 priorities" in body
    assert "A 2028 milestone" in body, "the 2028 milestone did not render"
    # And the default page is still the current year (2027).
    default = logged_in("Bill Gaudelli").get("/outcomes").text
    assert "The six 2027 priorities" in default
    assert "A 2028 milestone" not in default


def test_the_year_control_appears_only_with_more_than_one_year(fresh_db, logged_in):
    one = logged_in("Bill Gaudelli").get("/outcomes").text
    assert "year-control" not in one, "the year control showed with a single year"
    _add_2028(fresh_db)
    two = logged_in("Bill Gaudelli").get("/outcomes").text
    assert "year-control" in two, "the year control is missing with two years"
    assert "/outcomes?year=2028" in two


def test_priorities_index_folds_into_outcomes(logged_in):
    r = logged_in("Bill Gaudelli").get("/priorities", follow_redirects=False)
    assert r.status_code == 308
    assert r.headers["location"] == "/outcomes"


def test_a_milestone_cannot_attach_to_the_wrong_year(fresh_db):
    """A milestone joins by PriorityID, so it cannot land on another year's
    priority that shares a code."""
    from app import queries
    _add_2028(fresh_db)
    for o in queries.priority_outcomes(2028):
        if o["Code"] == "P01":
            assert [m["Name"] for m in o["milestones"]] == ["A 2028 milestone"]
    for o in queries.priority_outcomes(2027):
        if o["Code"] == "P01":
            assert "A 2028 milestone" not in [m["Name"] for m in o["milestones"]]
