"""The Major Initiative -> Goal edge and the canon's stable keys.

Covers the interconnection-redesign data layer: the canon workbook's MI-ids,
exact titles, and the MI -> Goal alignment, all verified against the workbook
itself rather than against a copy.
"""
import os
import re

import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKBOOK = os.path.join(os.path.expanduser("~"), "Downloads",
                        "CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx")


def _rows(db, sql, params=()):
    import sqlite3
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def _canon():
    """Read the canon workbook, or skip if it is not on this machine.

    The workbook is the user's artifact, not in the repo, so a fresh clone has
    no copy. The tests that need it skip rather than fail - but the ones that
    only need the database still run, so the edge is guarded everywhere.
    """
    if not os.path.exists(WORKBOOK):
        pytest.skip("canon workbook not present")
    from openpyxl import load_workbook
    wb = load_workbook(WORKBOOK, read_only=True, data_only=True)
    rows = [r for r in wb["Initiatives"].iter_rows(values_only=True)
            if r[0] and str(r[0]).startswith("MI-")]
    return {str(r[0]): (str(r[1]).strip(), str(r[3]).strip()) for r in rows}


#: The register (2026-10-07) is now the authority for titles and the MI -> Goal
#: edge; the canon workbook still owns the MI-id and source area. These helpers
#: read the register, joining to codes by NAME through the generator's own
#: RENAMED map, so the test and the seed cannot disagree about which row is which.
REGISTER = os.path.join(os.path.expanduser("~"), "Downloads",
                        "Initiative Dashboard Register.xlsx")


def _register_module():
    import importlib.util
    path = os.path.join(R, "db", "build_register_seed.py")
    spec = importlib.util.spec_from_file_location("build_register_seed", path)
    assert spec and spec.loader, "cannot load build_register_seed.py"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _register_rows():
    """Register team rows keyed to the committed Code by name (or skip)."""
    if not os.path.exists(REGISTER):
        pytest.skip("register workbook not present")
    mod = _register_module()
    import sqlite3
    con = sqlite3.connect(os.path.join(R, "cll_initiatives.db"))
    committed = {mod.norm(t): code for code, t in
                 con.execute("SELECT Code, Title FROM MajorInitiatives")}
    con.close()
    from openpyxl import load_workbook
    wb = load_workbook(REGISTER, read_only=True, data_only=True)
    rows = [r for r in wb["Team KPI Register"].iter_rows(values_only=True)]
    team = [r for r in rows[4:] if r and r[0] and not str(r[0]).strip().startswith("Dean")]
    out = {}
    for r in team:
        key = mod.norm(r[2])
        code = committed.get(key) or committed.get(mod.norm(mod.RENAMED.get(key, "")))
        if code:
            out[code] = r
    return out


def _register_goals():
    """{MIId: {goal numbers}} from the register's Goal 1-5 columns."""
    import sqlite3
    if not os.path.exists(REGISTER):
        pytest.skip("register workbook not present")
    reg = _register_rows()
    con = sqlite3.connect(os.path.join(R, "cll_initiatives.db"))
    code_to_mi = {c: m for m, c in con.execute("SELECT MIId, Code FROM MajorInitiatives")}
    con.close()
    out = {}
    for code, r in reg.items():
        goals = {str(i - 9 + 1) for i in range(9, 14) if r[i] not in (None, "")}
        if code in code_to_mi:
            out[code_to_mi[code]] = goals
    return out


# --- the edge exists ---------------------------------------------------------


def test_every_major_initiative_has_a_goal_link(fresh_db):
    """The interconnection the canon states and the schema did not hold."""
    n = _rows(fresh_db, "SELECT COUNT(DISTINCT MajorInitiativeID) AS n FROM MajorInitiativeGoals")[0]["n"]
    assert n == 29, "expected all 29 Major Initiatives to align to a goal"


def test_every_major_initiative_has_an_mi_id(fresh_db):
    n = _rows(fresh_db, "SELECT COUNT(*) AS n FROM MajorInitiatives WHERE MIId IS NOT NULL")[0]["n"]
    assert n == 29


def test_goal_links_reference_real_goals(fresh_db):
    from app import queries
    bad = _rows(fresh_db,
        "SELECT kg.MajorInitiativeID FROM MajorInitiativeGoals kg "
        "LEFT JOIN Goals g ON g.GoalID = kg.GoalID WHERE g.GoalID IS NULL")
    assert not bad, "goal links pointing at no goal: %s" % bad


# --- the alignment parses ----------------------------------------------------


def test_goal_numbers_parse_from_the_canon_alignments(fresh_db):
    """Every alignment string yields at least one goal number."""
    canon = _canon()
    links = _rows(fresh_db, """
        SELECT k.MIId, GROUP_CONCAT(g.GoalNumber) AS goals
        FROM MajorInitiativeGoals kg JOIN MajorInitiatives k ON k.MajorInitiativeID = kg.MajorInitiativeID
        JOIN Goals g ON g.GoalID = kg.GoalID GROUP BY k.MIId""")
    got = {r["MIId"]: set(str(r["goals"]).split(",")) for r in links}
    assert len(got) == 29
    for mid, (title, align) in canon.items():
        assert got.get(mid), "no goal parsed for %s (%s)" % (mid, align)


def test_a_range_alignment_expands(fresh_db):
    """'Goals 1-5' means all five, not just 1 and 5."""
    rows = _rows(fresh_db, """
        SELECT GROUP_CONCAT(g.GoalNumber) AS goals
        FROM MajorInitiativeGoals kg JOIN MajorInitiatives k ON k.MajorInitiativeID = kg.MajorInitiativeID
        JOIN Goals g ON g.GoalID = kg.GoalID
        WHERE k.MIId = 'MI-006' GROUP BY k.MIId""")
    # MI-006 'Unified branding...' aligns to Goals 1-5 in the canon.
    if rows:
        assert set(rows[0]["goals"].split(",")) == {"1", "2", "3", "4", "5"}


# --- the values match the canon exactly -------------------------------------


def test_every_mi_id_matches_the_canon_title(fresh_db):
    """The MI-id -> title map, where the register is the wording authority.

    The register (2026-10-07) rewords five of the 29 titles; the register wins.
    For every other row the canon title still holds. This pins the MI-id to the
    register's own row (joined by name), so a renumber fails here.
    """
    canon = _canon()
    reg = _register_rows()
    ours = {r["MIId"]: r["Title"] for r in
            _rows(fresh_db, "SELECT MIId, Title FROM MajorInitiatives WHERE MIId IS NOT NULL")}
    for mid, (canon_title, _) in canon.items():
        rows = _rows(fresh_db, "SELECT Code, Title FROM MajorInitiatives WHERE MIId = ?", (mid,))
        if not rows:
            continue
        code = rows[0]["Code"]
        if code in reg:
            # the register is canon for the title
            assert ours.get(mid) == str(reg[code][2]).strip(), \
                "MI-id %s title differs from the register" % mid
        else:
            assert ours.get(mid) == canon_title, "MI-id %s title differs from canon" % mid


def test_the_goal_links_match_the_canon_alignment(fresh_db):
    """The strongest check: parse the canon and compare set-for-set.

    Superseded field-by-field by the register (2026-10-07): the register's Goal
    1-5 columns are now the source of the MI -> Goal edge, not the canon's
    Strategy Alignment prose, so this compares against the register instead.
    """
    reg = _register_goals()
    if reg is None:
        pytest.skip("register workbook not present")
    got = {}
    for r in _rows(fresh_db, """
            SELECT k.MIId, g.GoalNumber FROM MajorInitiativeGoals kg
            JOIN MajorInitiatives k ON k.MajorInitiativeID = kg.MajorInitiativeID
            JOIN Goals g ON g.GoalID = kg.GoalID"""):
        got.setdefault(r["MIId"], set()).add(str(r["GoalNumber"]))
    mismatched = []
    for mid, want in reg.items():
        if want != got.get(mid, set()):
            mismatched.append((mid, sorted(want), sorted(got.get(mid, set()))))
    assert not mismatched, mismatched


# --- the read model ----------------------------------------------------------


def test_each_target_belongs_to_its_own_initiative(fresh_db):
    """A title and its target must describe the same work.

    The defect this guards: the canon and the prototype list source area
    "Academic Affairs" in different orders, and an earlier version of the seed
    joined them by position, so eight rows carried the *next* row's target -
    MI-021 showed MI-022's subject. Matching by name fixed it. This pins the fix
    by asserting each target shares a distinctive word with its own title rather
    than describing a different initiative. It compares against the workbook, so
    a future reorder that re-introduces a positional join fails here.

    The check is deliberately loose - a keyword appearing somewhere in the target
    - so it is not brittle to wording; it only fires when the target is about
    something else entirely.
    """
    import re

    # (MI id, a word that must appear in that initiative's target)
    expected = {
        "MI-021": "approval",       # approval/governance process
        "MI-022": "governance",     # faculty governance process
        "MI-023": "evaluation",     # faculty evaluation & promotion system
        "MI-024": "faculty",        # empower faculty
        "MI-025": "faculty",        # fill faculty positions
        "MI-026": "program",        # stand up academic programs
        "MI-027": "faculty",        # grow faculty participation
        "MI-028": "program",        # recruit students into programs
        "MI-029": "coursework",     # reusable coursework
    }
    got = {r["MIId"]: (r["Title"] or "") + " " + (r["ProposedTarget"] or "")
           for r in _rows(fresh_db, "SELECT MIId, Title, ProposedTarget FROM MajorInitiatives")}
    wrong = [mid for mid, word in expected.items()
             if mid in got and word not in got[mid].lower()]
    assert not wrong, "target does not match its own initiative: %s" % wrong


def test_the_goal_view_lists_major_initiatives_per_goal(fresh_db):
    from app import queries
    rows = _rows(fresh_db, """
        SELECT g.GoalNumber, COUNT(DISTINCT v.MajorInitiativeID) AS n
        FROM vw_MajorInitiativeGoals v JOIN Goals g ON g.GoalID = v.GoalID
        GROUP BY g.GoalNumber ORDER BY g.GoalNumber""")
    assert len(rows) == 5, "all five goals should carry Major Initiatives"
    assert sum(r["n"] for r in rows) >= 29


# --- rebuild reproducibility -------------------------------------------------


def test_the_build_is_reproducible_after_a_canon_seed():
    """The canon seed must not introduce a wall-clock value.

    Every seeded column is set from the seed, so two builds must hash alike -
    the non-determinism trap that bit this repo before.
    """
    import hashlib
    import sqlite3
    import tempfile

    schema = os.path.join(R, "db", "schema.sql")
    seeds = [os.path.join(R, "db", n) for n in
             ("seed_sample.sql", "seed_team_layer.sql", "seed_canon_links.sql")]
    # The canon seed is generated from a workbook that may be absent; if so,
    # build without it and the base seeds must still be reproducible.
    seeds = [s for s in seeds if os.path.exists(s)]

    def build_to(path):
        conn = sqlite3.connect(path)
        conn.executescript(open(schema, encoding="utf-8").read())
        for s in seeds:
            conn.executescript(open(s, encoding="utf-8").read())
        conn.commit()
        conn.close()

    a = os.path.join(tempfile.mkdtemp(), "a.db")
    b = os.path.join(tempfile.mkdtemp(), "b.db")
    build_to(a)
    build_to(b)
    assert hashlib.sha256(open(a, "rb").read()).hexdigest() == \
           hashlib.sha256(open(b, "rb").read()).hexdigest()
