"""Task 8.9 (import half) and task 8.7: the intake workbook round trip.

The data-intake spec requires an all-or-nothing import, upsert by Code,
retire-not-delete for missing initiatives, progress preserved after a
re-import, and a report naming the sheet row.
"""

import os
import shutil
import sqlite3
import sys

import pytest
from openpyxl import load_workbook

SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )))),
    "scripts",
)
sys.path.insert(0, SCRIPTS)

import import_xlsx  # noqa: E402
import make_template  # noqa: E402


def _counts(db):
    conn = sqlite3.connect(db)
    out = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("Initiatives", "ProgressUpdates", "InitiativeGoals", "InitiativeLinks")
    }
    out["active"] = conn.execute("SELECT COUNT(*) FROM Initiatives WHERE IsActive = 1").fetchone()[0]
    conn.close()
    return out


def _diary(db, code):
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT pu.PercentComplete, pu.Status, pu.Note FROM ProgressUpdates pu "
        "JOIN Initiatives i ON i.InitiativeID = pu.InitiativeID WHERE i.Code = ? "
        "ORDER BY pu.UpdateDate, pu.UpdateID",
        (code,),
    ).fetchall()
    conn.close()
    return rows


# --- 8.7 template ---------------------------------------------------------


def test_template_has_the_four_sheets(logged_in, fresh_db, tmp_path):
    out = tmp_path / "intake.xlsx"
    path, n_goals, n_priors, n_people = make_template.build(fresh_db, str(out))
    assert os.path.exists(path)
    wb = load_workbook(path)
    assert set(wb.sheetnames) == {"Initiatives", "Goals", "Priorities", "People"}
    assert (n_goals, n_priors) == (5, 6)


def test_initiatives_sheet_has_x_columns_for_every_goal_and_priority(logged_in, fresh_db, tmp_path):
    out = tmp_path / "intake.xlsx"
    path, _, _, _ = make_template.build(fresh_db, str(out))
    header = [str(c.value or "") for c in load_workbook(path)["Initiatives"][1]]
    goal_cols = [h for h in header if h.startswith("Goal:")]
    priority_cols = [h for h in header if h.startswith("Priority:")]
    assert len(goal_cols) == 5
    assert len(priority_cols) == 6
    assert "Code" in header and "Name" in header and "Level" in header and "Owner" in header


def test_template_round_trips_without_errors(logged_in, fresh_db, tmp_path):
    """A freshly generated template must import cleanly against its own database."""
    out = tmp_path / "intake.xlsx"
    make_template.build(fresh_db, str(out))
    # Drop the initiative rows; the workbook is headers-only by design.
    wb = load_workbook(out)
    ws = wb["Initiatives"]
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    wb.save(out)

    backup = tmp_path / "before.db"
    shutil.copy2(fresh_db, backup)
    ok, problems = import_xlsx.import_workbook(fresh_db, str(out))
    assert ok, [str(p) for p in problems]


# --- 8.8 clean import -----------------------------------------------------


def _filled_workbook(fresh_db, tmp_path, rows):
    """Build a workbook from the template and fill the Initiatives rows."""
    out = tmp_path / "filled.xlsx"
    make_template.build(fresh_db, str(out))
    wb = load_workbook(out)
    ws = wb["Initiatives"]
    for values in rows:
        ws.append(values)
    wb.save(out)
    return str(out)


def _row(code, name, level, owner, goals=(), priorities=(), feeds="", percent="", status=""):
    # header: Code, Name, Description, Level, Owner, Feeds, Percent, Status,
    #         then 5 goal X columns, then 6 priority X columns
    row = [code, name, f"{name} description", level, owner, feeds, percent, status]
    row += ["X" if g in goals else "" for g in ("1 Academic", "2 Extension", "3 Research",
                                                "4 Learner impact", "5 Operational")]
    row += ["X" if p in priorities else "" for p in ("Culture", "Data", "Identity",
                                                    "Innovation", "Pathways", "Scale")]
    return row


def test_clean_import_succeeds_and_swaps(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
        _row("ELIZ-1", "Elizabeth one", "D-1", "Elizabeth",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D-A"),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]
    conn = sqlite3.connect(fresh_db)
    assert conn.execute("SELECT InitiativeName FROM Initiatives WHERE Code='ELIZ-1'").fetchone()[0] \
        == "Elizabeth one"
    conn.close()


def test_new_initiative_from_the_workbook(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("ELIZ-9", "Brand new", "D-1", "Elizabeth",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D-A",
             percent="10", status="On track"),
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
    ])
    before = _counts(fresh_db)["Initiatives"]
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]
    assert _counts(fresh_db)["Initiatives"] == before + 1


# --- 8.8 diary preserved after re-import ----------------------------------


def test_diary_survives_a_re_import(logged_in, fresh_db, tmp_path):
    """The data-intake spec: every initiative that kept its code still shows
    its full diary."""
    diary_before = _diary(fresh_db, "ELIZ-1")
    assert diary_before

    path = _filled_workbook(fresh_db, tmp_path, [
        _row("ELIZ-1", "Renamed but same code", "D-1", "Elizabeth",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D-A"),
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]
    assert _diary(fresh_db, "ELIZ-1") == diary_before


# --- 8.8 retire missing, never delete -------------------------------------


def test_missing_initiatives_are_retired_not_deleted(logged_in, fresh_db, tmp_path):
    before = _counts(fresh_db)
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]

    after = _counts(fresh_db)
    assert after["Initiatives"] == before["Initiatives"], "rows are retired, never deleted"
    assert after["active"] < before["active"]
    conn = sqlite3.connect(fresh_db)
    assert conn.execute("SELECT IsActive FROM Initiatives WHERE Code='ELIZ-1'").fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM ProgressUpdates WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1')"
    ).fetchone()[0] > 0, "a retired initiative keeps its history"
    conn.close()


# --- 8.8 all-or-nothing ----------------------------------------------------


def test_a_failing_import_changes_nothing(logged_in, fresh_db, tmp_path):
    before = _counts(fresh_db)
    diary_before = _diary(fresh_db, "ELIZ-1")

    path = _filled_workbook(fresh_db, tmp_path, [
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
        _row("ELIZ-1", "Fine row", "D-1", "Elizabeth",
             goals=("3 Research",), priorities=("Data", "Innovation")),
        _row("BAD-1", "Broken", "Sideways", "Nobody", goals=("3 Research",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok is False
    assert problems, "a failing import must report at least one problem"
    assert _counts(fresh_db) == before, "the live database must be untouched"
    assert _diary(fresh_db, "ELIZ-1") == diary_before


def test_failure_names_the_sheet_row(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
        _row("BAD-1", "Broken", "Sideways", "Nobody", goals=("3 Research",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok is False
    text = " | ".join(str(p) for p in problems)
    assert "Initiatives" in text
    assert "BAD-1" in text
    assert "Dean or D-1" in text


def test_unknown_owner_is_reported(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
        _row("NEW-1", "New", "D-1", "Someone Not Here", goals=("3 Research",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok is False
    assert "Someone Not Here" in " | ".join(str(p) for p in problems)


def test_dry_run_reports_clean_without_swapping(logged_in, fresh_db, tmp_path):
    before = _counts(fresh_db)
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("D-A", "Dean A", "Dean", "Bill", goals=("3 Research",), priorities=("Data",)),
        _row("ELIZ-1", "Elizabeth one", "D-1", "Elizabeth",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D-A"),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path, dry_run=True)
    assert ok, [str(p) for p in problems]
    assert _counts(fresh_db) == before, "a dry run must not modify the database"


def test_workbook_without_an_initiatives_sheet_is_refused(logged_in, fresh_db, tmp_path):
    from openpyxl import Workbook

    out = tmp_path / "empty.xlsx"
    wb = Workbook()
    wb.active.title = "Goals"
    wb.save(out)
    ok, problems = import_xlsx.import_workbook(fresh_db, str(out))
    assert ok is False
    assert "Initiatives" in str(problems[0])