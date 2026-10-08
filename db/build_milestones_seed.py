"""Generate db/seed_milestones.sql: the Milestones table, the priority outcome
state, and the dataset-provenance row.

    python db/build_milestones_seed.py           # writes db/seed_milestones.sql
    python db/build_milestones_seed.py --check   # fail if the output differs

WHY THIS DATA IS HERE AND MARKED 'mock'.

The real milestone content does not exist yet: the wireframe workbook supplies
only the data-REQUIREMENTS (rows A-07..A-17), no names, dates, owners or
statuses, and its Summary says "Blocking: no owners are named yet". The app must
not hardcode data, so the milestone rows are a SEED (in the database), not a
literal in application code, and the dataset is tagged provenance='mock' so the
Outcomes page labels it instead of presenting it as confirmed (plan D5).

The 18 milestones and their statuses are the wireframe's illustrative scaffold
(the values formerly in scripts/build_oct16_data.py), preserved so the Outcomes
layout can be reviewed. Two wireframe pseudo-statuses are normalised to the real
model: "Due Dec" and "Confirm" are NOT milestone statuses - the first is a due
date and the second an unconfirmed state - so they become 'Not started' with the
date (where known) in PlannedDate. The reached counts are unchanged by that.

Owner names and planned dates are deliberately left NULL: inventing them would
be the exact dishonesty this model exists to prevent. The intake fills them.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seed_milestones.sql")

#: The plan year these milestones belong to. The six priorities recur each year;
#: this seed is for 2027, and Priorities rows are keyed by (PlanYear, Code).
PLAN_YEAR = 2027

#: The people beyond the register's owners (Strategic Operations and OIT
#: support), with the email Clerk matches an SSO identity to. (PersonID, name,
#: title, email). The register seed owns PersonIDs 1-7.
ROSTER_PEOPLE = [
    (8, "Cassie Parkin", "Strategic Operations", "cparkin6@gatech.edu"),
    (9, "Chris Reyes", "Strategic Operations", "creyes39@gatech.edu"),
    (10, "DeMarco Williams", "Strategic Operations", "dwilliams406@gatech.edu"),
    (11, "Mike Sewell", "OIT Technical Contact", "msewell7@gatech.edu"),
]

#: Emails for the people the register already seeds, from the roster.
ROSTER_EMAILS = {
    "Bill Gaudelli": "wgaudelli3@gatech.edu",
    "Elizabeth Smith": "esmith460@gatech.edu",
    "Tim Jacobbe": "tjacobbe3@gatech.edu",
    "Mario Herane": "mherane3@gatech.edu",
    "Meltem Alemdar": "ma128@gatech.edu",
    "Grace Flavin": "eflavin6@gatech.edu",
    "Kevin": "kwong318@gatech.edu",
}

#: Explicit role assignment: (person name, role name). A reviewable roster, not
#: a heuristic. The Viewer role is granted to everyone (read access); the four
#: leaders also hold it and gain Contributor later without losing Viewer.
ROSTER_ROLES = [
    ("Kevin", "PlatformAdmin"), ("Kevin", "Operator"), ("Kevin", "Viewer"),
    ("Cassie Parkin", "PlatformAdmin"), ("Cassie Parkin", "Operator"), ("Cassie Parkin", "Viewer"),
    ("Chris Reyes", "PlatformAdmin"), ("Chris Reyes", "Operator"), ("Chris Reyes", "Viewer"),
    ("DeMarco Williams", "PlatformAdmin"), ("DeMarco Williams", "Operator"), ("DeMarco Williams", "Viewer"),
    ("Elizabeth Smith", "DataOwner"), ("Elizabeth Smith", "Viewer"),
    ("Bill Gaudelli", "ExecutiveSponsor"), ("Bill Gaudelli", "Viewer"),
    ("Grace Flavin", "Viewer"),
    ("Mario Herane", "Viewer"),
    ("Meltem Alemdar", "Viewer"),
    ("Tim Jacobbe", "Viewer"),
    ("Mike Sewell", "TechnicalAdmin"), ("Mike Sewell", "Viewer"),
]

#: (priority_code, name, status, planned_date, sort) -- MOCK, see module docstring.
MILESTONES = [
    ("P01", "Message architecture approved", "Met", None, 1),
    ("P01", "Teams adopted (1 of 4)", "In progress", None, 2),
    ("P01", "First asset audit", "Not started", None, 3),
    ("P02", "RDI baseline complete", "Met", None, 1),
    ("P02", "Innovation call launched", "Met", None, 2),
    ("P02", "First stage-gate decisions", "Not started", "2026-12-31", 3),
    ("P03", "Unified approval process", "In progress", None, 1),
    ("P03", "First badged pathway", "In progress", None, 2),
    ("P03", "Mapping rule approved", "Met", None, 3),
    ("P04", "Quality standard approved", "Not started", None, 1),
    ("P04", "Reuse baseline", "In progress", None, 2),
    ("P04", "Build-time baseline", "Not started", None, 3),
    ("P05", "KPI definitions drafted", "Met", None, 1),
    ("P05", "College dashboard", "In progress", None, 2),
    ("P05", "Owners named", "Not started", None, 3),
    ("P06", "Target structure approved", "Not started", None, 1),
    ("P06", "Q1 learning reviews", "In progress", None, 2),
    ("P06", "Operating model template", "Met", None, 3),
]

#: priority_code -> (outcome status, last-updated). The reported state on the
#: Outcomes cards. Its own vocabulary (ADR-0002). MOCK.
OUTCOME_STATE = {
    "P01": ("On track", "2026-10-07"),
    "P02": ("On track", "2026-10-07"),
    "P03": ("At risk", "2026-10-07"),
    "P04": ("At risk", "2026-10-07"),
    "P05": ("On track", "2026-10-07"),
    "P06": ("On track", "2026-10-07"),
}


def _sq(s):
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def build(out=OUT):
    L = ["-- GENERATED by db/build_milestones_seed.py. Do not hand-edit.",
         "-- MOCK data: illustrative milestones pending the intake (see the",
         "-- generator's docstring). Provenance is tagged 'mock' below.", ""]

    L.append("-- Milestones: a checkable event per Priority (ADR-0001). Keyed to the")
    L.append("-- Priorities ROW for this plan year, since the code recurs each year.")
    L.append("DELETE FROM Milestones;")
    L.append("INSERT INTO Milestones (PriorityID, Name, Status, PlannedDate, SortOrder) VALUES")
    vals = []
    for code, name, status, planned, sort in MILESTONES:
        vals.append("  ((SELECT PriorityID FROM Priorities WHERE Code=%s AND PlanYear=%d), "
                    "%s, %s, %s, %d)"
                    % (_sq(code), PLAN_YEAR, _sq(name), _sq(status), _sq(planned), sort))
    L.append(",\n".join(vals) + ";")
    L.append("")

    L.append("-- The reported outcome state per Priority (workbook A-05/A-06).")
    for code, (status, updated) in OUTCOME_STATE.items():
        L.append("UPDATE Priorities SET Status=%s, LastUpdated=%s "
                 "WHERE Code=%s AND PlanYear=%d;"
                 % (_sq(status), _sq(updated), _sq(code), PLAN_YEAR))
    L.append("")

    L.append("-- Dataset provenance: the importer overwrites this with 'confirmed'.")
    L.append("DELETE FROM AppMeta;")
    L.append("INSERT INTO AppMeta (Key, Value) VALUES")
    L.append("  ('dataset_provenance', 'mock'),")
    L.append("  ('dataset_source', 'seed: illustrative milestones for build/layout review'),")
    L.append("  ('current_plan_year', '%d');" % PLAN_YEAR)
    L.append("")

    # Local roles (ADR-0005). The canonical set is the DR-05 role model, recorded
    # with the roster: capability-oriented roles, deliberately NOT a hierarchy
    # (DR-23). Assignment is EXPLICIT by person (a roster), not inferred from a
    # person's title/team, so the mapping is reviewable and stable. Emails come
    # from the roster and are the key Clerk matches an SSO identity to.
    L.append("-- Roles and their assignment (ADR-0005, DR-05, DR-23). App-local.")
    L.append("DELETE FROM PeopleRoles;")
    L.append("DELETE FROM Roles;")
    L.append("INSERT INTO Roles (RoleID, Name, Description) VALUES")
    L.append("  (1, 'PlatformAdmin', 'technical/application administration and approved access administration'),")
    L.append("  (2, 'ExecutiveSponsor', 'the Dean: portfolio read plus executive actions (never routine data edits)'),")
    L.append("  (3, 'DataOwner', 'governs portfolio data: approvals, exceptions, quality, accountability'),")
    L.append("  (4, 'Operator', 'Strategic Operations: portfolio and data maintenance'),")
    L.append("  (5, 'Contributor', 'edits assigned initiatives (future phase; unassigned initially)'),")
    L.append("  (6, 'Viewer', 'reads published content'),")
    L.append("  (7, 'TechnicalAdmin', 'OIT/Azure infrastructure support; platform health, not portfolio data');")

    # The people beyond the register's owners (Strategic Operations + OIT
    # support). Added here so the roster is complete; the register seed owns the
    # seven it already names.
    L.append("-- Additional roster people (Strategic Operations, OIT support).")
    for pid, name, title, email in ROSTER_PEOPLE:
        L.append("INSERT INTO People (PersonID, Name, Title, Email, IsActive) VALUES "
                 "(%d, %s, %s, %s, 1) ON CONFLICT(PersonID) DO UPDATE SET "
                 "Name=excluded.Name, Title=excluded.Title, Email=excluded.Email, IsActive=1;"
                 % (pid, _sq(name), _sq(title), _sq(email)))

    # Emails for the people the register already seeds (from the roster).
    L.append("-- Emails for the register people (roster).")
    for name, email in ROSTER_EMAILS.items():
        L.append("UPDATE People SET Email=%s WHERE Name=%s;" % (_sq(email), _sq(name)))

    # Explicit role assignment: (person name, role name).
    L.append("-- Explicit role assignment (a roster, not a heuristic).")
    L.append("INSERT INTO PeopleRoles (PersonID, RoleID) VALUES")
    vals = []
    for person_name, role_name in ROSTER_ROLES:
        vals.append("  ((SELECT PersonID FROM People WHERE Name=%s), "
                    "(SELECT RoleID FROM Roles WHERE Name=%s))"
                    % (_sq(person_name), _sq(role_name)))
    L.append(",\n".join(vals) + ";")
    L.append("")

    text = "\n".join(L)
    if "--check" in sys.argv:
        cur = io.open(out, encoding="utf-8").read() if os.path.exists(out) else ""
        if cur != text:
            print("seed_milestones.sql is STALE; re-run without --check")
            return 1
        print("seed_milestones.sql is current (%d milestones)" % len(MILESTONES))
        return 0

    io.open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s (%d milestones, %d outcome states)"
          % (out, len(MILESTONES), len(OUTCOME_STATE)))
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
