"""Read queries for screens that are not served directly by a view.

The seven views in db/schema.sql cover the list and card screens. The home
screen needs an initiative count per goal and per priority, which no view
provides, so it lives here. Writes go through app/repo.py instead.
"""

import datetime as _dt

from app.db import connect


def _conn():
    return connect()


def _today() -> _dt.date:
    """Today, on the same clock the dates were written with.

    Every stored date comes from SQLite's `date('now')`, which is UTC. Ageing
    them against Python's `date.today()` - the LOCAL date - drifts by a day
    whenever the local date and the UTC date differ (any evening west of UTC).
    The staleness windows then fire a day early or late, and the boundary tests
    pass or fail with the time of day. This reads the clock the data came from,
    so the comparison is on one clock. See the meeting-view spec.
    """
    with connect() as conn:
        return _dt.date.fromisoformat(conn.execute("SELECT date('now')").fetchone()[0])



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
                   COUNT(DISTINCT k.TeamInitiativeID) AS InitiativeCount
            FROM Goals g
            LEFT JOIN TeamInitiativeGoals kg ON kg.GoalID = g.GoalID
            LEFT JOIN TeamInitiatives k
                   ON k.TeamInitiativeID = kg.TeamInitiativeID AND k.IsActive = 1
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
                   p.Description,
                   p.Code, p.FullTitle, p.Measure, p.Target, p.Cadence,
                   p.OwnerLabel, p.Colour,
                   COUNT(DISTINCT k.TeamInitiativeID) AS InitiativeCount
            FROM Priorities p
            LEFT JOIN TeamInitiativePriorities ip ON ip.PriorityID = p.PriorityID
            LEFT JOIN TeamInitiatives k
                   ON k.TeamInitiativeID = ip.TeamInitiativeID AND k.IsActive = 1
            GROUP BY p.PriorityID, p.PriorityName, p.PlanYear, p.Description,
                     p.Code, p.FullTitle, p.Measure, p.Target, p.Cadence,
                     p.OwnerLabel, p.Colour
            ORDER BY p.PriorityName
            """
        ).fetchall()
    return [dict(r) for r in rows]


def blueprint_priorities() -> list[dict]:
    """The six priorities as the blueprint stage needs them.

    One read shaped to the stage (blueprint-redesign 2.4): each priority with
    its code, full title, canonical description, key colour and active
    initiative count. The code, title and description come from app.priorities,
    which is read from the Dean's prototype; the count comes from the database,
    which decides which priorities exist.

    Ordered by code so the stage reads P01..P06, not alphabetically.
    """
    from app import priorities as canon
    from app import status as status_mod

    rows = priority_tiles()
    out = []
    for r in rows:
        name = r["PriorityName"]
        code = canon.code(name)
        out.append({
            "Name": name,
            "Code": code,
            "Title": canon.title(name),
            "Description": canon.description(name),
            "PlanYear": r["PlanYear"],
            "InitiativeCount": r["InitiativeCount"],
            "ColourToken": status_mod.priority_colour_token(code) if code else "--priority-1",
            # The governed fields, now stored (scope correction). Read from the
            # database so the screen and the register cannot drift; the
            # generated module is only the fallback for a name not in the DB.
            "Measure": r.get("Measure"),
            "Target": r.get("Target"),
            "Cadence": r.get("Cadence"),
            "Owner": r.get("OwnerLabel"),
            "Colour": r.get("Colour"),
        })
    # A priority with a code sorts by it; one without falls to the end, so the
    # canonical six always lead.
    out.sort(key=lambda p: (p["Code"] == "", p["Code"] or p["Name"]))
    return out


def initiative_signals(limit: int = 12) -> list[dict]:
    """Existing initiatives with their current progress, for the home strip.

    Carries `HasUpdate` so the strip can show "no update yet" distinctly from a
    reported zero - the same distinction the person card makes.
    """
    with _conn() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT k.Code, k.MIId, k.Title AS InitiativeName,
                       'Team Initiative' AS Level,
                       p.Name AS Owner,
                       lp.PercentComplete, lp.Status
                FROM TeamInitiatives k
                LEFT JOIN People p ON p.PersonID = k.OwnerID
                LEFT JOIN vw_LatestTeamInitiativeProgress lp
                       ON lp.TeamInitiativeID = k.TeamInitiativeID
                WHERE k.IsActive = 1
                ORDER BY k.MIId
                LIMIT ?
                """,
                (limit,),
            )
        ]
    for r in rows:
        r["HasUpdate"] = r["PercentComplete"] is not None
        # Templates key on the canon id; the internal Code is kept too.
        r["Code"] = r["MIId"] or r["Code"]
    return rows



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
    """Team Initiatives aligned to one goal (the dropped vw_GoalInitiatives).

    Keeps the old view's keys, with `Level` now the constant "Team Initiative"
    (the merged model has no Dean/D-1 tier) and `IsPrimary` always 0 (the
    register's goal columns are plain marks, with no primary among them).
    """
    with _conn() as conn:
        rows = conn.execute(
            "SELECT g.GoalNumber, g.ShortName AS Goal, k.TeamInitiativeID AS InitiativeID, "
            "       'Team Initiative' AS Level, k.MIId AS Code, k.Title AS InitiativeName, "
            "       p.PersonID AS OwnerID, p.Name AS Owner, 0 AS IsPrimary, "
            "       lp.PercentComplete, lp.Status "
            "FROM TeamInitiativeGoals ig "
            "JOIN Goals g       ON g.GoalID = ig.GoalID "
            "JOIN TeamInitiatives k ON k.TeamInitiativeID = ig.TeamInitiativeID AND k.IsActive = 1 "
            "LEFT JOIN People p ON p.PersonID = k.OwnerID "
            "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
            "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
            "WHERE g.GoalNumber = ? ORDER BY k.MIId",
            (goal_number,),
        ).fetchall()
    out = [dict(r) for r in rows]
    for r in out:
        r["Code"] = r["Code"] or ""
    return out


def priority_rows(priority_name: str) -> list[dict]:
    """Team Initiatives feeding one priority (the dropped vw_PriorityInitiatives)."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT pr.PriorityName AS Priority, pr.PlanYear, "
            "       k.TeamInitiativeID AS InitiativeID, 'Team Initiative' AS Level, "
            "       k.MIId AS Code, k.Title AS InitiativeName, "
            "       p.PersonID AS OwnerID, p.Name AS Owner, tp.IsPrimary, "
            "       lp.PercentComplete, lp.Status "
            "FROM TeamInitiativePriorities tp "
            "JOIN Priorities pr ON pr.PriorityID = tp.PriorityID "
            "JOIN TeamInitiatives k ON k.TeamInitiativeID = tp.TeamInitiativeID AND k.IsActive = 1 "
            "LEFT JOIN People p ON p.PersonID = k.OwnerID "
            "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
            "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
            "WHERE pr.PriorityName = ? ORDER BY k.MIId",
            (priority_name,),
        ).fetchall()
    out = [dict(r) for r in rows]
    for r in out:
        r["Code"] = r["Code"] or ""
    return out


def split_for_list(rows: list[dict]):
    """Group initiative rows by owner, ordered by code within each owner.

    Before the 2026-10-07 merge this split the prototype's rows into a Dean
    block and a D-1 block. The merged model has one tier (the register's Major
    Initiatives), so there is no Dean/D-1 divider: every row groups by owner.
    Returns (dean_rows, groups) with dean_rows always empty, so callers that
    check `if dean_rows` simply render no divider. Each group is
    {"owner", "rows"}.
    """
    dean: list = []

    by_owner: dict = {}
    for row in sorted(rows, key=lambda r: (r.get("Owner") or "", r["Code"])):
        by_owner.setdefault(row.get("Owner") or "Unassigned", []).append(row)

    groups = [{"owner": owner, "rows": rs} for owner, rs in sorted(by_owner.items())]
    return dean, groups


#: The groupings the cascade offers, with the field each groups on. Kept here
#: so the route and the template cannot disagree about what is offered.
GROUPINGS = {
    "owner": "Owner",
    "tier": "Level",
    "status": "Status",
}


def group_rows(rows: list[dict], by: str) -> list[dict]:
    """Group initiative rows by owner, tier, or status (blueprint-redesign 3.1).

    Returns [{"label", "rows"}] with only non-empty groups, so a label never
    renders without rows under it. The old split_for_list is kept for the
    default Dean-then-D-1 view; this is the toggle the spec adds.
    """
    field = GROUPINGS.get(by)
    if field is None:
        return []
    buckets: dict = {}
    for row in rows:
        # A missing status reads as Not started, matching the header counts.
        key = (row.get(field) or ("Not started" if field == "Status" else "—"))
        buckets.setdefault(key, []).append(row)
    out = []
    for label in sorted(buckets):
        rs = sorted(buckets[label], key=lambda r: r["Code"])
        out.append({"label": label, "rows": rs})
    return out



def status_counts(rows: list[dict]) -> list[dict]:
    """Counts by status for the list header.

    Deliberately counts and never a mean: the design's risk entry says Bill Gaudelli
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


def rollup_label(total: int, counts: list[dict]) -> str:
    """The header rollup: the total, then a per-status breakdown.

        "10 initiatives · 10 on track"
        "12 initiatives · 9 on track · 3 at risk"

    Not "On track 10", which reads as a status word glued to a number and
    hides that the 10 is a total (the Accurate Rollup Labels requirement). A
    count of zero is omitted so the header stays short.
    """
    parts = ["%d initiative%s" % (total, "" if total == 1 else "s")]
    for c in counts:
        if c["Count"] <= 0:
            continue
        parts.append("%d %s" % (c["Count"], c["Status"].lower()))
    return " \u00b7 ".join(parts)


# --- cards (task 5.2, 5.4) -----------------------------------------------

# The person-card spec's requirement says 14 days; its scenario gives 20 as an
# example. 14 is the threshold, because it satisfies the requirement and the
# scenario too (a 20-day-old update is still older than 14). The earlier comment
# here claimed "the spec says 20 days" - true of the scenario, false of the
# requirement. Amended 2026-10-06.
STALE_DAYS = 14

# How long without an update puts an initiative on the meeting agenda
# (meeting-view spec). Same number today, but a separate decision: this one is
# about the leadership meeting, the other about a person's one-to-one card.
ATTENTION_STALE_DAYS = 14


def initiative_card(mi_id: str):
    """Everything the initiative card needs, in one call.

    Sections: details, goal and priority tags, the Dean Initiatives it
    contributes to, latest progress, and the full diary newest first. Keyed by
    the canon's MIId (or the internal Code for a row with none).
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT k.TeamInitiativeID AS InitiativeID, k.MIId AS Code, "
            "       k.Title AS InitiativeName, k.Description, k.MIId, "
            "       'Team Initiative' AS Level, k.OwnerID, p.Name AS Owner "
            "FROM TeamInitiatives k LEFT JOIN People p ON p.PersonID = k.OwnerID "
            "WHERE (k.MIId = ? OR k.Code = ?) AND k.IsActive = 1",
            (mi_id, mi_id),
        ).fetchone()
        if row is None:
            return None
        card = dict(row)
        # A row with no MI-id falls back to its internal Code for display/links.
        card["Code"] = card["MIId"] or card["Code"]

        # Goal tags: the register's goal columns are plain marks (no primary).
        card["goal_tags"] = [
            dict(r)
            for r in conn.execute(
                "SELECT g.GoalNumber, g.ShortName, 0 AS IsPrimary "
                "FROM TeamInitiativeGoals kg JOIN Goals g ON g.GoalID = kg.GoalID "
                "WHERE kg.TeamInitiativeID = ? ORDER BY g.GoalNumber",
                (card["InitiativeID"],),
            )
        ]
        card["priority_tags"] = [
            dict(r)
            for r in conn.execute(
                "SELECT pr.PriorityName, pr.PlanYear, tp.IsPrimary "
                "FROM TeamInitiativePriorities tp JOIN Priorities pr ON pr.PriorityID = tp.PriorityID "
                "WHERE tp.TeamInitiativeID = ? ORDER BY pr.PriorityName",
                (card["InitiativeID"],),
            )
        ]
        # What this initiative contributes to: the Dean FY27 Priorities. The
        # merged model has no reverse "Fed by" direction, so only the forward
        # direction is returned, in the old rows' shape.
        card["connections"] = [
            dict(r)
            for r in conn.execute(
                "SELECT 'Contributes to' AS Direction, d.Code AS Code, d.Title AS InitiativeName, "
                "       NULL AS OwnerID, NULL AS Owner, NULL AS PercentComplete, NULL AS Status "
                "FROM TeamInitiativeDeanLinks kl JOIN DeanInitiatives d ON d.DeanInitiativeID = kl.DeanInitiativeID "
                "WHERE kl.TeamInitiativeID = ? ORDER BY d.Code",
                (card["InitiativeID"],),
            )
        ]
        latest = conn.execute(
            "SELECT UpdateDate, PercentComplete, Status, Note "
            "FROM vw_LatestTeamInitiativeProgress WHERE TeamInitiativeID = ?",
            (card["InitiativeID"],),
        ).fetchone()
        card["latest"] = dict(latest) if latest else None
        card["diary"] = [
            dict(r)
            for r in conn.execute(
                "SELECT UpdateDate, PercentComplete, Status, Note, "
                "       (SELECT Name FROM People e WHERE e.PersonID = pu.EnteredByID) AS EnteredBy "
                "FROM TeamInitiativeUpdates pu WHERE TeamInitiativeID = ? "
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
                "SELECT k.TeamInitiativeID AS InitiativeID, 'Team Initiative' AS Level, "
                "       k.MIId AS Code, k.Title AS InitiativeName, "
                "       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated "
                "FROM TeamInitiatives k "
                "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
                "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
                "WHERE k.OwnerID = ? AND k.IsActive = 1 ORDER BY k.MIId",
                (person_id,),
            )
        ]
    for r in rows:
        r["Code"] = r["Code"] or ""

    today = _today()
    for row in rows:
        if row["LastUpdated"] is None:
            row["NeedsUpdate"] = True
            # Whether a figure exists at all, distinct from what it says. A
            # missing update is NOT "0% complete" - the confirmed-data spec
            # requires the two to be distinguishable, and the template renders
            # from this rather than inferring zero from an empty percent.
            row["HasUpdate"] = False
        else:
            age = (today - _dt.date.fromisoformat(row["LastUpdated"])).days
            row["AgeDays"] = age
            row["NeedsUpdate"] = age > STALE_DAYS
            row["HasUpdate"] = True
    card = {"person": dict(person), "initiatives": rows}
    return card


# --- meeting and checks (tasks 8.5, 8.6) ---------------------------------

DEFAULT_MEETING_WINDOW_DAYS = 7


def default_since(days: int = DEFAULT_MEETING_WINDOW_DAYS) -> str:
    return (_today() - _dt.timedelta(days=days)).isoformat()


def meeting_updates(since: str):
    """Updates entered on or after `since`, grouped by owner.

    Rebuilt inline from TeamInitiativeUpdates + TeamInitiatives + People (the
    prototype's vw_RecentUpdates was dropped in the 2026-10-07 merge). The
    window and the ordering are the caller's job, as before.
    """
    with _conn() as conn:
        rows = conn.execute(
            "SELECT pu.UpdateDate, pu.CreatedAt, k.TeamInitiativeID AS InitiativeID, "
            "       k.MIId AS Code, k.Title AS InitiativeName, 'Team Initiative' AS Level, "
            "       o.PersonID AS OwnerID, o.Name AS Owner, "
            "       pu.PercentComplete, pu.Status, pu.Note, e.Name AS EnteredBy "
            "FROM TeamInitiativeUpdates pu "
            "JOIN TeamInitiatives k ON k.TeamInitiativeID = pu.TeamInitiativeID AND k.IsActive = 1 "
            "LEFT JOIN People o ON o.PersonID = k.OwnerID "
            "LEFT JOIN People e ON e.PersonID = pu.EnteredByID "
            "WHERE pu.UpdateDate >= ? "
            "ORDER BY pu.UpdateDate DESC, k.MIId, o.Name",
            (since,),
        ).fetchall()
    groups: dict = {}
    for row in rows:
        entry = dict(row)
        entry["Code"] = entry["Code"] or ""
        groups.setdefault(entry["Owner"] or "Unassigned", []).append(entry)
    return [{"owner": owner, "rows": rs} for owner, rs in sorted(groups.items())]


def attention_list() -> list[dict]:
    """Active initiatives needing the Dean's attention, most severe first.

    The meeting-view spec lists three reasons, in this order: Off track, then
    At risk, then an update older than ATTENTION_STALE_DAYS or missing. A
    stalled initiative outranks a shaky one, which is why Off track leads.

    Each entry carries a Reason string. A list of bare codes tells the Dean
    *that* something is wrong but not *what*, and the one-page agenda has no
    room for him to open every card to find out.

    An initiative matching more than one reason appears once, with the most
    severe reason, because seeing the same initiative twice on a one-page
    agenda wastes the page.

    Amended 2026-10-06. This function previously selected only `At risk` and
    carried a docstring asserting the spec "names At risk and only At risk",
    which the requirement text does not say. Both clauses of the requirement -
    Off track, and the staleness window - were missing. The requirement is the
    contract; the scenario below it was one example of it.
    """
    with _conn() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT k.MIId AS Code, k.Title AS InitiativeName, "
                "       'Team Initiative' AS Level, k.OwnerID, "
                "       p.Name AS Owner, lp.PercentComplete, lp.Status, lp.UpdateDate "
                "FROM TeamInitiatives k "
                "LEFT JOIN People p ON p.PersonID = k.OwnerID "
                "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
                "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
                "WHERE k.IsActive = 1"
            )
        ]
    for r in rows:
        r["Code"] = r["Code"] or ""

    today = _today()

    # Lower rank sorts first. Off track outranks At risk outranks stale.
    SEVERITY = {"Off track": 0, "At risk": 1}

    attention = []
    for row in rows:
        rank = None
        reason = None

        if row["Status"] in SEVERITY:
            rank = SEVERITY[row["Status"]]
            # The row shows the status as a badge, so the Reason would repeat it
            # verbatim for these two. The reason is still populated - the spec
            # requires every entry to carry one - and the template decides whether
            # to render it, rather than the query guessing at presentation.
            reason = row["Status"]

        age = None
        if row["UpdateDate"]:
            age = (today - _dt.date.fromisoformat(row["UpdateDate"])).days
            if age > ATTENTION_STALE_DAYS and rank is None:
                rank = 2
                reason = "No update in %d days" % age
        elif rank is None:
            rank = 2
            reason = "No update yet"

        if rank is None:
            continue

        row["AgeDays"] = age
        row["Reason"] = reason
        row["_rank"] = rank
        attention.append(row)

    # Severity first; then oldest update first, so the most stalled leads. A
    # missing update sorts as oldest, and a tie falls back to code so the order
    # is stable between renders - an agenda that reorders itself week to week
    # is harder to follow in a meeting.
    attention.sort(
        key=lambda r: (
            r["_rank"],
            r["UpdateDate"] or "",          # "" sorts before any date = oldest
            r["Code"],
        )
    )
    for row in attention:
        del row["_rank"]
    return attention


def data_checks() -> list[dict]:
    with _conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT Code, Issue FROM vw_DataChecks ORDER BY Code, Issue"
            )
        ]


# --- edit-form reads (tasks 8.2, 8.3, 8.4; deepened per `screen-reads`) -----
#
# Each edit screen gets ONE read shaped to it, returning the options a caller
# may choose from and the values currently chosen. The card read
# (initiative_card) is the model: a screen names one read, not a pile of
# single-table readers it combines. The six single-table readers these replace
# (all_goals, all_priorities, active_dean_initiatives, current_goal_tags,
# current_priority_tags, current_links) are deleted - their only callers moved
# here, and the tag reads already lived inside initiative_card.


def tag_edit_options(initiative_id: int) -> dict:
    """What the tags edit screen needs: both lists and what is chosen."""
    with _conn() as conn:
        goals = [
            dict(r)
            for r in conn.execute(
                "SELECT GoalID, GoalNumber, ShortName, FullName, Description "
                "FROM Goals ORDER BY GoalNumber"
            )
        ]
        priorities = [
            dict(r)
            for r in conn.execute(
                "SELECT PriorityID, PriorityName, PlanYear, Description "
                "FROM Priorities ORDER BY PlanYear, PriorityName"
            )
        ]
        chosen_goals = {
            r["GoalID"]
            for r in conn.execute(
                "SELECT GoalID FROM TeamInitiativeGoals WHERE TeamInitiativeID = ?",
                (initiative_id,),
            )
        }
        chosen_priorities = {
            r["PriorityID"]
            for r in conn.execute(
                "SELECT PriorityID FROM TeamInitiativePriorities WHERE TeamInitiativeID = ?",
                (initiative_id,),
            )
        }
    return {
        "goals": goals,
        "priorities": priorities,
        "chosen_goals": chosen_goals,
        "chosen_priorities": chosen_priorities,
    }


def link_edit_options(initiative_id: int) -> dict:
    """What the links edit screen needs: the Dean Initiatives and what is chosen.

    The merged model links a Team Initiative to a DeanInitiative (the register's
    X-matrix), not to another "Dean initiative". The returned rows alias
    DeanInitiativeID -> InitiativeID and Title -> InitiativeName so the existing
    edit_links template keeps working unchanged.
    """
    with _conn() as conn:
        deans = [
            dict(r)
            for r in conn.execute(
                "SELECT DeanInitiativeID AS InitiativeID, Code, Title AS InitiativeName "
                "FROM DeanInitiatives ORDER BY FiscalYear, Code"
            )
        ]
        chosen = {
            r["DeanInitiativeID"]
            for r in conn.execute(
                "SELECT DeanInitiativeID FROM TeamInitiativeDeanLinks WHERE TeamInitiativeID = ?",
                (initiative_id,),
            )
        }
    return {"deans": deans, "chosen": chosen}


# --- index screens (task 1.6; filters and sorting land in tasks 4.2, 4.3) ---


def all_initiatives(filters: dict | None = None) -> list[dict]:
    """Every active initiative, one row each, for the /initiatives index.

    One row per initiative, not per tag, so the index does not repeat an
    initiative that carries several goals or priorities. The goal and priority
    names are collected per initiative rather than joined, for the same reason.
    """
    with _conn() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT k.TeamInitiativeID AS InitiativeID, k.MIId AS Code, "
                "       k.Title AS InitiativeName, 'Team Initiative' AS Level, "
                "       p.PersonID AS OwnerID, p.Name AS Owner, "
                "       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated "
                "FROM TeamInitiatives k "
                "LEFT JOIN People p ON p.PersonID = k.OwnerID "
                "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
                "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
                "WHERE k.IsActive = 1 "
                "ORDER BY k.MIId"
            )
        ]
        goals: dict = {}
        for r in conn.execute(
            "SELECT kg.TeamInitiativeID, g.ShortName FROM TeamInitiativeGoals kg "
            "JOIN Goals g ON g.GoalID = kg.GoalID ORDER BY g.GoalNumber"
        ):
            goals.setdefault(r["TeamInitiativeID"], []).append(r["ShortName"])
        priorities: dict = {}
        for r in conn.execute(
            "SELECT tp.TeamInitiativeID, pr.PriorityName, pr.Code FROM TeamInitiativePriorities tp "
            "JOIN Priorities pr ON pr.PriorityID = tp.PriorityID "
            "ORDER BY pr.PriorityName"
        ):
            # The short CODE, so the table reads "P03" like its other columns,
            # rather than the bare short name ("Pathways", #7).
            priorities.setdefault(r["TeamInitiativeID"], []).append(r["Code"] or r["PriorityName"])

    today = _today()
    for row in rows:
        row["Code"] = row["Code"] or ""
        row["Goals"] = goals.get(row["InitiativeID"], [])
        row["Priorities"] = priorities.get(row["InitiativeID"], [])
        row["HasUpdate"] = row["LastUpdated"] is not None
        row["AgeDays"] = (
            (today - _dt.date.fromisoformat(row["LastUpdated"])).days
            if row["LastUpdated"] else None
        )
        row["NeedsUpdate"] = row["AgeDays"] is None or row["AgeDays"] > STALE_DAYS

    # Filters (blueprint-redesign 3.4). Applied in Python rather than SQL because
    # the goal/priority names are collected above, not joined; the set is small
    # (<100 initiatives) so this is not a performance concern.
    if filters:
        if filters.get("status"):
            want = filters["status"].replace("-", " ").lower()
            rows = [r for r in rows
                    if (r["Status"] or "Not started").lower() == want]
        if filters.get("owner"):
            want = filters["owner"].lower()
            rows = [r for r in rows if (r["Owner"] or "").lower() == want]
        if filters.get("tier"):
            rows = [r for r in rows if (r["Level"] or "").lower() == filters["tier"].lower()]
        if filters.get("goal"):
            want = filters["goal"]
            rows = [r for r in rows if want in r["Goals"]]
        if filters.get("priority"):
            want = filters["priority"]
            rows = [r for r in rows if want in r["Priorities"]]
        if filters.get("stale"):
            rows = [r for r in rows if r["NeedsUpdate"]]
    return rows

def all_people() -> list[dict]:
    """Every active person with their active initiative count and breakdown.

    Task 1.6 gives the list; task 4.3 adds the status breakdown and ordering by
    attention.
    """
    with _conn() as conn:
        people = [
            dict(r)
            for r in conn.execute(
                "SELECT PersonID, Name, Title, IsAdmin FROM People "
                "WHERE IsActive = 1 ORDER BY Name"
            )
        ]
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT k.OwnerID AS PersonID, COALESCE(lp.Status, 'Not started') AS Status "
                "FROM TeamInitiatives k "
                "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
                "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
                "WHERE k.IsActive = 1 AND k.OwnerID IS NOT NULL"
            )
        ]
    by_person: dict = {}
    for r in rows:
        by_person.setdefault(r["PersonID"], []).append(r["Status"])
    for person in people:
        statuses = by_person.get(person["PersonID"], [])
        person["InitiativeCount"] = len(statuses)
        person["Counts"] = status_counts([{"Status": s} for s in statuses])
    return people


# --- relationships, for the cascade rows (blueprint-redesign 3.2) -----------


def relationships_for(codes: list) -> dict:
    """What each Team Initiative contributes to, keyed by its code.

    Before the merge this read vw_InitiativeConnections (a D-1 -> Dean link in
    both directions). The merged model has one direction: a Team Initiative
    contributes to the Dean FY27 Priorities it is linked to. Returns {} for an
    empty input, so a caller never iterates a missing key.

    `codes` are the canon ids (MI-###). Owner/Status/PercentComplete are not
    attributes of a DeanInitiative, so those keys are None here; the caller renders
    the Dean title and code.
    """
    if not codes:
        return {}
    placeholders = ",".join("?" * len(codes))
    with _conn() as conn:
        id_to_code = {
            r["TeamInitiativeID"]: (r["MIId"] or r["Code"])
            for r in conn.execute(
                "SELECT TeamInitiativeID, MIId, Code FROM TeamInitiatives "
                "WHERE MIId IN (%s) OR Code IN (%s)" % (placeholders, placeholders),
                tuple(codes) + tuple(codes))
        }
        if not id_to_code:
            return {}
        ids = list(id_to_code)
        id_ph = ",".join("?" * len(ids))
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT kl.TeamInitiativeID AS InitiativeID, 'Contributes to' AS Direction, "
                "       d.Code AS Code, d.Title AS InitiativeName, "
                "       NULL AS Owner, NULL AS Status, NULL AS PercentComplete "
                "FROM TeamInitiativeDeanLinks kl JOIN DeanInitiatives d "
                "       ON d.DeanInitiativeID = kl.DeanInitiativeID "
                "WHERE kl.TeamInitiativeID IN (%s) "
                "ORDER BY Direction, d.Code" % id_ph, tuple(ids))
        ]
    out: dict = {}
    for r in rows:
        subject = id_to_code.get(r["InitiativeID"])
        if subject:
            out.setdefault(subject, []).append(r)
    return out


# --- coverage (blueprint-redesign 5.4) --------------------------------------


def coverage_summary() -> dict:
    """How complete the taxonomy is: which goals and priorities carry work.

    Counts and completeness only. No performance figure and no average is
    computed - the design forbids an aggregate rollup, and "is this covered" is
    a different question from "is this going well".
    """
    goals = goal_tiles()
    priorities = priority_tiles()

    def row(entries, label_key):
        out = []
        for e in entries:
            total = e["InitiativeCount"]
            out.append({
                "label": str(e[label_key]),
                "count": total,
                # "Covered" means at least one active initiative is tagged.
                "covered": total > 0,
            })
        return out

    goal_rows = row(goals, "ShortName")
    priority_rows = row(priorities, "PriorityName")
    covered = sum(1 for r in goal_rows + priority_rows if r["covered"])
    total = len(goal_rows) + len(priority_rows)
    return {
        "goals": goal_rows,
        "priorities": priority_rows,
        "covered": covered,
        "total": total,
        "percent": round(100 * covered / total) if total else 0,
    }


# --- the organizational layer, for the redesigned screens -------------------


def priority_detail(name: str) -> dict | None:
    """A priority with every governed field, plus the Team Initiatives that feed it.

    Reads the four fields the schema used to lack (measure, target, cadence,
    owner) and the Team Initiative layer, so a priority screen can show all of
    it rather than a name and a count.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT PriorityID, PriorityName, PlanYear, Description, Code, "
            "       FullTitle, Measure, Target, Cadence, OwnerLabel, Colour "
            "FROM Priorities WHERE PriorityName = ?", (name,)).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["team_initiatives"] = [
            dict(r) for r in conn.execute(
                "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, k.Status, "
                "       k.TargetStatus, k.ProposedTarget, t.Name AS Team "
                "FROM TeamInitiativePriorities tp "
                "JOIN TeamInitiatives k ON k.TeamInitiativeID = tp.TeamInitiativeID "
                "LEFT JOIN Teams t ON t.TeamID = k.TeamID "
                "WHERE tp.PriorityID = ? ORDER BY k.Code", (out["PriorityID"],))
        ]
        out["initiative_count"] = conn.execute(
            "SELECT COUNT(DISTINCT k.TeamInitiativeID) FROM TeamInitiativePriorities tp "
            "JOIN TeamInitiatives k ON k.TeamInitiativeID = tp.TeamInitiativeID AND k.IsActive = 1 "
            "WHERE tp.PriorityID = ?", (out["PriorityID"],)).fetchone()[0]
    return out


def team_overview() -> list[dict]:
    """The four teams, each with its Team Initiatives, and every field they carry."""
    with _conn() as conn:
        teams = [dict(r) for r in conn.execute(
            "SELECT TeamID, Name, Description FROM Teams ORDER BY Name")]
        mis = [dict(r) for r in conn.execute(
            "SELECT TeamInitiativeID, Code, MIId, Title, TeamID, SourceAreaID, StrategyAlign, "
            "       Initiatives, ProposedTarget, TargetStatus, "
            "       Status, Note FROM TeamInitiatives "
            # Order by the canon's public key, not the internal Code: the Code
            # follows the prototype's order, so the MI-id column read
            # MI-014, MI-016, MI-018, MI-015… (#N8).
            "ORDER BY MIId")]
        areas = {r["SourceAreaID"]: r["Name"]
                 for r in conn.execute("SELECT SourceAreaID, Name FROM SourceAreas")}
        for k in mis:
            k["SourceArea"] = areas.get(k["SourceAreaID"])
        for team in teams:
            team["team_initiatives"] = [k for k in mis if k["TeamID"] == team["TeamID"]]
    return teams


def team_initiative_cards() -> list[dict]:
    """The 29 Team Initiatives, each with the priorities it feeds.

    One read per screen: the initiative and its links together, so a card can
    render without a second query per initiative.
    """
    with _conn() as conn:
        mis = [dict(r) for r in conn.execute(
            "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, k.Initiatives, "
            "       k.ProposedTarget, k.TargetStatus, "
            "       k.Status, k.Note, k.TeamID, t.Name AS Team, "
            "       sa.Name AS SourceArea "
            "FROM TeamInitiatives k LEFT JOIN Teams t ON t.TeamID = k.TeamID "
            "LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID "
            "ORDER BY k.Code")]
        links: dict = {}
        for r in conn.execute(
                "SELECT tp.TeamInitiativeID, p.PriorityName, p.Code, p.Colour "
                "FROM TeamInitiativePriorities tp JOIN Priorities p ON p.PriorityID = tp.PriorityID "
                "ORDER BY p.Code"):
            links.setdefault(r["TeamInitiativeID"], []).append(dict(r))
        # The goal edge, so the table can show and link each initiative's goals.
        goals: dict = {}
        for r in conn.execute(
                "SELECT kg.TeamInitiativeID, g.GoalNumber, g.ShortName "
                "FROM TeamInitiativeGoals kg JOIN Goals g ON g.GoalID = kg.GoalID "
                "ORDER BY g.GoalNumber"):
            goals.setdefault(r["TeamInitiativeID"], []).append(dict(r))
    for k in mis:
        k["priorities"] = links.get(k["TeamInitiativeID"], [])
        k["goals"] = goals.get(k["TeamInitiativeID"], [])
        k["_GroupLabel"] = None
    return mis


def filter_and_group_team_initiatives(mis: list, filter_: str | None, group: str | None) -> list:
    """Apply the Team Initiatives table's filter and grouping (4.2), returning rows in
    display order with a `_GroupLabel` on the first row of each group.

    A filter, not a search: `needs_review` is the state leadership must decide,
    and grouping is by team or source area, the two axes the register uses.
    """
    rows = mis
    if filter_ == "needs_review":
        rows = [k for k in rows if k["TargetStatus"] == "needs_review"]
    if group not in ("team", "source_area"):
        # Default order is the canon's public key, matching the query.
        return sorted(rows, key=lambda k: k.get("MIId") or k["Code"])
    field = "Team" if group == "team" else "SourceArea"
    rows = sorted(rows, key=lambda k: (k.get(field) or "~", k.get("MIId") or k["Code"]))
    last = None
    for k in rows:
        label = k.get(field) or "Unassigned"
        if label != last:
            k["_GroupLabel"] = label
            last = label
    return rows


def goal_team_initiatives(goal_number: int) -> list[dict]:
    """The Team Initiatives aligned to one goal (interconnection-redesign 3.1).

    The edge the canon states and the schema now holds. One row per initiative,
    the team, the source area, the target status and the MI-id, so the goal
    page can render it without a query per row.
    """
    with _conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, "
            "       k.ProposedTarget, k.TargetStatus, t.Name AS Team, "
            "       sa.Name AS SourceArea "
            "FROM TeamInitiativeGoals kg "
            "JOIN TeamInitiatives k ON k.TeamInitiativeID = kg.TeamInitiativeID "
            "JOIN Goals g ON g.GoalID = kg.GoalID "
            "LEFT JOIN Teams t ON t.TeamID = k.TeamID "
            "LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID "
            "WHERE g.GoalNumber = ? ORDER BY k.Code",
            (goal_number,),
        ).fetchall()
    return [dict(r) for r in rows]


def team_detail(team_id: int):
    """One team with its Team Initiatives (interconnection-redesign 3.2).

    Returns the team and its initiative rows, or None when no such team exists, so
    route can 404 rather than render an empty page.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT TeamID, Name, Description FROM Teams WHERE TeamID = ?",
            (team_id,),
        ).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["team_initiatives"] = [dict(r) for r in conn.execute(
            "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, "
            "       k.ProposedTarget, k.TargetStatus, sa.Name AS SourceArea "
            "FROM TeamInitiatives k LEFT JOIN SourceAreas sa "
            "       ON sa.SourceAreaID = k.SourceAreaID "
            "WHERE k.TeamID = ? ORDER BY k.Code", (team_id,))]
        # The source areas this team's initiatives came from. A team is a different
        # axis from a source area, so the page names both.
    areas = []
    for k in out["team_initiatives"]:
        if k["SourceArea"] and k["SourceArea"] not in areas:
            areas.append(k["SourceArea"])
    out["source_areas"] = areas
    return out


def team_initiative_detail(mi_id: str):
    """One Team Initiative by its canon key, with every edge (interconnection 3.3).

    The initiative itself, its team, its source area, the goals it aligns to, and
    the priorities it feeds. Found by `MIId` because that is the canon's stable
    key; one without an MI-id is reachable by code instead.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, "
            "       k.Initiatives, k.ProposedTarget, k.Description, "
            "       k.TargetStatus, k.Status, k.Note, "
            "       t.TeamID, t.Name AS Team, sa.Name AS SourceArea "
            "FROM TeamInitiatives k "
            "LEFT JOIN Teams t ON t.TeamID = k.TeamID "
            "LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID "
            "WHERE k.MIId = ? OR k.Code = ?",
            (mi_id, mi_id),
        ).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["goals"] = [dict(r) for r in conn.execute(
            "SELECT g.GoalNumber, g.ShortName, g.FullName "
            "FROM TeamInitiativeGoals kg JOIN Goals g ON g.GoalID = kg.GoalID "
            "WHERE kg.TeamInitiativeID = ? ORDER BY g.GoalNumber", (out["TeamInitiativeID"],))]
        out["priorities"] = [dict(r) for r in conn.execute(
            "SELECT p.PriorityName, p.Code, p.Colour "
            "FROM TeamInitiativePriorities tp JOIN Priorities p ON p.PriorityID = tp.PriorityID "
            "WHERE tp.TeamInitiativeID = ? ORDER BY p.Code", (out["TeamInitiativeID"],))]
    return out


# --- search (overhaul-ui-ux-navigation 3.5) ---------------------------------


def search(term: str, limit: int = 10) -> list[dict]:
    """Match initiatives, people, goals and priorities by name or code.

    One query per kind, each capped, and merged into a single ranked list. A
    code match ranks above a name match, so typing "MAR-3" puts MAR-3 first.
    Built per request from the database: acceptable at this size (<100 rows),
    and revisit above ~1,000.
    """
    from urllib.parse import urlencode

    q = (term or "").strip()
    if not q:
        return []
    like = "%" + q.lower() + "%"
    code_like = q.lower() + "%"
    out = []
    with _conn() as conn:
        for kind, rows in (
            ("person", conn.execute(
                "SELECT PersonID AS key, Name AS label, '' AS code FROM People "
                "WHERE IsActive = 1 AND LOWER(Name) LIKE ? ORDER BY Name LIMIT ?",
                (like, limit))),
            ("goal", conn.execute(
                "SELECT GoalNumber AS key, ShortName AS label, '' AS code FROM Goals "
                "WHERE LOWER(ShortName) LIKE ? OR LOWER(COALESCE(FullName,'')) LIKE ? "
                "ORDER BY GoalNumber LIMIT ?",
                (like, like, limit))),
            ("priority", conn.execute(
                "SELECT PriorityName AS key, COALESCE(Code || ' ' || PriorityName, PriorityName) AS label, COALESCE(Code,'') AS code "
                "FROM Priorities WHERE LOWER(PriorityName) LIKE ? "
                "OR LOWER(COALESCE(FullTitle,'')) LIKE ? ORDER BY PriorityName LIMIT ?",
                (like, like, limit))),
            # The one initiative kind: the register's Team Initiatives, matched
            # by their canon id (MI-001) or their title. The prototype's
            # `Initiatives` were dropped in the 2026-10-07 merge.
            ("team-initiative", conn.execute(
                "SELECT MIId AS key, Title AS label, COALESCE(MIId,'') AS code "
                "FROM TeamInitiatives "
                "WHERE IsActive = 1 AND (LOWER(COALESCE(MIId,'')) LIKE ? OR LOWER(Title) LIKE ?) "
                "ORDER BY (LOWER(COALESCE(MIId,'')) LIKE ?) DESC, Code LIMIT ?",
                (like, like, code_like, limit))),
        ):
            for r in rows:
                r = dict(r)
                if kind == "person":
                    href = "/people/" + str(r["key"])
                elif kind == "goal":
                    href = "/goals/" + str(r["key"])
                elif kind == "team-initiative":
                    href = "/team-initiatives/" + str(r["key"])
                else:
                    href = "/priorities/" + urlencode({"": r["key"]})[1:]
                out.append({"kind": kind, "label": r["label"],
                            "code": r["code"], "href": href})
    # Codes first (an exact-ish code hit is usually what was meant), then label.
    out.sort(key=lambda r: (r["code"] == "", r["code"] or r["label"]))
    return out[:limit]


# --- meeting deltas (overhaul-ui-ux-navigation 6.3) -------------------------


def update_deltas(since: str) -> list[dict]:
    """Each update in the window with the progress and status before it.

    The "before" is the previous update for the same initiative by date, so the
    meeting can show "20% -> 30%" and "At risk -> On track" rather than only the
    current value. An initiative's first update has no previous, so its delta is
    marked as the first rather than invented as zero.
    """
    with _conn() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT pu.TeamInitiativeID, k.MIId AS Code, k.Title AS InitiativeName,
                       p.Name AS Owner,
                       pu.UpdateDate, pu.PercentComplete, pu.Status, pu.Note,
                       (SELECT pu2.PercentComplete FROM TeamInitiativeUpdates pu2
                        WHERE pu2.TeamInitiativeID = pu.TeamInitiativeID
                          AND (pu2.UpdateDate < pu.UpdateDate
                               OR (pu2.UpdateDate = pu.UpdateDate
                                   AND pu2.UpdateID < pu.UpdateID))
                        ORDER BY pu2.UpdateDate DESC, pu2.UpdateID DESC LIMIT 1)
                       AS PrevPercent,
                       (SELECT pu2.Status FROM TeamInitiativeUpdates pu2
                        WHERE pu2.TeamInitiativeID = pu.TeamInitiativeID
                          AND (pu2.UpdateDate < pu.UpdateDate
                               OR (pu2.UpdateDate = pu.UpdateDate
                                   AND pu2.UpdateID < pu.UpdateID))
                        ORDER BY pu2.UpdateDate DESC, pu2.UpdateID DESC LIMIT 1)
                       AS PrevStatus
                FROM TeamInitiativeUpdates pu
                JOIN TeamInitiatives k ON k.TeamInitiativeID = pu.TeamInitiativeID
                LEFT JOIN People p ON p.PersonID = k.OwnerID
                WHERE pu.UpdateDate >= ?
                ORDER BY pu.UpdateDate DESC, k.MIId
                """, (since,))
        ]
    for r in rows:
        r["IsFirst"] = r["PrevPercent"] is None and r["PrevStatus"] is None
        r["Code"] = r["Code"] or ""
    return rows


# --- the Dean Initiatives layer and the change log (register, 2026-10-07) -------


def dean_initiatives() -> list[dict]:
    """The Dean's own initiatives, FY26 then FY27, each with its priority AND the
    Team Initiatives that roll up to it.

    The register's "Dean KPI 26"/"Dean KPI 27" rows. FiscalYear 26 is complete,
    27 is in flight; PercentComplete is 0-100. The roll-up (which team
    initiatives contribute to each) is read from the link edge, so the Dean page
    can name them rather than show a bare count (design review, 2026-10-07).
    """
    with _conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT DeanInitiativeID, FiscalYear AS fiscal_year, Code AS code, "
            "       Title AS title, Description AS description, "
            "       PercentComplete AS percent_complete, "
            "       PriorityCode AS priority_code, PriorityTitle AS priority_title, "
            "       PriorityColour AS priority_colour "
            "FROM vw_DeanInitiatives ORDER BY FiscalYear, Code")]
        rolled: dict = {}
        for r in conn.execute(
                "SELECT kl.DeanInitiativeID, k.MIId, k.Title "
                "FROM TeamInitiativeDeanLinks kl "
                "JOIN TeamInitiatives k ON k.TeamInitiativeID = kl.TeamInitiativeID "
                "WHERE k.IsActive = 1 ORDER BY k.MIId"):
            rolled.setdefault(r["DeanInitiativeID"], []).append(
                {"mi_id": r["MIId"], "title": r["Title"]})
    for r in rows:
        r["initiatives"] = rolled.get(r["DeanInitiativeID"], [])
    return rows


def team_initiative_dean_links(mi_id: str) -> list[dict]:
    """The Dean FY27 items a Team Initiative contributes to."""
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT DeanCode AS dean_code, DeanTitle AS dean_title "
            "FROM vw_TeamInitiativeDeanLinks WHERE MIId = ? ORDER BY DeanCode",
            (mi_id,))]


def recent_changes(limit: int = 100) -> list[dict]:
    """The change log, newest first, with who made each change."""
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT a.CreatedAt AS created_at, p.Name AS person, a.Action AS action, "
            "       a.EntityType AS entity_type, a.EntityKey AS entity_key "
            "FROM AuditLog a LEFT JOIN People p ON p.PersonID = a.PersonID "
            "ORDER BY a.CreatedAt DESC, a.AuditID DESC LIMIT ?", (limit,))]
