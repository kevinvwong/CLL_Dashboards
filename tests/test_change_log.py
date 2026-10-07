"""The change log: correct EntityType, an index, and a reader.

The EntityType bug (fixed 2026-10-07): the old map was keyed by entity but looked
up by the action's first word, so every non-initiative change was recorded as an
"Initiative". test_every_repo_action_has_an_entity guards against a new write
path being added without a mapping.
"""
import inspect
import re
import sqlite3

from app import queries, repo


def test_a_retire_then_restore_round_trips_and_is_logged(fresh_db):
    """The restore path the review found missing: retire is reversible, and both
    directions are audited."""
    import sqlite3

    repo.retire_initiative("MI-004", person_id=5)
    conn = sqlite3.connect(fresh_db)
    assert conn.execute("SELECT IsActive FROM TeamInitiatives WHERE MIId='MI-004'").fetchone()[0] == 0
    conn.close()

    repo.restore_initiative("MI-004", person_id=5, reason="retired in error")
    conn = sqlite3.connect(fresh_db)
    conn.row_factory = sqlite3.Row
    assert conn.execute("SELECT IsActive FROM TeamInitiatives WHERE MIId='MI-004'").fetchone()[0] == 1
    row = conn.execute(
        "SELECT Action, Reason FROM AuditLog WHERE Action='restore_initiative'").fetchone()
    conn.close()
    assert row is not None, "the restore was not logged"
    assert row["Reason"] == "retired in error"


def test_the_change_log_query_returns_reason_and_source(fresh_db):
    import sqlite3
    conn = sqlite3.connect(fresh_db)
    conn.execute("INSERT INTO AuditLog (PersonID, Action, EntityType, EntityKey, Details, "
                 "Reason, Source, CorrelationID) VALUES (5,'x','Initiative','MI-001','{}',"
                 "'why','JIRA-7','corr-1')")
    conn.commit()
    conn.close()
    rows = queries.recent_changes()
    r = next(x for x in rows if x["action"] == "x")
    assert r["reason"] == "why" and r["source"] == "JIRA-7" and r["correlation_id"] == "corr-1"



def test_every_repo_action_has_an_entity():
    """A new write path cannot silently mislabel again."""
    src = inspect.getsource(repo)
    actions = set(re.findall(r'_audit\(\s*conn,\s*person_id,\s*"(\w+)"', src))
    actions |= set(re.findall(r"_audit\(\s*conn,\s*person_id,\s*'(\w+)'", src))
    assert actions, "no _audit calls found - the probe is broken"
    missing = {a for a in actions if a not in repo._ACTION_ENTITY}
    assert not missing, f"actions with no EntityType mapping: {missing}"


def test_goal_edit_logs_entity_goal(fresh_db):
    repo.update_entry_description("goal", 1, "new text", person_id=5)
    con = sqlite3.connect(fresh_db)
    row = con.execute(
        "SELECT EntityType FROM AuditLog ORDER BY AuditID DESC LIMIT 1").fetchone()
    con.close()
    assert row[0] == "Goal"


def test_priority_edit_logs_entity_priority(fresh_db):
    repo.update_entry_description("priority", "Identity", "t", person_id=5)
    con = sqlite3.connect(fresh_db)
    row = con.execute(
        "SELECT EntityType FROM AuditLog ORDER BY AuditID DESC LIMIT 1").fetchone()
    con.close()
    assert row[0] == "Priority"


def test_recent_changes_returns_rows(fresh_db):
    repo.update_entry_description("priority", "Identity", "t", person_id=5)
    rows = queries.recent_changes()
    assert rows and rows[0]["entity_type"] == "Priority"


def test_changes_page_is_admin_gated(logged_in):
    assert logged_in("Kevin").get("/changes").status_code == 200
    assert logged_in("Bill Gaudelli").get("/changes").status_code == 403
