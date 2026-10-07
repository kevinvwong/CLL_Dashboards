"""All writes go through here (design.md decision 4).

One module, one transaction per write, and SQLite constraint errors mapped to
messages a person can act on rather than surfaced as driver exceptions.

Writes are append-only. A progress update never modifies its initiative and
never rolls up to a Dean initiative - `progress-updates` requires that a D-1
update leaves the Dean's latest percent untouched, and doing nothing is the
only way to guarantee it.
"""

import sqlite3

from app.db import connect

# The vocabulary the ProgressUpdates CHECK constraint enforces.
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
    if "ProgressUpdates.PercentComplete" in text or "PercentComplete" in text:
        return RuleError("Percent must be between 0 and 100.")
    if "ProgressUpdates.Status" in text or "Status" in text:
        return RuleError(f"Status must be one of: {', '.join(STATUSES)}.")
    if "EnteredByID" in text:
        return RuleError("That person is not in the directory.")
    if "InitiativeID" in text:
        return RuleError("That initiative does not exist or has been retired.")
    return RuleError("That change does not follow the initiative rules.")


def write(body, on_integrity=None):
    """Run ``body(conn)`` as one atomic write. Returns what the body returns.

    This is the one write seam (design D1). It owns the whole transaction
    discipline so that each write below states only its own rules:

    * opens a write connection (``BEGIN IMMEDIATE``, from db.connect);
    * commits when the body returns;
    * rolls back on any failure and closes the connection;
    * maps a constraint failure to an actionable RuleError, never letting a
      driver error escape -- callers are routes and templates, not tests.

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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_progress_update(
    code: str,
    percent: int | str,
    status: str,
    note: str,
    entered_by_id: int,
):
    """Append one diary entry. Returns the new UpdateID.

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
            "SELECT InitiativeID FROM Initiatives WHERE Code = ? AND IsActive = 1",
            (code,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        cur = conn.execute(
            "INSERT INTO ProgressUpdates "
            "(InitiativeID, PercentComplete, Status, Note, EnteredByID) "
            "VALUES (?, ?, ?, ?, ?)",
            (row["InitiativeID"], percent, status, note or None, entered_by_id),
        )
        return cur.lastrowid

    return write(body)


def update_initiative_details(code: str, name: str, description: str, person_id: int):
    """Rename/re-describe an initiative and record it in AuditLog (task 8.1)."""
    name = (name or "").strip()
    if not name:
        raise RuleError("An initiative needs a name.")

    def body(conn):
        row = conn.execute(
            "SELECT InitiativeID, InitiativeName, Description FROM Initiatives "
            "WHERE Code = ? AND IsActive = 1",
            (code,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        conn.execute(
            "UPDATE Initiatives SET InitiativeName = ?, Description = ? WHERE InitiativeID = ?",
            (name, (description or "").strip() or None, row["InitiativeID"]),
        )
        conn.execute(
            "INSERT INTO AuditLog (PersonID, Action, EntityType, EntityKey, Details) "
            "VALUES (?, 'update_initiative', 'Initiative', ?, ?)",
            (
                person_id,
                code,
                '{"before":{"name":%s,"description":%s},'
                '"after":{"name":%s,"description":%s}}'
                % (
                    _json_str(row["InitiativeName"]),
                    _json_str(row["Description"]),
                    _json_str(name),
                    _json_str((description or "").strip() or None),
                ),
            ),
        )

    write(body)


def _json_str(value) -> str:
    import json

    return json.dumps(value)


# --- tags, links, create, retire (tasks 8.2, 8.3, 8.4) -------------------


def replace_tags(code: str, goal_tags: list, priority_tags: list, person_id: int):
    """Replace an initiative's goal and priority tags in one transaction.

    `goal_tags` and `priority_tags` are lists of
    {"id": int, "primary": bool}. At most one may be primary per list; the
    database enforces that too, but checking here produces the message the
    admin-editing spec requires instead of a driver error.
    """
    for label, tags in (("goal", goal_tags), ("priority", priority_tags)):
        primaries = [t for t in tags if t.get("primary")]
        if len(primaries) > 1:
            raise RuleError(f"Only one primary {label} is allowed.")

    def body(conn):
        row = conn.execute(
            "SELECT InitiativeID FROM Initiatives WHERE Code = ? AND IsActive = 1",
            (code,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        iid = row["InitiativeID"]

        conn.execute("DELETE FROM InitiativeGoals WHERE InitiativeID = ?", (iid,))
        # executemany with an empty list raises ProgrammingError ("Incorrect
        # number of bindings"), so clearing every tag is a delete and no insert.
        if goal_tags:
            conn.executemany(
                "INSERT INTO InitiativeGoals (InitiativeID, GoalID, IsPrimary) "
                "VALUES (?, ?, ?)",
                [(iid, t["id"], 1 if t.get("primary") else 0) for t in goal_tags],
            )
        conn.execute("DELETE FROM InitiativePriorities WHERE InitiativeID = ?", (iid,))
        if priority_tags:
            conn.executemany(
                "INSERT INTO InitiativePriorities (InitiativeID, PriorityID, IsPrimary) "
                "VALUES (?, ?, ?)",
                [(iid, t["id"], 1 if t.get("primary") else 0) for t in priority_tags],
            )
        _audit(
            conn,
            person_id,
            "replace_tags",
            code,
            {"goals": goal_tags, "priorities": priority_tags},
        )

    write(body)


def replace_links(code: str, dean_initiative_ids: list, person_id: int):
    """Replace the Dean initiatives a D-1 initiative feeds.

    Only a D-1 initiative has links, and every target must be a Dean
    initiative. `trg_Links_LevelCheck` enforces the second rule in the
    database; this rejects it first with a readable message.
    """
    def body(conn):
        row = conn.execute(
            "SELECT InitiativeID, Level FROM Initiatives WHERE Code = ? AND IsActive = 1",
            (code,),
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist or has been retired.")
        if row["Level"] != "D-1":
            raise RuleError("Only a D-1 initiative feeds a Dean initiative.")
        iid = row["InitiativeID"]

        if dean_initiative_ids:
            placeholders = ",".join("?" * len(dean_initiative_ids))
            bad = conn.execute(
                f"SELECT Code FROM Initiatives WHERE InitiativeID IN ({placeholders}) "
                "AND (Level <> 'Dean' OR IsActive = 0)",
                dean_initiative_ids,
            ).fetchall()
            if bad:
                raise RuleError(
                    "Links must connect a D-1 initiative to a Dean initiative"
                )

        conn.execute("DELETE FROM InitiativeLinks WHERE InitiativeID = ?", (iid,))
        if dean_initiative_ids:
            conn.executemany(
                "INSERT INTO InitiativeLinks (InitiativeID, DeanInitiativeID) VALUES (?, ?)",
                [(iid, dean_id) for dean_id in dean_initiative_ids],
            )
        _audit(conn, person_id, "replace_links", code, {"dean_initiative_ids": dean_initiative_ids})

    write(body)


def create_initiative(
    code: str, name: str, level: str, owner_id: int, description: str, person_id: int
):
    """Create an initiative (task 8.4). New initiatives have no tags and no
    links, so they appear on /checks until an admin gives them both."""
    code = (code or "").strip()
    name = (name or "").strip()
    if not code:
        raise RuleError("An initiative needs a code.")
    if not name:
        raise RuleError("An initiative needs a name.")
    if level not in ("Dean", "D-1"):
        raise RuleError("Level must be Dean or D-1.")

    def body(conn):
        conn.execute(
            "INSERT INTO Initiatives (Code, InitiativeName, Description, Level, OwnerID) "
            "VALUES (?, ?, ?, ?, ?)",
            (code, name, (description or "").strip() or None, level, owner_id),
        )
        _audit(conn, person_id, "create_initiative", code, {"name": name, "level": level})

    def on_integrity(exc):
        # A duplicate code arrives as UNIQUE; an unknown owner arrives as a bare
        # "FOREIGN KEY constraint failed" -- SQLite does not name the column.
        # Initiatives has exactly one foreign key on this INSERT (OwnerID ->
        # People), so a foreign-key failure here is unambiguously the owner.
        # This branch previously tested for the literal text "OwnerID", which
        # SQLite never emits, so the unknown-owner case fell through to the
        # generic message and did not name what to change (found by
        # test_unknown_owner_is_a_message_not_a_driver_error).
        text = str(exc)
        if "Initiatives.Code" in text or "UNIQUE" in text.upper():
            return RuleError(f"There is already an initiative with the code {code}.")
        if "FOREIGN KEY" in text.upper():
            return RuleError("That person is not in the directory.")
        return _friendly(exc)

    write(body, on_integrity=on_integrity)


def retire_initiative(code: str, person_id: int):
    """Retire rather than delete (task 8.4). Progress history is kept, and a
    retired initiative disappears from every list and card."""
    def body(conn):
        row = conn.execute(
            "SELECT InitiativeID, IsActive FROM Initiatives WHERE Code = ?", (code,)
        ).fetchone()
        if row is None:
            raise RuleError("That initiative does not exist.")
        if not row["IsActive"]:
            raise RuleError(f"{code} is already retired.")
        conn.execute("UPDATE Initiatives SET IsActive = 0 WHERE InitiativeID = ?", (row["InitiativeID"],))
        _audit(conn, person_id, "retire_initiative", code, {})

    write(body)


def update_entry_description(
    kind: str, key, description: str, person_id: int
):
    """Edit a goal or priority description (task 8.4)."""
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
            conn,
            person_id,
            f"update_{kind}_description",
            str(key),
            {"before": row["Description"], "after": (description or "").strip() or None},
        )

    write(body)



def _audit(conn, person_id: int, action: str, entity_key: str, details: dict):
    import json

    entity = _ACTION_ENTITY.get(action, "Unknown")
    conn.execute(
        "INSERT INTO AuditLog (PersonID, Action, EntityType, EntityKey, Details) "
        "VALUES (?, ?, ?, ?, ?)",
        (person_id, action, entity, entity_key, json.dumps(details)),
    )