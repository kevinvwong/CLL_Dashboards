"""The KPI -> Goal edge and the canon's stable keys.

Covers the interconnection-redesign data layer: the canon workbook's MI-ids,
exact titles, and the KPI -> Goal alignment, all verified against the workbook
itself rather than against a copy.
"""
import os
import re

import pytest

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
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


# --- the edge exists ---------------------------------------------------------


def test_every_team_kpi_has_a_goal_link(fresh_db):
    """The interconnection the canon states and the schema did not hold."""
    n = _rows(fresh_db, "SELECT COUNT(DISTINCT KPIID) AS n FROM TeamKPIGoals")[0]["n"]
    assert n == 29, "expected all 29 KPIs to align to at least one goal"


def test_every_team_kpi_has_an_mi_id(fresh_db):
    n = _rows(fresh_db, "SELECT COUNT(*) AS n FROM TeamKPIs WHERE MIId IS NOT NULL")[0]["n"]
    assert n == 29


def test_goal_links_reference_real_goals(fresh_db):
    from app import queries
    bad = _rows(fresh_db,
        "SELECT kg.KPIID FROM TeamKPIGoals kg "
        "LEFT JOIN Goals g ON g.GoalID = kg.GoalID WHERE g.GoalID IS NULL")
    assert not bad, "goal links pointing at no goal: %s" % bad


# --- the alignment parses ----------------------------------------------------


def test_goal_numbers_parse_from_the_canon_alignments(fresh_db):
    """Every alignment string yields at least one goal number."""
    canon = _canon()
    links = _rows(fresh_db, """
        SELECT k.MIId, GROUP_CONCAT(g.GoalNumber) AS goals
        FROM TeamKPIGoals kg JOIN TeamKPIs k ON k.KPIID = kg.KPIID
        JOIN Goals g ON g.GoalID = kg.GoalID GROUP BY k.MIId""")
    got = {r["MIId"]: set(str(r["goals"]).split(",")) for r in links}
    assert len(got) == 29
    for mid, (title, align) in canon.items():
        assert got.get(mid), "no goal parsed for %s (%s)" % (mid, align)


def test_a_range_alignment_expands(fresh_db):
    """'Goals 1-5' means all five, not just 1 and 5."""
    rows = _rows(fresh_db, """
        SELECT GROUP_CONCAT(g.GoalNumber) AS goals
        FROM TeamKPIGoals kg JOIN TeamKPIs k ON k.KPIID = kg.KPIID
        JOIN Goals g ON g.GoalID = kg.GoalID
        WHERE k.MIId = 'MI-006' GROUP BY k.MIId""")
    # MI-006 'Unified branding...' aligns to Goals 1-5 in the canon.
    if rows:
        assert set(rows[0]["goals"].split(",")) == {"1", "2", "3", "4", "5"}


# --- the values match the canon exactly -------------------------------------


def test_every_mi_id_matches_the_canon_title(fresh_db):
    canon = _canon()
    ours = {r["MIId"]: r["Title"] for r in
            _rows(fresh_db, "SELECT MIId, Title FROM TeamKPIs WHERE MIId IS NOT NULL")}
    for mid, (title, _) in canon.items():
        assert ours.get(mid) == title, "MI-id %s title differs from canon" % mid


def test_the_goal_links_match_the_canon_alignment(fresh_db):
    """The strongest check: parse the canon and compare set-for-set."""
    canon = _canon()
    got = {}
    for r in _rows(fresh_db, """
            SELECT k.MIId, g.GoalNumber FROM TeamKPIGoals kg
            JOIN TeamKPIs k ON k.KPIID = kg.KPIID
            JOIN Goals g ON g.GoalID = kg.GoalID"""):
        got.setdefault(r["MIId"], set()).add(str(r["GoalNumber"]))
    mismatched = []
    for mid, (title, align) in canon.items():
        m = re.search(r"Goals?\s+([\d\s,+\-–]+)", align)
        want = set(re.findall(r"\d", m.group(1))) if m else set()
        rng = re.search(r"(\d)\s*[-–]\s*(\d)", align)
        if rng:
            want = {str(x) for x in range(int(rng.group(1)), int(rng.group(2)) + 1)}
        if want != got.get(mid, set()):
            mismatched.append((mid, sorted(want), sorted(got.get(mid, set()))))
    assert not mismatched, mismatched


# --- the read model ----------------------------------------------------------


def test_the_goal_view_lists_kpis_per_goal(fresh_db):
    from app import queries
    rows = _rows(fresh_db, """
        SELECT g.GoalNumber, COUNT(DISTINCT v.KPIID) AS n
        FROM vw_TeamKPIGoals v JOIN Goals g ON g.GoalID = v.GoalID
        GROUP BY g.GoalNumber ORDER BY g.GoalNumber""")
    assert len(rows) == 5, "all five goals should carry team KPIs"
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
