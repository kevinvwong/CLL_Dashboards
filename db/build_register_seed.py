"""Generate db/seed_register.sql FROM the Initiative Dashboard Register.

The register (`Initiative Dashboard Register.xlsx`, sheet "Team KPI Register")
is the current canon for the Team Initiatives: it carries the named owners, a
description per row, a Goals 1-5 alignment matrix, and the eight Dean KPI 27
linkage columns, plus an 11-row Dean layer.

Join by NAME, not position: the canon reorder previously paired eight rows with
the wrong target. Fail loudly on an unmatched title; never fall back to position.

Run:  python db/build_register_seed.py           # writes db/seed_register.sql
      python db/build_register_seed.py --check   # fail if the output differs
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seed_register.sql")
WORKBOOK = os.environ.get(
    "CLL_REGISTER_XLSX",
    os.path.join(os.path.expanduser("~"), "Downloads",
                 "Initiative Dashboard Register.xlsx"))

#: register title (normalized) -> committed TeamInitiatives.Title (normalized),
#: for the five rows the register reworded. Chosen by word overlap, verified
#: against the register itself (see git history).
RENAMED = {
    "empowerfacultytoengageininnovativeprogramdevelopmentandalignworkfunctions":
        "empowerallfacultytoengageininnovativeprogramdevelopment",
    "fillopenrankfacultypositionsandalignfacultyworkwithstrategy2035":
        "fillmultiplefacultypositionsandalignexistingfacultywork",
    "standupinnovativetraditionalacademicprograms":
        "standupinnovativeyettraditionalacademicprograms",
    "growtheinstitutewidefacultynetworkengagedincllprograms":
        "networkacrosscampustogrowfacultyparticipationincllprograms",
    "buildcourseworkasreusablelearningexperiences":
        "buildacademiccourseworkasreusableisolatedlearningexperiences",
}

#: The Goals 1-5 register columns.
GOAL_COLS = list(range(9, 14))

#: The eight Dean KPI 27 register columns, in order 1..8.
DEAN27_COLS = list(range(14, 22))

#: The register's priority spellings -> the committed Priorities.Code.
PRIORITY_BY_TITLE = {
    "Culture & Learning": "P06",
    "Quality at Scale": "P04",
    "One Shared Identity": "P01",
    "Champion Innovation": "P02",
    "Integrated Portfolio & Pathways": "P03",
    "Data-Informed Action": "P05",
}

#: The register's named owners -> (PersonID, team). PersonID 5 (Kevin, the
#: dashboard admin) is deliberately NOT here and is left untouched.
OWNERS = [
    (1, "Bill Gaudelli", "Dean", None),
    (2, "Elizabeth Smith", None, "Learning Infrastructure"),
    (3, "Tim Jacobbe", None, "Learning Experiences"),
    (4, "Mario Herane", None, "Learning Ecosystems"),
]

#: The additional people the register introduces: Learning Futures' two
#: co-owners ("Meltem Alemdar/Grace Flavin" in one cell) and nothing else yet.
NEW_PEOPLE = [
    (6, "Meltem Alemdar", None, "Learning Futures"),
    (7, "Grace Flavin", None, "Learning Futures"),
]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _sq(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def read_register(path=WORKBOOK):
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    rows = [r for r in wb["Team KPI Register"].iter_rows(values_only=True)]
    data = [r for r in rows[4:] if r and r[0] and str(r[0]).strip()]
    team = [r for r in data if not str(r[0]).strip().startswith("Dean")]
    dean = [r for r in data if str(r[0]).strip().startswith("Dean")]
    return team, dean


def pct(value):
    """The register's 0-1 completion as 0-100; blank/0 -> 0."""
    if value in (None, ""):
        return 0
    return int(round(float(value) * 100))


def split_owners(raw: str) -> list:
    """The people named in an owner cell, split on '/'.

    Most rows name one owner. Learning Futures names two in one cell
    ("Meltem Alemdar/Grace Flavin"); the first is the accountable lead.
    """
    return [p.strip() for p in re.split(r"[/,]", raw or "") if p.strip()]


def build(path=WORKBOOK, out=OUT):
    team, dean = read_register(path)

    import sqlite3
    con = sqlite3.connect(os.path.join(HERE, "..", "cll_initiatives.db"))
    committed = {norm(t): (code, mid) for mid, t, code in
                 con.execute("SELECT MIId, Title, Code FROM TeamInitiatives")}
    con.close()

    unmatched = []
    team_rows = []
    for r in team:
        key = norm(r[2])
        hit = committed.get(key)
        if hit is None and key in RENAMED:
            hit = committed.get(norm(RENAMED[key]))
        if hit is None:
            unmatched.append((str(r[0]), str(r[2])))
        team_rows.append({
            "team": str(r[0]).strip(), "title": str(r[2]).strip(),
            "prio": str(r[3] or "").strip(), "sec": str(r[4] or "").strip(),
            "target": r[5], "owner_raw": str(r[7] or "").strip(),
            "owners": split_owners(str(r[7] or "")), "desc": r[8],
            "goals": [i - 9 + 1 for i in GOAL_COLS if r[i] not in (None, "")],
            "dean27": [i - 14 + 1 for i in DEAN27_COLS if r[i] not in (None, "")],
            "code": hit[0] if hit else None,
        })
    if unmatched:
        for sec, title in unmatched:
            sys.stderr.write("UNMATCHED register row [%s]: %r\n" % (sec, title))
        sys.stderr.write("Add a RENAMED entry rather than falling back to position.\n")
        return 1

    dean_rows = []
    for r in dean:
        fy = 26 if "26" in str(r[0]) else 27
        dean_rows.append({
            "fy": fy, "num": int(str(r[1])), "title": str(r[2]).strip(),
            "desc": r[8], "prio": str(r[3] or "").strip(), "pct": pct(r[6]),
        })

    L = ["-- GENERATED by db/build_register_seed.py from",
         "-- 'Initiative Dashboard Register.xlsx'. Do not hand-edit.",
         "-- Rows are matched to the committed rows by NAME, not position.", ""]

    # People: update in place (never delete - OwnerID/EnteredByID/AuditLog hold
    # FKs onto these rows), preserving Kevin (PersonID 5) the dashboard admin.
    L.append("-- Named owners (the register's 'Named Owner' column).")
    for pid, name, title, team in OWNERS + NEW_PEOPLE:
        team_sql = ("(SELECT TeamID FROM Teams WHERE Name=%s)" % _sq(team)
                    if team else "NULL")
        title_sql = _sq(title) if title else "NULL"
        L.append("INSERT INTO People (PersonID, Name, Title, TeamID) "
                 "VALUES (%d, %s, %s, %s) "
                 "ON CONFLICT(PersonID) DO UPDATE SET "
                 "Name=excluded.Name, Title=excluded.Title, TeamID=excluded.TeamID;"
                 % (pid, _sq(name), title_sql, team_sql))
    L.append("")

    # TeamInitiatives: title, description, owner, team, target from the register.
    L.append("-- Title, description, owner, team and target from the register.")
    for r in team_rows:
        L.append("UPDATE TeamInitiatives SET Title=%s, Description=%s, "
                 "ProposedTarget=%s, "
                 "OwnerID=(SELECT PersonID FROM People WHERE Name=%s), "
                 "TeamID=(SELECT TeamID FROM Teams WHERE Name=%s) WHERE Code=%s;"
                 % (_sq(r["title"]), _sq(r["desc"]), _sq(r["target"]),
                    _sq(r["owners"][0] if r["owners"] else None),
                    _sq(r["team"]), _sq(r["code"])))
    L.append("")

    # Co-owners: everyone named after the lead on a row (Learning Futures names
    # two). The lead is TeamInitiatives.OwnerID; the rest go here.
    L.append("-- Additional co-owners (rows naming more than one person).")
    L.append("DELETE FROM TeamInitiativeCoOwners;")
    covals = []
    for r in team_rows:
        for name in r["owners"][1:]:
            covals.append("  ((SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code=%s), "
                          "(SELECT PersonID FROM People WHERE Name=%s))"
                          % (_sq(r["code"]), _sq(name)))
    if covals:
        L.append("INSERT INTO TeamInitiativeCoOwners (TeamInitiativeID, PersonID) VALUES")
        L.append(",\n".join(covals) + ";")
    L.append("")

    # Priorities: replace with primary + secondary, IsPrimary set.
    L.append("DELETE FROM TeamInitiativePriorities;")
    L.append("INSERT INTO TeamInitiativePriorities "
             "(TeamInitiativeID, PriorityID, IsPrimary) VALUES")
    pvals = []
    for r in team_rows:
        for label, is_primary in ((r["prio"], 1), (r["sec"], 0)):
            if not label:
                continue
            code = PRIORITY_BY_TITLE.get(label)
            if code is None:
                raise SystemExit("unmapped priority label: %r" % label)
            pvals.append("  ((SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code=%s), "
                         "(SELECT PriorityID FROM Priorities WHERE Code=%s), %d)"
                         % (_sq(r["code"]), _sq(code), is_primary))
    L.append(",\n".join(pvals) + ";")
    L.append("")

    # Dean Initiatives.
    L.append("-- Dean Initiatives (FY26 complete, FY27 in flight).")
    L.append("INSERT INTO DeanInitiatives (FiscalYear, Code, Title, Description, "
             "PriorityID, PercentComplete) VALUES")
    dvals = []
    for d in dean_rows:
        code = "D%d-%d" % (d["fy"], d["num"])
        pcode = PRIORITY_BY_TITLE.get(d["prio"])
        dvals.append("  (%d, %s, %s, %s, (SELECT PriorityID FROM Priorities WHERE Code=%s), %d)"
                      % (d["fy"], _sq(code), _sq(d["title"]), _sq(d["desc"]),
                         _sq(pcode), d["pct"]))
    L.append(",\n".join(dvals) + ";")
    L.append("")

    # MI -> Goal edges.
    L.append("-- Team Initiative -> Strategy Goal edges (register Goals columns).")
    L.append("DELETE FROM TeamInitiativeGoals;")
    L.append("INSERT INTO TeamInitiativeGoals (TeamInitiativeID, GoalID) VALUES")
    gvals = []
    for r in team_rows:
        for g in r["goals"]:
            gvals.append("  ((SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code=%s), "
                         "(SELECT GoalID FROM Goals WHERE GoalNumber=%d))"
                         % (_sq(r["code"]), g))
    L.append(",\n".join(gvals) + ";")
    L.append("")

    # MI -> Dean FY27 edges.
    L.append("-- Team Initiative -> Dean FY27 edges (the register's X-matrix).")
    L.append("INSERT INTO TeamInitiativeDeanLinks (TeamInitiativeID, DeanInitiativeID) VALUES")
    lvals = []
    for r in team_rows:
        for n in r["dean27"]:
            lvals.append("  ((SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code=%s), "
                         "(SELECT DeanInitiativeID FROM DeanInitiatives WHERE Code='D27-%d'))"
                         % (_sq(r["code"]), n))
    L.append(",\n".join(lvals) + ";")
    L.append("")

    text = "\n".join(L)
    if "--check" in sys.argv:
        cur = io.open(out, encoding="utf-8").read() if os.path.exists(out) else ""
        if cur != text:
            print("seed_register.sql is STALE; re-run without --check")
            return 1
        print("seed_register.sql is current (%d MI, %d Dean, %d goal links, %d dean links)"
              % (len(team_rows), len(dean_rows), len(gvals), len(lvals)))
        return 0

    io.open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s" % out)
    print("  MI %d | Dean %d | goal links %d | dean links %d"
          % (len(team_rows), len(dean_rows), len(gvals), len(lvals)))
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
