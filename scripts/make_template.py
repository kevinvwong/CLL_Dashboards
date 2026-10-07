"""Generate the intake workbook (task 8.7).

    python scripts/make_template.py [output.xlsx]

One Initiatives sheet carries an X column per goal and per priority, generated
from the database, so a leader marks a tag with an X rather than typing a name
that might not match. Goals, Priorities and People are reference sheets so an
admin can correct the wording without opening the database.
"""

import os
import sqlite3
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "..", "cll_initiatives.db")
DEFAULT_OUT = os.path.join(HERE, "..", "intake_template.xlsx")

HEAD_FILL = PatternFill("solid", fgColor="003057")
HEAD_FONT = Font(color="FFFFFF", bold=True)
X_FILL = PatternFill("solid", fgColor="FFF4CE")


def _header(ws, labels, widths=None):
    ws.append(labels)
    for cell in ws[1]:
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"
    for index, label in enumerate(labels, start=1):
        letter = ws.cell(row=1, column=index).column_letter
        ws.column_dimensions[letter].width = (widths or {}).get(label, 18)
    return ws


def build(db_path: str, out_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    goals = conn.execute(
        "SELECT GoalNumber, ShortName, FullName, Description FROM Goals ORDER BY GoalNumber"
    ).fetchall()
    priorities = conn.execute(
        "SELECT PriorityName, PlanYear, Description FROM Priorities ORDER BY PlanYear, PriorityName"
    ).fetchall()
    people = conn.execute(
        "SELECT p.Name, p.Title, p.Email, m.Name AS ReportsTo "
        "FROM People p LEFT JOIN People m ON m.PersonID = p.ReportsToID "
        "WHERE p.IsActive = 1 ORDER BY p.Name"
    ).fetchall()

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Initiatives"
    goal_cols = [f"Goal: {g['GoalNumber']} {g['ShortName']}" for g in goals]
    priority_cols = [f"Priority: {p['PriorityName']}" for p in priorities]
    # The merged model (2026-10-07) has no Dean/D-1 Level; the columns are Code,
    # Name, Description, Owner, Feeds, Percent, Status, then the goal and
    # priority X columns. "Feeds" carries the Dean Priority codes (D27-n) a Major
    # Initiative contributes to, so a new initiative can clear vw_DataChecks.
    base_cols = ["Code", "Name", "Description", "Owner", "Feeds", "Percent", "Status"]
    _header(
        ws,
        base_cols + goal_cols + priority_cols,
        {"Code": 12, "Name": 42, "Description": 50, "Owner": 16,
         "Feeds": 18, "Percent": 10, "Status": 16},
    )

    # Percent and Status carry a brand-new initiative's first diary entry.
    status_letter = get_column_letter(base_cols.index("Status") + 1)
    dv_status = DataValidation(
        type="list",
        formula1='"Not started,On track,At risk,Off track,Complete,Paused"',
        allow_blank=True,
    )
    ws.add_data_validation(dv_status)
    dv_status.add(f"{status_letter}2:{status_letter}500")

    feeds_letter = get_column_letter(base_cols.index("Feeds") + 1)
    dean_codes = [
        r["Code"]
        for r in conn.execute(
            "SELECT Code FROM DeanPriorities ORDER BY FiscalYear, Code"
        )
    ]
    dv_feeds = DataValidation(
        type="list", formula1='"' + ",".join(dean_codes) + '"', allow_blank=True
    )
    ws.add_data_validation(dv_feeds)
    dv_feeds.add(f"{feeds_letter}2:{feeds_letter}500")

    owner_letter = get_column_letter(base_cols.index("Owner") + 1)

    dv_owner = DataValidation(
        type="list",
        formula1='"' + ",".join(p["Name"] for p in people) + '"',
        allow_blank=True,
    )
    ws.add_data_validation(dv_owner)
    dv_owner.add(f"{owner_letter}2:{owner_letter}500")

    # Shade the X columns so they read as mark-these boxes.
    first_x = len(base_cols) + 1
    for index in range(len(goal_cols) + len(priority_cols)):
        cell = ws.cell(row=1, column=first_x + index)
        cell.fill = X_FILL
        cell.font = Font(bold=True)

    # --- reference sheets --------------------------------------------------
    goals_ws = wb.create_sheet("Goals")
    _header(goals_ws, ["GoalNumber", "ShortName", "FullName", "Description"],
            {"GoalNumber": 12, "ShortName": 18, "FullName": 60, "Description": 60})
    for g in goals:
        goals_ws.append([g["GoalNumber"], g["ShortName"], g["FullName"], g["Description"] or ""])

    prio_ws = wb.create_sheet("Priorities")
    _header(prio_ws, ["PriorityName", "PlanYear", "Description"],
            {"PriorityName": 20, "PlanYear": 10, "Description": 60})
    for p in priorities:
        prio_ws.append([p["PriorityName"], p["PlanYear"], p["Description"] or ""])

    people_ws = wb.create_sheet("People")
    _header(people_ws, ["Name", "Title", "Email", "ReportsTo"],
            {"Name": 20, "Title": 32, "Email": 28, "ReportsTo": 20})
    for p in people:
        people_ws.append([p["Name"], p["Title"] or "", p["Email"] or "", p["ReportsTo"] or ""])

    wb.save(out_path)
    conn.close()
    return out_path, len(goals), len(priorities), len(people)


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    path, ng, np_, npe = build(db, out)
    print(f"Wrote {path}")
    print(f"  {ng} goal columns, {np_} priority columns, {npe} people in the dropdown")