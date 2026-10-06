"""Read queries for screens that are not served directly by a view.

The seven views in db/schema.sql cover the list and card screens. The home
screen needs an initiative count per goal and per priority, which no view
provides, so it lives here. Writes go through app/repo.py instead.
"""

from app.db import connect


def _conn():
    return connect()


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
                SELECT i.Code, i.InitiativeName, i.Level,
                       p.Name AS Owner,
                       lp.PercentComplete, lp.Status
                FROM Initiatives i
                JOIN People p ON p.PersonID = i.OwnerID
                LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID
                WHERE i.IsActive = 1
                ORDER BY i.Code
                LIMIT ?
                """,
                (limit,),
            )
        ]
    for r in rows:
        r["HasUpdate"] = r["PercentComplete"] is not None
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
                # Status and PercentComplete are carried too, so the detail's
                # relationship list can show each connected initiative's health
                # in BOTH directions (blueprint-redesign 3.3) rather than only
                # the Fed-by direction, which happened to be the only one the
                # old template rendered a status for.
                "SELECT Direction, Code, InitiativeName, OwnerID, Owner, "
                "       PercentComplete, Status "
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
    import datetime as _dt

    with _conn() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT i.Code, i.InitiativeName, i.Level, i.OwnerID, "
                "       p.Name AS Owner, lp.PercentComplete, lp.Status, lp.UpdateDate "
                "FROM Initiatives i "
                "JOIN People p ON p.PersonID = i.OwnerID "
                "LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID "
                "WHERE i.IsActive = 1"
            )
        ]

    today = _dt.date.today()

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
                "SELECT GoalID FROM InitiativeGoals WHERE InitiativeID = ?",
                (initiative_id,),
            )
        }
        chosen_priorities = {
            r["PriorityID"]
            for r in conn.execute(
                "SELECT PriorityID FROM InitiativePriorities WHERE InitiativeID = ?",
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
    """What the links edit screen needs: the Dean targets and what is chosen."""
    with _conn() as conn:
        deans = [
            dict(r)
            for r in conn.execute(
                "SELECT InitiativeID, Code, InitiativeName FROM Initiatives "
                "WHERE Level = 'Dean' AND IsActive = 1 ORDER BY Code"
            )
        ]
        chosen = {
            r["DeanInitiativeID"]
            for r in conn.execute(
                "SELECT DeanInitiativeID FROM InitiativeLinks WHERE InitiativeID = ?",
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
    import datetime as _dt

    with _conn() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT i.InitiativeID, i.Code, i.InitiativeName, i.Level, "
                "       p.PersonID AS OwnerID, p.Name AS Owner, "
                "       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated "
                "FROM Initiatives i "
                "JOIN People p ON p.PersonID = i.OwnerID "
                "LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID "
                "WHERE i.IsActive = 1 "
                "ORDER BY i.Level, i.Code"
            )
        ]
        goals: dict = {}
        for r in conn.execute(
            "SELECT ig.InitiativeID, g.ShortName FROM InitiativeGoals ig "
            "JOIN Goals g ON g.GoalID = ig.GoalID ORDER BY g.GoalNumber"
        ):
            goals.setdefault(r["InitiativeID"], []).append(r["ShortName"])
        priorities: dict = {}
        for r in conn.execute(
            "SELECT ip.InitiativeID, pr.PriorityName FROM InitiativePriorities ip "
            "JOIN Priorities pr ON pr.PriorityID = ip.PriorityID "
            "ORDER BY pr.PriorityName"
        ):
            priorities.setdefault(r["InitiativeID"], []).append(r["PriorityName"])

    today = _dt.date.today()
    for row in rows:
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
                "SELECT PersonID, Status FROM vw_PersonInitiatives"
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
    """What each initiative feeds and what feeds it, keyed by its code.

    vw_InitiativeConnections is keyed on the SUBJECT's InitiativeID and returns
    the RELATED initiative's code. So this resolves the subject ids first, then
    reads the connections for all of them in one query rather than one per row.

    Returns {} for an empty input, so a caller never iterates a missing key.
    """
    if not codes:
        return {}
    placeholders = ",".join("?" * len(codes))
    with _conn() as conn:
        id_to_code = {
            r["InitiativeID"]: r["Code"]
            for r in conn.execute(
                "SELECT InitiativeID, Code FROM Initiatives WHERE Code IN (%s)"
                % placeholders, tuple(codes))
        }
        if not id_to_code:
            return {}
        ids = list(id_to_code)
        id_ph = ",".join("?" * len(ids))
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT InitiativeID, Direction, Code, InitiativeName, Owner, "
                "       Status, PercentComplete "
                "FROM vw_InitiativeConnections WHERE InitiativeID IN (%s) "
                "ORDER BY Direction, Code" % id_ph, tuple(ids))
        ]
    out: dict = {}
    for r in rows:
        subject = id_to_code.get(r["InitiativeID"])
        if subject:
            out.setdefault(subject, []).append(r)
    return out
