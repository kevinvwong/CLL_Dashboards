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
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
)
sys.path.insert(0, SCRIPTS)

import import_xlsx  # noqa: E402
import make_template  # noqa: E402
from app import queries  # noqa: E402


def _goal_header(short_name: str) -> str:
    """The goal column header, built the way make_template builds it.

    These fixtures previously hardcoded "Goal: 3 Research". That went stale when
    the goal numbering was corrected - the number is now 4 - and the import then
    refused the workbook because the label named a goal that did not exist. Build
    the label from the goal list so the fixture cannot disagree with the template.
    """
    for goal in queries.goal_tiles():
        if goal["ShortName"] == short_name:
            return "Goal: %d %s" % (goal["GoalNumber"], goal["ShortName"])
    raise AssertionError("no goal named %r in the sample data" % short_name)


def _counts(db):
    conn = sqlite3.connect(db)
    out = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("MajorInitiatives", "MajorInitiativeUpdates",
                      "MajorInitiativeGoals", "MajorInitiativeDeanLinks")
    }
    out["active"] = conn.execute("SELECT COUNT(*) FROM MajorInitiatives WHERE IsActive = 1").fetchone()[0]
    conn.close()
    return out


def _diary(db, code):
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "SELECT pu.PercentComplete, pu.Status, pu.Note FROM MajorInitiativeUpdates pu "
        "JOIN MajorInitiatives i ON i.MajorInitiativeID = pu.MajorInitiativeID "
        "WHERE i.MIId = ? OR i.Code = ? "
        "ORDER BY pu.UpdateDate, pu.UpdateID",
        (code, code),
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
    # The merged model (2026-10-07) has no Dean/D-1 Level column.
    assert "Code" in header and "Name" in header and "Owner" in header
    assert "Level" not in header


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


def _goal_columns(fresh_db):
    """The goal X columns as the REAL template generates them.

    This used to hardcode ("1 Academic", "2 Extension", "3 Research",
    "4 Learner impact", "5 Operational") - the transposed numbering - while the
    template had been corrected to 3 Learner / 4 Research. The fixture agreed with
    itself and disagreed with production, so it passed while testing a shape no
    workbook would contain. Reading the template's own output removes the seam.
    """
    import tempfile

    from openpyxl import load_workbook

    out = os.path.join(tempfile.mkdtemp(), "cols.xlsx")
    make_template.build(fresh_db, out)
    header = [c.value for c in load_workbook(out)["Initiatives"][1]]
    return [h for h in header if h and str(h).startswith("Goal:")]


def _row(code, name, owner, goals=(), priorities=(), feeds="",
         percent="", status="", goal_cols=None):
    """One Initiatives row, in the merged template's column order.

    The merged model (2026-10-07) has no Level: the columns are
    Code, Name, Description, Owner, Feeds, Percent, Status, then the X columns.
    """
    cols = goal_cols or ("1 Academic", "2 Extension", "3 Research",
                         "4 Learner impact", "5 Operational")
    row = [code, name, f"{name} description", owner, feeds, percent, status]
    row += ["X" if g in goals else "" for g in cols]
    row += ["X" if p in priorities else "" for p in ("Culture", "Data", "Identity",
                                                     "Innovation", "Pathways", "Scale")]
    return row


def test_clean_import_succeeds_and_swaps(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
        _row("MI-004", "Elizabeth Smith one", "Elizabeth Smith",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D27-1"),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]
    conn = sqlite3.connect(fresh_db)
    assert conn.execute("SELECT Title FROM MajorInitiatives WHERE MIId='MI-004'").fetchone()[0] \
        == "Elizabeth Smith one"
    conn.close()


def test_new_initiative_from_the_workbook(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-900", "Brand new", "Elizabeth Smith",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D27-1",
             percent="10", status="On track"),
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
    ])
    before = _counts(fresh_db)["MajorInitiatives"]
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]
    assert _counts(fresh_db)["MajorInitiatives"] == before + 1


# --- 8.8 diary preserved after re-import ----------------------------------


def test_diary_survives_a_re_import(logged_in, fresh_db, tmp_path, diary):
    """The data-intake spec: every initiative that kept its code still shows
    its full diary."""
    diary("MI-004", 25, "On track", on="2026-09-20")
    diary_before = _diary(fresh_db, "MI-004")
    assert diary_before

    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-004", "Renamed but same code", "Elizabeth Smith",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D27-1"),
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]
    assert _diary(fresh_db, "MI-004") == diary_before


# --- 8.8 retire missing, never delete -------------------------------------


def test_missing_initiatives_are_retired_not_deleted(logged_in, fresh_db, tmp_path, diary):
    diary("MI-004", 25, "On track", on="2026-09-20")
    before = _counts(fresh_db)
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok, [str(p) for p in problems]

    after = _counts(fresh_db)
    assert after["MajorInitiatives"] == before["MajorInitiatives"], "rows are retired, never deleted"
    assert after["active"] < before["active"]
    conn = sqlite3.connect(fresh_db)
    assert conn.execute("SELECT IsActive FROM MajorInitiatives WHERE MIId='MI-004'").fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM MajorInitiativeUpdates WHERE MajorInitiativeID = "
        "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId='MI-004')"
    ).fetchone()[0] > 0, "a retired initiative keeps its history"
    conn.close()


# --- 8.8 all-or-nothing ----------------------------------------------------


def test_a_failing_import_changes_nothing(logged_in, fresh_db, tmp_path):
    before = _counts(fresh_db)
    diary_before = _diary(fresh_db, "MI-004")

    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
        _row("MI-004", "Fine row", "Elizabeth Smith",
             goals=("3 Research",), priorities=("Data", "Innovation")),
        _row("BAD-1", "Broken", "Nobody", goals=("3 Research",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok is False
    assert problems, "a failing import must report at least one problem"
    assert _counts(fresh_db) == before, "the live database must be untouched"
    assert _diary(fresh_db, "MI-004") == diary_before


def test_failure_names_the_sheet_row(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
        _row("BAD-1", "Broken", "Nobody", goals=("3 Research",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok is False
    text = " | ".join(str(p) for p in problems)
    assert "Initiatives" in text
    assert "BAD-1" in text
    assert "owner" in text.lower() or "Nobody" in text


def test_unknown_owner_is_reported(logged_in, fresh_db, tmp_path):
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
        _row("NEW-1", "New", "Someone Not Here", goals=("3 Research",)),
    ])
    ok, problems = import_xlsx.import_workbook(fresh_db, path)
    assert ok is False
    assert "Someone Not Here" in " | ".join(str(p) for p in problems)


def test_dry_run_reports_clean_without_swapping(logged_in, fresh_db, tmp_path):
    before = _counts(fresh_db)
    path = _filled_workbook(fresh_db, tmp_path, [
        _row("MI-002", "Dean A", "Bill Gaudelli", goals=("3 Research",), priorities=("Data",)),
        _row("MI-004", "Elizabeth Smith one", "Elizabeth Smith",
             goals=("3 Research",), priorities=("Data", "Innovation"), feeds="D27-1"),
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


# --- amended 2026-10-06: the columns the spec had not described -----------


def test_the_generated_template_carries_the_import_columns(logged_in, fresh_db, tmp_path):
    """Feeds, Percent and Status were added so a new initiative can import at
    all - vw_DataChecks flags both "no Dean link" and "no progress update yet",
    and the importer refuses any file that leaves a check outstanding. They were
    in the generator but in no spec, so nothing would have caught their removal
    except indirectly, through the round-trip test.

    Amended 2026-10-06.
    """
    out = tmp_path / "intake.xlsx"
    path, _, _, _ = make_template.build(fresh_db, str(out))
    wb = load_workbook(path)
    header = [c.value for c in wb["Initiatives"][1]]

    for column in ("Feeds", "Percent", "Status"):
        assert column in header, "the template lost its %s column" % column

    # Feeds and Status carry dropdowns; Percent is a free number and correctly
    # has none. Asserting a dropdown on Percent was wrong the first time this
    # test was written - a number has nothing to pick from.
    validations = {
        str(dv.sqref).split(":")[0][0]: dv
        for dv in wb["Initiatives"].data_validations.dataValidation
    }
    for column in ("Feeds", "Status"):
        idx = header.index(column) + 1
        letter = wb["Initiatives"].cell(row=1, column=idx).column_letter
        assert letter in validations, "%s has no dropdown" % column

    percent_idx = header.index("Percent") + 1
    percent_letter = wb["Initiatives"].cell(row=1, column=percent_idx).column_letter
    assert percent_letter not in validations, (
        "Percent acquired a dropdown; it is a free number, so check whether "
        "that was deliberate before updating this test"
    )

    # the Feeds dropdown must hold the active Dean codes, because it drives links
    feeds_idx = header.index("Feeds") + 1
    feeds_letter = wb["Initiatives"].cell(row=1, column=feeds_idx).column_letter
    formula = validations[feeds_letter].formula1
    conn = sqlite3.connect(fresh_db)
    deans = [r[0] for r in conn.execute(
        "SELECT Code FROM DeanPriorities ORDER BY FiscalYear, Code")]
    conn.close()
    for code in deans:
        assert code in formula, "Feeds dropdown is missing Dean code %s" % code


# test_a_dean_row_with_feeds_is_refused_and_says_why: retired 2026-10-07 - the merged model has no Dean/D-1
# level and Feeds is a Dean Priority list, so neither premise holds.

# test_a_d1_row_with_no_feeds_is_refused_by_the_data_check: retired 2026-10-07 - the merged model has no Dean/D-1
# level and Feeds is a Dean Priority list, so neither premise holds.

# test_the_template_cannot_mark_a_primary_and_import_leaves_none: retired 2026-10-07 - the merged register model has no goal
# primacy (MajorInitiativeGoals has no IsPrimary), so this gap is gone.

# test_primacy_can_be_set_after_import_through_the_edit_screen: retired 2026-10-07 - the merged register model has no goal
# primacy (MajorInitiativeGoals has no IsPrimary), so this gap is gone.

# test_imported_initiative_has_no_primary_but_a_second_is_still_refused: retired 2026-10-07 - the merged register model has no goal
# primacy (MajorInitiativeGoals has no IsPrimary), so this gap is gone.

def test_the_row_helper_uses_the_templates_goal_columns(fresh_db):
    """The fixture's goal columns must be the ones the template generates.

    This is the seam that let a transposition hide: _row hardcoded the old goal
    labels while the template had been corrected, and because the fixtures also
    requested those same stale labels, everything agreed with itself and disagreed
    with the workbook a leader would receive.
    """
    real = _goal_columns(fresh_db)
    assert real, "the template produced no goal columns"
    built = _row("X-1", "x", "Bill Gaudelli", goals=(real[0],), goal_cols=real)
    # The first goal column is marked, and the labels are prefix-compatible with
    # the template's, so a row can be appended under the real header.
    assert built[7] == "X", "the row does not line up with the template's first goal column"
    for label in real:
        assert label.startswith("Goal: "), label
    assert "Learner" in " ".join(real), "the corrected Learner goal is missing"
    assert "Research" in " ".join(real), "the corrected Research goal is missing"
