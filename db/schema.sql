-- =====================================================================
-- SUPERSEDED 2026-10-06 by Revision 2 (db/rev2/, db/mssql/)
-- =====================================================================
-- This file describes the PROTOTYPE schema - nine tables, one owner per
-- initiative, one meaning per initiative link. It remains accurate as a record
-- of what the prototype does, and the prototype is still deployed, so it is NOT
-- deleted. It is no longer the target model.
--
-- Revision 2 supersedes it: 27 tables plus one addition, effective-dated
-- multi-role ownership, ten-or-five typed relationships, a traceability tier
-- between goals and initiatives, and reusable priority definitions.
-- See db/rev2/PROVENANCE.md for the package this was transcribed from.
--
-- Table mapping, prototype -> Revision 2:
--
--   Goals                 -> goal  (+ strategic_objective, a tier this model lacks)
--   Priorities(PlanYear)  -> annual_priority  and, in Rev2,
--                            priority_definition + planning_cycle + priority_cycle
--   People                -> person  (+ team); the prototype's IsAdmin flag is an
--                            application concern and has no Rev2 counterpart
--   Initiatives           -> initiative  (gains type, validation status, dates)
--   InitiativeGoals       -> initiative_goal  (gains relationship type and dates)
--   InitiativePriorities  -> initiative_priority / initiative_priority_cycle
--   InitiativeLinks       -> initiative_relationship  (one meaning becomes five
--                            permitted types; direction is level-enforced)
--   Initiatives.OwnerID   -> initiative_owner  (one slot becomes four roles,
--                            effective-dated) + stewardship_assignment
--   ProgressUpdates       -> initiative_update  (append-only, attributed)
--   AuditLog              -> NO Rev2 COUNTERPART. Effective-dated rows and
--                            validation_event carry what it held. See design.md D7.
--   vw_* views            -> redefined in Rev2; the prototype's versions resolve
--                            through OwnerID and InitiativeLinks, both replaced
--
-- NOT carried forward: nothing. The prototype's behaviour is either represented
-- in Rev2 or recorded as deliberately dropped, with the drop named above.
-- =====================================================================

-- =====================================================================
-- CLL Strategic Initiatives Database  (v3, SQLite for local dev)
-- Two entry points: Strategy 2035 Goals (5) and Annual Priorities (6)
-- Two initiative levels: Dean, and D-1 (each D-1 feeds 1+ Dean initiatives)
-- Progress is self-reported: percent + status + narrative diary
-- Run with foreign keys ON:  PRAGMA foreign_keys = ON;
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------- Lookup tables ----------

CREATE TABLE Goals (
    GoalID       INTEGER PRIMARY KEY,
    GoalNumber   INTEGER NOT NULL UNIQUE CHECK (GoalNumber BETWEEN 1 AND 5),
    ShortName    TEXT    NOT NULL UNIQUE,      -- standardized label
    FullName     TEXT,                         -- official Strategy 2035 wording
    Description  TEXT
);

CREATE TABLE Priorities (
    PriorityID   INTEGER PRIMARY KEY,
    PriorityName TEXT    NOT NULL,
    PlanYear     INTEGER NOT NULL,
    Description  TEXT,
    -- The prototype's governed definition, per priority (blueprint-redesign
    -- scope correction). These four are its fields we did not hold.
    Code         TEXT,      -- 'P01'..'P06'
    FullTitle    TEXT,      -- 'One Shared Identity'
    Measure      TEXT,      -- how the priority is measured
    Target       TEXT,      -- its stated target
    Cadence      TEXT,      -- review rhythm
    OwnerLabel   TEXT,      -- e.g. 'Dean + Learning Infrastructure'
    Colour       TEXT,      -- its key colour
    UNIQUE (PriorityName, PlanYear)
);

-- ---------- Organizational layer (blueprint-redesign scope correction) -------
-- The Dean's prototype carries a layer beneath the six priorities: four
-- organizational TEAMS, and 29 Major Initiatives grouped by FIVE source areas. Our
-- schema held none of it.
--
-- NOTE: this deliberately contradicts config.yaml's "Nothing below D-1 (no
-- tasks, no metrics)". The user directed that every prototype field be
-- included, and the contradiction is recorded rather than left silent.

CREATE TABLE Teams (
    TeamID       INTEGER PRIMARY KEY,
    Name         TEXT    NOT NULL UNIQUE,
    Description  TEXT
);

CREATE TABLE SourceAreas (
    SourceAreaID INTEGER PRIMARY KEY,
    Name         TEXT    NOT NULL UNIQUE
);

-- The 29 Major Initiatives. `TeamID` is the team accountable; `SourceAreaID` is the
-- workbook area they came from; the two are different axes.
CREATE TABLE MajorInitiatives (
    MajorInitiativeID          INTEGER PRIMARY KEY,
    Code           TEXT    NOT NULL UNIQUE,   -- e.g. '3-02'
    -- The canon workbook's own stable key (MI-001..MI-029), so a row can be
    -- cited by the identifier the source register uses.
    MIId           TEXT    UNIQUE,
    Title          TEXT    NOT NULL,
    TeamID         INTEGER REFERENCES Teams(TeamID),
    SourceAreaID   INTEGER REFERENCES SourceAreas(SourceAreaID),
    StrategyAlign  TEXT,        -- 'Goals 1 + 3: Credentials & pathways'
    Initiatives    TEXT,        -- the initiatives named in the prototype
    -- The only target we hold. The canon workbook carries no target column, and
    -- the prototype's separate `SourceTarget` was always equal to this or null,
    -- so it was dropped as a duplicate (2026-10-07).
    ProposedTarget TEXT,
    TargetStatus   TEXT NOT NULL DEFAULT 'needs_review'
                   CHECK (TargetStatus IN ('source','needs_review')),
    Status         TEXT NOT NULL DEFAULT 'Not started',
    Note           TEXT
);

-- Which priorities a Major Initiative feeds (its `priorities` array).
CREATE TABLE MajorInitiativePriorities (
    MajorInitiativeID      INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    PriorityID INTEGER NOT NULL REFERENCES Priorities(PriorityID),
    PRIMARY KEY (MajorInitiativeID, PriorityID)
);

-- Which Strategy 2035 goals a Major Initiative aligns to, parsed from the
-- canon workbook's `Strategy Alignment` column. This is the MI -> Goal edge that
-- register states and the schema did not hold.
CREATE TABLE MajorInitiativeGoals (
    MajorInitiativeID  INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    GoalID INTEGER NOT NULL REFERENCES Goals(GoalID),
    PRIMARY KEY (MajorInitiativeID, GoalID)
);


CREATE TABLE People (
    PersonID     INTEGER PRIMARY KEY,
    Name         TEXT NOT NULL,
    Title        TEXT,
    Email        TEXT,
    ReportsToID  INTEGER REFERENCES People(PersonID),   -- NULL for the Dean
    IsAdmin      INTEGER NOT NULL DEFAULT 0 CHECK (IsAdmin IN (0,1)),  -- dashboard team: edits everything
    IsActive     INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1))
);

-- ---------- Initiatives ----------

CREATE TABLE Initiatives (
    InitiativeID   INTEGER PRIMARY KEY,
    Code           TEXT NOT NULL UNIQUE,       -- e.g. 'D-A', 'ELIZ-1'
    InitiativeName TEXT NOT NULL,
    Description    TEXT,
    Level          TEXT NOT NULL CHECK (Level IN ('Dean','D-1')),
    OwnerID        INTEGER NOT NULL REFERENCES People(PersonID),
    IsActive       INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1))  -- retire, don't delete
);

-- ---------- Tag tables (many-to-many) ----------

CREATE TABLE InitiativeGoals (
    InitiativeID INTEGER NOT NULL REFERENCES Initiatives(InitiativeID),
    GoalID       INTEGER NOT NULL REFERENCES Goals(GoalID),
    IsPrimary    INTEGER NOT NULL DEFAULT 0 CHECK (IsPrimary IN (0,1)),
    PRIMARY KEY (InitiativeID, GoalID)
);

CREATE TABLE InitiativePriorities (
    InitiativeID INTEGER NOT NULL REFERENCES Initiatives(InitiativeID),
    PriorityID   INTEGER NOT NULL REFERENCES Priorities(PriorityID),
    IsPrimary    INTEGER NOT NULL DEFAULT 0 CHECK (IsPrimary IN (0,1)),
    PRIMARY KEY (InitiativeID, PriorityID)
);

-- "This initiative feeds that Dean initiative"
CREATE TABLE InitiativeLinks (
    InitiativeID     INTEGER NOT NULL REFERENCES Initiatives(InitiativeID),
    DeanInitiativeID INTEGER NOT NULL REFERENCES Initiatives(InitiativeID),
    PRIMARY KEY (InitiativeID, DeanInitiativeID),
    CHECK (InitiativeID <> DeanInitiativeID)
);

-- Only one primary goal and one primary priority per initiative
CREATE UNIQUE INDEX UX_IG_OnePrimary ON InitiativeGoals(InitiativeID)      WHERE IsPrimary = 1;
CREATE UNIQUE INDEX UX_IP_OnePrimary ON InitiativePriorities(InitiativeID) WHERE IsPrimary = 1;

-- ---------- Progress diary ----------

CREATE TABLE ProgressUpdates (
    UpdateID        INTEGER PRIMARY KEY,
    InitiativeID    INTEGER NOT NULL REFERENCES Initiatives(InitiativeID),  -- no cascade: history is kept
    UpdateDate      TEXT    NOT NULL DEFAULT (date('now')),
    PercentComplete INTEGER NOT NULL CHECK (PercentComplete BETWEEN 0 AND 100),
    Status          TEXT    NOT NULL DEFAULT 'On track'
                    CHECK (Status IN ('Not started','On track','At risk','Off track','Complete','Paused')),
    Note            TEXT,                       -- 2-3 sentence narrative
    EnteredByID     INTEGER REFERENCES People(PersonID),
    CreatedAt       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Who changed what (edits to initiatives, tags, links, descriptions)
CREATE TABLE AuditLog (
    AuditID     INTEGER PRIMARY KEY,
    CreatedAt   TEXT    NOT NULL DEFAULT (datetime('now')),
    PersonID    INTEGER REFERENCES People(PersonID),
    Action      TEXT    NOT NULL,     -- e.g. 'update_initiative', 'add_goal_tag', 'remove_link'
    EntityType  TEXT    NOT NULL,     -- 'Initiative','Goal','Priority','Link','Tag'
    EntityKey   TEXT    NOT NULL,     -- Code or ID
    Details     TEXT                  -- JSON of before/after
);

CREATE INDEX IX_Initiatives_Owner ON Initiatives(OwnerID);
CREATE INDEX IX_IG_Goal           ON InitiativeGoals(GoalID);
CREATE INDEX IX_IP_Priority       ON InitiativePriorities(PriorityID);
CREATE INDEX IX_IL_Dean           ON InitiativeLinks(DeanInitiativeID);
CREATE INDEX IX_PU_Init_Date      ON ProgressUpdates(InitiativeID, UpdateDate);

-- ---------- Rule enforcement (Level rules) ----------

-- Links must go D-1 -> Dean
CREATE TRIGGER trg_Links_LevelCheck
BEFORE INSERT ON InitiativeLinks
WHEN (SELECT Level FROM Initiatives WHERE InitiativeID = NEW.InitiativeID) <> 'D-1'
  OR (SELECT Level FROM Initiatives WHERE InitiativeID = NEW.DeanInitiativeID) <> 'Dean'
BEGIN
    SELECT RAISE(ABORT, 'Links must connect a D-1 initiative to a Dean initiative');
END;

CREATE TRIGGER trg_Links_LevelCheck_Upd
BEFORE UPDATE ON InitiativeLinks
WHEN (SELECT Level FROM Initiatives WHERE InitiativeID = NEW.InitiativeID) <> 'D-1'
  OR (SELECT Level FROM Initiatives WHERE InitiativeID = NEW.DeanInitiativeID) <> 'Dean'
BEGIN
    SELECT RAISE(ABORT, 'Links must connect a D-1 initiative to a Dean initiative');
END;

-- ---------- Views (one per card / list) ----------

CREATE VIEW vw_LatestProgress AS
SELECT InitiativeID, UpdateDate, PercentComplete, Status, Note
FROM (
    SELECT pu.*, ROW_NUMBER() OVER (PARTITION BY InitiativeID
                                    ORDER BY UpdateDate DESC, UpdateID DESC) AS rn
    FROM ProgressUpdates pu
)
WHERE rn = 1;

-- Goal list / goal card: Dean initiatives above the line, D-1 below
CREATE VIEW vw_GoalInitiatives AS
SELECT g.GoalNumber, g.ShortName AS Goal, i.InitiativeID, i.Level, i.Code, i.InitiativeName,
       p.PersonID AS OwnerID, p.Name AS Owner, ig.IsPrimary, lp.PercentComplete, lp.Status
FROM InitiativeGoals ig
JOIN Goals g       ON g.GoalID = ig.GoalID
JOIN Initiatives i ON i.InitiativeID = ig.InitiativeID AND i.IsActive = 1
JOIN People p      ON p.PersonID = i.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;

-- Priority list / priority card: same shape, other entry point
CREATE VIEW vw_PriorityInitiatives AS
SELECT pr.PriorityName AS Priority, pr.PlanYear, i.InitiativeID, i.Level, i.Code, i.InitiativeName,
       p.PersonID AS OwnerID, p.Name AS Owner, ip.IsPrimary, lp.PercentComplete, lp.Status
FROM InitiativePriorities ip
JOIN Priorities pr ON pr.PriorityID = ip.PriorityID
JOIN Initiatives i ON i.InitiativeID = ip.InitiativeID AND i.IsActive = 1
JOIN People p      ON p.PersonID = i.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;

-- Initiative card: what it feeds (up) and what feeds it (down)
CREATE VIEW vw_InitiativeConnections AS
SELECT l.DeanInitiativeID AS InitiativeID, 'Fed by' AS Direction,
       c.Code, c.InitiativeName, pc.PersonID AS OwnerID, pc.Name AS Owner,
       lp.PercentComplete, lp.Status
FROM InitiativeLinks l
JOIN Initiatives c ON c.InitiativeID = l.InitiativeID
JOIN People pc     ON pc.PersonID = c.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = c.InitiativeID
UNION ALL
SELECT l.InitiativeID, 'Feeds', d.Code, d.InitiativeName, pd.PersonID, pd.Name,
       lp.PercentComplete, lp.Status
FROM InitiativeLinks l
JOIN Initiatives d ON d.InitiativeID = l.DeanInitiativeID
JOIN People pd     ON pd.PersonID = d.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = d.InitiativeID;

-- Person card: everything a person owns, with latest progress
CREATE VIEW vw_PersonInitiatives AS
SELECT p.PersonID, p.Name AS Owner, i.InitiativeID, i.Level, i.Code, i.InitiativeName,
       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated
FROM People p
JOIN Initiatives i ON i.OwnerID = p.PersonID AND i.IsActive = 1
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;

-- Data checks: fix these before the dashboard goes live
CREATE VIEW vw_DataChecks AS
SELECT i.Code, 'D-1 initiative not linked to any Dean initiative' AS Issue
FROM Initiatives i
WHERE i.Level = 'D-1' AND i.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM InitiativeLinks l WHERE l.InitiativeID = i.InitiativeID)
UNION ALL
SELECT i.Code, 'No goal tagged'
FROM Initiatives i
WHERE i.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM InitiativeGoals g WHERE g.InitiativeID = i.InitiativeID)
UNION ALL
SELECT i.Code, 'No priority tagged'
FROM Initiatives i
WHERE i.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM InitiativePriorities p WHERE p.InitiativeID = i.InitiativeID)
UNION ALL
SELECT i.Code, 'No progress update yet'
FROM Initiatives i
WHERE i.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM ProgressUpdates u WHERE u.InitiativeID = i.InitiativeID)
UNION ALL
-- Alignment: D-1 tagged to a goal that none of its Dean initiatives carry
SELECT DISTINCT c.Code, 'Tagged to goal ' || g.ShortName || ' but no linked Dean initiative is'
FROM Initiatives c
JOIN InitiativeGoals cg ON cg.InitiativeID = c.InitiativeID
JOIN Goals g            ON g.GoalID = cg.GoalID
WHERE c.Level = 'D-1' AND c.IsActive = 1
  AND EXISTS (SELECT 1 FROM InitiativeLinks l WHERE l.InitiativeID = c.InitiativeID)
  AND NOT EXISTS (
      SELECT 1 FROM InitiativeLinks l
      JOIN InitiativeGoals dg ON dg.InitiativeID = l.DeanInitiativeID
      WHERE l.InitiativeID = c.InitiativeID AND dg.GoalID = cg.GoalID);

-- Meeting view: updates entered in a date range, newest first
-- Updates in a date window, newest first.
-- NOTE: the view deliberately carries no WHERE and no ORDER BY. The window
-- and the ordering are the caller's job, so the same view serves /meeting
-- for any window without the schema knowing about meeting dates.
CREATE VIEW vw_RecentUpdates AS
SELECT pu.UpdateDate, pu.CreatedAt, i.InitiativeID, i.Code, i.InitiativeName, i.Level,
       o.PersonID AS OwnerID, o.Name AS Owner, pu.PercentComplete, pu.Status, pu.Note,
       e.Name AS EnteredBy
FROM ProgressUpdates pu
JOIN Initiatives i ON i.InitiativeID = pu.InitiativeID AND i.IsActive = 1
JOIN People o      ON o.PersonID = i.OwnerID
LEFT JOIN People e ON e.PersonID = pu.EnteredByID;


-- ---------- Read models for the organizational layer -------------------------
-- One view per screen, matching the existing convention. These expose the
-- 29 Major Initiatives with their team, source area, and what they feed.

CREATE VIEW vw_MajorInitiatives AS
SELECT k.MajorInitiativeID, k.Code, k.Title, k.StrategyAlign, k.Initiatives,
       k.ProposedTarget, k.TargetStatus,
       k.Status, k.Note,
       t.TeamID, t.Name AS Team,
       sa.SourceAreaID, sa.Name AS SourceArea
FROM MajorInitiatives k
LEFT JOIN Teams t       ON t.TeamID = k.TeamID
LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID;

-- Which priorities each Major Initiative feeds, one row per link.
CREATE VIEW vw_MajorInitiativePriorities AS
SELECT kp.MajorInitiativeID, k.Code AS MajorInitiativeCode, k.Title AS MajorInitiativeTitle,
       p.PriorityID, p.PriorityName, p.Code AS PriorityCode,
       p.FullTitle AS PriorityTitle, p.Colour AS PriorityColour
FROM MajorInitiativePriorities kp
JOIN MajorInitiatives k       ON k.MajorInitiativeID = kp.MajorInitiativeID
JOIN Priorities p     ON p.PriorityID = kp.PriorityID;

-- Team rollup: how many Major Initiatives each team carries, and how many review.
CREATE VIEW vw_TeamSummary AS
SELECT t.TeamID, t.Name AS Team, t.Description,
       COUNT(k.MajorInitiativeID) AS MajorInitiativeCount,
       SUM(CASE WHEN k.TargetStatus = 'needs_review' THEN 1 ELSE 0 END) AS NeedsReview
FROM Teams t
LEFT JOIN MajorInitiatives k ON k.TeamID = t.TeamID
GROUP BY t.TeamID, t.Name, t.Description;


-- The MI -> Goal edge, one row per link, for the goal page and MI page.
CREATE VIEW vw_MajorInitiativeGoals AS
SELECT kg.MajorInitiativeID, k.Code AS MajorInitiativeCode, k.MIId, k.Title AS MajorInitiativeTitle,
       g.GoalID, g.GoalNumber, g.ShortName AS GoalShort
FROM MajorInitiativeGoals kg
JOIN MajorInitiatives k ON k.MajorInitiativeID = kg.MajorInitiativeID
JOIN Goals g    ON g.GoalID = kg.GoalID;
