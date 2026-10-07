"""The write paths, on the register model."""
import sqlite3

import pytest

from app import repo


def _latest(db):
    con = sqlite3.connect(db)
    row = con.execute("SELECT PercentComplete, Status FROM MajorInitiativeUpdates "
                      "ORDER BY UpdateID DESC LIMIT 1").fetchone()
    con.close()
    return row


def test_add_update_lands_on_a_major_initiative(fresh_db):
    repo.add_progress_update("MI-002", 40, "On track", "note", entered_by_id=5)
    assert _latest(fresh_db) == (40, "On track")


def test_add_update_refuses_unknown_mi(fresh_db):
    with pytest.raises(repo.RuleError):
        repo.add_progress_update("MI-999", 10, "On track", "", entered_by_id=5)


def test_add_update_refuses_bad_status(fresh_db):
    with pytest.raises(repo.RuleError):
        repo.add_progress_update("MI-002", 10, "Nonsense", "", entered_by_id=5)


def test_retire_sets_isactive(fresh_db):
    repo.retire_initiative("MI-002", person_id=5)
    con = sqlite3.connect(fresh_db)
    v = con.execute("SELECT IsActive FROM MajorInitiatives WHERE MIId='MI-002'").fetchone()[0]
    con.close()
    assert v == 0


def test_update_details_renames_and_audits(fresh_db):
    repo.update_initiative_details("MI-002", "Renamed", "a description", person_id=5)
    con = sqlite3.connect(fresh_db)
    title = con.execute("SELECT Title FROM MajorInitiatives WHERE MIId='MI-002'").fetchone()[0]
    et = con.execute("SELECT EntityType FROM AuditLog ORDER BY AuditID DESC LIMIT 1").fetchone()[0]
    con.close()
    assert title == "Renamed"
    assert et == "Initiative"


def test_replace_links_points_at_dean_priorities(fresh_db):
    d27 = 1  # D27-1 exists in the seed
    repo.replace_links("MI-002", [d27], person_id=5)
    con = sqlite3.connect(fresh_db)
    n = con.execute("SELECT COUNT(*) FROM MajorInitiativeDeanLinks WHERE MajorInitiativeID="
                    "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId='MI-002')").fetchone()[0]
    con.close()
    assert n == 1


def test_replace_links_refuses_a_fake_dean_priority(fresh_db):
    with pytest.raises(repo.RuleError):
        repo.replace_links("MI-002", [9999], person_id=5)
