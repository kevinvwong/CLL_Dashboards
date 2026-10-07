"""The merged model: the diary exists, the prototype tables are gone."""
import os
import sqlite3

import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(R, "db", "schema.sql")


def _con():
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(open(SCHEMA, encoding="utf-8").read())
    return con


def test_diary_table_exists():
    con = _con()
    t = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "TeamInitiativeUpdates" in t
    con.close()


def test_prototype_tables_are_gone():
    """The five prototype tables are dropped; only the register model survives.

    The names are written as joins so a well-meaning rename pass cannot rewrite
    them out of this guard.
    """
    con = _con()
    t = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    dropped = ["Initia" + "tives", "Initia" + "tiveGoals",
               "Initia" + "tivePriorities", "Initia" + "tiveLinks",
               "Progress" + "Updates"]
    for gone in dropped:
        assert gone not in t, gone
    con.close()


def test_team_initiatives_has_isactive():
    con = _con()
    cols = {d[1] for d in con.execute("PRAGMA table_info(TeamInitiatives)")}
    assert "IsActive" in cols
    con.close()


def test_diary_status_check():
    con = _con()
    con.execute("INSERT INTO TeamInitiatives (Code, Title) VALUES ('x','t')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO TeamInitiativeUpdates (TeamInitiativeID, PercentComplete, Status) "
            "VALUES (1, 10, 'Nonsense')")
    con.close()


def test_latest_progress_view_exists():
    con = _con()
    v = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='view'")}
    assert "vw_LatestTeamInitiativeProgress" in v
    con.close()
