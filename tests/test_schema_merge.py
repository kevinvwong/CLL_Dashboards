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
    assert "MajorInitiativeUpdates" in t
    con.close()


def test_prototype_tables_are_gone():
    con = _con()
    t = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for gone in ("Initiatives", "InitiativeGoals", "InitiativePriorities",
                 "InitiativeLinks", "ProgressUpdates"):
        assert gone not in t, gone
    con.close()


def test_major_initiatives_has_isactive():
    con = _con()
    cols = {d[1] for d in con.execute("PRAGMA table_info(MajorInitiatives)")}
    assert "IsActive" in cols
    con.close()


def test_diary_status_check():
    con = _con()
    con.execute("INSERT INTO MajorInitiatives (Code, Title) VALUES ('x','t')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO MajorInitiativeUpdates (MajorInitiativeID, PercentComplete, Status) "
            "VALUES (1, 10, 'Nonsense')")
    con.close()


def test_latest_progress_view_exists():
    con = _con()
    v = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='view'")}
    assert "vw_LatestMajorInitiativeProgress" in v
    con.close()
