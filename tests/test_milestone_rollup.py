"""Weighted attainment is independent of owner estimates and includes soft marks."""
import sqlite3

import pytest
from openpyxl import load_workbook


def _connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def test_one_met_mark_earns_only_its_weight(fresh_db):
    with _connect(fresh_db) as conn:
        tid = conn.execute("SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code='3-02'").fetchone()[0]
        conn.execute("UPDATE Milestones SET Status='Met' WHERE TeamInitiativeID=? AND SortOrder=1", (tid,))
        rollup = conn.execute("SELECT * FROM vw_TeamInitiativeStatus WHERE TeamInitiativeID=?", (tid,)).fetchone()
        assert rollup['AttainmentPct'] == 40
        assert rollup['Status'] == 'In progress'


def test_unfinished_mark_prevents_met_status(fresh_db):
    with _connect(fresh_db) as conn:
        tid = conn.execute("SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code='1-02'").fetchone()[0]
        conn.execute("UPDATE Milestones SET Status='Met' WHERE TeamInitiativeID=?", (tid,))
        conn.execute("UPDATE Milestones SET Status='In progress' WHERE TeamInitiativeID=? AND SortOrder=3", (tid,))
        row = conn.execute("SELECT * FROM vw_TeamInitiativeStatus WHERE TeamInitiativeID=?", (tid,)).fetchone()
        assert row['AttainmentPct'] == 75
        assert row['Status'] == 'In progress'


def test_soft_marks_stay_in_the_denominator(fresh_db):
    with _connect(fresh_db) as conn:
        tid = conn.execute("SELECT TeamInitiativeID FROM TeamInitiatives WHERE Code='1-03'").fetchone()[0]
        conn.execute("UPDATE Milestones SET Status='Met' WHERE TeamInitiativeID=? AND NeedsRewrite=0", (tid,))
        row = conn.execute("SELECT * FROM vw_TeamInitiativeStatus WHERE TeamInitiativeID=?", (tid,)).fetchone()
        assert row['NeedsRewriteCount'] == 1
        assert row['AttainmentPct'] == 82
        assert row['Status'] == 'In progress'


def test_seed_has_no_reported_attainment(fresh_db):
    with _connect(fresh_db) as conn:
        rows = conn.execute("SELECT * FROM vw_TeamInitiativeStatus").fetchall()
        assert len(rows) == 29
        assert all(r['AttainmentPct'] is None for r in rows)
        assert conn.execute("SELECT SUM(NeedsRewrite) FROM Milestones").fetchone()[0] == 12
        for row in conn.execute("SELECT SUM(Weight) FROM Milestones GROUP BY TeamInitiativeID, PlanYear"):
            assert row[0] == pytest.approx(1)


def test_milestone_year_must_match_its_parent(fresh_db):
    with _connect(fresh_db) as conn:
        tid = conn.execute("SELECT TeamInitiativeID FROM TeamInitiatives LIMIT 1").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO Milestones (TeamInitiativeID,PlanYear,Name,SortOrder) VALUES (?,2028,'Wrong year',1)", (tid,))


def test_intake_can_add_a_brand_new_milestone_row(fresh_db, tmp_path):
    from tests.test_intake import make_template, import_xlsx
    path = tmp_path / 'intake.xlsx'
    make_template.build(fresh_db, str(path))
    wb = load_workbook(path)
    ws = wb['Milestones']
    # Append a row for an existing initiative that has never been seen. An
    # earlier importer inserted the previous MilestoneID, which is NULL for a NEW
    # row and violates the primary key - so this row is the regression.
    ws.append(['1-02', 'A newly added milestone', 'Not started', '2',
               'no', None, None, 'Mario Herane', None, 'headline-quant', 'confirmed'])
    wb.save(path)
    ok, problems = import_xlsx.import_workbook(fresh_db, str(path))
    assert ok, problems
    with _connect(fresh_db) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM Milestones WHERE Name='A newly added milestone'").fetchone()[0] == 1
        # and it must join the rollup, not sit outside it
        assert conn.execute(
            "SELECT COUNT(*) FROM vw_TeamInitiativeStatus s JOIN TeamInitiatives t "
            "ON t.TeamInitiativeID=s.TeamInitiativeID WHERE t.Code='1-02'"
        ).fetchone()[0] == 1
        row = conn.execute(
            "SELECT * FROM vw_TeamInitiativeStatus s JOIN TeamInitiatives t "
            "ON t.TeamInitiativeID=s.TeamInitiativeID WHERE t.Code='1-02'").fetchone()
        assert row['MilestoneCount'] == 4
        assert row['AttainmentPct'] is None


def test_a_milestone_without_a_parent_is_refused(fresh_db):
    with _connect(fresh_db) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO Milestones (TeamInitiativeID,PlanYear,Name,SortOrder) "
                "VALUES (999999999,2027,'Orphan',1)")


def test_intake_roundtrip_preserves_weight_provenance_and_rewrite_flags(fresh_db, tmp_path):
    from tests.test_intake import make_template, import_xlsx
    with _connect(fresh_db) as conn:
        before = [tuple(r) for r in conn.execute("SELECT TeamInitiativeID,Name,Weight,WeightBasis,WeightSource,NeedsRewrite FROM Milestones ORDER BY TeamInitiativeID,Name")]
    path = tmp_path / 'intake.xlsx'
    make_template.build(fresh_db, str(path))
    ok, problems = import_xlsx.import_workbook(fresh_db, str(path))
    assert ok, problems
    with _connect(fresh_db) as conn:
        after = [tuple(r) for r in conn.execute("SELECT TeamInitiativeID,Name,Weight,WeightBasis,WeightSource,NeedsRewrite FROM Milestones ORDER BY TeamInitiativeID,Name")]
    assert len(after) == len(before) == 84
    for a, b in zip(after, before):
        assert a[:2] == b[:2]
        assert a[2] == pytest.approx(b[2], abs=1e-8)
        assert a[3:] == b[3:]


def test_detail_displays_weighted_attainment_and_rewrite_flags(logged_in):
    body = logged_in('Bill Gaudelli').get('/team-initiatives/MI-003').text
    assert 'Weighted milestone attainment' in body
    assert 'Needs rewrite' in body
    assert 'personalized journey' in body
    assert 'inferred' in body
