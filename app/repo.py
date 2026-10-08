"""All writes go through here (design.md decision 4).

One module, one transaction per write, and SQLite constraint errors mapped to
messages a person can act on rather than surfaced as driver exceptions.

After the 2026-10-07 merge there is ONE initiative model: the register's
`TeamInitiatives` (the 29) and its `TeamInitiativeUpdates` diary. The
prototype's `Initiatives`/`ProgressUpdates` are gone. Writes are append-only:
a progress update never modifies its initiative.
"""

import sqlite3

from app.db import connect, engine as _engine

# The vocabulary the TeamInitiativeUpdates CHECK constraint enforces.
STATUSES = (
    "Not started",
    "On track",
    "At risk",
    "Off track",
    "Complete",
    "Paused",
)

# The column allows 2000; the form and this module cap it at 500
# (task 6.2). Kept here so the form and the write path cannot disagree.
NOTE_MAX = 500

#: Action -> the kind of thing it changed. KEYED BY ACTION, not by entity. The
#: first version looked up a dict keyed by entity ("Initiative","Goal",...) with
#: action.split("_")[0].capitalize() -- "update"/"replace"/"create" -- none of
#: which are keys, so the default "Initiative" was written for EVERY change,
#: mislabelling goal, priority, tag and link edits (found 2026-10-07).
_ACTION_ENTITY = {
    "update_initiative": "Initiative",
    "create_initiative": "Initiative",
    "retire_initiative": "Initiative",
    "restore_initiative": "Initiative",
    "replace_tags": "Tag",
    "replace_links": "Link",
    "update_goal_description": "Goal",
    "update_priority_description": "Priority",
}


class RuleError(Exception):
    """A write was refused by a rule, in terms worth showing a person."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _conn():
    # Kept for callers that need a bare write connection outside `write()`.
    # write=True takes BEGIN IMMEDIATE, so the write lock is taken in exactly
    # one place -- db.connect.
    return connect(write=True)


def _friendly(exc: sqlite3.IntegrityError) -> RuleError:
    """Turn a constraint failure into an actionable message."""
    text = str(exc)
    if "PercentComplete" in text:
        return RuleError("Percent must be between 0 and 100.")
    if "Status" in text:
        return RuleError(f"Status must be one of: {', '.join(STATUSES)}.")
    if "EnteredByID" in text:
        return RuleError("That person is not in the directory.")
    if "TeamInitiativeID" in text:
        return RuleError("That initiative does not exist or has been retired.")
    return RuleError("That change does not follow the initiative rules.")


def _friendly_integrity(exc) -> RuleError:
    """The existing sqlite constraint mapper (unchanged wording)."""
    return _friendly(exc)


def _friendly_mssql(exc) -> RuleError:
    """Map a pymssql constraint/integrity failure to the same actionable
    messages the sqlite path produces (change `adopt-rev2-store` D6). Keyed on
    the constraint/column names T-SQL reports."""
    text = str(exc)
    if "progress" in text.lower() or "ck_update_progress" in text or "ck_initiative_progress" in text:
        return RuleError("Percent must be between 0 and 100.")
    if "ck_initiative_code" in text or "unique" in text.lower():
        return RuleError("That code is already in use.")
    if "foreign key" in text.lower() or text.lower().startswith("fk_"):
        return RuleError("That change references something that does not exist.")
    return RuleError("That change does not follow the initiative rules.")


def write(body, on_integrity=None):
    """Run ``body(conn)`` as one atomic write. Returns what the body returns.

    This is the one write seam (design D1). It owns the whole transaction
    discipline so that each write below states only its own rules:

    * opens a write connection (``BEGIN IMMEDIATE`` on sqlite; a transaction on
      mssql, from db.connect);
    * commits when the body returns;
    * rolls back on any failure and closes the connection;
    * maps a constraint failure to an actionable RuleError, never letting a
      driver error escape -- callers are routes and templates, not tests. The
      mapping is engine-aware: sqlite raises sqlite3.IntegrityError, mssql raises
      a pymssql error, and both land on the same messages (D6).

    ``on_integrity`` lets a write supply its own mapping when the shared one
    cannot tell its cases apart (for example, a duplicate code versus an
    unknown owner, which both arrive as a bare UNIQUE or FOREIGN KEY failure).
    A body may raise RuleError for a rule it checks itself; that propagates
    unchanged, and the transaction still rolls back.
    """
    conn = _conn()
    try:
        result = body(conn)
        conn.commit()
        return result
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        mapper = on_integrity or _friendly
        raise mapper(exc) from exc
    except Exception as exc:
        conn.rollback()
        # Only an integrity/constraint failure maps to a RuleError. A RuleError
        # the body raised, or any other real error (a ValueError, a bug),
        # propagates unchanged on both engines.
        if isinstance(exc, RuleError):
            raise
        if _engine(conn) == "mssql" and not isinstance(exc, sqlite3.IntegrityError):
            mapper = on_integrity or _friendly_mssql
            raise mapper(exc) from exc
        raise
    finally:
        conn.close()


def add_progress_update(
    mi_id: str,
    percent: int | str,
    status: str,
    note: str,
    entered_by_id: int,
):
    """Append one diary entry to a Team Initiative. Returns the new UpdateID.

    `percent` accepts a string because form data arrives as one; anything
    uncoercible is refused with a RuleError rather than raising.
    """
    note = (note or "").strip()
    if len(note) > NOTE_MAX:
        raise RuleError(f"Note must be {NOTE_MAX} characters or fewer.")
    if status not in STATUSES:
        raise RuleError(f"Status must be one of: {', '.join(STATUSES)}.")
    try:
        percent = int(percent)
    except (TypeError, ValueError):
        raise RuleError("Percent must be a whole number between 0 and 100.") from None
    if not 0 <= percent <= 100:
        raise RuleError("Percent must be between 0 and 100.")

    def body(conn):
        row = conn.execute(
            "SELECT TeamInitiativeID FROM TeamInitiatives "
            "WHERE MIId = ? AND IsActive = 1",
            (mi_id,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        cur = conn.execute(
            "INSERT INTO TeamInitiativeUpdates "
            "(TeamInitiativeID, PercentComplete, Status, Note, EnteredByID) "
            "VALUES (?, ?, ?, ?, ?)",
            (row["TeamInitiativeID"], percent, status, note or None, entered_by_id),
        )
        return cur.lastrowid

    return write(body)


def update_initiative_details(mi_id: str, name: str, description: str, person_id: int):
    """Rename/re-describe a Team Initiative and record it in AuditLog."""
    name = (name or "").strip()
    if not name:
        raise RuleError("An initiative needs a name.")

    def body(conn):
        row = conn.execute(
            "SELECT TeamInitiativeID, Title, Description FROM TeamInitiatives "
            "WHERE MIId = ? AND IsActive = 1",
            (mi_id,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        conn.execute(
            "UPDATE TeamInitiatives SET Title = ?, Description = ? "
            "WHERE TeamInitiativeID = ?",
            (name, (description or "").strip() or None, row["TeamInitiativeID"]),
        )
        _audit(
            conn, person_id, "update_initiative", mi_id,
            {
                "before": {"name": row["Title"], "description": row["Description"]},
                "after": {"name": name, "description": (description or "").strip() or None},
            },
        )

    write(body)


def _json_str(value) -> str:
    import json

    return json.dumps(value)


# --- tags, links, create, retire ------------------------------------------


def replace_tags(mi_id: str, goal_tags: list, priority_tags: list, person_id: int):
    """Replace a Team Initiative's goal and priority tags in one transaction.

    `goal_tags` and `priority_tags` are lists of {"id": int, "primary": bool}.
    Goal tags carry no primary on the register model (its goal columns are plain
    marks); priority tags do, and at most one may be primary. The database
    enforces the priority rule too, but checking here produces the message the
    admin-editing spec requires instead of a driver error.
    """
    primaries = [t for t in priority_tags if t.get("primary")]
    if len(primaries) > 1:
        raise RuleError("Only one primary priority is allowed.")

    def body(conn):
        row = conn.execute(
            "SELECT TeamInitiativeID FROM TeamInitiatives "
            "WHERE MIId = ? AND IsActive = 1",
            (mi_id,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        iid = row["TeamInitiativeID"]

        conn.execute("DELETE FROM TeamInitiativeGoals WHERE TeamInitiativeID = ?", (iid,))
        # executemany with an empty list raises ProgrammingError ("Incorrect
        # number of bindings"), so clearing every tag is a delete and no insert.
        if goal_tags:
            conn.executemany(
                "INSERT INTO TeamInitiativeGoals (TeamInitiativeID, GoalID) VALUES (?, ?)",
                [(iid, t["id"]) for t in goal_tags],
            )
        conn.execute("DELETE FROM TeamInitiativePriorities WHERE TeamInitiativeID = ?", (iid,))
        if priority_tags:
            conn.executemany(
                "INSERT INTO TeamInitiativePriorities (TeamInitiativeID, PriorityID, IsPrimary) "
                "VALUES (?, ?, ?)",
                [(iid, t["id"], 1 if t.get("primary") else 0) for t in priority_tags],
            )
        _audit(
            conn, person_id, "replace_tags", mi_id,
            {"goals": goal_tags, "priorities": priority_tags},
        )

    write(body)


def replace_links(mi_id: str, dean_initiative_ids: list, person_id: int):
    """Replace the Dean FY27 priorities a Team Initiative contributes to.

    The register's X-matrix: a team Team Initiative contributes to one or more
    Dean Initiatives (the register's "Dean KPI 27" items). Every target must be a
    real DeanInitiative row.
    """
    def body(conn):
        row = conn.execute(
            "SELECT TeamInitiativeID FROM TeamInitiatives "
            "WHERE MIId = ? AND IsActive = 1",
            (mi_id,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        iid = row["TeamInitiativeID"]

        if dean_initiative_ids:
            placeholders = ",".join("?" * len(dean_initiative_ids))
            bad = conn.execute(
                f"SELECT DeanInitiativeID FROM DeanInitiatives WHERE DeanInitiativeID IN ({placeholders})",
                dean_initiative_ids,
            ).fetchall()
            if len(bad) != len(set(dean_initiative_ids)):
                raise RuleError("Links must point at real Dean Initiatives.")

        conn.execute("DELETE FROM TeamInitiativeDeanLinks WHERE TeamInitiativeID = ?", (iid,))
        if dean_initiative_ids:
            conn.executemany(
                "INSERT INTO TeamInitiativeDeanLinks (TeamInitiativeID, DeanInitiativeID) "
                "VALUES (?, ?)",
                [(iid, d) for d in dean_initiative_ids],
            )
        _audit(conn, person_id, "replace_links", mi_id,
               {"dean_initiative_ids": dean_initiative_ids})

    write(body)


def create_initiative(code: str, name: str, owner_id: int, description: str, person_id: int):
    """Create a Team Initiative. New initiatives have no tags and no links, so
    they appear on /checks until an admin gives them both.

    `Code` is the internal stable key the register's own rows carry
    ('1-01'..'5-09'); `MIId` is assigned by the canon and is NULL here.
    """
    code = (code or "").strip()
    name = (name or "").strip()
    if not code:
        raise RuleError("An initiative needs a code.")
    if not name:
        raise RuleError("An initiative needs a name.")

    def body(conn):
        conn.execute(
            "INSERT INTO TeamInitiatives (Code, Title, Description, OwnerID) "
            "VALUES (?, ?, ?, ?)",
            (code, name, (description or "").strip() or None, owner_id),
        )
        _audit(conn, person_id, "create_initiative", code, {"name": name})

    def on_integrity(exc):
        # A duplicate code arrives as UNIQUE; an unknown owner arrives as a bare
        # "FOREIGN KEY constraint failed" -- SQLite does not name the column.
        # TeamInitiatives has exactly one foreign key on this INSERT (OwnerID ->
        # People), so a foreign-key failure here is unambiguously the owner.
        text = str(exc)
        if "Code" in text or "UNIQUE" in text.upper():
            return RuleError(f"There is already an initiative with the code {code}.")
        if "FOREIGN KEY" in text.upper():
            return RuleError("That person is not in the directory.")
        return _friendly(exc)

    write(body, on_integrity=on_integrity)


def retire_initiative(mi_id: str, person_id: int):
    """Retire rather than delete. History is kept, and a retired initiative
    disappears from every list and card."""
    def body(conn):
        row = conn.execute(
            "SELECT TeamInitiativeID, IsActive FROM TeamInitiatives WHERE MIId = ?",
            (mi_id,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist.")
        if not row["IsActive"]:
            raise RuleError(f"{mi_id} is already retired.")
        conn.execute("UPDATE TeamInitiatives SET IsActive = 0 WHERE TeamInitiativeID = ?",
                     (row["TeamInitiativeID"],))
        _audit(conn, person_id, "retire_initiative", mi_id, {})

    write(body)


def restore_initiative(mi_id: str, person_id: int, reason: str = None):
    """Undo a retire: bring a retired initiative back.

    Retire kept the row, so a restore is the inverse flag flip - the "restore
    path" the change-management review found missing. Audited like any write.
    """
    def body(conn):
        row = conn.execute(
            "SELECT TeamInitiativeID, IsActive FROM TeamInitiatives WHERE MIId = ?",
            (mi_id,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist.")
        if row["IsActive"]:
            raise RuleError(f"{mi_id} is not retired.")
        conn.execute("UPDATE TeamInitiatives SET IsActive = 1 WHERE TeamInitiativeID = ?",
                     (row["TeamInitiativeID"],))
        _audit(conn, person_id, "restore_initiative", mi_id, {}, reason=reason)

    write(body)


def update_entry_description(
    kind: str, key, description: str, person_id: int
):
    """Edit a goal or priority description."""
    table = {"goal": "Goals", "priority": "Priorities"}.get(kind)
    if table is None:
        raise RuleError("Unknown entry type.")
    column = "GoalNumber" if kind == "goal" else "PriorityName"

    def body(conn):
        row = conn.execute(
            f"SELECT Description FROM {table} WHERE {column} = ?", (key,)
        ).fetchone()
        if row is None:
            raise RuleError("No such goal or priority.")
        conn.execute(
            f"UPDATE {table} SET Description = ? WHERE {column} = ?",
            ((description or "").strip() or None, key),
        )
        _audit(
            conn, person_id, f"update_{kind}_description", str(key),
            {"before": row["Description"], "after": (description or "").strip() or None},
        )

    write(body)


def _audit(conn, person_id: int, action: str, entity_key: str, details: dict,
           reason: str = None, source: str = None, correlation_id: str = None):
    """Record one change. Reason, source and correlation id are the change-
    management fields (2026-10-07); all optional, so existing writers are
    unchanged.

    On mssql the target is audit_log (change `rev2-full-reconciliation` /
    008_app_layer.sql) and person_id is the Rev2 string id 'PERS-N', resolved
    from the app's int PersonID; the rest of the shape is unchanged."""
    import json

    entity = _ACTION_ENTITY.get(action, "Unknown")
    if _engine(conn) == "mssql":
        pid = "PERS-%d" % person_id if person_id is not None else None
        conn.execute(
            "INSERT INTO dbo.audit_log (person_id, action, entity_type, entity_key, details, "
            "reason, source, correlation_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (pid, action, entity, entity_key, json.dumps(details),
             reason, source, correlation_id),
        )
        return
    conn.execute(
        "INSERT INTO AuditLog (PersonID, Action, EntityType, EntityKey, Details, "
        "Reason, Source, CorrelationID) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (person_id, action, entity, entity_key, json.dumps(details),
         reason, source, correlation_id),
    )
