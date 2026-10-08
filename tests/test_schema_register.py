"""The Dean Initiatives layer and the columns the register needs.

Loads schema.sql into a throwaway in-memory database, so the test describes the
schema itself and not the state of any built db.
"""
import os
import sqlite3

import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(R, "db", "schema.sql")


def _schema_con():
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(open(SCHEMA, encoding="utf-8").read())
    return con


def test_dean_tables_and_columns_exist():
    con = _schema_con()
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "DeanInitiatives" in tables
    assert "TeamInitiativeDeanLinks" in tables

    mi_cols = {d[1] for d in con.execute("PRAGMA table_info(TeamInitiatives)")}
    assert {"Description", "OwnerID"} <= mi_cols

    mip_cols = {d[1] for d in con.execute(
        "PRAGMA table_info(TeamInitiativePriorities)")}
    assert "IsPrimary" in mip_cols

    people_cols = {d[1] for d in con.execute("PRAGMA table_info(People)")}
    assert "TeamID" in people_cols
    con.close()


def test_one_primary_priority_per_mi():
    con = _schema_con()
    idx = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='index'")}
    assert "UX_MIP_OnePrimary" in idx
    con.close()


def test_auditlog_indexes_exist():
    con = _schema_con()
    idx = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='AuditLog'")}
    assert {"IX_AuditLog_CreatedAt", "IX_AuditLog_Entity"} <= idx
    con.close()


def test_fiscal_year_check():
    """A 2-digit fiscal year; the range is open so later years are storable
    (multi-year fix, 2026-10-08). FY26 works and FY28 works; 99 is out of range."""
    con = _schema_con()
    con.execute("INSERT INTO DeanInitiatives (FiscalYear, Code, Title) VALUES (26,'D26-1','x')")
    con.execute("INSERT INTO DeanInitiatives (FiscalYear, Code, Title) VALUES (28,'D28-1','x')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO DeanInitiatives (FiscalYear, Code, Title) VALUES (12,'D12-1','x')")
    con.close()


def test_a_priority_code_recurs_across_plan_years():
    """Priorities are keyed by (PlanYear, Code): a 2028 'P01' is storable beside
    the 2027 one (multi-year fix, 2026-10-08)."""
    con = _schema_con()
    con.execute("INSERT INTO Priorities (PriorityName, PlanYear, Code) VALUES ('Identity',2027,'P01')")
    con.execute("INSERT INTO Priorities (PriorityName, PlanYear, Code) VALUES ('Identity',2028,'P01')")
    # But the same (year, code) twice is refused.
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO Priorities (PriorityName, PlanYear, Code) VALUES ('X',2027,'P01')")
    con.close()


def test_dean_views_exist():
    con = _schema_con()
    views = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%Dean%'")}
    assert {"vw_DeanInitiatives", "vw_TeamInitiativeDeanLinks"} <= views
    con.close()
