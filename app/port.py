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


#: dict(row) for a single mssql/sqlite row in a port (not the seed's SQL-quoting
#: `_d`). Named for the pattern it serves in the card/edit ports below.
def _d(row):
    return dict(row)


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


#: ---------------------------------------------------------------------------
#: Card reads (adopt-rev2-store task group 5). initiative_card composes details,
#: tags, connections (initiative_relationship), latest and diary
#: (initiative_update). person_card uses vw_person_portfolio. priority_* read the
#: reconciled milestone table (008). Goal option ids are the app's goal_number;
#: priority option ids the canon short name; Dean ids the Dean row's code - the
#: app's edit templates key on these display ids, which are store-independent.
#: ---------------------------------------------------------------------------


def initiative_card(conn, mi_id):
    if engine(conn) == "mssql":
        row = conn.execute(
            "SELECT i.initiative_id AS InitiativeID, i.initiative_code AS Code, "
            "       i.initiative_name AS InitiativeName, i.description AS Description, "
            "       o.person_id AS OwnerID, o.display_name AS Owner "
            "FROM dbo.initiative i "
            "LEFT JOIN dbo.vw_primary_reporting_owner o ON o.initiative_id = i.initiative_id "
            "WHERE (i.initiative_code = %s OR i.initiative_id = %s) "
            "  AND i.active_flag = 1 AND i.initiative_level = 'D-1'",
            (mi_id, "INI-" + mi_id)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["Level"] = "Team Initiative"
        d["MIId"] = d["Code"]
        iid = d["InitiativeID"]
        d["goal_tags"] = [_d(r) for r in conn.execute(
            "SELECT g.goal_number AS GoalNumber, g.short_label AS ShortName, 0 AS IsPrimary "
            "FROM dbo.initiative_goal kg JOIN dbo.goal g ON g.goal_id = kg.goal_id "
            "WHERE kg.initiative_id = %s ORDER BY g.goal_number", (iid,)).fetchall()]
        pris = []
        for r in conn.execute(
                "SELECT ap.priority_code AS Code, "
                "       CASE WHEN tp.relationship_type = 'Primary' THEN 1 ELSE 0 END AS IsPrimary "
                "FROM dbo.initiative_priority tp JOIN dbo.annual_priority ap ON ap.priority_id = tp.priority_id "
                "WHERE tp.initiative_id = %s ORDER BY ap.priority_code", (iid,)):
            from app import priorities as canon
            pris.append({"PriorityName": canon.short_for_code(r["Code"]) or r["Code"],
                         "PlanYear": _plan_year_int_from_id(conn, iid),
                         "IsPrimary": r["IsPrimary"]})
        d["priority_tags"] = pris
        d["connections"] = [_d(r) for r in conn.execute(
            "SELECT 'Contributes to' AS Direction, parent.initiative_code AS Code, "
            "       parent.initiative_name AS InitiativeName, NULL AS OwnerID, NULL AS Owner, "
            "       NULL AS PercentComplete, NULL AS Status "
            "FROM dbo.initiative_relationship kl JOIN dbo.initiative parent "
            "       ON parent.initiative_id = kl.to_initiative_id "
            "WHERE kl.from_initiative_id = %s AND parent.initiative_level = 'Dean' "
            "  AND kl.relationship_type = 'Supports' ORDER BY parent.initiative_code", (iid,)).fetchall()]
        latest = conn.execute(
            "SELECT CONVERT(VARCHAR(10), lu.update_date, 23) AS UpdateDate, "
            "       CAST(lu.progress_value AS FLOAT) AS PercentComplete, "
            "       lu.status_at_update AS Status, lu.narrative AS Note "
            "FROM dbo.vw_latest_update lu WHERE lu.initiative_id = %s", (iid,)).fetchone()
        d["latest"] = dict(latest) if latest else None
        d["diary"] = []
        for r in conn.execute(
                "SELECT CONVERT(VARCHAR(10), pu.update_date, 23) AS UpdateDate, "
                "       CAST(pu.progress_value AS FLOAT) AS PercentComplete, "
                "       pu.status_at_update AS Status, pu.narrative AS Note, "
                "       e.display_name AS EnteredBy "
                "FROM dbo.initiative_update pu "
                "LEFT JOIN dbo.person e ON e.person_id = pu.updated_by_person_id "
                "WHERE pu.initiative_id = %s ORDER BY pu.update_date DESC, pu.update_id DESC",
                (iid,)):
            d["diary"].append(_d(r))
        d["OwnerID_int"] = _pid_int(d["OwnerID"])
        return d
    # sqlite (unchanged)
    row = conn.execute(
        "SELECT k.TeamInitiativeID AS InitiativeID, k.MIId AS Code, "
        "       k.Title AS InitiativeName, k.Description, k.MIId, "
        "       'Team Initiative' AS Level, k.OwnerID, p.Name AS Owner "
        "FROM TeamInitiatives k LEFT JOIN People p ON p.PersonID = k.OwnerID "
        "WHERE (k.MIId = ? OR k.Code = ?) AND k.IsActive = 1",
        (mi_id, mi_id)).fetchone()
    if row is None:
        return None
    card = dict(row)
    card["Code"] = card["MIId"] or card["Code"]
    card["goal_tags"] = [dict(r) for r in conn.execute(
        "SELECT g.GoalNumber, g.ShortName, 0 AS IsPrimary "
        "FROM TeamInitiativeGoals kg JOIN Goals g ON g.GoalID = kg.GoalID "
        "WHERE kg.TeamInitiativeID = ? ORDER BY g.GoalNumber", (card["InitiativeID"],))]
    card["priority_tags"] = [dict(r) for r in conn.execute(
        "SELECT pr.PriorityName, pr.PlanYear, tp.IsPrimary "
        "FROM TeamInitiativePriorities tp JOIN Priorities pr ON pr.PriorityID = tp.PriorityID "
        "WHERE tp.TeamInitiativeID = ? ORDER BY pr.PriorityName", (card["InitiativeID"],))]
    card["connections"] = [dict(r) for r in conn.execute(
        "SELECT 'Contributes to' AS Direction, d.Code AS Code, d.Title AS InitiativeName, "
        "       NULL AS OwnerID, NULL AS Owner, NULL AS PercentComplete, NULL AS Status "
        "FROM TeamInitiativeDeanLinks kl JOIN DeanInitiatives d ON d.DeanInitiativeID = kl.DeanInitiativeID "
        "WHERE kl.TeamInitiativeID = ? ORDER BY d.Code", (card["InitiativeID"],))]
    latest = conn.execute(
        "SELECT UpdateDate, PercentComplete, Status, Note "
        "FROM vw_LatestTeamInitiativeProgress WHERE TeamInitiativeID = ?",
        (card["InitiativeID"],)).fetchone()
    card["latest"] = dict(latest) if latest else None
    card["diary"] = [dict(r) for r in conn.execute(
        "SELECT UpdateDate, PercentComplete, Status, Note, "
        "       (SELECT Name FROM People e WHERE e.PersonID = pu.EnteredByID) AS EnteredBy "
        "FROM TeamInitiativeUpdates pu WHERE TeamInitiativeID = ? "
        "ORDER BY UpdateDate DESC, UpdateID DESC", (card["InitiativeID"],))]
    return card


def _plan_year_int_from_id(conn, initiative_id):
    """helper used by ports that need a row's plan year; looks via annual_priority."""
    r = conn.execute(
        "SELECT ap.planning_period AS pp FROM dbo.initiative_priority ip "
        "JOIN dbo.annual_priority ap ON ap.priority_id = ip.priority_id "
        "WHERE ip.initiative_id = %s", (initiative_id,)).fetchone()
    return _plan_year_int(r["pp"]) if r else None


def person_card(conn, person_id):
    if engine(conn) == "mssql":
        rid = "PERS-%d" % person_id
        person = conn.execute(
            "SELECT person_id, display_name AS Name, working_title AS Title, active_flag "
            "FROM dbo.person WHERE person_id = %s AND active_flag = 1", (rid,)).fetchone()
        if person is None:
            return None
        p = {"PersonID": person_id, "Name": person["Name"], "Title": person["Title"],
             "ReportsToID": None, "IsAdmin": 1 if person_id in _admin_pids(conn) else 0}
        rows = []
        for r in conn.execute(
                "SELECT s.initiative_id AS InitiativeID, 'Team Initiative' AS Level, "
                "       s.initiative_code AS Code, s.initiative_name AS InitiativeName, "
                "       CAST(s.progress_current AS FLOAT) AS PercentComplete, "
                "       s.status_current AS Status, "
                "       CONVERT(VARCHAR(10), s.last_updated, 23) AS LastUpdated "
                "FROM dbo.initiative_owner o JOIN dbo.vw_initiative_summary s "
                "       ON s.initiative_id = o.initiative_id "
                "WHERE o.person_id = %s AND o.ownership_role = 'Reporting Owner' "
                "  AND o.primary_flag = 1 AND o.effective_end IS NULL "
                "  AND s.initiative_level = 'D-1' ORDER BY s.initiative_code",
                (rid,)):
            rows.append(_d(r))
        return {"person": p, "initiatives": rows}
    person = conn.execute(
        "SELECT PersonID, Name, Title, ReportsToID, IsAdmin FROM People "
        "WHERE PersonID = ? AND IsActive = 1", (person_id,)).fetchone()
    if person is None:
        return None
    rows = [dict(r) for r in conn.execute(
        "SELECT k.TeamInitiativeID AS InitiativeID, 'Team Initiative' AS Level, "
        "       k.MIId AS Code, k.Title AS InitiativeName, "
        "       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated "
        "FROM TeamInitiatives k "
        "LEFT JOIN vw_LatestTeamInitiativeProgress lp "
        "       ON lp.TeamInitiativeID = k.TeamInitiativeID "
        "WHERE k.OwnerID = ? AND k.IsActive = 1 ORDER BY k.MIId", (person_id,)).fetchall()]
    for r in rows:
        r["Code"] = r["Code"] or ""
    return {"person": dict(person), "initiatives": rows}


def _admin_pids(conn):
    """int PersonIDs holding PlatformAdmin (mssql only)."""
    return {_pid_int(r["person_id"]) for r in conn.execute(
        "SELECT pr.person_id FROM dbo.person_role pr JOIN dbo.role ro ON ro.role_id = pr.role_id "
        "WHERE ro.name = 'PlatformAdmin'")}


def priority_detail(conn, name):
    from app import priorities as canon
    if engine(conn) == "mssql":
        code = canon.code(name)
        if not code:
            return None
        row = conn.execute(
            "SELECT ap.priority_id, ap.priority_code AS Code, ap.priority_name AS FullTitle, "
            "       ap.planning_period, ap.description AS Description "
            "FROM dbo.annual_priority ap WHERE ap.priority_code = %s", (code,)).fetchone()
        if row is None:
            return None
        out = {"PriorityID": row["priority_id"], "PriorityName": canon.short_for_code(code) or code,
               "PlanYear": _plan_year_int(row["planning_period"]), "Description": row["Description"],
               "Code": code, "FullTitle": row["FullTitle"],
               "Measure": None, "Target": None, "Cadence": None, "OwnerLabel": None, "Colour": None}
        out["team_initiatives"] = [_d(r) for r in conn.execute(
            "SELECT i.initiative_id AS TeamInitiativeID, i.initiative_code AS Code, "
            "       i.initiative_code AS MIId, i.initiative_name AS Title, i.strategy_align AS StrategyAlign, "
            "       s.status_current AS Status, i.target_status AS TargetStatus, "
            "       i.proposed_target AS ProposedTarget, t.team_name AS Team "
            "FROM dbo.initiative_priority tp JOIN dbo.initiative i ON i.initiative_id = tp.initiative_id "
            "LEFT JOIN dbo.vw_initiative_summary s ON s.initiative_id = i.initiative_id "
            "LEFT JOIN dbo.team t ON t.team_id = i.team_id "
            "WHERE tp.priority_id = %s AND i.active_flag = 1 AND i.initiative_level = 'D-1' "
            "ORDER BY i.initiative_code", (row["priority_id"],)).fetchall()]
        out["initiative_count"] = conn.execute(
            "SELECT COUNT(DISTINCT i.initiative_id) FROM dbo.initiative_priority tp "
            "JOIN dbo.initiative i ON i.initiative_id = tp.initiative_id "
            "WHERE tp.priority_id = %s AND i.active_flag = 1 AND i.initiative_level = 'D-1'",
            (row["priority_id"],)).fetchone()[0]
        return out
    row = conn.execute(
        "SELECT PriorityID, PriorityName, PlanYear, Description, Code, "
        "       FullTitle, Measure, Target, Cadence, OwnerLabel, Colour "
        "FROM Priorities WHERE PriorityName = ?", (name,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["team_initiatives"] = [dict(r) for r in conn.execute(
        "SELECT k.TeamInitiativeID, k.Code, k.MIId, k.Title, k.StrategyAlign, k.Status, "
        "       k.TargetStatus, k.ProposedTarget, t.Name AS Team "
        "FROM TeamInitiativePriorities tp "
        "JOIN TeamInitiatives k ON k.TeamInitiativeID = tp.TeamInitiativeID "
        "LEFT JOIN Teams t ON t.TeamID = k.TeamID "
        "WHERE tp.PriorityID = ? ORDER BY k.Code", (out["PriorityID"],))]
    out["initiative_count"] = conn.execute(
        "SELECT COUNT(DISTINCT k.TeamInitiativeID) FROM TeamInitiativePriorities tp "
        "JOIN TeamInitiatives k ON k.TeamInitiativeID = tp.TeamInitiativeID AND k.IsActive = 1 "
        "WHERE tp.PriorityID = ?", (out["PriorityID"],)).fetchone()[0]
    return out


def priority_outcomes(conn, year):
    """The six priorities for one plan year with milestone progress + the
    milestones. Now portable: the reconciled milestone table exists on Rev2."""
    if engine(conn) == "mssql":
        from app import priorities as canon
        rows = []
        for r in conn.execute(
                "SELECT ap.priority_id, ap.priority_code AS Code, ap.priority_name AS FullTitle, "
                "       ap.planning_period, ap.description AS Description, "
                "       (SELECT COUNT(*) FROM dbo.milestone m WHERE m.priority_id = ap.priority_id AND m.active_flag = 1) AS Planned, "
                "       (SELECT COUNT(*) FROM dbo.milestone m WHERE m.priority_id = ap.priority_id AND m.active_flag = 1 AND m.status = 'Met') AS Reached "
                "FROM dbo.annual_priority ap "
                "WHERE ap.priority_code IS NOT NULL AND ap.planning_period = %s "
                "ORDER BY ap.priority_code",
                ("FY%d" % year,)):
            rows.append({
                "PriorityID": r["priority_id"], "Code": r["Code"], "PlanYear": _plan_year_int(r["planning_period"]),
                "FullTitle": r["FullTitle"], "PriorityName": canon.short_for_code(r["Code"]) or r["FullTitle"],
                "Description": r["Description"], "Measure": None, "Target": None, "OwnerLabel": None,
                "Status": None, "LastUpdated": None, "Planned": r["Planned"], "Reached": r["Reached"],
            })
        ms = milestones_for_year(conn, year)
        for r in rows:
            r["milestones"] = ms.get(r["Code"], [])
        return rows
    rows = _dicts(conn.execute(
        "SELECT p.PriorityID, p.Code, p.PlanYear, p.FullTitle, p.PriorityName, "
        "       p.Description, p.Measure, p.Target, p.OwnerLabel, p.Status, "
        "       p.LastUpdated, "
        "       COALESCE(v.Planned, 0) AS Planned, COALESCE(v.Reached, 0) AS Reached "
        "FROM Priorities p "
        "LEFT JOIN vw_PriorityMilestoneProgress v ON v.PriorityID = p.PriorityID "
        "WHERE p.Code IS NOT NULL AND p.PlanYear = ? ORDER BY p.Code", (year,)).fetchall())
    by_id: dict = {}
    for m in conn.execute(
            "SELECT PriorityID, Name, Status, PlannedDate, DateMet, "
            "       OwnerLabel, EvidenceURL FROM Milestones "
            "WHERE IsActive = 1 ORDER BY PriorityID, SortOrder, MilestoneID"):
        by_id.setdefault(m["PriorityID"], []).append(dict(m))
    out = []
    for r in rows:
        d = dict(r)
        d["milestones"] = by_id.get(r["PriorityID"], [])
        out.append(d)
    return out


def tag_edit_options(conn, initiative_id):
    """The goals + priorities choice lists and what's chosen. initiative_id is the
    app's int on sqlite and the Rev2 id on mssql; the caller resolves it before
    calling (the row's InitiativeID). Option keys: goal = GoalNumber, priority =
    PriorityID (the app's id) / priority_code (Rev2)."""
    if engine(conn) == "mssql":
        goals = [_d(r) for r in conn.execute(
            "SELECT g.goal_id AS GoalID, g.goal_number AS GoalNumber, g.short_label AS ShortName, "
            "       g.canonical_title AS FullName, g.canonical_description AS Description "
            "FROM dbo.goal g ORDER BY g.goal_number").fetchall()]
        pri = []
        for r in conn.execute(
                "SELECT ap.priority_id, ap.priority_code AS Code, ap.priority_name AS FullTitle, "
                "       ap.planning_period, ap.description AS Description FROM dbo.annual_priority ap "
                "ORDER BY ap.priority_code"):
            from app import priorities as canon
            pri.append({"PriorityID": r["priority_id"], "PriorityName": canon.short_for_code(r["Code"]) or r["FullTitle"],
                        "PlanYear": _plan_year_int(r["planning_period"]), "Description": r["Description"]})
        chosen_g = {r["GoalNumber"] for r in conn.execute(
            "SELECT g.goal_number AS GoalNumber FROM dbo.initiative_goal kg JOIN dbo.goal g ON g.goal_id = kg.goal_id "
            "WHERE kg.initiative_id = %s", (initiative_id,))}
        chosen_p = {r["priority_id"] for r in conn.execute(
            "SELECT tp.priority_id FROM dbo.initiative_priority tp WHERE tp.initiative_id = %s",
            (initiative_id,))}
        return {"goals": goals, "priorities": pri,
                "chosen_goals": chosen_g, "chosen_priorities": chosen_p}
    goals = _dicts(conn.execute(
        "SELECT GoalID, GoalNumber, ShortName, FullName, Description FROM Goals ORDER BY GoalNumber").fetchall())
    pri = _dicts(conn.execute(
        "SELECT PriorityID, PriorityName, PlanYear, Description FROM Priorities ORDER BY PlanYear, PriorityName").fetchall())
    chosen_g = {r["GoalID"] for r in conn.execute(
        "SELECT GoalID FROM TeamInitiativeGoals WHERE TeamInitiativeID = ?", (initiative_id,))}
    chosen_p = {r["PriorityID"] for r in conn.execute(
        "SELECT PriorityID FROM TeamInitiativePriorities WHERE TeamInitiativeID = ?", (initiative_id,))}
    return {"goals": goals, "priorities": pri,
            "chosen_goals": chosen_g, "chosen_priorities": chosen_p}


def link_edit_options(conn, initiative_id):
    """The Dean initiatives + what's chosen. The edit template keys on
    InitiativeID/Title; Dean rows on Rev2 are initiatives with level='Dean'."""
    if engine(conn) == "mssql":
        deans = [_d(r) for r in conn.execute(
            "SELECT initiative_id AS InitiativeID, initiative_code AS Code, initiative_name AS InitiativeName "
            "FROM dbo.initiative WHERE initiative_level = 'Dean' ORDER BY initiative_code").fetchall()]
        chosen = {r["to_initiative_id"] for r in conn.execute(
            "SELECT to_initiative_id FROM dbo.initiative_relationship "
            "WHERE from_initiative_id = %s AND relationship_type = 'Supports'", (initiative_id,))}
        return {"deans": deans, "chosen": chosen}
    deans = _dicts(conn.execute(
        "SELECT DeanInitiativeID AS InitiativeID, Code, Title AS InitiativeName "
        "FROM DeanInitiatives ORDER BY FiscalYear, Code").fetchall())
    chosen = {r["DeanInitiativeID"] for r in conn.execute(
        "SELECT DeanInitiativeID FROM TeamInitiativeDeanLinks WHERE TeamInitiativeID = ?", (initiative_id,))}
    return {"deans": deans, "chosen": chosen}


#: ---------------------------------------------------------------------------
#: Writes (adopt-rev2-store task group 6). Called from repo.py bodies under
#: mssql. Each resolves the initiative by its public key, runs the T-SQL, and
#: returns the new id. audit_log writes go through repo._audit, which already
#: dual-paths. update_id is generated (UPD-<code>-<n>) because Rev2's
#: initiative_update has no IDENTITY column.
#: ---------------------------------------------------------------------------


def _rev2_iid(conn, mi_id):
    row = conn.execute(
        "SELECT initiative_id FROM dbo.initiative "
        "WHERE (initiative_code = %s OR initiative_id = %s) AND active_flag = 1 "
        "  AND initiative_level = 'D-1'",
        (mi_id, "INI-" + mi_id)).fetchone()
    return row["initiative_id"] if row else None


def _rev2_iid_any_active(conn, mi_id):
    row = conn.execute(
        "SELECT initiative_id, active_flag FROM dbo.initiative "
        "WHERE (initiative_code = %s OR initiative_id = %s) AND initiative_level = 'D-1'",
        (mi_id, "INI-" + mi_id)).fetchone()
    return (row["initiative_id"], row["active_flag"]) if row else (None, None)


def write_add_progress_update(conn, mi_id, percent, status, note, entered_by_id):
    iid = _rev2_iid(conn, mi_id)
    if iid is None:
        from app.repo import RuleError
        raise RuleError("That initiative does not exist or has been retired.")
    seq = conn.execute(
        "SELECT COUNT(*) + 1 AS n FROM dbo.initiative_update WHERE initiative_id = %s",
        (iid,)).fetchone()[0]
    update_id = "UPD-%s-%03d" % (mi_id, seq)
    conn.execute(
        "INSERT INTO dbo.initiative_update (update_id, initiative_id, updated_by_person_id, "
        "       narrative, progress_value, status_at_update) VALUES (%s, %s, %s, %s, %s, %s)",
        (update_id, iid, "PERS-%d" % entered_by_id if entered_by_id else None,
         note or "", percent, status))
    return update_id


def write_update_initiative_details(conn, mi_id, name, description, person_id, audit):
    iid = _rev2_iid(conn, mi_id)
    if iid is None:
        from app.repo import RuleError
        raise RuleError("That initiative does not exist or has been retired.")
    row = conn.execute(
        "SELECT initiative_name, description FROM dbo.initiative WHERE initiative_id = %s",
        (iid,)).fetchone()
    conn.execute(
        "UPDATE dbo.initiative SET initiative_name = %s, description = %s, "
        "       updated_at = SYSUTCDATETIME() WHERE initiative_id = %s",
        (name, (description or "").strip() or None, iid))
    audit(person_id, "update_initiative", mi_id,
          {"before": {"name": row["initiative_name"], "description": row["description"]},
           "after": {"name": name, "description": (description or "").strip() or None}})


def _goal_id(conn, goal_number):
    return "GOAL-%d" % goal_number


def _priority_id_for_code(conn, code):
    r = conn.execute(
        "SELECT priority_id FROM dbo.annual_priority WHERE priority_code = %s", (code,)).fetchone()
    return r["priority_id"] if r else None


def write_replace_tags(conn, mi_id, goal_tags, priority_tags, person_id, audit):
    """goal_tags/priority_tags: [{"id": <goal_number|priority_id>, "primary": bool}].
    On mssql a goal id is its goal_number; a priority id is the app's int PriorityID,
    so it is resolved through the canon code first."""
    from app.repo import RuleError
    iid = _rev2_iid(conn, mi_id)
    if iid is None:
        raise RuleError("That initiative does not exist or has been retired.")
    conn.execute("DELETE FROM dbo.initiative_goal WHERE initiative_id = %s", (iid,))
    for t in goal_tags:
        gid = _goal_id(conn, t["id"])
        conn.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type, "
                     "validation_status, effective_start) VALUES (%s, %s, 'Contributing', 'Validated', "
                     "CAST(GETUTCDATE() AS date))", (iid, gid))
    conn.execute("DELETE FROM dbo.initiative_priority WHERE initiative_id = %s", (iid,))
    from app import priorities as canon
    for t in priority_tags:
        # the sqlite id is the app's int PriorityID; resolve it to the code, then
        # to the Rev2 annual_priority instance for the initiative's plan year.
        apri = _priority_id_for_name_arg(conn, t["id"])
        if apri is None:
            raise RuleError("That priority does not exist.")
        conn.execute("INSERT INTO dbo.initiative_priority (initiative_id, priority_id, relationship_type, "
                     "validation_status, effective_start) VALUES (%s, %s, %s, 'Validated', "
                     "CAST(GETUTCDATE() AS date))",
                     (iid, apri, "Primary" if t.get("primary") else "Supporting"))
    audit(person_id, "replace_tags", mi_id, {"goals": goal_tags, "priorities": priority_tags})


def _priority_id_for_name_arg(conn, priority_id_or_code):
    """priority_tags carry the app's int PriorityID. Resolve through sqlite's
    Priorities (Code IS NOT NULL map) to the code, then the Rev2 FY instance."""
    # The app id is 1..6 mapping to P01..P06 via the code in the row. Rev2 keys
    # by code, so find the current plan year's instance for the code that this
    # int PriorityID maps to: the app's Priorities row ordering is by code, and
    # P0N == PriorityID ordering == P0N. The port uses the code directly.
    from app import priorities as canon
    # priority_id int -> code: the app's register has exactly six, P01..P06.
    try:
        n = int(priority_id_or_code)
    except (TypeError, ValueError):
        return _priority_id_for_code(conn, priority_id_or_code)
    # int PriorityID maps to the code by the register order; safer to read it.
    row = conn.execute(
        "SELECT priority_code FROM dbo.annual_priority WHERE display_order = %s", (n,)).fetchone()
    if row:
        return _priority_id_for_code(conn, row["priority_code"])
    return None


def write_replace_links(conn, mi_id, dean_initiative_ids, person_id, audit):
    from app.repo import RuleError
    iid = _rev2_iid(conn, mi_id)
    if iid is None:
        raise RuleError("That initiative does not exist or has been retired.")
    # Dean ids on the app's link edit are the Dean row's code (e.g. 'D27-1').
    conn.execute("DELETE FROM dbo.initiative_relationship "
                 "WHERE from_initiative_id = %s AND relationship_type = 'Supports'", (iid,))
    if dean_initiative_ids:
        ph = ",".join("%s" for _ in dean_initiative_ids)
        good = {r["initiative_code"] for r in conn.execute(
            "SELECT initiative_code FROM dbo.initiative WHERE initiative_level = 'Dean' "
            "AND initiative_code IN (%s)" % ph, tuple(dean_initiative_ids))}
        for d in dean_initiative_ids:
            if d not in good:
                raise RuleError("Links must point at real Dean Initiatives.")
            conn.execute("INSERT INTO dbo.initiative_relationship (from_initiative_id, to_initiative_id, "
                         "relationship_type, effective_start) VALUES (%s, %s, 'Supports', "
                         "CAST(GETUTCDATE() AS date))", (iid, "INI-" + d))
    audit(person_id, "replace_links", mi_id, {"dean_initiative_ids": dean_initiative_ids})


def write_create_initiative(conn, code, name, owner_id, description, person_id, audit):
    """Create a D-1 initiative on Rev2. The app's `Code` is the internal key; on
    Rev2 there is no separate internal Code, so initiative_code = the app Code.
    Inserted Proposed (no K1 goal requirement yet), with the Reporting Owner
    relation when an owner is given."""
    from app.repo import RuleError
    iid = "INI-" + code
    exists = conn.execute("SELECT 1 FROM dbo.initiative WHERE initiative_code = %s",
                         (code,)).fetchone()
    if exists:
        raise RuleError(f"There is already an initiative with the code {code}.")
    if owner_id is not None:
        pid = "PERS-%d" % owner_id
        person = conn.execute("SELECT 1 FROM dbo.person WHERE person_id = %s", (pid,)).fetchone()
        if person is None:
            raise RuleError("That person is not in the directory.")
    conn.execute(
        "INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name, "
        "       description, initiative_level, initiative_type, status, progress_method, "
        "       source_id, active_flag) VALUES "
        "       (%s, %s, %s, %s, 'D-1', 'Initiative', 'Proposed', 'Owner Estimate', %s, 1)",
        (iid, code, name, (description or "").strip() or name, "SRC-CLL-REGISTER"))
    if owner_id is not None:
        conn.execute(
            "INSERT INTO dbo.initiative_owner (initiative_id, person_id, ownership_role, "
            "       primary_flag, effective_start) VALUES (%s, %s, 'Reporting Owner', 1, "
            "       CAST(GETUTCDATE() AS date))", (iid, "PERS-%d" % owner_id))
    audit(person_id, "create_initiative", code, {"name": name})


def write_retire_initiative(conn, mi_id, person_id, audit):
    from app.repo import RuleError
    iid, active = _rev2_iid_any_active(conn, mi_id)
    if iid is None:
        raise RuleError("That initiative does not exist.")
    if not active:
        raise RuleError(f"{mi_id} is already retired.")
    conn.execute("UPDATE dbo.initiative SET active_flag = 0, updated_at = SYSUTCDATETIME() "
                 "WHERE initiative_id = %s", (iid,))
    audit(person_id, "retire_initiative", mi_id, {})


def write_restore_initiative(conn, mi_id, person_id, reason, audit):
    from app.repo import RuleError
    iid, active = _rev2_iid_any_active(conn, mi_id)
    if iid is None:
        raise RuleError("That initiative does not exist.")
    if active:
        raise RuleError(f"{mi_id} is not retired.")
    conn.execute("UPDATE dbo.initiative SET active_flag = 1, updated_at = SYSUTCDATETIME() "
                 "WHERE initiative_id = %s", (iid,))
    audit(person_id, "restore_initiative", mi_id, {}, reason=reason)


def write_update_entry_description(conn, kind, key, description, person_id, audit):
    from app.repo import RuleError
    from app import priorities as canon
    if kind == "goal":
        gid = "GOAL-%d" % key
        row = conn.execute("SELECT canonical_description FROM dbo.goal WHERE goal_id = %s", (gid,)).fetchone()
        if row is None:
            raise RuleError("No such goal or priority.")
        conn.execute("UPDATE dbo.goal SET canonical_description = %s WHERE goal_id = %s",
                     ((description or "").strip() or None, gid))
        audit(person_id, "update_goal_description", str(key),
              {"before": row["canonical_description"], "after": (description or "").strip() or None})
    elif kind == "priority":
        code = canon.code(key)
        if not code:
            raise RuleError("No such goal or priority.")
        row = conn.execute("SELECT description FROM dbo.annual_priority WHERE priority_code = %s", (code,)).fetchone()
        if row is None:
            raise RuleError("No such goal or priority.")
        conn.execute("UPDATE dbo.annual_priority SET description = %s WHERE priority_code = %s",
                     ((description or "").strip() or None, code))
        audit(person_id, "update_priority_description", str(key),
              {"before": row["description"], "after": (description or "").strip() or None})
    else:
        raise RuleError("Unknown entry type.")


#: ---------------------------------------------------------------------------
#: The remaining active surfaces (change `rev2-remaining-surfaces`).
#: ---------------------------------------------------------------------------


def initiative_signals(conn, limit=12):
    """The home page's current-progress strip: existing initiatives with their
    derived current progress."""
    if engine(conn) == "mssql":
        rows = [_d(r) for r in conn.execute(
            "SELECT s.initiative_code AS Code, s.initiative_code AS MIId, "
            "       s.initiative_name AS InitiativeName, 'Team Initiative' AS Level, "
            "       o.display_name AS Owner, CAST(s.progress_current AS FLOAT) AS PercentComplete, "
            "       s.status_current AS Status "
            "FROM dbo.vw_initiative_summary s "
            "LEFT JOIN dbo.vw_primary_reporting_owner o ON o.initiative_id = s.initiative_id "
            "WHERE s.initiative_level = 'D-1' "
            "ORDER BY s.initiative_code "
            "OFFSET 0 ROWS FETCH NEXT " + str(int(limit)) + " ROWS ONLY").fetchall()]
        for r in rows:
            r["HasUpdate"] = r["PercentComplete"] is not None
            r["Code"] = r["MIId"] or r["Code"]
        return rows
    rows = [_d(r) for r in conn.execute(
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
        (limit,)).fetchall()]
    for r in rows:
        r["HasUpdate"] = r["PercentComplete"] is not None
        r["Code"] = r["MIId"] or r["Code"]
    return rows


def relationships_for(conn, codes):
    """What each Team Initiative contributes to, keyed by its canon id."""
    if not codes:
        return {}
    if engine(conn) == "mssql":
        ph = ",".join("%s" for _ in codes)
        idmap = {r["initiative_id"]: r["initiative_code"] for r in conn.execute(
            "SELECT initiative_id, initiative_code FROM dbo.initiative "
            "WHERE initiative_code IN (%s) AND initiative_level = 'D-1'" % ph, tuple(codes))}
        if not idmap:
            return {}
        ids = list(idmap)
        idph = ",".join("%s" for _ in ids)
        rows = [_d(r) for r in conn.execute(
            "SELECT kl.from_initiative_id AS InitiativeID, 'Contributes to' AS Direction, "
            "       d.initiative_code AS Code, d.initiative_name AS InitiativeName, "
            "       NULL AS Owner, NULL AS Status, NULL AS PercentComplete "
            "FROM dbo.initiative_relationship kl JOIN dbo.initiative d "
            "       ON d.initiative_id = kl.to_initiative_id "
            "WHERE kl.from_initiative_id IN (%s) AND kl.relationship_type IN ('Supports','Contributes To') "
            "ORDER BY d.initiative_code" % idph, tuple(ids)).fetchall()]
        out = {}
        for r in rows:
            subj = idmap.get(r["InitiativeID"])
            if subj:
                out.setdefault(subj, []).append(r)
        return out
    placeholders = ",".join("?" * len(codes))
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
    rows = [_d(r) for r in conn.execute(
        "SELECT kl.TeamInitiativeID AS InitiativeID, 'Contributes to' AS Direction, "
        "       d.Code AS Code, d.Title AS InitiativeName, "
        "       NULL AS Owner, NULL AS Status, NULL AS PercentComplete "
        "FROM TeamInitiativeDeanLinks kl JOIN DeanInitiatives d "
        "       ON d.DeanInitiativeID = kl.DeanInitiativeID "
        "WHERE kl.TeamInitiativeID IN (%s) "
        "ORDER BY Direction, d.Code" % id_ph, tuple(ids)).fetchall()]
    out = {}
    for r in rows:
        subject = id_to_code.get(r["InitiativeID"])
        if subject:
            out.setdefault(subject, []).append(r)
    return out


def dean_initiatives(conn):
    """The Dean's initiatives, FY26 then FY27, with priority + D-1 roll-up."""
    if engine(conn) == "mssql":
        from app import priorities as canon
        rows = []
        for r in conn.execute(
                "SELECT i.initiative_id, i.initiative_code AS code, i.initiative_name AS title, "
                "       i.description AS description, NULL AS percent_complete, "
                "       LEFT(i.initiative_code, 3) AS yr, "
                "       ap.priority_code AS priority_code "
                "FROM dbo.initiative i "
                "LEFT JOIN dbo.initiative_priority ip ON ip.initiative_id = i.initiative_id AND ip.relationship_type = 'Primary' "
                "LEFT JOIN dbo.annual_priority ap ON ap.priority_id = ip.priority_id "
                "WHERE i.initiative_level = 'Dean' AND i.active_flag = 1 "
                "ORDER BY i.initiative_code"):
            code = r["code"] or ""
            fy = 27 if "D27" in code else 26
            pcode = r["priority_code"]
            rows.append({
                "DeanInitiativeID": r["initiative_id"], "fiscal_year": fy, "code": code,
                "title": r["title"], "description": r["description"],
                "percent_complete": r["percent_complete"],
                "priority_code": pcode,
                "priority_title": canon.title_for_code(pcode) if pcode else None,
                "priority_colour": None,
            })
        rolled = {}
        for r in conn.execute(
                "SELECT kl.to_initiative_id AS did, d.initiative_code AS MIId, d.initiative_name AS Title "
                "FROM dbo.initiative_relationship kl JOIN dbo.initiative d ON d.initiative_id = kl.from_initiative_id "
                "WHERE kl.relationship_type = 'Supports' AND d.initiative_level = 'D-1' AND d.active_flag = 1 "
                "ORDER BY d.initiative_code"):
            rolled.setdefault(r["did"], []).append({"mi_id": r["MIId"], "title": r["Title"]})
        for r in rows:
            r["initiatives"] = rolled.get(r["DeanInitiativeID"], [])
        return rows
    rows = [_d(r) for r in conn.execute(
        "SELECT DeanInitiativeID, FiscalYear AS fiscal_year, Code AS code, "
        "       Title AS title, Description AS description, "
        "       PercentComplete AS percent_complete, "
        "       PriorityCode AS priority_code, PriorityTitle AS priority_title, "
        "       PriorityColour AS priority_colour "
        "FROM vw_DeanInitiatives ORDER BY FiscalYear, Code").fetchall()]
    rolled = {}
    for r in conn.execute(
            "SELECT kl.DeanInitiativeID, k.MIId, k.Title "
            "FROM TeamInitiativeDeanLinks kl "
            "JOIN TeamInitiatives k ON k.TeamInitiativeID = kl.TeamInitiativeID "
            "WHERE k.IsActive = 1 ORDER BY k.MIId"):
        rolled.setdefault(r["DeanInitiativeID"], []).append({"mi_id": r["MIId"], "title": r["Title"]})
    for r in rows:
        r["initiatives"] = rolled.get(r["DeanInitiativeID"], [])
    return rows


def team_initiative_dean_links(conn, mi_id):
    """The Dean items a Team Initiative contributes to, keyed by the dean code."""
    if engine(conn) == "mssql":
        return [_d(r) for r in conn.execute(
            "SELECT p.initiative_code AS dean_code, p.initiative_name AS dean_title "
            "FROM dbo.initiative_relationship kl JOIN dbo.initiative p ON p.initiative_id = kl.to_initiative_id "
            "WHERE kl.from_initiative_id = (SELECT initiative_id FROM dbo.initiative WHERE initiative_code = %s) "
            "  AND kl.relationship_type = 'Supports' AND p.initiative_level = 'Dean' "
            "ORDER BY p.initiative_code", (mi_id,)).fetchall()]
    return [_d(r) for r in conn.execute(
        "SELECT DeanCode AS dean_code, DeanTitle AS dean_title "
        "FROM vw_TeamInitiativeDeanLinks WHERE MIId = ? ORDER BY DeanCode", (mi_id,)).fetchall()]


def data_checks(conn):
    """The data-quality checks: active initiatives with no goal or no priority."""
    if engine(conn) == "mssql":
        return [_d(r) for r in conn.execute(
            "SELECT i.initiative_code AS Code, 'No goal tagged' AS Issue FROM dbo.initiative i "
            "WHERE i.active_flag = 1 AND i.initiative_level = 'D-1' "
            "  AND NOT EXISTS (SELECT 1 FROM dbo.initiative_goal g WHERE g.initiative_id = i.initiative_id) "
            "UNION ALL "
            "SELECT i.initiative_code, 'No priority tagged' FROM dbo.initiative i "
            "WHERE i.active_flag = 1 AND i.initiative_level = 'D-1' "
            "  AND NOT EXISTS (SELECT 1 FROM dbo.initiative_priority p WHERE p.initiative_id = i.initiative_id) "
            "ORDER BY Code, Issue").fetchall()]
    return [_d(r) for r in conn.execute(
        "SELECT Code, Issue FROM vw_DataChecks ORDER BY Code, Issue").fetchall()]


def recent_changes(conn, limit=100):
    """The change log, newest first, with who made each change."""
    if engine(conn) == "mssql":
        return [_d(r) for r in conn.execute(
            "SELECT a.created_at AS created_at, per.display_name AS person, a.action AS action, "
            "       a.entity_type AS entity_type, a.entity_key AS entity_key, "
            "       a.reason AS reason, a.source AS source, a.correlation_id AS correlation_id "
            "FROM dbo.audit_log a LEFT JOIN dbo.person per ON per.person_id = a.person_id "
            "ORDER BY a.created_at DESC, a.audit_id DESC "
            "OFFSET 0 ROWS FETCH NEXT " + str(int(limit)) + " ROWS ONLY").fetchall()]
    return [_d(r) for r in conn.execute(
        "SELECT a.CreatedAt AS created_at, p.Name AS person, a.Action AS action, "
        "       a.EntityType AS entity_type, a.EntityKey AS entity_key, "
        "       a.Reason AS reason, a.Source AS source, "
        "       a.CorrelationID AS correlation_id "
        "FROM AuditLog a LEFT JOIN People p ON p.PersonID = a.PersonID "
        "ORDER BY a.CreatedAt DESC, a.AuditID DESC LIMIT ?", (limit,)).fetchall()]


#: ---------------------------------------------------------------------------
#: Auth surface (change `port-auth-to-rev2`). The app's key shape is preserved:
#: PersonID is the app's int (PERS-N on Rev2 projected back), Name/Title are the
#: display fields. Roles come from the reconciled role/person_role.
#: ---------------------------------------------------------------------------


def _person_row_mssql(conn, person_id):
    row = conn.execute(
        "SELECT person_id, display_name, working_title FROM dbo.person "
        "WHERE person_id = %s AND active_flag = 1", ("PERS-%d" % person_id,)).fetchone()
    if row is None:
        return None
    return {"PersonID": person_id, "Name": row["display_name"],
            "Title": row["working_title"], "ReportsToID": None, "IsAdmin": None}


def auth_person(conn, person_id):
    """The person record for current_person / person_exists, or None."""
    if engine(conn) == "mssql":
        return _person_row_mssql(conn, person_id)
    row = conn.execute(
        "SELECT PersonID, Name, Title, ReportsToID, IsAdmin "
        "FROM People WHERE PersonID = ? AND IsActive = 1", (person_id,)).fetchone()
    return dict(row) if row else None


def auth_active_people(conn):
    if engine(conn) == "mssql":
        out = []
        for r in conn.execute(
                "SELECT person_id, display_name, working_title FROM dbo.person "
                "WHERE active_flag = 1 ORDER BY display_name"):
            out.append({"PersonID": _pid_int(r["person_id"]), "Name": r["display_name"],
                        "Title": r["working_title"]})
        return out
    return [_d(r) for r in conn.execute(
        "SELECT PersonID, Name, Title FROM People WHERE IsActive = 1 ORDER BY Name").fetchall()]


def auth_get_initiative(conn, mi_id):
    """Resolve a Team Initiative by its canon key, if active."""
    if engine(conn) == "mssql":
        row = conn.execute(
            "SELECT initiative_id, initiative_code, initiative_name, "
            "       (SELECT TOP 1 o.person_id FROM dbo.initiative_owner o "
            "        WHERE o.initiative_id = i.initiative_id AND o.ownership_role = 'Reporting Owner' "
            "          AND o.primary_flag = 1 AND o.effective_end IS NULL) AS owner_id "
            "FROM dbo.initiative i WHERE i.initiative_code = %s AND i.active_flag = 1 "
            "  AND i.initiative_level = 'D-1'", (mi_id,)).fetchone()
        if row is None:
            return None
        return {"TeamInitiativeID": row["initiative_id"], "MIId": row["initiative_code"],
                "InitiativeName": row["initiative_name"], "OwnerID": _pid_int(row["owner_id"])}
    row = conn.execute(
        "SELECT TeamInitiativeID, MIId, Title AS InitiativeName, OwnerID "
        "FROM TeamInitiatives WHERE MIId = ? AND IsActive = 1", (mi_id,)).fetchone()
    return dict(row) if row else None


def auth_roles_of(conn, person_id):
    """The role names a person holds, from the reconciled role store."""
    if engine(conn) == "mssql":
        return {r["name"] for r in conn.execute(
            "SELECT ro.name FROM dbo.person_role pr JOIN dbo.role ro ON ro.role_id = pr.role_id "
            "WHERE pr.person_id = %s", ("PERS-%d" % person_id,))}
    return {r["Name"] for r in conn.execute(
        "SELECT r.Name FROM PeopleRoles pr JOIN Roles r ON r.RoleID = pr.RoleID "
        "WHERE pr.PersonID = ?", (person_id,))}


def auth_person_by_clerk_id(conn, clerk_user_id):
    if engine(conn) == "mssql":
        row = conn.execute(
            "SELECT person_id, display_name, working_title FROM dbo.person "
            "WHERE clerk_user_id = %s AND active_flag = 1", (clerk_user_id,)).fetchone()
        if row is None:
            return None
        return {"PersonID": _pid_int(row["person_id"]), "Name": row["display_name"],
                "Title": row["working_title"], "ReportsToID": None, "IsAdmin": None}
    row = conn.execute(
        "SELECT PersonID, Name, Title, ReportsToID, IsAdmin "
        "FROM People WHERE ClerkUserID = ? AND IsActive = 1", (clerk_user_id,)).fetchone()
    return dict(row) if row else None


def auth_link_person_to_clerk(conn, person_id, clerk_user_id):
    if engine(conn) == "mssql":
        conn.execute("UPDATE dbo.person SET clerk_user_id = %s WHERE person_id = %s",
                     (clerk_user_id or None, "PERS-%d" % person_id))
        return
    conn.execute("UPDATE People SET ClerkUserID = ? WHERE PersonID = ?",
                 ((clerk_user_id or None), int(person_id)))


def auth_role_ids(conn):
    """role name -> role id, read once. Empty if the store predates roles."""
    if engine(conn) == "mssql":
        return {r["name"]: r["role_id"] for r in conn.execute(
            "SELECT name, role_id FROM dbo.role")}
    return {r["Name"]: r["RoleID"] for r in conn.execute("SELECT RoleID, Name FROM Roles")}


def auth_database_reachable(conn):
    """A trivial read proving the configured store answers (/healthz)."""
    if engine(conn) == "mssql":
        conn.execute("SELECT TOP 1 initiative_id FROM dbo.initiative").fetchone()
    else:
        conn.execute("SELECT 1 FROM TeamInitiatives LIMIT 1").fetchone()
    return True
