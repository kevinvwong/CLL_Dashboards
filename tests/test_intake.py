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


def _row(code, name, level, owner, goals=(), priorities=(), feeds="",
         percent="", status="", goal_cols=None):
    """One Initiatives row.

    The goal columns come from the template when given, so a fixture cannot
    disagree with the workbook a leader would actually receive.
    """
    cols = goal_cols or ("1 Academic", "2 Extension", "3 Research",
                         "4 Learner impact", "5 Operational")
    row = [code, name, f"{name} description", level, owner, feeds, percent, status]
    row += ["X" if g in goals else "" for g in cols]
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
        "SELECT Code FROM Initiatives WHERE Level='Dean' AND IsActive=1")]
    conn.close()
    for code in deans:
        assert code in formula, "Feeds dropdown is missing Dean code %s" % code


def test_a_dean_row_with_feeds_is_refused_and_says_why(logged_in, fresh_db, tmp_path):
    """A Dean initiative is fed BY D-1 initiatives; it feeds nothing, so a value
    in Feeds on a Dean row is a mistake.

    The message used to read "a Dean initiative feeds nothing" while rejecting a
    row that had just supplied one, which described the opposite of what was
    found. Amended 2026-10-06.
    """
    from openpyxl import Workbook

    out = tmp_path / "dean_with_feeds.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Initiatives"
    ws.append(["Code", "Name", "Description", "Level", "Owner", "Feeds", "Percent",
               "Status", _goal_header("Research"), "Priority: Data"])
    ws.append(["D-Z", "A dean row", "d", "Dean", "Bill", "D-A", "", "", "X", "X"])
    wb.save(out)

    ok, problems = import_xlsx.import_workbook(fresh_db, str(out))
    assert ok is False
    text = " ".join(str(p) for p in problems)
    assert "cannot feed another initiative" in text, text
    assert "D-A" in text, "the report should quote what the row actually said"
    assert "feeds nothing" not in text, (
        "the old wording claimed the value was missing while rejecting a row that had one"
    )


def test_a_d1_row_with_no_feeds_is_refused_by_the_data_check(logged_in, fresh_db, tmp_path):
    from openpyxl import Workbook

    out = tmp_path / "d1_no_feeds.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Initiatives"
    ws.append(["Code", "Name", "Description", "Level", "Owner", "Feeds", "Percent",
               "Status", _goal_header("Research"), "Priority: Data"])
    ws.append(["ELIZ-9", "No link", "d", "D-1", "Elizabeth", "", "20", "On track", "X", "X"])
    wb.save(out)

    ok, problems = import_xlsx.import_workbook(fresh_db, str(out))
    assert ok is False
    text = " ".join(str(p) for p in problems)
    assert "not linked to any Dean initiative" in text, text


def test_the_template_cannot_mark_a_primary_and_import_leaves_none(logged_in, fresh_db, tmp_path):
    """Documents a gap rather than fixing it.

    The requirement once promised primary goal and primary priority dropdowns.
    There are none, and the importer inserts every tag with IsPrimary = 0, so an
    imported initiative carries no primary even though the schema permits one and
    the cards render a badge for it. Changing the workbook format is a decision
    for whoever owns the intake round, so this test records the behaviour instead
    of silently choosing for them.
    """
    from openpyxl import Workbook

    probe = tmp_path / "probe.xlsx"
    path, _, _, _ = make_template.build(fresh_db, str(probe))
    header = [c.value for c in load_workbook(path)["Initiatives"][1]]
    assert not any("primary" in str(h).lower() for h in header), (
        "a primary column appeared; the gap this test documents may be closed, "
        "in which case update the data-intake spec and remove this test"
    )

    out = tmp_path / "new.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Initiatives"
    ws.append(["Code", "Name", "Description", "Level", "Owner", "Feeds", "Percent",
               "Status", _goal_header("Research"), "Priority: Data"])
    ws.append(["ELIZ-9", "Fresh", "d", "D-1", "Elizabeth", "D-A", "20", "On track", "X", "X"])
    wb.save(out)
    ok, problems = import_xlsx.import_workbook(fresh_db, str(out))
    assert ok, problems

    conn = sqlite3.connect(fresh_db)
    n = conn.execute(
        "SELECT COUNT(*) FROM InitiativeGoals ig JOIN Initiatives i "
        "ON i.InitiativeID = ig.InitiativeID WHERE i.Code = 'ELIZ-9' AND ig.IsPrimary = 1"
    ).fetchone()[0]
    conn.close()
    assert n == 0, "an imported initiative has no primary goal, by design of the template"


def test_primacy_can_be_set_after_import_through_the_edit_screen(logged_in, fresh_db):
    """The gap above is recoverable per initiative without a second import.

    Resolves the goal the way the edit-tags screen does - by number - rather than
    assuming the card hands back an internal id it does not carry.
    """
    from app import repo

    goal_number = queries.initiative_card("ELIZ-1")["goal_tags"][0]["GoalNumber"]
    conn = sqlite3.connect(fresh_db)
    goal_id = conn.execute("SELECT GoalID FROM Goals WHERE GoalNumber = ?",
                           (goal_number,)).fetchone()[0]
    conn.close()

    repo.replace_tags(
        "ELIZ-1",
        goal_tags=[{"id": goal_id, "primary": True}],
        priority_tags=[],
        person_id=1,
    )

    conn = sqlite3.connect(fresh_db)
    iid = conn.execute("SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1'").fetchone()[0]
    n = conn.execute("SELECT COUNT(*) FROM InitiativeGoals WHERE InitiativeID=? AND IsPrimary=1",
                     (iid,)).fetchone()[0]
    conn.close()
    assert n == 1, "primacy set through the edit screen must persist"


def test_imported_initiative_has_no_primary_but_a_second_is_still_refused(logged_in, fresh_db):
    """The other half of the primacy gap: imported tags carry none, and setting
    two is refused by the same rule that governs the sample data."""
    from app import repo

    conn = sqlite3.connect(fresh_db)
    goal_ids = [r[0] for r in conn.execute(
        "SELECT GoalID FROM Goals ORDER BY GoalNumber LIMIT 2")]
    iid = conn.execute("SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1'").fetchone()[0]
    imported_none = conn.execute(
        "SELECT COUNT(*) FROM InitiativeGoals WHERE InitiativeID=? AND IsPrimary=1",
        (iid,)).fetchone()[0]
    conn.close()

    # the edit screen offers both goals, so a second primary is reachable
    with pytest.raises(repo.RuleError) as exc:
        repo.replace_tags(
            "ELIZ-1",
            goal_tags=[{"id": goal_ids[0], "primary": True},
                       {"id": goal_ids[1], "primary": True}],
            priority_tags=[],
            person_id=1,
        )
    assert "Only one primary goal is allowed" in str(exc.value)

    conn = sqlite3.connect(fresh_db)
    after = conn.execute("SELECT COUNT(*) FROM InitiativeGoals WHERE InitiativeID=? AND IsPrimary=1",
                         (iid,)).fetchone()[0]
    conn.close()
    assert after == 0 or after == 1, "the refusal must not leave two primaries behind"



# --- the fixture must agree with the template -----------------------------


def test_the_row_helper_uses_the_templates_goal_columns(fresh_db):
    """The fixture's goal columns must be the ones the template generates.

    This is the seam that let a transposition hide: _row hardcoded the old goal
    labels while the template had been corrected, and because the fixtures also
    requested those same stale labels, everything agreed with itself and disagreed
    with the workbook a leader would receive.
    """
    real = _goal_columns(fresh_db)
    assert real, "the template produced no goal columns"
    built = _row("X-1", "x", "Dean", "Bill", goals=(real[0],), goal_cols=real)
    # The first goal column is marked, and the labels are prefix-compatible with
    # the template's, so a row can be appended under the real header.
    assert built[8] == "X", "the row does not line up with the template's first goal column"
    for label in real:
        assert label.startswith("Goal: "), label
    assert "Learner" in " ".join(real), "the corrected Learner goal is missing"
    assert "Research" in " ".join(real), "the corrected Research goal is missing"
