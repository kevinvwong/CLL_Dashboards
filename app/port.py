"""Cross-engine SQL for the two stores (change `adopt-rev2-store`).

One function per ported query, each returning the app's existing key set under
either engine. Every function takes an open connection (from `app.db.connect`),
asks it `engine()`, and runs the engine's formulation. When `engine` is "sqlite"
the result is byte-for-byte what `app/queries.py` / `app/repo.py` produce today.

The column mapping app-model -> Rev2 lives here, so a query reads the same code
for both stores and the two schemas cannot drift apart in two copies of a body.

Differences that are NOT just naming:
  * placeholders:   sqlite '?', pymssql '%s'
  * current state:  Rev2 derives it (vw_latest_update / vw_initiative_current);
                    SQLite reads vw_LatestTeamInitiativeProgress. The port never
                    reads a stored progress/status cache (design D3).
  * owner:          SQLite TeamInitiatives.OwnerID (single FK); Rev2
                    vw_primary_reporting_owner (Reporting Owner + primary).
  * identity:       the app's int PersonID becomes Rev2 person.person_id (a
                    string like 'p-01'); the public initiative key is MIId ->
                    Rev2 initiative_code. The route-facing shapes keep the app's
                    key names regardless of engine.
"""

from app.db import connect, engine, dialect


def _dicts(rows):
    return [dict(r) for r in rows]


#: ---------------------------------------------------------------------------
#: Read ports (wired into app/queries.py task-group by task-group). A function
#: whose engine is sqlite returns exactly what app/queries.py produced before;
#: the mssql formulation is written to match it, aliasing Rev2 columns to the
#: app's key names on select so the templates and groupers are unchanged.
#: ---------------------------------------------------------------------------


def goal_tiles(conn):
    """One row per Strategy 2035 goal with its active initiative count.

    sqlite: Goals LEFT JOIN TeamInitiativeGoals LEFT JOIN TeamInitiatives.
    mssql : goal LEFT JOIN initiative_goal LEFT JOIN initiative (D-1 only - a
            Dean's goal membership is derived, not an initiative of work).
    """
    if engine(conn) == "mssql":
        return _dicts(conn.execute(
            "SELECT g.goal_number AS GoalNumber, g.short_label AS ShortName, "
            "       g.canonical_title AS FullName, "
            "       COUNT(DISTINCT i.initiative_id) AS InitiativeCount "
            "FROM dbo.goal g "
            "LEFT JOIN dbo.initiative_goal ig ON ig.goal_id = g.goal_id "
            "LEFT JOIN dbo.initiative i ON i.initiative_id = ig.initiative_id "
            "       AND i.active_flag = 1 AND i.initiative_level = 'D-1' "
            "GROUP BY g.goal_id, g.goal_number, g.short_label, g.canonical_title "
            "ORDER BY g.goal_number").fetchall())
    return _dicts(conn.execute(
        """
        SELECT g.GoalNumber, g.ShortName, g.FullName,
               COUNT(DISTINCT k.TeamInitiativeID) AS InitiativeCount
        FROM Goals g
        LEFT JOIN TeamInitiativeGoals kg ON kg.GoalID = g.GoalID
        LEFT JOIN TeamInitiatives k
               ON k.TeamInitiativeID = kg.TeamInitiativeID AND k.IsActive = 1
        GROUP BY g.GoalID, g.GoalNumber, g.ShortName, g.FullName
        ORDER BY g.GoalNumber
        """
    ).fetchall())


def _plan_year_int(planning_period: str):
    """Rev2 stores the plan year as a planning_period string ('FY2027'); the app
    as an int (2027). Parse it so an annual view compares like with like."""
    import re
    m = re.search(r"(\d{4})", planning_period or "")
    return int(m.group(1)) if m else None


def priority_tiles(conn):
    """One row per annual priority with the governed fields and a count.

    sqlite reads the register's stored Measure/Target/Cadence/OwnerLabel/Colour.
    Rev2 does not store those five columns (see design Open issue), so they come
    back None under mssql and the screen falls back to the generated canon in
    app.priorities for display. PriorityName is projected to the app's SHORT name
    via app.priorities.short_for_code(priority_code) (the code is the durable
    key on both stores, and Rev2's priority_name is the full title), and PlanYear
    is the int year, so the result matches sqlite's shape.
    """
    if engine(conn) == "mssql":
        from app import priorities as canon

        rows = _dicts(conn.execute(
            "SELECT ap.priority_name, ap.planning_period, ap.description, "
            "       ap.priority_code, "
            "       COUNT(DISTINCT i.initiative_id) AS InitiativeCount "
            "FROM dbo.annual_priority ap "
            "LEFT JOIN dbo.initiative_priority ip ON ip.priority_id = ap.priority_id "
            "LEFT JOIN dbo.initiative i ON i.initiative_id = ip.initiative_id "
            "       AND i.active_flag = 1 AND i.initiative_level = 'D-1' "
            "GROUP BY ap.priority_id, ap.priority_name, ap.planning_period, "
            "         ap.description, ap.priority_code "
            "ORDER BY ap.priority_code").fetchall())
        out = []
        for r in rows:
            code = r["priority_code"]
            out.append({
                "PriorityName": canon.short_for_code(code) or r["priority_name"],
                "PlanYear": _plan_year_int(r["planning_period"]),
                "Description": r["description"],
                "Code": code,
                "FullTitle": canon.title_for_code(code) or r["priority_name"],
                "Measure": None, "Target": None, "Cadence": None,
                "OwnerLabel": None, "Colour": None,
                "InitiativeCount": r["InitiativeCount"],
            })
        return out
    return _dicts(conn.execute(
        """
        SELECT p.PriorityName, p.PlanYear, p.Description,
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
    ).fetchall())


def goal_by_number(conn, goal_number):
    if engine(conn) == "mssql":
        row = conn.execute(
            "SELECT goal_number AS GoalNumber, short_label AS ShortName, "
            "       canonical_title AS FullName, canonical_description AS Description "
            "FROM dbo.goal WHERE goal_number = %s", (goal_number,)).fetchone()
        return dict(row) if row else None
    row = conn.execute(
        "SELECT GoalNumber, ShortName, FullName, Description "
        "FROM Goals WHERE GoalNumber = ?", (goal_number,)).fetchone()
    return dict(row) if row else None


def priority_by_name(conn, name):
    from app import priorities as canon

    if engine(conn) == "mssql":
        code = canon.code(name)
        if not code:
            return None
        row = conn.execute(
            "SELECT priority_name, planning_period, description "
            "FROM dbo.annual_priority WHERE priority_code = %s", (code,)).fetchone()
        if not row:
            return None
        return {
            "PriorityName": canon.short_for_code(code) or row["priority_name"],
            "PlanYear": _plan_year_int(row["planning_period"]),
            "Description": row["description"],
        }
    row = conn.execute(
        "SELECT PriorityName, PlanYear, Description "
        "FROM Priorities WHERE PriorityName = ?", (name,)).fetchone()
    return dict(row) if row else None


def plan_years(conn):
    if engine(conn) == "mssql":
        return [int(r["PlanYear"]) for r in conn.execute(
            "SELECT DISTINCT CAST(SUBSTRING(planning_period, 3, 4) AS INT) AS PlanYear "
            "FROM dbo.annual_priority WHERE priority_code IS NOT NULL "
            "ORDER BY PlanYear DESC") if r["PlanYear"] is not None]
    return [r["PlanYear"] for r in conn.execute(
        "SELECT DISTINCT PlanYear FROM Priorities "
        "WHERE Code IS NOT NULL ORDER BY PlanYear DESC")]


def _appmeta(conn, key):
    """Read one AppMeta key. Rev2 has held this as `app_meta` since change
    `rev2-full-reconciliation` / 008_app_layer.sql, so both engines read their
    own store. ([Key]/[Value] are reserved words, bracketed on mssql.)"""
    if engine(conn) == "mssql":
        row = conn.execute(
            "SELECT [value] AS Value FROM dbo.app_meta WHERE [key] = %s", (key,)).fetchone()
        return row["Value"] if row else None
    row = conn.execute(
        "SELECT Value FROM AppMeta WHERE Key = ?", (key,)).fetchone()
    return row["Value"] if row else None


def current_plan_year(conn):
    v = _appmeta(conn, "current_plan_year")
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def dataset_provenance(conn):
    return _appmeta(conn, "dataset_provenance") or "unknown"


def milestones_for_year(conn, year: int):
    """The milestones for one plan year's priorities, keyed by priority code.

    Rev2's milestone.priority_id is PRI-<Code>-FY<year>; sqlite joins Milestones
    to the year-scoped Priorities row. Returns {code: [milestone dict,...]}.
    (change `rev2-full-reconciliation` task 3.x / adopt-rev2-store Open issue 1.)
    """
    if engine(conn) == "mssql":
        rows = _dicts(conn.execute(
            "SELECT ap.priority_code AS Code, m.name AS Name, m.status AS Status, "
            "       CONVERT(VARCHAR(10), m.planned_date, 23) AS PlannedDate, "
            "       CONVERT(VARCHAR(10), m.date_met, 23) AS DateMet, "
            "       m.owner_label AS OwnerLabel, m.evidence_url AS EvidenceURL "
            "FROM dbo.milestone m JOIN dbo.annual_priority ap ON ap.priority_id = m.priority_id "
            "WHERE m.active_flag = 1 AND ap.planning_period = %s "
            "ORDER BY ap.priority_code, m.sort_order, m.milestone_id",
            ("FY%d" % year,)).fetchall())
        by_code: dict = {}
        for r in rows:
            by_code.setdefault(r.pop("Code"), []).append(r)
        return by_code
    rows = _dicts(conn.execute(
        "SELECT p.Code, m.Name, m.Status, m.PlannedDate, m.DateMet, "
        "       m.OwnerLabel, m.EvidenceURL "
        "FROM Milestones m JOIN Priorities p ON p.PriorityID = m.PriorityID "
        "WHERE m.IsActive = 1 AND p.Code IS NOT NULL AND p.PlanYear = ? "
        "ORDER BY p.Code, m.SortOrder, m.MilestoneID",
        (year,)).fetchall())
    by_code = {}
    for r in rows:
        by_code.setdefault(r.pop("Code"), []).append(r)
    return by_code
