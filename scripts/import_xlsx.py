"""Import a filled intake workbook (register model, 2026-10-07).

    python scripts/import_xlsx.py workbook.xlsx [--db cll_initiatives.db]

All-or-nothing (design.md decision 9): the workbook is loaded into a
temporary copy of the database, every rule is checked there, and the live
database is only swapped in when there are zero errors. A failed import
leaves the working database byte-for-byte unchanged and reports the offending
sheet and row.

The 2026-10-07 merge made the register's Team Initiatives the one initiative
model. This targets `TeamInitiatives` and `TeamInitiativeUpdates`, drops the
prototype's Dean/D-1 "Level", and re-expresses "Feeds" as the Dean Initiatives
(the register's "Dean KPI 27" items) a Team Initiative contributes to.
Initiatives are upserted by Code; ones absent from the workbook are retired,
not deleted.
"""

import argparse
import os
import shutil
import sqlite3
import sys
import tempfile

from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "..", "cll_initiatives.db")

TRUEISH = {"x", "X", "y", "Y", "yes", "Yes", "1", "true", "TRUE"}

# The vocabulary TeamInitiativeUpdates.Status enforces.
VALID_STATUSES = (
    "Not started",
    "On track",
    "At risk",
    "Off track",
    "Complete",
    "Paused",
)

# The Milestones.Status vocabulary (ADR-0002).
MILESTONE_STATUSES = ("Met", "In progress", "Not started", "Missed")
# The reported outcome vocabulary on Priorities.Status (ADR-0002).
OUTCOME_STATUSES = ("On track", "At risk", "Behind", "Not started")


class Problem(Exception):
    def __init__(self, sheet, row, message):
        super().__init__(message)
        self.sheet = sheet
        self.row = row
        self.message = message

    def __str__(self):
        return f"{self.sheet} row {self.row}: {self.message}"


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _marked(value):
    return _text(value) in TRUEISH


def _connect(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _sheet_rows(ws):
    """(excel_row, {header: value}) for each non-blank row of a sheet."""
    header = [_text(c.value) for c in ws[1]]
    for r in range(2, ws.max_row + 1):
        values = [_text(c.value) for c in ws[r]]
        if any(values):
            yield r, dict(zip(header, values))


def _import_milestones(conn, wb, problems) -> int:
    """Replace the Milestones from the Milestones sheet; return how many.

    A PRESENT sheet replaces the milestone set: supplying the confirmed rows IS
    the confirmation act (ADR-0001). An empty sheet is ignored, so an admin who
    leaves it blank does not wipe the model by accident.
    """
    if "Milestones" not in wb.sheetnames:
        return 0
    rows = list(_sheet_rows(wb["Milestones"]))
    if not rows:
        return 0
    known = {r["Code"] for r in conn.execute(
        "SELECT Code FROM Priorities WHERE Code IS NOT NULL")}
    conn.execute("DELETE FROM Milestones")
    n = 0
    for excel_row, r in rows:
        code = r.get("Priority", "")
        name = r.get("Milestone", "")
        status = r.get("Status", "") or "Not started"
        if not name:
            problems.append(Problem("Milestones", excel_row, "missing Milestone"))
            continue
        if code not in known:
            problems.append(Problem("Milestones", excel_row,
                                    f"{name!r}: priority {code!r} is not a known priority"))
            continue
        if status not in MILESTONE_STATUSES:
            problems.append(Problem("Milestones", excel_row,
                                    f"{name!r}: status {status!r} is not a milestone status"))
            continue
        conn.execute(
            "INSERT INTO Milestones (PriorityCode, Name, Status, PlannedDate, "
            "DateMet, OwnerLabel, EvidenceURL, SortOrder) VALUES (?,?,?,?,?,?,?,?)",
            (code, name, status, r.get("Planned date") or None, r.get("Date met") or None,
             r.get("Owner") or None, r.get("Evidence URL") or None, n + 1))
        n += 1
    return n


def _import_outcomes(conn, wb, problems) -> int:
    """Set each priority's reported outcome state from the Outcomes sheet."""
    if "Outcomes" not in wb.sheetnames:
        return 0
    known = {r["Code"] for r in conn.execute(
        "SELECT Code FROM Priorities WHERE Code IS NOT NULL")}
    n = 0
    for excel_row, r in _sheet_rows(wb["Outcomes"]):
        code = r.get("Priority", "")
        status = r.get("Outcome status", "")
        updated = r.get("Last updated", "")
        if not code:
            problems.append(Problem("Outcomes", excel_row, "missing Priority"))
            continue
        if code not in known:
            problems.append(Problem("Outcomes", excel_row,
                                    f"priority {code!r} is not a known priority"))
            continue
        if status and status not in OUTCOME_STATUSES:
            problems.append(Problem("Outcomes", excel_row,
                                    f"{code}: status {status!r} is not an outcome status"))
            continue
        conn.execute("UPDATE Priorities SET Status=?, LastUpdated=? WHERE Code=?",
                     (status or None, updated or None, code))
        n += 1
    return n


def import_workbook(db_path: str, workbook_path: str, dry_run: bool = False):
    """Returns (ok, [Problem]). Never raises for data problems."""
    problems: list = []

    wb = load_workbook(workbook_path, data_only=True)
    if "Initiatives" not in wb.sheetnames:
        return False, [Problem("-", "-", "The workbook has no Initiatives sheet.")]

    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "staging.db")
    shutil.copy2(db_path, temp_db)

    conn = _connect(temp_db)
    try:
        goals = {
            r["ShortName"]: r["GoalID"]
            for r in conn.execute("SELECT GoalID, ShortName FROM Goals")
        }
        goal_by_number = {
            r["GoalNumber"]: r["GoalID"]
            for r in conn.execute("SELECT GoalID, GoalNumber FROM Goals")
        }
        priorities = {
            r["PriorityName"]: r["PriorityID"]
            for r in conn.execute("SELECT PriorityID, PriorityName FROM Priorities")
        }
        people = {
            r["Name"]: r["PersonID"]
            for r in conn.execute("SELECT PersonID, Name FROM People")
        }
        dean_initiatives = {
            r["Code"]: r["DeanInitiativeID"]
            for r in conn.execute("SELECT DeanInitiativeID, Code FROM DeanInitiatives")
        }

        ws = wb["Initiatives"]
        header = [(_text(c.value) or "") for c in ws[1]]
        goal_cols, priority_cols, feeds_col = {}, {}, None
        percent_col = status_col = None
        for index, name in enumerate(header):
            if name.startswith("Goal:"):
                goal_cols[index] = name.split(":", 1)[1].strip()
            elif name.startswith("Priority:"):
                priority_cols[index] = name.split(":", 1)[1].strip()
            elif name == "Feeds":
                feeds_col = index
            elif name == "Percent":
                percent_col = index
            elif name == "Status":
                status_col = index

        seen_codes = []
        for excel_row in range(2, ws.max_row + 1):
            values = [_text(c.value) for c in ws[excel_row]]
            if not any(values):
                continue
            code = values[0] if values else ""
            if not code:
                problems.append(Problem("Initiatives", excel_row, "missing Code"))
                continue
            seen_codes.append(code)

            name = values[1] if len(values) > 1 else ""
            description = values[2] if len(values) > 2 else ""
            owner = values[3] if len(values) > 3 else ""

            if not name:
                problems.append(Problem("Initiatives", excel_row, f"{code}: missing Name"))
            if owner and owner not in people:
                problems.append(
                    Problem("Initiatives", excel_row, f"{code}: owner {owner!r} is not in the People sheet")
                )
                owner_id = None
            else:
                owner_id = people.get(owner)

            existing = conn.execute(
                "SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code = ? OR MIId = ?",
                (code, code),
            ).fetchone()
            if existing:
                iid = existing["TeamInitiativeID"]
                conn.execute(
                    "UPDATE TeamInitiatives SET Title = ?, Description = ?, "
                    "OwnerID = COALESCE(?, OwnerID), IsActive = 1 WHERE TeamInitiativeID = ?",
                    (name, description or None, owner_id, iid),
                )
            else:
                if not owner or owner_id is None:
                    if not owner:
                        problems.append(
                            Problem("Initiatives", excel_row, f"{code}: new initiative needs an owner")
                        )
                    continue
                cur = conn.execute(
                    "INSERT INTO TeamInitiatives (Code, Title, Description, OwnerID) "
                    "VALUES (?, ?, ?, ?)",
                    (code, name, description or None, owner_id),
                )
                iid = cur.lastrowid

            # Tags come from the X columns.
            conn.execute("DELETE FROM TeamInitiativeGoals WHERE TeamInitiativeID = ?", (iid,))
            conn.execute("DELETE FROM TeamInitiativePriorities WHERE TeamInitiativeID = ?", (iid,))
            for index, label in goal_cols.items():
                if index < len(values) and _marked(values[index]):
                    head = label.split(" ", 1)[0]
                    goal_id = goal_by_number.get(int(head)) if head.isdigit() else None
                    if goal_id is None:
                        goal_id = goals.get(label)
                    if goal_id is None:
                        problems.append(
                            Problem("Initiatives", excel_row, f"{code}: unknown goal {label!r}")
                        )
                    else:
                        conn.execute(
                            "INSERT INTO TeamInitiativeGoals (TeamInitiativeID, GoalID) VALUES (?, ?)",
                            (iid, goal_id),
                        )
            for index, label in priority_cols.items():
                if index < len(values) and _marked(values[index]):
                    priority_id = priorities.get(label)
                    if priority_id is None:
                        problems.append(
                            Problem("Initiatives", excel_row, f"{code}: unknown priority {label!r}")
                        )
                    else:
                        conn.execute(
                            "INSERT INTO TeamInitiativePriorities (TeamInitiativeID, PriorityID, IsPrimary) "
                            "VALUES (?, ?, 0)",
                            (iid, priority_id),
                        )

            # Feeds: the Dean Initiative codes (D27-1..) this initiative contributes
            # to. Without this a new initiative could never clear vw_DataChecks.
            if feeds_col is not None and feeds_col < len(values):
                feeds = [f.strip() for f in values[feeds_col].split(",") if f.strip()]
                for dean_code in feeds:
                    target_id = dean_initiatives.get(dean_code)
                    if target_id is None:
                        problems.append(
                            Problem("Initiatives", excel_row,
                                    f"{code}: Feeds references {dean_code!r}, "
                                    "which is not a known Dean Initiative")
                        )
                    else:
                        conn.execute(
                            "INSERT OR IGNORE INTO TeamInitiativeDeanLinks "
                            "(TeamInitiativeID, DeanInitiativeID) VALUES (?, ?)",
                            (iid, target_id),
                        )

            # Percent and Status give a brand-new initiative its first diary entry.
            if percent_col is not None and percent_col < len(values):
                percent_text = _text(values[percent_col])
                if percent_text:
                    status_text = (
                        _text(values[status_col]) if status_col is not None and status_col < len(values) else ""
                    ) or "Not started"
                    if status_text not in VALID_STATUSES:
                        problems.append(
                            Problem("Initiatives", excel_row,
                                    f"{code}: status {status_text!r} is not a known status")
                        )
                    else:
                        try:
                            percent_value = int(float(percent_text))
                        except ValueError:
                            problems.append(
                                Problem("Initiatives", excel_row,
                                        f"{code}: Percent {percent_text!r} is not a number")
                            )
                            percent_value = None
                        if percent_value is not None and not 0 <= percent_value <= 100:
                            problems.append(
                                Problem("Initiatives", excel_row,
                                        f"{code}: Percent must be between 0 and 100")
                            )
                        elif percent_value is not None:
                            conn.execute(
                                "INSERT INTO TeamInitiativeUpdates "
                                "(TeamInitiativeID, PercentComplete, Status, Note, EnteredByID) "
                                "VALUES (?, ?, ?, ?, NULL)",
                                (iid, percent_value, status_text,
                                 "Created from the intake workbook."),
                            )

        # --- retire the ones the workbook left out -------------------------
        if seen_codes:
            placeholders = ",".join("?" * len(seen_codes))
            retired = conn.execute(
                f"SELECT Code, MIId FROM TeamInitiatives WHERE IsActive = 1 "
                f"AND Code NOT IN ({placeholders}) "
                f"AND COALESCE(MIId,'') NOT IN ({placeholders})",
                tuple(seen_codes) + tuple(seen_codes),
            ).fetchall()
            for row in retired:
                conn.execute("UPDATE TeamInitiatives SET IsActive = 0 WHERE Code = ?",
                             (row["Code"],))

        conn.commit()

        # The Milestones and the outcome state (enhancement, 2026-10-07). A
        # present sheet replaces that model: supplying the confirmed rows IS the
        # confirmation act, which flips the dataset provenance to 'confirmed' so
        # the Outcomes page stops labelling itself as a mock.
        ms_n = _import_milestones(conn, wb, problems)
        out_n = _import_outcomes(conn, wb, problems)
        if ms_n or out_n:
            conn.execute("INSERT OR REPLACE INTO AppMeta (Key, Value) "
                         "VALUES ('dataset_provenance', 'confirmed')")
        conn.commit()

        # --- the data checks must be clear before anything is swapped in ----
        for row in conn.execute("SELECT Code, Issue FROM vw_DataChecks ORDER BY Code"):
            problems.append(Problem("checks", "-", f"{row['Code']}: {row['Issue']}"))

    except sqlite3.Error as exc:
        conn.rollback()
        problems.append(Problem("-", "-", f"database error: {exc}"))
    finally:
        conn.close()

    if problems:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False, problems

    if dry_run:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return True, []

    # --- zero errors: swap the staged file in ------------------------------
    shutil.copy2(temp_db, db_path)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return True, []


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import a filled intake workbook.")
    parser.add_argument("workbook")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    ok, problems = import_workbook(args.db, args.workbook, dry_run=args.dry_run)
    if ok:
        print("Import complete.")
        if args.dry_run:
            print("  (dry run: the live database was not modified)")
        return 0

    print(f"Import refused: {len(problems)} problem(s). The database was not changed.", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
