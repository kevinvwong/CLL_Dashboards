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


#: ---------------------------------------------------------------------------
#: Cascade + index reads (adopt-rev2-store task group 3)
#:
#: Rev2 derives current progress/status from the update history
#: (vw_latest_update / vw_initiative_current); status_at_update already holds the
#: app's vocabulary words. The D-1 initiative layer maps to initiative_level='D-1'
#: with initiative_code == the app's MIId. Owner is vw_initiative_summary's
#: Reporting-Owner-primary columns. LastUpdated is a date, emitted ISO.
#: ---------------------------------------------------------------------------


def _d1_summary_sql(prefix=""):
    """The shared projection of one active D-1 row, used by the index/cascade
    mssql ports. Returns columns aliased to the app's key names."""
    return (
        "SELECT s.initiative_id AS InitiativeID, s.initiative_code AS Code, "
        "       s.initiative_name AS InitiativeName, 'Team Initiative' AS Level, "
        "       s.owner_person_id AS OwnerID, s.owner_name AS Owner, "
        "       CAST(s.progress_current AS FLOAT) AS PercentComplete, "
        "       s.status_current AS Status, "
        "       CONVERT(VARCHAR(10), s.last_updated, 23) AS LastUpdated "
        f"FROM {prefix}dbo.vw_initiative_summary s "
        "WHERE s.initiative_level = 'D-1'"
    )


def goal_rows(conn, goal_number):
    """Team Initiatives aligned to one goal (sqlite: the dropped
    vw_GoalInitiatives). mssql sources the same card from vw_goal_initiatives."""
    if engine(conn) == "mssql":
        rows = _dicts(conn.execute(
            "SELECT g.goal_number AS GoalNumber, g.short_label AS Goal, "
            "       s.initiative_id AS InitiativeID, 'Team Initiative' AS Level, "
            "       s.initiative_code AS Code, s.initiative_name AS InitiativeName, "
            "       s.owner_person_id AS OwnerID, s.owner_name AS Owner, 0 AS IsPrimary, "
            "       CAST(s.progress_current AS FLOAT) AS PercentComplete, "
            "       s.status_current AS Status "
            "FROM dbo.vw_goal_initiatives s "
            "JOIN dbo.goal g ON g.goal_id = s.goal_id "
            "WHERE g.goal_number = %s AND s.initiative_level = 'D-1' "
            "ORDER BY s.initiative_code",
            (goal_number,)).fetchall())
        for r in rows:
            r["Code"] = r["Code"] or ""
        return rows
    rows = _dicts(conn.execute(
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
        (goal_number,)).fetchall())
    for r in rows:
        r["Code"] = r["Code"] or ""
    return rows


def priority_rows(conn, priority_name):
    """Team Initiatives feeding one priority. sqlite keys by the priority's short
    name; Rev2 by its code (canon.code resolves name->code)."""
    if engine(conn) == "mssql":
        from app import priorities as canon
        code = canon.code(priority_name)
        if not code:
            return []
        short = canon.short_for_code(code) or priority_name
        rows = _dicts(conn.execute(
            "SELECT s.priority_id, ap.planning_period AS PlanYear, "
            "       s.initiative_id AS InitiativeID, 'Team Initiative' AS Level, "
            "       s.initiative_code AS Code, s.initiative_name AS InitiativeName, "
            "       s.owner_person_id AS OwnerID, s.owner_name AS Owner, "
            "       CASE WHEN s.priority_relationship = 'Primary' THEN 1 ELSE 0 END AS IsPrimary, "
            "       CAST(s.progress_current AS FLOAT) AS PercentComplete, "
            "       s.status_current AS Status "
            "FROM dbo.vw_priority_initiatives s "
            "JOIN dbo.annual_priority ap ON ap.priority_id = s.priority_id "
            "WHERE ap.priority_code = %s AND s.initiative_level = 'D-1' "
            "ORDER BY s.initiative_code",
            (code,)).fetchall())
        # PriorityName must be the app's short name (the sqlite key), not Rev2's
        # full title.
        for r in rows:
            r["Priority"] = short
            r["PriorityName"] = short
            r["PlanYear"] = _plan_year_int(r["PlanYear"])
            r["Code"] = r["Code"] or ""
        return rows
    rows = _dicts(conn.execute(
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
        (priority_name,)).fetchall())
    for r in rows:
        r["Code"] = r["Code"] or ""
    return rows


def all_initiatives(conn):
    """Every active D-1 initiative, one row each, with LastUpdated for the
    staleness flag the index shows."""
    if engine(conn) == "mssql":
        return _dicts(conn.execute(_d1_summary_sql() + " ORDER BY Code").fetchall())
    return _dicts(conn.execute(
        "SELECT k.TeamInitiativeID AS InitiativeID, k.MIId AS Code, "
        "       k.Title AS InitiativeName, 'Team Initiative' AS Level, "
        "       p.PersonID AS OwnerID, p.Name AS Owner, "
        "       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated "
        "FROM TeamInitiatives k "
        "LEFT JOIN People p ON p.PersonID = k.OwnerID "
        "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
        "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
        "WHERE k.IsActive = 1 "
        "ORDER BY k.MIId").fetchall())


def initiative_tag_names(conn):
    """The goal short names and priority codes per initiative, for the index's
    collection columns. Returns ({initiative_id: [goal shortnames]},
    {initiative_id: [priority codes]}) keyed by the row's InitiativeID (on mssql
    the Rev2 initiative_id string; on sqlite TeamInitiativeID int) so the caller
    can join on row['InitiativeID'] identically on both engines."""
    if engine(conn) == "mssql":
        goals: dict = {}
        for r in conn.execute(
                "SELECT ig.initiative_id AS iid, g.short_label AS nm "
                "FROM dbo.initiative_goal ig JOIN dbo.goal g ON g.goal_id = ig.goal_id "
                "JOIN dbo.initiative i ON i.initiative_id = ig.initiative_id "
                "WHERE i.initiative_level = 'D-1' AND i.active_flag = 1 "
                "ORDER BY g.goal_number"):
            goals.setdefault(r["iid"], []).append(r["nm"])
        pri: dict = {}
        for r in conn.execute(
                "SELECT ip.initiative_id AS iid, ap.priority_code AS Code "
                "FROM dbo.initiative_priority ip "
                "JOIN dbo.annual_priority ap ON ap.priority_id = ip.priority_id "
                "JOIN dbo.initiative i ON i.initiative_id = ip.initiative_id "
                "WHERE i.initiative_level = 'D-1' AND i.active_flag = 1 "
                "ORDER BY ip.priority_id"):
            pri.setdefault(r["iid"], []).append(r["Code"])
        return goals, pri
    goals = {}
    for r in conn.execute(
            "SELECT kg.TeamInitiativeID AS iid, g.ShortName AS nm FROM TeamInitiativeGoals kg "
            "JOIN Goals g ON g.GoalID = kg.GoalID ORDER BY g.GoalNumber"):
        goals.setdefault(r["iid"], []).append(r["nm"])
    pri = {}
    for r in conn.execute(
            "SELECT tp.TeamInitiativeID AS iid, pr.Code AS Code FROM TeamInitiativePriorities tp "
            "JOIN Priorities pr ON pr.PriorityID = tp.PriorityID ORDER BY pr.PriorityName"):
        pri.setdefault(r["iid"], []).append(r["Code"])
    return goals, pri


def all_people(conn):
    """People + per-person status rows (for the attention count). Returns
    (people, stat_rows); the per-person aggregation stays in queries.py.

    On mssql PersonID is projected to the app's int form ('PERS-3' -> 3) in both
    the people list and the stat rows, so the caller's grouping (keyed by
    PersonID) joins identically on both engines. IsAdmin is derived from
    person_role/role (reconciled in 008), not the dropped People column.
    """
    if engine(conn) == "mssql":
        admins = {r["PersonID"] for r in conn.execute(
            "SELECT pr.person_id AS PersonID FROM dbo.person_role pr "
            "JOIN dbo.role ro ON ro.role_id = pr.role_id WHERE ro.name IN "
            "('PlatformAdmin','admin')")}
        people = []
        for r in conn.execute(
                "SELECT person_id AS raw, display_name AS Name, working_title AS Title "
                "FROM dbo.person WHERE active_flag = 1 ORDER BY display_name"):
            p = {"PersonID": _pid_int(r["raw"]), "Name": r["Name"],
                 "Title": r["Title"], "IsAdmin": 1 if r["raw"] in admins else 0}
            people.append(p)
        stats = []
        for r in conn.execute(
                "SELECT o.person_id AS raw, "
                "       COALESCE(s.status_current, 'Not started') AS Status "
                "FROM dbo.initiative_owner o "
                "JOIN dbo.vw_initiative_summary s ON s.initiative_id = o.initiative_id "
                "WHERE o.ownership_role = 'Reporting Owner' AND o.primary_flag = 1 "
                "  AND o.effective_end IS NULL "
                "  AND s.initiative_level = 'D-1'"):
            stats.append({"PersonID": _pid_int(r["raw"]), "Status": r["Status"]})
        return people, stats
    people = _dicts(conn.execute(
        "SELECT PersonID, Name, Title, IsAdmin FROM People "
        "WHERE IsActive = 1 ORDER BY Name").fetchall())
    stats = _dicts(conn.execute(
        "SELECT k.OwnerID AS PersonID, COALESCE(lp.Status, 'Not started') AS Status "
        "FROM TeamInitiatives k "
        "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
        "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
        "WHERE k.IsActive = 1 AND k.OwnerID IS NOT NULL").fetchall())
    return people, stats


#: ---------------------------------------------------------------------------
#: Team-initiative layer (adopt-rev2-store task group 4). mssql sources the
#: register's richer fields from the 009 columns on dbo.initiative and resolves
#: team/source-area names through dbo.team / dbo.source_area. TeamID/TeamInitiativeID
#: are projected to the app's int form where the caller keys on an int.
#: ---------------------------------------------------------------------------


def _team_id_int(team_id):
    try:
        return int(str(team_id).split("-", 1)[1])
    except (IndexError, ValueError, TypeError):
        return None


#: 'PERS-N' -> the app's int PersonID. Defined once here so the person-facing
#: ports (all_people, search, person_card) and the owner mapping share it.
def _pid_int(person_id):
    try:
        return int(str(person_id).split("-", 1)[1])
    except (IndexError, ValueError, TypeError):
        return None


def _source_area_name_map(conn):
    """Rev2 source_area.id -> name; the app's SourceArea key is its name, so this
    is how the richer rows carry SourceArea. Returns {source_area_id: name}."""
    return {r["iid"]: r["nm"] for r in conn.execute(
        "SELECT source_area_id AS iid, name AS nm FROM dbo.source_area")}


def team_overview(conn):
    """The four teams, each with its Team Initiatives, and every field they carry."""
    if engine(conn) == "mssql":
        areas = {r["iid"]: r["nm"] for r in conn.execute(
            "SELECT source_area_id AS iid, name AS nm FROM dbo.source_area")}
        teams = []
        for t in conn.execute(
                "SELECT team_id AS tid, team_name AS Name, description AS Description "
                "FROM dbo.team WHERE active_flag = 1 ORDER BY team_name"):
            teams.append({"TeamID": _team_id_int(t["tid"]), "Name": t["Name"],
                          "Description": t["Description"]})
        mis = []
        for r in conn.execute(
                "SELECT i.initiative_id AS TeamInitiativeID, i.initiative_code AS Code, "
                "       i.initiative_code AS MIId, i.initiative_name AS Title, "
                "       i.strategy_align AS StrategyAlign, i.initiatives_text AS Initiatives, "
                "       i.proposed_target AS ProposedTarget, i.target_status AS TargetStatus, "
                "       s.status_current AS Status, NULL AS Note, "
                "       i.team_id AS teamid, i.source_area_id AS said "
                "FROM dbo.initiative i "
                "LEFT JOIN dbo.vw_initiative_summary s ON s.initiative_id = i.initiative_id "
                "WHERE i.initiative_level = 'D-1' AND i.active_flag = 1 "
                "ORDER BY i.initiative_code"):
            mis.append({
                "TeamInitiativeID": r["TeamInitiativeID"], "Code": r["Code"],
                "MIId": r["MIId"], "Title": r["Title"], "StrategyAlign": r["StrategyAlign"],
                "Initiatives": r["Initiatives"], "ProposedTarget": r["ProposedTarget"],
                "TargetStatus": r["TargetStatus"], "Status": r["Status"], "Note": r["Note"],
                "TeamID": _team_id_int(r["teamid"]), "SourceArea": areas.get(r["said"]),
            })
        for team in teams:
            team["team_initiatives"] = [k for k in mis if k["TeamID"] == team["TeamID"]]
        return teams
    teams = _dicts(conn.execute(
        "SELECT TeamID, Name, Description FROM Teams ORDER BY Name").fetchall())
    mis = _dicts(conn.execute(
        "SELECT TeamInitiativeID, Code, MIId, Title, TeamID, SourceAreaID, StrategyAlign, "
        "       Initiatives, ProposedTarget, TargetStatus, Status, Note FROM TeamInitiatives "
        "ORDER BY MIId").fetchall())
    areas = {r["SourceAreaID"]: r["Name"] for r in conn.execute("SELECT SourceAreaID, Name FROM SourceAreas")}
    for k in mis:
        k["SourceArea"] = areas.get(k["SourceAreaID"])
    for team in teams:
        team["team_initiatives"] = [k for k in mis if k["TeamID"] == team["TeamID"]]
    return teams


def team_initiative_cards(conn):
    """The 29 Team Initiatives, each with the priorities and goals it feeds."""
    if engine(conn) == "mssql":
        areas = _source_area_name_map(conn)
        by_id = {r["iid"]: r["tid"] for r in conn.execute(
            "SELECT initiative_id AS iid, team_id AS tid FROM dbo.initiative "
            "WHERE initiative_level='D-1'")}
        mis = []
        for r in conn.execute(
                "SELECT i.initiative_id AS iid, i.initiative_code AS Code, "
                "       i.initiative_code AS MIId, i.initiative_name AS Title, "
                "       i.strategy_align AS StrategyAlign, i.initiatives_text AS Initiatives, "
                "       i.proposed_target AS ProposedTarget, i.target_status AS TargetStatus, "
                "       s.status_current AS Status, NULL AS Note, "
                "       i.team_id AS teamid, t.team_name AS Team, "
                "       i.source_area_id AS said "
                "FROM dbo.initiative i "
                "LEFT JOIN dbo.vw_initiative_summary s ON s.initiative_id = i.initiative_id "
                "LEFT JOIN dbo.team t ON t.team_id = i.team_id "
                "WHERE i.initiative_level = 'D-1' AND i.active_flag = 1 "
                "ORDER BY i.initiative_code"):
            k = {"TeamInitiativeID": r["iid"], "Code": r["Code"], "MIId": r["MIId"],
                 "Title": r["Title"], "StrategyAlign": r["StrategyAlign"],
                 "Initiatives": r["Initiatives"], "ProposedTarget": r["ProposedTarget"],
                 "TargetStatus": r["TargetStatus"], "Status": r["Status"], "Note": r["Note"],
                 "TeamID": _team_id_int(r["teamid"]), "Team": r["Team"],
                 "SourceArea": areas.get(r["said"])}
            mis.append(k)
        links: dict = {}
        for r in conn.execute(
                "SELECT ip.initiative_id AS iid, "
                "       (SELECT priority_name FROM dbo.priority_definition pd "
                "        WHERE pd.priority_code = ap.priority_code) AS PriorityName, "
                "       ap.priority_code AS Code, NULL AS Colour "
                "FROM dbo.initiative_priority ip "
                "JOIN dbo.annual_priority ap ON ap.priority_id = ip.priority_id "
                "ORDER BY ap.priority_code"):
            links.setdefault(r["iid"], []).append({"TeamInitiativeID": r["iid"],
                "PriorityName": r["PriorityName"], "Code": r["Code"], "Colour": r["Colour"]})
        goals: dict = {}
        for r in conn.execute(
                "SELECT ig.initiative_id AS iid, g.goal_number AS GoalNumber, g.short_label AS ShortName "
                "FROM dbo.initiative_goal ig JOIN dbo.goal g ON g.goal_id = ig.goal_id "
                "JOIN dbo.initiative i ON i.initiative_id = ig.initiative_id "
                "WHERE i.initiative_level = 'D-1' ORDER BY g.goal_number"):
            goals.setdefault(r["iid"], []).append(
                {"TeamInitiativeID": r["iid"], "GoalNumber": r["GoalNumber"], "ShortName": r["ShortName"]})
        for k in mis:
            k["priorities"] = links.get(k["TeamInitiativeID"], [])
            k["goals"] = goals.get(k["TeamInitiativeID"], [])
            k["_GroupLabel"] = None
        return mis
    mis = _dicts(conn.execute(
        "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, k.Initiatives, "
        "       k.ProposedTarget, k.TargetStatus, "
        "       k.Status, k.Note, k.TeamID, t.Name AS Team, "
        "       sa.Name AS SourceArea "
        "FROM TeamInitiatives k LEFT JOIN Teams t ON t.TeamID = k.TeamID "
        "LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID "
        "ORDER BY k.Code").fetchall())
    links: dict = {}
    for r in conn.execute(
            "SELECT tp.TeamInitiativeID, p.PriorityName, p.Code, p.Colour "
            "FROM TeamInitiativePriorities tp JOIN Priorities p ON p.PriorityID = tp.PriorityID "
            "ORDER BY p.Code"):
        links.setdefault(r["TeamInitiativeID"], []).append(dict(r))
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


def goal_team_initiatives(conn, goal_number):
    """Team Initiatives aligned to one goal, with team/source-area/target."""
    if engine(conn) == "mssql":
        areas = _source_area_name_map(conn)
        return _dicts(conn.execute(
            "SELECT i.initiative_id AS TeamInitiativeID, i.initiative_code AS Code, "
            "       i.initiative_code AS MIId, i.initiative_name AS Title, "
            "       i.strategy_align AS StrategyAlign, i.proposed_target AS ProposedTarget, "
            "       i.target_status AS TargetStatus, t.team_name AS Team, "
            "       COALESCE(s.status_current, i.status, 'Not started') AS Status, "
            "       i.source_area_id AS said "
            "FROM dbo.initiative_goal kg "
            "JOIN dbo.initiative i ON i.initiative_id = kg.initiative_id "
            "JOIN dbo.goal g ON g.goal_id = kg.goal_id "
            "LEFT JOIN dbo.vw_initiative_summary s ON s.initiative_id = i.initiative_id "
            "LEFT JOIN dbo.team t ON t.team_id = i.team_id "
            "WHERE g.goal_number = %s AND i.initiative_level = 'D-1' AND i.active_flag = 1 "
            "ORDER BY i.initiative_code",
            (goal_number,)).fetchall())
    return _dicts(conn.execute(
        "SELECT DISTINCT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, "
        "       k.ProposedTarget, k.TargetStatus, t.Name AS Team, "
        "       COALESCE(lp.Status, k.Status, 'Not started') AS Status, "
        "       sa.Name AS SourceArea "
        "FROM TeamInitiativeGoals kg "
        "JOIN TeamInitiatives k ON k.TeamInitiativeID = kg.TeamInitiativeID "
        "JOIN Goals g ON g.GoalID = kg.GoalID "
        "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
        "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
        "LEFT JOIN Teams t ON t.TeamID = k.TeamID "
        "LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID "
        "WHERE g.GoalNumber = ? ORDER BY k.Code",
        (goal_number,)).fetchall())


def team_detail(conn, team_id):
    if engine(conn) == "mssql":
        tid = "TEAM-%d" % team_id
        row = conn.execute(
            "SELECT team_id, team_name AS Name, description AS Description FROM dbo.team "
            "WHERE team_id = %s", (tid,)).fetchone()
        if row is None:
            return None
        areas = _source_area_name_map(conn)
        out = {"TeamID": _team_id_int(row["team_id"]), "Name": row["Name"],
               "Description": row["Description"]}
        ti = []
        for r in conn.execute(
                "SELECT initiative_id AS TeamInitiativeID, initiative_code AS Code, "
                "       initiative_code AS MIId, initiative_name AS Title, "
                "       strategy_align AS StrategyAlign, proposed_target AS ProposedTarget, "
                "       target_status AS TargetStatus, source_area_id AS said "
                "FROM dbo.initiative WHERE team_id = %s AND initiative_level='D-1' "
                "AND active_flag = 1 ORDER BY initiative_code", (row["team_id"],)):
            ti.append({"TeamInitiativeID": r["TeamInitiativeID"], "Code": r["Code"],
                       "MIId": r["MIId"], "Title": r["Title"], "StrategyAlign": r["StrategyAlign"],
                       "ProposedTarget": r["ProposedTarget"], "TargetStatus": r["TargetStatus"],
                       "SourceArea": areas.get(r["said"])})
        out["team_initiatives"] = ti
        return out
    row = conn.execute(
        "SELECT TeamID, Name, Description FROM Teams WHERE TeamID = ?",
        (team_id,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["team_initiatives"] = _dicts(conn.execute(
        "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, "
        "       k.ProposedTarget, k.TargetStatus, sa.Name AS SourceArea "
        "FROM TeamInitiatives k LEFT JOIN SourceAreas sa "
        "       ON sa.SourceAreaID = k.SourceAreaID "
        "WHERE k.TeamID = ? ORDER BY k.Code", (team_id,)).fetchall())
    return out


def team_initiative_detail(conn, mi_id):
    """One Team Initiative by code, with its team/source-area/goals/priorities."""
    if engine(conn) == "mssql":
        areas = _source_area_name_map(conn)
        row = conn.execute(
            "SELECT i.initiative_id AS TeamInitiativeID, i.initiative_code AS Code, "
            "       i.initiative_code AS MIId, i.initiative_name AS Title, "
            "       i.strategy_align AS StrategyAlign, i.initiatives_text AS Initiatives, "
            "       i.proposed_target AS ProposedTarget, i.description AS Description, "
            "       i.target_status AS TargetStatus, s.status_current AS Status, NULL AS Note, "
            "       i.team_id, t.team_name AS Team, i.source_area_id AS said "
            "FROM dbo.initiative i "
            "LEFT JOIN dbo.vw_initiative_summary s ON s.initiative_id = i.initiative_id "
            "LEFT JOIN dbo.team t ON t.team_id = i.team_id "
            "WHERE i.initiative_code = %s OR i.initiative_id = %s",
            (mi_id, "INI-" + mi_id)).fetchone()
        if row is None:
            return None
        out = {"TeamInitiativeID": row["TeamInitiativeID"], "Code": row["Code"],
               "MIId": row["MIId"], "Title": row["Title"], "StrategyAlign": row["StrategyAlign"],
               "Initiatives": row["Initiatives"], "ProposedTarget": row["ProposedTarget"],
               "Description": row["Description"], "TargetStatus": row["TargetStatus"],
               "Status": row["Status"], "Note": row["Note"],
               "TeamID": _team_id_int(row["team_id"]), "Team": row["Team"],
               "SourceArea": areas.get(row["said"])}
        iid = row["TeamInitiativeID"]
        out["goals"] = _dicts(conn.execute(
            "SELECT g.goal_number AS GoalNumber, g.short_label AS ShortName, g.canonical_title AS FullName "
            "FROM dbo.initiative_goal kg JOIN dbo.goal g ON g.goal_id = kg.goal_id "
            "WHERE kg.initiative_id = %s ORDER BY g.goal_number", (iid,)).fetchall())
        pris = []
        for r in conn.execute(
                "SELECT pdef.priority_name AS PriorityName, ap.priority_code AS Code, NULL AS Colour "
                "FROM dbo.initiative_priority tp JOIN dbo.annual_priority ap ON ap.priority_id = tp.priority_id "
                "JOIN dbo.priority_definition pdef ON pdef.priority_code = ap.priority_code "
                "WHERE tp.initiative_id = %s ORDER BY ap.priority_code", (iid,)):
            pris.append({"PriorityName": r["PriorityName"], "Code": r["Code"], "Colour": r["Colour"]})
        out["priorities"] = pris
        return out
    row = conn.execute(
        "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, "
        "       k.Initiatives, k.ProposedTarget, k.Description, "
        "       k.TargetStatus, k.Status, k.Note, "
        "       t.TeamID, t.Name AS Team, sa.Name AS SourceArea "
        "FROM TeamInitiatives k "
        "LEFT JOIN Teams t ON t.TeamID = k.TeamID "
        "LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID "
        "WHERE k.MIId = ? OR k.Code = ?",
        (mi_id, mi_id)).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["goals"] = _dicts(conn.execute(
        "SELECT g.GoalNumber, g.ShortName, g.FullName "
        "FROM TeamInitiativeGoals kg JOIN Goals g ON g.GoalID = kg.GoalID "
        "WHERE kg.TeamInitiativeID = ? ORDER BY g.GoalNumber", (out["TeamInitiativeID"],)).fetchall())
    out["priorities"] = _dicts(conn.execute(
        "SELECT p.PriorityName, p.Code, p.Colour "
        "FROM TeamInitiativePriorities tp JOIN Priorities p ON p.PriorityID = tp.PriorityID "
        "WHERE tp.TeamInitiativeID = ? ORDER BY p.Code", (out["TeamInitiativeID"],)).fetchall())
    return out


def search(conn, term, limit=10):
    """Match people, goals, priorities and team initiatives by name or code.
    Returns (kind, label, code) rows; the caller composes hrefs (engine-agnostic)."""
    q = (term or "").strip()
    if not q:
        return []
    like = "%" + q.lower() + "%"
    code_like = q.lower() + "%"
    out = []
    if engine(conn) == "mssql":
        lim = str(int(limit))
        # Eagerly fetchall each query: a pymssql connection holds one result
        # buffer, so a later execute() would empty an earlier unread cursor.
        queries = (
            ("person",
             "SELECT person_id AS [key], display_name AS label, '' AS code FROM dbo.person "
             "WHERE active_flag = 1 AND LOWER(display_name) LIKE %s "
             "ORDER BY display_name OFFSET 0 ROWS FETCH NEXT " + lim + " ROWS ONLY",
             (like,)),
            ("goal",
             "SELECT goal_number AS [key], short_label AS label, '' AS code FROM dbo.goal "
             "WHERE LOWER(short_label) LIKE %s OR LOWER(COALESCE(canonical_title,'')) LIKE %s "
             "ORDER BY goal_number OFFSET 0 ROWS FETCH NEXT " + lim + " ROWS ONLY",
             (like, like)),
            ("priority",
             "SELECT pdef.priority_name AS [key], pdef.priority_name AS label, pdef.priority_code AS code "
             "FROM dbo.priority_definition pdef WHERE LOWER(pdef.priority_name) LIKE %s "
             "ORDER BY pdef.priority_code OFFSET 0 ROWS FETCH NEXT " + lim + " ROWS ONLY",
             (like,)),
            ("team-initiative",
             "SELECT initiative_code AS [key], initiative_name AS label, initiative_code AS code "
             "FROM dbo.initiative WHERE active_flag = 1 AND initiative_level='D-1' "
             "AND (LOWER(initiative_code) LIKE %s OR LOWER(initiative_name) LIKE %s) "
             "ORDER BY (CASE WHEN LOWER(initiative_code) LIKE %s THEN 0 ELSE 1 END), initiative_code "
             "OFFSET 0 ROWS FETCH NEXT " + lim + " ROWS ONLY",
             (like, like, code_like)),
        )
        for kind, sql, params in queries:
            for r in conn.execute(sql, params).fetchall():
                key = r["key"]
                label = r["label"]
                if kind == "person":
                    key = _pid_int(key) if isinstance(key, str) and "-" in str(key) else key
                elif kind == "priority":
                    # sqlite labels a priority hit 'P06 Culture' (code + SHORT
                    # name); Rev2's priority_name is the full title, so recompose
                    # with the canon's short name to match.
                    from app import priorities as canon
                    label = "%s %s" % (r["code"], canon.short_for_code(r["code"]) or label)
                out.append({"kind": kind, "label": label,
                            "code": r["code"], "key": key})
        return out
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
        ("team-initiative", conn.execute(
            "SELECT MIId AS key, Title AS label, COALESCE(MIId,'') AS code "
            "FROM TeamInitiatives "
            "WHERE IsActive = 1 AND (LOWER(COALESCE(MIId,'')) LIKE ? OR LOWER(Title) LIKE ?) "
            "ORDER BY (LOWER(COALESCE(MIId,'')) LIKE ?) DESC, Code LIMIT ?",
            (like, like, code_like, limit))),
    ):
        for r in rows:
            out.append({"kind": kind, "label": r["label"],
                        "code": r["code"], "key": r["key"]})
    return out
