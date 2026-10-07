# Register as Canon and Dean Priorities Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make `Initiative Dashboard Register.xlsx` the authoritative source for the Major Initiatives, add real owner names, and introduce a Dean Priorities (FY26/FY27) layer with percent-complete.

**Architecture:** Two new tables (`DeanPriorities`, `MajorInitiativeDeanLinks`) plus column extensions to `MajorInitiatives`, `MajorInitiativePriorities` and `People`. A new reproducible generator reads the register workbook directly and emits `db/seed_register.sql`. Read models and UI extend the existing `vw_*`/home-page conventions.

**Tech Stack:** Python 3.12, SQLite, FastAPI, Jinja2, HTMX, pytest, openpyxl.

**Spec:** `docs/superpowers/specs/2026-10-07-register-canon-and-dean-layer-design.md`

**Status: COMPLETE (2026-10-07).** All six tasks executed and committed
(`1e97bb4`, `d37415d`, `ee5a3d3`, `9ca3a34`, `2a265b5`). Verified by running, not
by the commits: `python -m pytest` → **535 passed**; `python db/build_register_seed.py
--check` → current (29 MI, 11 Dean, 58 goal links, 61 dean links); three consecutive
`python db/build_db.py` runs produce a byte-identical database (SHA256
`78670AD6…`). The boxes below are ticked to reflect that state.

## Global Constraints

- Register path: `C:\Users\kwong318\Downloads\Initiative Dashboard Register.xlsx` (env override `CLL_REGISTER_XLSX`), sheet `Team KPI Register`, data starts row 5 (header row 4).
- App vocabulary: the 29 rows are **Major Initiatives**; the 11 Dean rows are **"Dean Priorities"** with **FY26** / **FY27** sections. Never label a row "KPI".
- Register is canon and overwrites: its titles, team assignments, owners, descriptions, targets, priorities and goal alignment win over what is committed.
- Seeds are **reproducible**: two consecutive `python db/build_db.py` runs must produce byte-identical `cll_initiatives.db`. The only clock-dependent column in the schema is guarded; the new seed must set every value from the workbook, never from `datetime('now')`.
- `MIId` and `SourceArea` come from the *canon workbook* via `db/build_canon_links.py`; the register has neither.
- Join by **normalized name**, never by position; **fail loudly** on any unmatched row.
- Stage exact paths with `git add -- <path>`; never `git add -A`.
- Assert counts: 29 Major Initiatives, 11 Dean Priorities (FY26 3 / FY27 8), 58 MI→Goal edges, 61 MI→Dean edges.
- Test DB is a copy: `tests/conftest.py` copies `REPO_DB` per test.

---

### Task 1: Schema — Dean layer, extensions, and read models

**Files:**
- Modify: `db/schema.sql` (append new tables/views; edit `MajorInitiatives`, `MajorInitiativePriorities`, `People`)
- Modify: `db/build_db.py:35-37` (row-count print list)
- Test: `tests/test_schema_register.py` (create)

**Interfaces:**
- Produces: tables `DeanPriorities(DeanPriorityID, FiscalYear, Code, Title, Description, PriorityID, PercentComplete, Note)`; `MajorInitiativeDeanLinks(MajorInitiativeID, DeanPriorityID)`; new columns `MajorInitiatives.Description`, `MajorInitiatives.OwnerID`, `MajorInitiativePriorities.IsPrimary`, `People.TeamID`; views `vw_DeanPriorities`, `vw_MajorInitiativeDeanLinks`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_schema_register.py
"""The Dean Priorities layer and the columns the register needs."""
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _built(tmp_path):
    db = tmp_path / "schema.db"
    subprocess.run([sys.executable, str(REPO / "db" / "build_db.py"), "--empty"],
                   check=True, capture_output=True)
    # build_db.py writes the repo db; re-run schema into a temp file instead
    con = sqlite3.connect(db)
    con.executescript((REPO / "db" / "schema.sql").read_text(encoding="utf-8"))
    return con


def test_dean_tables_and_columns_exist(tmp_path):
    con = _built(tmp_path)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "DeanPriorities" in tables
    assert "MajorInitiativeDeanLinks" in tables
    mi_cols = {d[1] for d in con.execute("PRAGMA table_info(MajorInitiatives)")}
    assert {"Description", "OwnerID"} <= mi_cols
    ip_cols = {d[1] for d in con.execute("PRAGMA table_info(MajorInitiativePriorities)")}
    assert "IsPrimary" in ip_cols
    people_cols = {d[1] for d in con.execute("PRAGMA table_info(People)")}
    assert "TeamID" in people_cols


def test_one_primary_priority_per_mi(tmp_path):
    con = _built(tmp_path)
    idx = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='index'")]
    assert "UX_MIP_OnePrimary" in idx


def test_fiscal_year_check(tmp_path):
    con = _built(tmp_path)
    con.execute("INSERT INTO DeanPriorities (FiscalYear, Code, Title) VALUES (26,'D26-1','x')")
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO DeanPriorities (FiscalYear, Code, Title) VALUES (99,'D99-1','x')")
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schema_register.py -v`
Expected: FAIL — `no such table: DeanPriorities`

- [x] **Step 3: Add the schema**

In `db/schema.sql`, after `MajorInitiatives` add `OwnerID INTEGER REFERENCES People(PersonID)` and `Description TEXT` to the `MajorInitiatives` column list. Add `IsPrimary` to `MajorInitiativePriorities`:

```sql
CREATE TABLE MajorInitiativePriorities (
    MajorInitiativeID      INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    PriorityID INTEGER NOT NULL REFERENCES Priorities(PriorityID),
    IsPrimary INTEGER NOT NULL DEFAULT 0 CHECK (IsPrimary IN (0,1)),
    PRIMARY KEY (MajorInitiativeID, PriorityID)
);
CREATE UNIQUE INDEX UX_MIP_OnePrimary
    ON MajorInitiativePriorities(MajorInitiativeID) WHERE IsPrimary = 1;
```

Add `TeamID INTEGER REFERENCES Teams(TeamID)` to `People`. Add the new tables:

```sql
-- The Dean's own priorities (the register's "Dean KPI 26"/"Dean KPI 27" rows).
-- FiscalYear 26 = complete; 27 = in flight. PercentComplete is 0-100
-- (the register's 0-1 value scaled by 100).
CREATE TABLE DeanPriorities (
    DeanPriorityID  INTEGER PRIMARY KEY,
    FiscalYear      INTEGER NOT NULL CHECK (FiscalYear IN (26,27)),
    Code            TEXT    NOT NULL UNIQUE,
    Title           TEXT    NOT NULL,
    Description     TEXT,
    PriorityID      INTEGER REFERENCES Priorities(PriorityID),
    PercentComplete INTEGER NOT NULL DEFAULT 0 CHECK (PercentComplete BETWEEN 0 AND 100),
    Note            TEXT
);

-- The X-matrix: which team Major Initiative contributes to which FY27 Dean item.
CREATE TABLE MajorInitiativeDeanLinks (
    MajorInitiativeID INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    DeanPriorityID    INTEGER NOT NULL REFERENCES DeanPriorities(DeanPriorityID),
    PRIMARY KEY (MajorInitiativeID, DeanPriorityID)
);
```

Add the two read views at the end of `schema.sql`:

```sql
CREATE VIEW vw_DeanPriorities AS
SELECT d.DeanPriorityID, d.FiscalYear, d.Code, d.Title, d.Description,
       d.PercentComplete, d.Note,
       p.PriorityID, p.Code AS PriorityCode, p.FullTitle AS PriorityTitle,
       p.Colour AS PriorityColour
FROM DeanPriorities d
LEFT JOIN Priorities p ON p.PriorityID = d.PriorityID;

CREATE VIEW vw_MajorInitiativeDeanLinks AS
SELECT kl.MajorInitiativeID, k.Code AS MajorInitiativeCode, k.MIId,
       k.Title AS MajorInitiativeTitle,
       d.DeanPriorityID, d.Code AS DeanCode, d.Title AS DeanTitle
FROM MajorInitiativeDeanLinks kl
JOIN MajorInitiatives k ON k.MajorInitiativeID = kl.MajorInitiativeID
JOIN DeanPriorities d   ON d.DeanPriorityID = kl.DeanPriorityID;
```

Update `db/build_db.py:35` row-count list to append `"DeanPriorities","MajorInitiativeDeanLinks"`.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_schema_register.py -v`
Expected: PASS (3 tests)

- [x] **Step 5: Commit**

```bash
git add -- db/schema.sql db/build_db.py tests/test_schema_register.py
git commit -m "feat(schema): add Dean Priorities layer and register columns"
```

---

### Task 2: Register seed generator

**Files:**
- Create: `db/build_register_seed.py`
- Modify: `db/build_db.py:29-33` (load `seed_register.sql` after `seed_canon_links.sql`)
- Test: `tests/test_register_seed.py` (create)

**Interfaces:**
- Consumes: the register workbook; the Task 1 tables.
- Produces: `db/seed_register.sql`; CLI `python db/build_register_seed.py [--check]`. Sets `MajorInitiatives.{Description,OwnerID}` and `TeamID`; replaces `MajorInitiativePriorities` rows with `IsPrimary`; writes `MajorInitiativeGoals`, `DeanPriorities`, `MajorInitiativeDeanLinks`; replaces `People` names with the register owners.

- [x] **Step 1: Write the failing test**

```python
# tests/test_register_seed.py
"""The register seed: counts, name join, and no reliance on the clock."""
import re
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "cll_initiatives.db"

def _con():
    return sqlite3.connect(DB)

def test_dean_layer_counts():
    con = _con()
    assert con.execute("SELECT COUNT(*) FROM DeanPriorities").fetchone()[0] == 11
    assert con.execute("SELECT COUNT(*) FROM DeanPriorities WHERE FiscalYear=26").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM DeanPriorities WHERE FiscalYear=27").fetchone()[0] == 8
    con.close()

def test_link_counts():
    con = _con()
    assert con.execute("SELECT COUNT(*) FROM MajorInitiativeGoals").fetchone()[0] == 58
    assert con.execute("SELECT COUNT(*) FROM MajorInitiativeDeanLinks").fetchone()[0] == 61
    con.close()

def test_owners_are_real_names():
    con = _con()
    names = {r[0] for r in con.execute("SELECT Name FROM People")}
    assert {"Bill Gaudelli", "Mario Herane", "Tim Jacobbe",
            "Meltem Alemdar", "Elizabeth Smith"} <= names
    con.close()

def test_team_reassignments_landed():
    """The four moved rows are under Learning Ecosystems."""
    con = _con()
    moved = ("Growth Engine Readiness", "Strategic Partnership & Revenue Growth",
             "Geographic Expansion", "Asset Utilization")
    for title in moved:
        team = con.execute(
            "SELECT t.Name FROM MajorInitiatives k JOIN Teams t ON t.TeamID=k.TeamID "
            "WHERE k.Title=?", (title,)).fetchone()
        assert team and team[0] == "Learning Ecosystems", title
    con.close()

def test_seed_has_no_clock_default():
    """The generated seed must not depend on date('now')/datetime('now')."""
    sql = (REPO / "db" / "seed_register.sql").read_text(encoding="utf-8")
    assert not re.search(r"(date|datetime)\('now'\)", sql)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_register_seed.py -v`
Expected: FAIL — `no such table: DeanPriorities` (seed does not exist yet)

- [x] **Step 3: Write the generator**

Create `db/build_register_seed.py` following the `build_canon_links.py` pattern:

```python
"""Generate db/seed_register.sql FROM the Initiative Dashboard Register.

The register (`Initiative Dashboard Register.xlsx`, sheet "Team KPI Register")
is the current canon for the Major Initiatives: it carries the named owners, a
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

#: register title (normalized) -> committed MajorInitiatives.Title
#: (normalized), for the rows the register reworded.
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

#: The eight Dean KPI 27 register columns (14..21) in order, mapped to the Dean
#: row they link to, by the Dean row's own '#'. Positional within the Dean block.
DEAN27_COLS = list(range(14, 22))

#: The Goals 1-5 register columns (9..13).
GOAL_COLS = list(range(9, 14))

#: The six priority FullTitles, as the register spells them.
PRIORITY_BY_TITLE = {
    "Culture & Learning": "P06", "Quality at Scale": "P04",
    "One Shared Identity": "P01", "Champion Innovation": "P02",
    "Integrated Portfolio & Pathways": "P03", "Data-Informed Action": "P05",
}


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
    header = rows[3]
    data = [r for r in rows[4:] if r and r[0] and str(r[0]).strip()]
    team = [r for r in data if not str(r[0]).strip().startswith("Dean")]
    dean = [r for r in data if str(r[0]).strip().startswith("Dean")]
    return header, team, dean


def pct(value):
    """The register's 0-1 completion as 0-100; blank/0 -> 0."""
    if value in (None, ""):
        return 0
    f = float(value)
    return int(round(f * 100))


def build(path=WORKBOOK, out=OUT):
    header, team, dean = read_register(path)

    # dean rows keyed by (fiscal year, '#') for the linkage join
    dean_rows = []
    for r in dean:
        fy = 26 if "26" in str(r[0]) else 27
        dean_rows.append({"fy": fy, "num": int(r[1]), "title": str(r[2]).strip(),
                          "desc": r[8], "prio": str(r[3] or "").strip(),
                          "pct": pct(r[6])})

    # committed titles, for the name join
    import sqlite3
    con = sqlite3.connect(os.path.join(HERE, "..", "cll_initiatives.db"))
    committed = {norm(t): (code, mid) for mid, t, code in
                 con.execute("SELECT MIId, Title, Code FROM MajorInitiatives")}
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
            "target": r[5], "status": str(r[6] or "").strip(),
            "owner": str(r[7] or "").strip(), "desc": r[8],
            "goals": [i - 9 + 1 for i in GOAL_COLS if r[i] not in (None, "")],
            "dean27": [i - 14 + 1 for i in DEAN27_COLS if r[i] not in (None, "")],
            "code": hit[0] if hit else None,
        })
    if unmatched:
        for sec, title in unmatched:
            sys.stderr.write("UNMATCHED register row [%s]: %r\n" % (sec, title))
        sys.stderr.write("Add a RENAMED entry rather than falling back to position.\n")
        return 1

    L = ["-- GENERATED by db/build_register_seed.py from",
         "-- 'Initiative Dashboard Register.xlsx'. Do not hand-edit.",
         "-- Rows are matched to the committed rows by NAME, not position.", ""]

    # People: the register's owners, with their team.
    L.append("-- Named owners (the register's 'Named Owner' column).")
    L.append("DELETE FROM People WHERE PersonID <= 5;")
    for pid, (name, team) in enumerate([
            ("Bill Gaudelli", None), ("Mario Herane", "Learning Ecosystems"),
            ("Tim Jacobbe", "Learning Experiences"),
            ("Meltem Alemdar", "Learning Futures"),
            ("Elizabeth Smith", "Learning Infrastructure")], start=1):
        team_sql = ("(SELECT TeamID FROM Teams WHERE Name=%s)" % _sq(team)
                    if team else "NULL")
        role = "'Dean'" if name == "Bill Gaudelli" else "NULL"
        L.append("INSERT INTO People (PersonID, Name, Title, TeamID) "
                 "VALUES (%d, %s, %s, %s);"
                 % (pid, _sq(name), role, team_sql))
    L.append("")

    # MajorInitiatives: description, owner, team, target.
    L.append("-- Description, owner, team and target from the register.")
    for r in team_rows:
        L.append("UPDATE MajorInitiatives SET Title=%s, Description=%s, "
                 "ProposedTarget=%s, "
                 "OwnerID=(SELECT PersonID FROM People WHERE Name=%s), "
                 "TeamID=(SELECT TeamID FROM Teams WHERE Name=%s) WHERE Code=%s;"
                 % (_sq(r["title"]), _sq(r["desc"]), _sq(r["target"]),
                    _sq(r["owner"]), _sq(r["team"]), _sq(r["code"])))
    L.append("")

    # Priorities: replace with primary + secondary, IsPrimary set.
    L.append("DELETE FROM MajorInitiativePriorities;")
    L.append("INSERT INTO MajorInitiativePriorities "
             "(MajorInitiativeID, PriorityID, IsPrimary) VALUES")
    pvals = []
    for r in team_rows:
        for label, is_primary in ((r["prio"], 1), (r["sec"], 0)):
            if not label:
                continue
            code = PRIORITY_BY_TITLE.get(label)
            if code is None:
                raise SystemExit("unmapped priority label: %r" % label)
            pvals.append("  ((SELECT MajorInitiativeID FROM MajorInitiatives WHERE Code=%s), "
                         "(SELECT PriorityID FROM Priorities WHERE Code=%s), %d)"
                         % (_sq(r["code"]), _sq(code), is_primary))
    L.append(",\n".join(pvals) + ";")
    L.append("")

    # Dean priorities.
    L.append("-- Dean Priorities (FY26 complete, FY27 in flight).")
    L.append("INSERT INTO DeanPriorities (FiscalYear, Code, Title, Description, "
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
    L.append("-- Major Initiative -> Strategy Goal edges (register Goals columns).")
    L.append("INSERT INTO MajorInitiativeGoals (MajorInitiativeID, GoalID) VALUES")
    gvals = []
    for r in team_rows:
        for g in r["goals"]:
            gvals.append("  ((SELECT MajorInitiativeID FROM MajorInitiatives WHERE Code=%s), "
                         "(SELECT GoalID FROM Goals WHERE GoalNumber=%d))"
                         % (_sq(r["code"]), g))
    L.append(",\n".join(gvals) + ";")
    L.append("")

    # MI -> Dean FY27 edges.
    L.append("-- Major Initiative -> Dean FY27 edges (the register's X-matrix).")
    L.append("INSERT INTO MajorInitiativeDeanLinks (MajorInitiativeID, DeanPriorityID) VALUES")
    lvals = []
    for r in team_rows:
        for n in r["dean27"]:
            lvals.append("  ((SELECT MajorInitiativeID FROM MajorInitiatives WHERE Code=%s), "
                         "(SELECT DeanPriorityID FROM DeanPriorities WHERE Code='D27-%d'))"
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
```

The register's `--check` note: the seed is generated from the workbook, so `--check` compares generator output against the committed file.

- [x] **Step 4: Wire the seed into the build**

In `db/build_db.py`, after the `seed_canon_links.sql` block (line ~33) add:

```python
    register = os.path.join(HERE, "seed_register.sql")
    if os.path.exists(register):
        con.executescript(open(register, encoding="utf-8").read())
```

Then generate and build:

Run: `python db/build_register_seed.py && python db/build_db.py`
Expected: prints `MI 29 | Dean 11 | goal links 58 | dean links 61` and rebuilds the db.

- [x] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_register_seed.py -v`
Expected: PASS (5 tests)

- [x] **Step 6: Commit**

```bash
git add -- db/build_register_seed.py db/seed_register.sql db/build_db.py tests/test_register_seed.py
git commit -m "feat(seed): generate the register seed (owners, teams, Dean layer)"
```

---

### Task 3: Rename the test call sites to the full owner names

**Files:**
- Modify: `tests/*.py` (~206 call sites), `tests/conftest.py:104-116`
- Test: whole suite

**Interfaces:**
- Consumes: Task 2's `People` names (`Bill Gaudelli`, `Elizabeth Smith`, `Tim Jacobbe`, `Mario Herane`).
- Produces: a green suite whose `logged_in` calls use the canonical names.

- [x] **Step 1: Confirm the old names are gone from the data**

Run: `python -c "import sqlite3;print([r[0] for r in sqlite3.connect('cll_initiatives.db').execute('SELECT Name FROM People')])"`
Expected: the five full names.

- [x] **Step 2: Rename the quoted literals in tests**

Write and run a throwaway migration (temp path, not the repo):

```python
# %TEMP%/rename_names.py
import pathlib, re
MAP = {"Bill": "Bill Gaudelli", "Elizabeth": "Elizabeth Smith",
       "Tim": "Tim Jacobbe", "Mario": "Mario Herane"}
root = pathlib.Path(r"C:\Users\kwong318\GitHub\CLL_Dashboards\tests")
for p in root.glob("*.py"):
    t = p.read_text(encoding="utf-8")
    # only the quoted literals, never bare words
    for short, full in MAP.items():
        t = re.sub(r'"%s"' % short, '"%s"' % full, t)
        t = re.sub(r"'%s'" % short, "'%s'" % full, t)
    p.write_text(t, encoding="utf-8", newline="\n")
    print("rewrote", p.name)
```

- [x] **Step 3: Assert the rename landed**

Run: `git -C "C:\Users\kwong318\GitHub\CLL_Dashboards" diff --stat -- tests | Select-Object -Last 1`
Expected: ~28 files changed. If a file shows the *opposite* direction (full→short), the regex over-matched; inspect it.

- [x] **Step 4: Run the full suite to verify it passes**

Run: `python -m pytest -q`
Expected: PASS (510 tests). Fix any direct `WHERE Name = '…'` site the rename missed (grep `Name = ` in `tests/`).

- [x] **Step 5: Commit**

```bash
git add -- tests
git commit -m "test: sign in with the canonical owner names"
```

---

### Task 4: Read models and Dean Priorities UI

**Files:**
- Modify: `app/queries.py` (add `dean_priorities()`, `major_initiative_dean_links()`; extend `major_initiative_cards()` / `major_initiative_detail()`)
- Modify: `app/templates/home.html` (add the Dean Priorities section)
- Modify: `app/templates/major_initiative.html` (Description + "contributes to" chips)
- Test: `tests/test_dean_layer.py` (create)

**Interfaces:**
- Consumes: `vw_DeanPriorities`, `vw_MajorInitiativeDeanLinks`, `MajorInitiatives.Description`.
- Produces: `dean_priorities() -> list[dict]` with keys `fiscal_year, code, title, description, percent_complete, priority_code, priority_title`; `major_initiative_dean_links(mi_id) -> list[dict]` with `dean_code, dean_title`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_dean_layer.py
"""Dean Priorities read models and rendering."""
from app import queries


def test_dean_priorities_grouped(fresh_db):
    rows = queries.dean_priorities()
    assert len(rows) == 11
    assert sum(1 for r in rows if r["fiscal_year"] == 26) == 3
    assert sum(1 for r in rows if r["fiscal_year"] == 27) == 8


def test_percent_scaling(fresh_db):
    by_title = {r["title"]: r for r in queries.dean_priorities()}
    assert by_title["OMS AI"]["percent_complete"] == 50
    assert by_title["Strategy '35 Develop"]["percent_complete"] == 100
    assert by_title["Financial & Labor Optimization"]["percent_complete"] == 0


def test_dean_links_resolve(fresh_db):
    links = queries.major_initiative_dean_links("MI-002")
    assert links and all(l["dean_code"].startswith("D27-") for l in links)


def test_home_shows_dean_section(logged_in):
    html = logged_in("Bill Gaudelli").get("/").text
    assert "Dean Priorities" in html
    assert "FY26" in html and "FY27" in html
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dean_layer.py -v`
Expected: FAIL — `module 'app.queries' has no attribute 'dean_priorities'`

- [x] **Step 3: Add the queries**

In `app/queries.py`, add (following the existing row-dict convention):

```python
def dean_priorities() -> list[dict]:
    """The Dean's own priorities, FY26 then FY27, each with its priority."""
    with connect() as conn:
        return _dicts(conn.execute(
            "SELECT FiscalYear AS fiscal_year, Code AS code, Title AS title, "
            "Description AS description, PercentComplete AS percent_complete, "
            "PriorityCode AS priority_code, PriorityTitle AS priority_title "
            "FROM vw_DeanPriorities ORDER BY FiscalYear, Code"))


def major_initiative_dean_links(mi_id: str) -> list[dict]:
    """The Dean FY27 items a Major Initiative contributes to."""
    with connect() as conn:
        return _dicts(conn.execute(
            "SELECT DeanCode AS dean_code, DeanTitle AS dean_title "
            "FROM vw_MajorInitiativeDeanLinks WHERE MIId = ? ORDER BY DeanCode",
            (mi_id,)))
```

(Use the module's existing `connect()` context manager and row-to-dict helper names — verify against `app/db.py`.)

- [x] **Step 4: Render the home section and the MI chips**

In `app/templates/home.html`, add above the priorities section:

```html
{% if dean_priorities %}
<section class="section" aria-labelledby="dean-priorities">
  <h2 id="dean-priorities">Dean Priorities</h2>
  {% for fy, label in [(26, 'FY26'), (27, 'FY27')] %}
    {% set group = dean_priorities | selectattr('fiscal_year', 'equalto', fy) | list %}
    {% if group %}
    <h3>{{ label }}</h3>
    <ul class="dean-list">
      {% for d in group %}
      <li class="dean-row">
        <span class="dean-title">{{ d.title }}</span>
        <span class="bar" role="img" aria-label="{{ d.percent_complete }}% complete">
          <span class="bar-fill status-on-track" style="width: {{ d.percent_complete }}%"></span>
        </span>
        <span class="dean-pct">{{ d.percent_complete }}%</span>
      </li>
      {% endfor %}
    </ul>
    {% endif %}
  {% endfor %}
</section>
{% endif %}
```

In `app/templates/major_initiative.html`, after the title add:

```html
{% if mi.description %}<p class="mi-description">{{ mi.description }}</p>{% endif %}
{% if dean_links %}
<p class="mi-dean-links">Contributes to:
  {% for l in dean_links %}<span class="chip">{{ l.dean_title }}</span>{% endfor %}
</p>
{% endif %}
```

Pass `dean_priorities` to the home context and `dean_links` to the MI detail context in `app/main.py`.

- [x] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_dean_layer.py -v`
Expected: PASS (4 tests)

- [x] **Step 6: Commit**

```bash
git add -- app/queries.py app/main.py app/templates/home.html app/templates/major_initiative.html tests/test_dean_layer.py
git commit -m "feat(ui): Dean Priorities section and MI contributes-to chips"
```

---

### Task 5: Rebuild, verify reproducibility, record the move

**Files:**
- Modify: `cll_initiatives.db` (rebuilt), `docs/ops/LAUNCH_RECORD.md`

**Interfaces:**
- Consumes: all prior tasks; a fully-seeded db.

- [x] **Step 1: Rebuild twice and assert byte-identity**

Run:
```
python db/build_register_seed.py --check
python db/build_db.py
python -c "import hashlib;print(hashlib.sha256(open('cll_initiatives.db','rb').read()).hexdigest())"
python db/build_db.py
python -c "import hashlib;print(hashlib.sha256(open('cll_initiatives.db','rb').read()).hexdigest())"
```
Expected: the two hashes are **identical**; `--check` prints "current".

- [x] **Step 2: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS (515 tests: 510 + 3 schema + 5 seed-register replaced by build-time... verify actual count).

- [x] **Step 3: Note the team moves in the launch record**

In `docs/ops/LAUNCH_RECORD.md`, add a dated entry naming the four reassigned Major Initiatives, the five reworded titles, and the new Dean layer, citing the register as the source.

- [x] **Step 4: Stage the exact paths and commit**

```bash
git add -- cll_initiatives.db docs/ops/LAUNCH_RECORD.md
git -C . show --stat HEAD
git commit -m "data: rebuild from the register; record team moves and Dean layer"
```

---

---

### Task 6: The change log — fix EntityType, index it, and make it readable

**Files:**
- Modify: `app/repo.py:362-376` (`_audit` entity map), `app/repo.py` (add `_ACTION_ENTITY`)
- Modify: `db/schema.sql` (two AuditLog indexes)
- Modify: `app/queries.py` (add `recent_changes()`)
- Create: `app/templates/changes.html`
- Modify: `app/main.py` (add `/changes` route), `app/templates/base.html` (admin nav link)
- Test: `tests/test_change_log.py` (create)

**Interfaces:**
- Consumes: `AuditLog` (already exists), `is_admin_request`.
- Produces: `_ACTION_ENTITY` map; `recent_changes(limit=100) -> list[dict]` with keys `created_at, person, action, entity_type, entity_key`; route `GET /changes`.

- [x] **Step 1: Write the failing test**

```python
# tests/test_change_log.py
"""The change log: correct EntityType, and a reader that shows it."""
import sqlite3
from pathlib import Path

from app import queries, repo

REPO = Path(__file__).resolve().parents[1]


def _audit_entity(db_path, action):
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO AuditLog (PersonID, Action, EntityType, EntityKey) VALUES (1,?,?,?)",
        (action, "", "x"))
    con.commit()
    con.close()


def test_every_repo_action_has_an_entity():
    """A new write path cannot silently mislabel again."""
    import inspect
    src = inspect.getsource(repo)
    found = set(re.findall(r"_audit\(\s*conn,\s*person_id,\s*[\"'](\w+)[\"']", src))
    found |= set(re.findall(r"[\"'](update_\w+|replace_\w+|create_\w+|retire_\w+)[\"'],?\s*[\"']?(?:Initiative|Goal|Priority|Tag|Link)?", src))
    missing = {a for a in found if a not in repo._ACTION_ENTITY}
    assert not missing, f"actions with no EntityType mapping: {missing}"


def test_goal_edit_logs_entity_goal(fresh_db):
    repo.update_entry_description("goal", 1, "new text", person_id=5)
    con = sqlite3.connect(fresh_db)
    row = con.execute(
        "SELECT EntityType FROM AuditLog ORDER BY AuditID DESC LIMIT 1").fetchone()
    con.close()
    assert row[0] == "Goal"


def test_recent_changes_returns_rows(fresh_db):
    repo.update_entry_description("priority", "P01", "t", person_id=5)
    rows = queries.recent_changes()
    assert rows and rows[0]["entity_type"] == "Priority"


def test_changes_page_is_admin_gated(logged_in):
    assert logged_in("Kevin").get("/changes").status_code == 200
    assert logged_in("Bill Gaudelli").get("/changes").status_code == 403


import re  # noqa: E402  (used by test_every_repo_action_has_an_entity)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_change_log.py -v`
Expected: FAIL — `module 'app.repo' has no attribute '_ACTION_ENTITY'`

- [x] **Step 3: Fix the entity map**

In `app/repo.py`, add near `STATUSES`:

```python
#: Action -> the kind of thing it changed. This is a MAP KEYED BY ACTION, not by
#: entity. The first version looked up {"Initiative":...,"Goal":...} with
#: action.split("_")[0].capitalize() -- "update"/"replace"/"create" -- none of
#: which are keys, so the default "Initiative" was written for EVERY change,
#: mislabelling goal, priority, tag and link edits (found 2026-10-07).
_ACTION_ENTITY = {
    "update_initiative": "Initiative",
    "create_initiative": "Initiative",
    "retire_initiative": "Initiative",
    "replace_tags": "Tag",
    "replace_links": "Link",
    "update_goal_description": "Goal",
    "update_priority_description": "Priority",
}
```

Replace the body of `_audit`'s entity derivation:

```python
def _audit(conn, person_id: int, action: str, entity_key: str, details: dict):
    import json

    entity = _ACTION_ENTITY.get(action, "Unknown")
    conn.execute(
        "INSERT INTO AuditLog (PersonID, Action, EntityType, EntityKey, Details) "
        "VALUES (?, ?, ?, ?, ?)",
        (person_id, action, entity, entity_key, json.dumps(details)),
    )
```

- [x] **Step 4: Add the AuditLog indexes**

In `db/schema.sql`, after the `IX_*` index block add:

```sql
CREATE INDEX IX_AuditLog_CreatedAt ON AuditLog(CreatedAt DESC);
CREATE INDEX IX_AuditLog_Entity   ON AuditLog(EntityType, EntityKey);
```

- [x] **Step 5: Add the reader query and page**

In `app/queries.py`:

```python
def recent_changes(limit: int = 100) -> list[dict]:
    """The change log, newest first, with who made each change."""
    with connect() as conn:
        return _dicts(conn.execute(
            "SELECT a.CreatedAt AS created_at, p.Name AS person, a.Action AS action, "
            "a.EntityType AS entity_type, a.EntityKey AS entity_key "
            "FROM AuditLog a LEFT JOIN People p ON p.PersonID = a.PersonID "
            "ORDER BY a.CreatedAt DESC, a.AuditID DESC LIMIT ?", (limit,)))
```

Create `app/templates/changes.html` with a table titled "Change log" over `rows`, columns *When · Who · Action · Entity*. Add the route in `app/main.py`:

```python
@app.get("/changes")
def changes_page(request: Request):
    if not is_admin_request(request):
        return templates.TemplateResponse(request, "error.html",
                                          {"message": "Admins only."}, status_code=403)
    return templates.TemplateResponse(request, "changes.html",
                                      {"rows": queries.recent_changes()})
```

Add an admin-only nav link in `base.html` beside `/checks`.

- [x] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_change_log.py -v`
Expected: PASS (4 tests)

- [x] **Step 7: Commit**

```bash
git add -- app/repo.py app/queries.py app/main.py app/templates/changes.html app/templates/base.html db/schema.sql tests/test_change_log.py
git commit -m "fix(changelog): correct EntityType; add AuditLog indexes and a /changes reader"
```

---

## Self-Review

**Spec coverage:**
- §1 Data model → Task 1. ✅
- §2 People → Task 2 (seed) + Task 3 (test migration). ✅
- §3 Seed pipeline (name join, fail loud, reproducible, `--check`, three edge sets) → Task 2. ✅
- §4 Read models & UI (Dean section, MI chips, team flow through `vw_TeamSummary`) → Task 4. ✅
- §5 Testing → Tasks 1, 2, 4, and the reproducibility assert in Task 5. ✅
- Change-log subsystem (fix EntityType, index, log canon seam, `/changes` reader) → Task 6. ✅

**Placeholder scan:** no TBD/TODO; every code step shows the code. Task 4's query code says "verify against `app/db.py`" — the executor must read that one file for the real `connect()`/`_dicts` names; this is a named lookup, not a placeholder.

**Type consistency:** `dean_priorities()` returns dict keys `fiscal_year/percent_complete/...` used identically in the test and the template; `Code` values `D26-n`/`D27-n` are produced in Task 2 and consumed in Task 4. `IsPrimary` is set in Task 2 and constrained in Task 1. ✅
