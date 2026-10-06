"""Read queries for screens that are not served directly by a view.

The seven views in db/schema.sql cover the list and card screens. The home
screen needs an initiative count per goal and per priority, which no view
provides, so it lives here. Writes go through app/repo.py instead.
"""

from app.config import Config
from app.db import get_connection


def _conn():
    return get_connection(Config().DB_PATH)


def goal_tiles() -> list[dict]:
    """One row per Strategy 2035 goal with its active initiative count.

    COUNT(DISTINCT ...) guards against an initiative being counted twice if
    it ever carries the same goal tag more than once.
    """
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT g.GoalNumber,
                   g.ShortName,
                   g.FullName,
                   COUNT(DISTINCT i.InitiativeID) AS InitiativeCount
            FROM Goals g
            LEFT JOIN InitiativeGoals ig ON ig.GoalID = g.GoalID
            LEFT JOIN Initiatives i
                   ON i.InitiativeID = ig.InitiativeID AND i.IsActive = 1
            GROUP BY g.GoalID, g.GoalNumber, g.ShortName, g.FullName
            ORDER BY g.GoalNumber
            """
        ).fetchall()
    return [dict(r) for r in rows]


def priority_tiles() -> list[dict]:
    """One row per annual priority with its active initiative count.

    Not filtered to a single plan year: the home route has no year selector,
    so every priority is shown and labelled with the year it belongs to.
    """
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT p.PriorityName,
                   p.PlanYear,
                   COUNT(DISTINCT i.InitiativeID) AS InitiativeCount
            FROM Priorities p
            LEFT JOIN InitiativePriorities ip ON ip.PriorityID = p.PriorityID
            LEFT JOIN Initiatives i
                   ON i.InitiativeID = ip.InitiativeID AND i.IsActive = 1
            GROUP BY p.PriorityID, p.PriorityName, p.PlanYear
            ORDER BY p.PriorityName
            """
        ).fetchall()
    return [dict(r) for r in rows]


def goal_by_number(goal_number: int):
    with _conn() as conn:
        row = conn.execute(
            "SELECT GoalNumber, ShortName, FullName, Description "
            "FROM Goals WHERE GoalNumber = ?",
            (goal_number,),
        ).fetchone()
    return dict(row) if row else None


def priority_by_name(name: str):
    with _conn() as conn:
        row = conn.execute(
            "SELECT PriorityName, PlanYear, Description "
            "FROM Priorities WHERE PriorityName = ?",
            (name,),
        ).fetchone()
    return dict(row) if row else None


# --- list screens (tasks 4.1-4.3) ----------------------------------------


def goal_rows(goal_number: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM vw_GoalInitiatives WHERE GoalNumber = ?", (goal_number,)
        ).fetchall()
    return [dict(r) for r in rows]


def priority_rows(priority_name: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM vw_PriorityInitiatives WHERE Priority = ?", (priority_name,)
        ).fetchall()
    return [dict(r) for r in rows]


def split_for_list(rows: list[dict]):
    """Apply design.md decision 8: Dean initiatives ordered by code, then a
    divider, then D-1 initiatives grouped by owner name and ordered by code
    within each owner.

    Returns (dean_rows, d1_groups) where each group is {"owner", "rows"}.
    """
    dean = sorted((r for r in rows if r["Level"] == "Dean"), key=lambda r: r["Code"])

    by_owner: dict = {}
    for row in sorted(
        (r for r in rows if r["Level"] == "D-1"),
        key=lambda r: (r["Owner"], r["Code"]),
    ):
        by_owner.setdefault(row["Owner"], []).append(row)

    groups = [{"owner": owner, "rows": rs} for owner, rs in sorted(by_owner.items())]
    return dean, groups


def status_counts(rows: list[dict]) -> list[dict]:
    """Counts by status for the list header.

    Deliberately counts and never a mean: the design's risk entry says Bill
    expects rollups, and the decision is "no aggregate percent anywhere".
    An initiative with no progress update is counted as Not started.
    """
    counts: dict = {}
    for row in rows:
        status = row["Status"] or "Not started"
        counts[status] = counts.get(status, 0) + 1
    order = ["On track", "At risk", "Off track", "Not started", "Paused", "Complete"]
    known = [(s, counts.pop(s)) for s in order if s in counts]
    return [{"Status": s, "Count": c} for s, c in known + sorted(counts.items())]


# --- cards (task 5.2, 5.4) -----------------------------------------------

# The person-card spec says 20 days; task 5.4 said 14. The spec wins, because
# it is the requirement the task derives from. Recorded in tasks.md so the
# choice is visible rather than silent.
STALE_DAYS = 20


def initiative_card(code: str):
    """Everything the initiative card needs, in one call.

    Sections: details, goal and priority tags, what it feeds or what feeds
    it, latest progress, and the full diary newest first.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT i.InitiativeID, i.Code, i.InitiativeName, i.Description, "
            "       i.Level, i.OwnerID, p.Name AS Owner "
            "FROM Initiatives i JOIN People p ON p.PersonID = i.OwnerID "
            "WHERE i.Code = ? AND i.IsActive = 1",
            (code,),
        ).fetchone()
        if row is None:
            return None
        card = dict(row)

        card["goal_tags"] = [
            dict(r)
            for r in conn.execute(
                "SELECT g.GoalNumber, g.ShortName, ig.IsPrimary "
                "FROM InitiativeGoals ig JOIN Goals g ON g.GoalID = ig.GoalID "
                "WHERE ig.InitiativeID = ? ORDER BY g.GoalNumber",
                (card["InitiativeID"],),
            )
        ]
        card["priority_tags"] = [
            dict(r)
            for r in conn.execute(
                "SELECT pr.PriorityName, pr.PlanYear, ip.IsPrimary "
                "FROM InitiativePriorities ip JOIN Priorities pr ON pr.PriorityID = ip.PriorityID "
                "WHERE ip.InitiativeID = ? ORDER BY pr.PriorityName",
                (card["InitiativeID"],),
            )
        ]
        card["connections"] = [
            dict(r)
            for r in conn.execute(
                "SELECT Direction, Code, InitiativeName, OwnerID, Owner "
                "FROM vw_InitiativeConnections WHERE InitiativeID = ? "
                "ORDER BY Direction, Code",
                (card["InitiativeID"],),
            )
        ]
        latest = conn.execute(
            "SELECT UpdateDate, PercentComplete, Status, Note FROM vw_LatestProgress "
            "WHERE InitiativeID = ?",
            (card["InitiativeID"],),
        ).fetchone()
        card["latest"] = dict(latest) if latest else None
        card["diary"] = [
            dict(r)
            for r in conn.execute(
                "SELECT UpdateDate, PercentComplete, Status, Note, "
                "       (SELECT Name FROM People e WHERE e.PersonID = pu.EnteredByID) AS EnteredBy "
                "FROM ProgressUpdates pu WHERE InitiativeID = ? "
                "ORDER BY UpdateDate DESC, UpdateID DESC",
                (card["InitiativeID"],),
            )
        ]
    return card


def person_card(person_id: int):
    """A person's active initiatives with a staleness flag.

    The spec's "Needs update" flag covers two cases: no update at all, and an
    update older than STALE_DAYS. The sample data only ever satisfies the
    first negatively, so the second is what usually fires.
    """
    import datetime as _dt

    with _conn() as conn:
        person = conn.execute(
            "SELECT PersonID, Name, Title, ReportsToID, IsAdmin FROM People "
            "WHERE PersonID = ? AND IsActive = 1",
            (person_id,),
        ).fetchone()
        if person is None:
            return None
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT InitiativeID, Level, Code, InitiativeName, "
                "       PercentComplete, Status, LastUpdated "
                "FROM vw_PersonInitiatives WHERE PersonID = ? ORDER BY Code",
                (person_id,),
            )
        ]

    today = _dt.date.today()
    for row in rows:
        if row["LastUpdated"] is None:
            row["NeedsUpdate"] = True
        else:
            age = (today - _dt.date.fromisoformat(row["LastUpdated"])).days
            row["AgeDays"] = age
            row["NeedsUpdate"] = age > STALE_DAYS
    card = {"person": dict(person), "initiatives": rows}
    return card


# --- meeting and checks (tasks 8.5, 8.6) ---------------------------------

DEFAULT_MEETING_WINDOW_DAYS = 7


def default_since(days: int = DEFAULT_MEETING_WINDOW_DAYS) -> str:
    import datetime as _dt

    return (_dt.date.today() - _dt.timedelta(days=days)).isoformat()


def meeting_updates(since: str):
    """Updates entered on or after `since`, grouped by owner.

    vw_RecentUpdates deliberately carries no WHERE and no ORDER BY - the
    window and the ordering are the caller's job, which is what this does.
    """
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM vw_RecentUpdates WHERE UpdateDate >= ? "
            "ORDER BY UpdateDate DESC, Code, Owner",
            (since,),
        ).fetchall()
    groups: dict = {}
    for row in rows:
        entry = dict(row)
        groups.setdefault(entry["Owner"], []).append(entry)
    return [{"owner": owner, "rows": rs} for owner, rs in sorted(groups.items())]


def attention_list() -> list[dict]:
    """Active initiatives whose latest status is At risk.

    The meeting-view spec names At risk and only At risk. Off track is
    arguably more urgent and is *not* included here; flagged as an open
    question rather than assumed.
    """
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT i.Code, i.InitiativeName, i.Level, i.OwnerID, "
                "       p.Name AS Owner, lp.PercentComplete, lp.Status, lp.UpdateDate "
                "FROM Initiatives i "
                "JOIN People p ON p.PersonID = i.OwnerID "
                "JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID "
                "WHERE i.IsActive = 1 AND lp.Status = 'At risk' "
                "ORDER BY lp.UpdateDate, i.Code"
            )
        ]


def data_checks() -> list[dict]:
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT Code, Issue FROM vw_DataChecks ORDER BY Code, Issue"
            )
        ]


# --- edit form options (tasks 8.2, 8.3, 8.4) ------------------------------


def all_goals() -> list[dict]:
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT GoalID, GoalNumber, ShortName, FullName, Description "
                "FROM Goals ORDER BY GoalNumber"
            )
        ]


def all_priorities() -> list[dict]:
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT PriorityID, PriorityName, PlanYear, Description "
                "FROM Priorities ORDER BY PlanYear, PriorityName"
            )
        ]


def active_dean_initiatives() -> list[dict]:
    """Link targets for a D-1 initiative: active Dean-level ones only."""
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT InitiativeID, Code, InitiativeName FROM Initiatives "
                "WHERE Level = 'Dean' AND IsActive = 1 ORDER BY Code"
            )
        ]


def current_goal_tags(initiative_id: int) -> list[int]:
    with _conn() as conn:
        return [
            r["GoalID"]
            for r in conn.execute(
                "SELECT GoalID FROM InitiativeGoals WHERE InitiativeID = ?", (initiative_id,)
            )
        ]


def current_priority_tags(initiative_id: int) -> list[int]:
    with _conn() as conn:
        return [
            r["PriorityID"]
            for r in conn.execute(
                "SELECT PriorityID FROM InitiativePriorities WHERE InitiativeID = ?",
                (initiative_id,),
            )
        ]


def current_links(initiative_id: int) -> list[int]:
    with _conn() as conn:
        return [
            r["DeanInitiativeID"]
            for r in conn.execute(
                "SELECT DeanInitiativeID FROM InitiativeLinks WHERE InitiativeID = ?",
                (initiative_id,),
            )
        ]