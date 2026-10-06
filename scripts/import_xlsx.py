"""Import a filled intake workbook (task 8.8).

    python scripts/import_xlsx.py workbook.xlsx [--db cll_initiatives.db]

All-or-nothing (design.md decision 9): the workbook is loaded into a
temporary copy of the database, every rule is checked there, and the live
database is only swapped in when there are zero errors. A failed import
leaves the working database byte-for-byte unchanged and reports the offending
sheet and row.

Initiatives are upserted by Code, so an initiative that keeps its code keeps
its progress history. Initiatives absent from the workbook are retired, not
deleted.
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

# The vocabulary ProgressUpdates.Status enforces.
VALID_STATUSES = (
    "Not started",
    "On track",
    "At risk",
    "Off track",
    "Complete",
    "Paused",
)


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


def import_workbook(db_path: str, workbook_path: str, dry_run: bool = False):
    """Returns (ok, [Problem]). Never raises for data problems."""
    problems: list = []

    wb = load_workbook(workbook_path, data_only=True)
    if "Initiatives" not in wb.sheetnames:
        return False, [Problem("-", "-", "The workbook has no Initiatives sheet.")]

    # --- work on a temporary copy so a failure cannot touch the live file ---
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
            level = values[3] if len(values) > 3 else ""
            owner = values[4] if len(values) > 4 else ""

            if not name:
                problems.append(Problem("Initiatives", excel_row, f"{code}: missing Name"))
            if level not in ("Dean", "D-1"):
                problems.append(
                    Problem("Initiatives", excel_row, f"{code}: Level must be Dean or D-1, got {level!r}")
                )
            if owner and owner not in people:
                problems.append(
                    Problem("Initiatives", excel_row, f"{code}: owner {owner!r} is not in the People sheet")
                )
                owner_id = None
            else:
                owner_id = people.get(owner)

            existing = conn.execute(
                "SELECT InitiativeID FROM Initiatives WHERE Code = ?", (code,)
            ).fetchone()
            if existing:
                iid = existing["InitiativeID"]
                # An unresolvable owner is already reported; keep the existing
                # owner rather than writing NULL into a NOT NULL column.
                conn.execute(
                    "UPDATE Initiatives SET InitiativeName = ?, Description = ?, Level = ?, "
                    "OwnerID = COALESCE(?, OwnerID), IsActive = 1 WHERE InitiativeID = ?",
                    (
                        name,
                        values[2] if len(values) > 2 else None,
                        level,
                        owner_id,
                        iid,
                    ),
                )
            else:
                if not owner or owner_id is None:
                    if not owner:
                        problems.append(
                            Problem("Initiatives", excel_row, f"{code}: new initiative needs an owner")
                        )
                    continue
                cur = conn.execute(
                    "INSERT INTO Initiatives (Code, InitiativeName, Description, Level, OwnerID) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (code, name, values[2] if len(values) > 2 else None, level, owner_id),
                )
                iid = cur.lastrowid

            # Tags come from the X columns.
            conn.execute("DELETE FROM InitiativeGoals WHERE InitiativeID = ?", (iid,))
            conn.execute("DELETE FROM InitiativePriorities WHERE InitiativeID = ?", (iid,))
            for index, label in goal_cols.items():
                if index < len(values) and _marked(values[index]):
                    # The column header is "Goal: 3 Research", so try the
                    # number first and fall back to the short name.
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
                            "INSERT INTO InitiativeGoals (InitiativeID, GoalID, IsPrimary) VALUES (?, ?, 0)",
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
                            "INSERT INTO InitiativePriorities (InitiativeID, PriorityID, IsPrimary) "
                            "VALUES (?, ?, 0)",
                            (iid, priority_id),
                        )

            # Feeds: the Dean codes this D-1 initiative feeds. Without this a
            # new D-1 initiative could never clear vw_DataChecks.
            if feeds_col is not None and feeds_col < len(values):
                feeds = [f.strip() for f in values[feeds_col].split(",") if f.strip()]
                if level == "Dean" and feeds:
                    # A Dean initiative is fed BY D-1 initiatives; it feeds
                    # nothing itself, so a value here is a mistake in the row.
                    # The message used to read "a Dean initiative feeds nothing",
                    # which described the opposite of what was found and would
                    # have sent the reader looking for a missing value in a row
                    # that had one. Fixed 2026-10-06.
                    problems.append(
                        Problem(
                            "Initiatives",
                            excel_row,
                            f"{code}: a Dean initiative cannot feed another "
                            f"initiative, but Feeds is set to {values}",
                        )
                    )
                elif feeds:
                    for dean_code in feeds:
                        target = conn.execute(
                            "SELECT InitiativeID FROM Initiatives "
                            "WHERE Code = ? AND Level = 'Dean' AND IsActive = 1",
                            (dean_code,),
                        ).fetchone()
                        if target is None:
                            problems.append(
                                Problem(
                                    "Initiatives",
                                    excel_row,
                                    f"{code}: Feeds references {dean_code!r}, "
                                    "which is not an active Dean initiative",
                                )
                            )
                        else:
                            conn.execute(
                                "INSERT OR IGNORE INTO InitiativeLinks "
                                "(InitiativeID, DeanInitiativeID) VALUES (?, ?)",
                                (iid, target["InitiativeID"]),
                            )

            # Percent and Status give a brand-new initiative its first diary
            # entry. vw_DataChecks flags "No progress update yet", so without
            # them a new initiative could never be imported.
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
                                "INSERT INTO ProgressUpdates "
                                "(InitiativeID, PercentComplete, Status, Note, EnteredByID) "
                                "VALUES (?, ?, ?, ?, NULL)",
                                (iid, percent_value, status_text,
                                 f"Created from the intake workbook."),
                            )

        # --- retire the ones the workbook left out -------------------------
        if seen_codes:
            placeholders = ",".join("?" * len(seen_codes))
            retired = conn.execute(
                f"SELECT Code FROM Initiatives WHERE IsActive = 1 AND Code NOT IN ({placeholders})",
                seen_codes,
            ).fetchall()
            for row in retired:
                conn.execute("UPDATE Initiatives SET IsActive = 0 WHERE Code = ?", (row["Code"],))

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