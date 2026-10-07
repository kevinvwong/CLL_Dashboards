"""Reconcile the canon workbook with the prototype's rows, keyed by NAME.

Source of truth: `CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx`,
supplied 2026-10-06 as the most recent canon. Read directly, not retyped.

The canon gives each Major Initiative an id (MI-001..MI-029), an exact title, a
source area and a Strategy Alignment. The prototype's `data.js` gives the *same
29 rows* a target, initiatives and priority links. We need both on one row.

THE JOIN KEY IS THE NAME, NOT THE POSITION. `build_team_layer.py` writes each row
at a Code derived from the *prototype's* order ('5-01'..'5-09'), and the target
travels with it. The first version of this script derived a Code from the
*canon's* order and assumed the two orders agreed. They do not: the canon
reorders source area "Academic Affairs" (the prototype's area 5), so matching by
position paired each title with the next row's target and shifted eight rows -
visible as MI-021 carrying MI-022's target. A name join cannot drift when a
source reorders rows.

Run:  python db/build_canon_links.py           # writes db/seed_canon_links.sql
      python db/build_canon_links.py --check   # fail if the output differs
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seed_canon_links.sql")

WORKBOOK = os.path.join(os.path.expanduser("~"), "Downloads",
                        "CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx")

#: The prototype's data.js, read for its row names. Same env default as
#: build_team_layer.py.
PROTO = os.path.join(os.environ.get("TEMP", "/tmp"), "opencode",
                     "dean-proto", "data.js")

#: Canon name -> prototype name, for the rows the canon renamed. Keyed and valued
#: by a normalised name (see `norm`). Each pair was chosen by word overlap, not
#: position: it shares most of its significant words, and its next-best candidate
#: shares almost none (see the build notes in git history for the scores).
RENAMED = {
    "empowerallfacultytoengageininnovativeprogramdevelopment":
        "empowerfacultytoengageininnovativeprogramdevelopmentandalignworkfunctions",
    "fillmultiplefacultypositionsandalignexistingfacultywork":
        "fillopenrankfacultypositionsandalignfacultyworkwithstrategy2035",
    "standupinnovativeyettraditionalacademicprograms":
        "standupinnovativetraditionalacademicprograms",
    "networkacrosscampustogrowfacultyparticipationincllprograms":
        "growtheinstitutewidefacultynetworkengagedincllprograms",
    "buildacademiccourseworkasreusableisolatedlearningexperiences":
        "buildcourseworkasreusablelearningexperiences",
}


def _sq(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def norm(s: str) -> str:
    """A name reduced to letters and digits, for a forgiving exact match."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def read_canon(path=WORKBOOK):
    """The Initiatives sheet: [(MI-id, name, source_area, alignment), ...]."""
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    rows = [r for r in wb["Initiatives"].iter_rows(values_only=True)
            if any(v is not None for v in r)]
    out = []
    for r in rows:
        mid = str(r[0] or "").strip()
        if re.match(r"^MI-\d+$", mid):
            out.append((mid, str(r[1] or "").strip(),
                        str(r[2] or "").strip(), str(r[3] or "").strip()))
    return out


def read_proto_names(path=PROTO):
    """The prototype's rows as {Code: Title}, in the prototype's own order."""
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r"const GOALS = \[(.*?)\n\];", t, re.S)
    calls = re.findall(
        r'goal\(SOURCE_AREAS\[(\d+)\],\s*"(\d+)",\s*"((?:[^"\\]|\\.)*)"',
        m.group(1))
    return {"%s-%s" % (int(a) + 1, n): title for a, n, title in calls}


def goals_from_alignment(text: str) -> list:
    """The goal numbers an alignment string names.

    'Goal 5' -> [5]; 'Goals 3 + 4 + 5' -> [3,4,5]; 'Goals 1-5' -> [1,2,3,4,5];
    'Goals 1, 2, 3, 4' -> [1,2,3,4]. A range expands.
    """
    text = text or ""
    m = re.search(r"Goals?\s+([\d\s,+\-–]+)", text)
    if not m:
        return []
    span = m.group(1)
    rng = re.search(r"(\d)\s*[-–]\s*(\d)", span)
    if rng:
        return list(range(int(rng.group(1)), int(rng.group(2)) + 1))
    return sorted({int(n) for n in re.findall(r"\d", span)})


def build(path=WORKBOOK, out=OUT, proto_path=PROTO):
    canon = read_canon(path)
    proto_by_name = {norm(name): code for code, name in read_proto_names(proto_path).items()}

    rows = []
    unmatched = []
    for mid, name, sa, align in canon:
        key = norm(name)
        code = proto_by_name.get(key)
        if code is None and key in RENAMED:
            code = proto_by_name.get(norm(RENAMED[key]))
        if code is None:
            unmatched.append((mid, name))
        rows.append({
            "mi_id": mid, "name": name, "source_area": sa,
            "alignment": align, "code": code,
            "goals": goals_from_alignment(align),
        })

    if unmatched:
        for mid, name in unmatched:
            sys.stderr.write("UNMATCHED canon row %s: %r\n" % (mid, name))
        sys.stderr.write(
            "A canon row matched no prototype name or rename. The canon may have "
            "reordered or renamed rows again; add a RENAMED entry rather than "
            "letting the join fall back to position.\n")
        return 1

    L = ["-- GENERATED by db/build_canon_links.py from",
         "-- CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx.",
         "-- Do not hand-edit. Read from the workbook, not retyped.",
         "-- Rows are matched to the prototype by NAME, not position.",
         ""]
    L.append("-- The canon's stable key and exact title for each Major Initiative.")
    for r in rows:
        L.append("UPDATE MajorInitiatives SET MIId=%s, Title=%s WHERE Code=%s;"
                 % (_sq(r["mi_id"]), _sq(r["name"]), _sq(r["code"])))
    L.append("")
    L.append("-- The MI -> Goal edge, parsed from each alignment string.")
    L.append("INSERT INTO MajorInitiativeGoals (MajorInitiativeID, GoalID) VALUES")
    vals = []
    for r in rows:
        for g in r["goals"]:
            vals.append("  ((SELECT MajorInitiativeID FROM MajorInitiatives WHERE Code=%s), "
                        "(SELECT GoalID FROM Goals WHERE GoalNumber=%d))"
                        % (_sq(r["code"]), g))
    L.append(",\n".join(vals) + ";")
    L.append("")

    text = "\n".join(L)
    if "--check" in sys.argv:
        current = io.open(out, encoding="utf-8").read() if os.path.exists(out) else ""
        if current != text:
            print("seed_canon_links.sql is STALE; re-run without --check")
            return 1
        print("seed_canon_links.sql is current (%d MI rows, %d goal links)"
              % (len(rows), len(vals)))
        return 0

    io.open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s" % out)
    print("  MI rows: %d | goal links: %d" % (len(rows), len(vals)))
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
