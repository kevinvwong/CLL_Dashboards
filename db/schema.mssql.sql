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

/* =====================================================================
   CLL Strategic Initiatives Database  (v3, T-SQL for Azure SQL / SQL Server)
   Mirrors db/schema.sql (SQLite) table-for-table and view-for-view.
   Keep the two files in sync: any schema change goes into both.

   Two entry points: Strategy 2035 Goals (5) and Annual Priorities (6)
   Two initiative levels: Dean, and D-1 (each D-1 feeds 1+ Dean initiatives)
   Progress is self-reported: percent + status + narrative diary

   Dialect notes vs SQLite:
     INTEGER PRIMARY KEY -> INT IDENTITY; 0/1 flags -> BIT; TEXT -> NVARCHAR
     date('now') -> CAST(SYSUTCDATETIME() AS DATE); datetime('now') -> SYSUTCDATETIME()
     BEFORE trigger -> AFTER trigger with THROW (rolls back the statement)
     '||' string concat -> '+'
   ===================================================================== */

/* ---------- Lookup tables ---------- */

CREATE TABLE Goals (
    GoalID       INT IDENTITY(1,1) PRIMARY KEY,
    GoalNumber   TINYINT NOT NULL,
    ShortName    NVARCHAR(50)  NOT NULL,            -- standardized label
    FullName     NVARCHAR(300) NULL,                -- official Strategy 2035 wording
    Description  NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_Goals_Number    UNIQUE (GoalNumber),
    CONSTRAINT UQ_Goals_ShortName UNIQUE (ShortName),
    CONSTRAINT CK_Goals_Number    CHECK (GoalNumber BETWEEN 1 AND 5)
);

CREATE TABLE Priorities (
    PriorityID   INT IDENTITY(1,1) PRIMARY KEY,
    PriorityName NVARCHAR(100) NOT NULL,
    PlanYear     SMALLINT      NOT NULL,
    Description  NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_Priorities_NameYear UNIQUE (PriorityName, PlanYear)
);

CREATE TABLE People (
    PersonID     INT IDENTITY(1,1) PRIMARY KEY,
    Name         NVARCHAR(150) NOT NULL,
    Title        NVARCHAR(200) NULL,
    Email        NVARCHAR(200) NULL,
    ReportsToID  INT NULL                                   -- NULL for the Dean
                 CONSTRAINT FK_People_ReportsTo REFERENCES People(PersonID),
    IsAdmin      BIT NOT NULL CONSTRAINT DF_People_IsAdmin  DEFAULT 0,  -- dashboard team
    IsActive     BIT NOT NULL CONSTRAINT DF_People_IsActive DEFAULT 1
);

/* ---------- Initiatives ---------- */

CREATE TABLE Initiatives (
    InitiativeID   INT IDENTITY(1,1) PRIMARY KEY,
    Code           NVARCHAR(20)  NOT NULL UNIQUE,       -- e.g. 'D-A', 'ELIZ-1'
    InitiativeName NVARCHAR(250) NOT NULL,
    Description    NVARCHAR(MAX) NULL,
    Level          NVARCHAR(10)  NOT NULL
                   CONSTRAINT CK_Initiatives_Level CHECK (Level IN ('Dean','D-1')),
    OwnerID        INT NOT NULL
                   CONSTRAINT FK_Initiatives_Owner REFERENCES People(PersonID),
    IsActive       BIT NOT NULL CONSTRAINT DF_Initiatives_IsActive DEFAULT 1  -- retire, don't delete
);

/* ---------- Tag tables (many-to-many) ---------- */

CREATE TABLE InitiativeGoals (
    InitiativeID INT NOT NULL CONSTRAINT FK_IG_Initiative REFERENCES Initiatives(InitiativeID),
    GoalID       INT NOT NULL CONSTRAINT FK_IG_Goal       REFERENCES Goals(GoalID),
    IsPrimary    BIT NOT NULL CONSTRAINT DF_IG_IsPrimary DEFAULT 0,
    CONSTRAINT PK_InitiativeGoals PRIMARY KEY (InitiativeID, GoalID)
);

CREATE TABLE InitiativePriorities (
    InitiativeID INT NOT NULL CONSTRAINT FK_IP_Initiative REFERENCES Initiatives(InitiativeID),
    PriorityID   INT NOT NULL CONSTRAINT FK_IP_Priority   REFERENCES Priorities(PriorityID),
    IsPrimary    BIT NOT NULL CONSTRAINT DF_IP_IsPrimary DEFAULT 0,
    CONSTRAINT PK_InitiativePriorities PRIMARY KEY (InitiativeID, PriorityID)
);

/* "This initiative feeds that Dean initiative" */
CREATE TABLE InitiativeLinks (
    InitiativeID     INT NOT NULL CONSTRAINT FK_IL_Initiative REFERENCES Initiatives(InitiativeID),
    DeanInitiativeID INT NOT NULL CONSTRAINT FK_IL_Dean       REFERENCES Initiatives(InitiativeID),
    CONSTRAINT PK_InitiativeLinks PRIMARY KEY (InitiativeID, DeanInitiativeID),
    CONSTRAINT CK_IL_NotSelf CHECK (InitiativeID <> DeanInitiativeID)
);

/* Only one primary goal and one primary priority per initiative */
CREATE UNIQUE INDEX UX_IG_OnePrimary ON InitiativeGoals(InitiativeID)      WHERE IsPrimary = 1;
CREATE UNIQUE INDEX UX_IP_OnePrimary ON InitiativePriorities(InitiativeID) WHERE IsPrimary = 1;

/* ---------- Progress diary ---------- */

CREATE TABLE ProgressUpdates (
    UpdateID        INT IDENTITY(1,1) PRIMARY KEY,
    InitiativeID    INT NOT NULL                       -- no cascade: history is kept
                    CONSTRAINT FK_PU_Initiative REFERENCES Initiatives(InitiativeID),
    UpdateDate      DATE NOT NULL CONSTRAINT DF_PU_UpdateDate DEFAULT CAST(SYSUTCDATETIME() AS DATE),
    PercentComplete TINYINT NOT NULL
                    CONSTRAINT CK_PU_Percent CHECK (PercentComplete BETWEEN 0 AND 100),
    Status          NVARCHAR(20) NOT NULL CONSTRAINT DF_PU_Status DEFAULT 'On track'
                    CONSTRAINT CK_PU_Status
                    CHECK (Status IN ('Not started','On track','At risk','Off track','Complete','Paused')),
    Note            NVARCHAR(2000) NULL,               -- 2-3 sentence narrative
    EnteredByID     INT NULL CONSTRAINT FK_PU_EnteredBy REFERENCES People(PersonID),
    CreatedAt       DATETIME2(0) NOT NULL CONSTRAINT DF_PU_CreatedAt DEFAULT SYSUTCDATETIME()
);

/* Who changed what (edits to initiatives, tags, links, descriptions) */
CREATE TABLE AuditLog (
    AuditID     INT IDENTITY(1,1) PRIMARY KEY,
    CreatedAt   DATETIME2(0) NOT NULL CONSTRAINT DF_AL_CreatedAt DEFAULT SYSUTCDATETIME(),
    PersonID    INT NULL CONSTRAINT FK_AL_Person REFERENCES People(PersonID),
    Action      NVARCHAR(50)  NOT NULL,     -- e.g. 'update_initiative', 'add_goal_tag'
    EntityType  NVARCHAR(30)  NOT NULL,     -- 'Initiative','Goal','Priority','Link','Tag'
    EntityKey   NVARCHAR(50)  NOT NULL,     -- Code or ID
    Details     NVARCHAR(MAX) NULL          -- JSON of before/after
);

CREATE INDEX IX_People_ReportsTo  ON People(ReportsToID);
CREATE INDEX IX_Initiatives_Owner ON Initiatives(OwnerID);
CREATE INDEX IX_IG_Goal           ON InitiativeGoals(GoalID);
CREATE INDEX IX_IP_Priority       ON InitiativePriorities(PriorityID);
CREATE INDEX IX_IL_Dean           ON InitiativeLinks(DeanInitiativeID);
CREATE INDEX IX_PU_Init_Date      ON ProgressUpdates(InitiativeID, UpdateDate);
GO

/* ---------- Rule enforcement: links must go D-1 -> Dean ---------- */

CREATE TRIGGER trg_Links_LevelCheck
ON InitiativeLinks
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted ins
        JOIN Initiatives c ON c.InitiativeID = ins.InitiativeID
        JOIN Initiatives d ON d.InitiativeID = ins.DeanInitiativeID
        WHERE c.Level <> 'D-1' OR d.Level <> 'Dean'
    )
        THROW 50001, 'Links must connect a D-1 initiative to a Dean initiative', 1;
END;
GO

/* ---------- Views (one per card / list) ---------- */

CREATE VIEW vw_LatestProgress AS
SELECT InitiativeID, UpdateDate, PercentComplete, Status, Note
FROM (
    SELECT pu.InitiativeID, pu.UpdateDate, pu.PercentComplete, pu.Status, pu.Note,
           ROW_NUMBER() OVER (PARTITION BY pu.InitiativeID
                              ORDER BY pu.UpdateDate DESC, pu.UpdateID DESC) AS rn
    FROM ProgressUpdates pu
) x
WHERE rn = 1;
GO

/* Goal list / goal card: Dean initiatives above the line, D-1 below */
CREATE VIEW vw_GoalInitiatives AS
SELECT g.GoalNumber, g.ShortName AS Goal, i.InitiativeID, i.Level, i.Code, i.InitiativeName,
       p.PersonID AS OwnerID, p.Name AS Owner, ig.IsPrimary, lp.PercentComplete, lp.Status
FROM InitiativeGoals ig
JOIN Goals g       ON g.GoalID = ig.GoalID
JOIN Initiatives i ON i.InitiativeID = ig.InitiativeID AND i.IsActive = 1
JOIN People p      ON p.PersonID = i.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;
GO

/* Priority list / priority card: same shape, other entry point */
CREATE VIEW vw_PriorityInitiatives AS
SELECT pr.PriorityName AS Priority, pr.PlanYear, i.InitiativeID, i.Level, i.Code, i.InitiativeName,
       p.PersonID AS OwnerID, p.Name AS Owner, ip.IsPrimary, lp.PercentComplete, lp.Status
FROM InitiativePriorities ip
JOIN Priorities pr ON pr.PriorityID = ip.PriorityID
JOIN Initiatives i ON i.InitiativeID = ip.InitiativeID AND i.IsActive = 1
JOIN People p      ON p.PersonID = i.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;
GO

/* Initiative card: what it feeds (up) and what feeds it (down) */
CREATE VIEW vw_InitiativeConnections AS
SELECT l.DeanInitiativeID AS InitiativeID, CAST('Fed by' AS NVARCHAR(10)) AS Direction,
       c.Code, c.InitiativeName, pc.PersonID AS OwnerID, pc.Name AS Owner,
       lp.PercentComplete, lp.Status
FROM InitiativeLinks l
JOIN Initiatives c ON c.InitiativeID = l.InitiativeID
JOIN People pc     ON pc.PersonID = c.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = c.InitiativeID
UNION ALL
SELECT l.InitiativeID, CAST('Feeds' AS NVARCHAR(10)), d.Code, d.InitiativeName, pd.PersonID, pd.Name,
       lp.PercentComplete, lp.Status
FROM InitiativeLinks l
JOIN Initiatives d ON d.InitiativeID = l.DeanInitiativeID
JOIN People pd     ON pd.PersonID = d.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = d.InitiativeID;
GO

/* Person card: everything a person owns, with latest progress */
CREATE VIEW vw_PersonInitiatives AS
SELECT p.PersonID, p.Name AS Owner, i.InitiativeID, i.Level, i.Code, i.InitiativeName,
       lp.PercentComplete, lp.Status, lp.UpdateDate AS LastUpdated
FROM People p
JOIN Initiatives i ON i.OwnerID = p.PersonID AND i.IsActive = 1
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;
GO

/* Data checks: fix these before the dashboard goes live */
CREATE VIEW vw_DataChecks AS
SELECT i.Code, CAST('D-1 initiative not linked to any Dean initiative' AS NVARCHAR(200)) AS Issue
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
/* Alignment: D-1 tagged to a goal that none of its Dean initiatives carry */
SELECT DISTINCT c.Code, 'Tagged to goal ' + g.ShortName + ' but no linked Dean initiative is'
FROM Initiatives c
JOIN InitiativeGoals cg ON cg.InitiativeID = c.InitiativeID
JOIN Goals g            ON g.GoalID = cg.GoalID
WHERE c.Level = 'D-1' AND c.IsActive = 1
  AND EXISTS (SELECT 1 FROM InitiativeLinks l WHERE l.InitiativeID = c.InitiativeID)
  AND NOT EXISTS (
      SELECT 1 FROM InitiativeLinks l
      JOIN InitiativeGoals dg ON dg.InitiativeID = l.DeanInitiativeID
      WHERE l.InitiativeID = c.InitiativeID AND dg.GoalID = cg.GoalID);
GO

/* Updates in a date window, newest first.
   NOTE: the view deliberately carries no WHERE and no ORDER BY. The window
   and the ordering are the caller's job, so the same view serves /meeting
   for any window without the schema knowing about meeting dates. */
CREATE VIEW vw_RecentUpdates AS
SELECT pu.UpdateDate, pu.CreatedAt, i.InitiativeID, i.Code, i.InitiativeName, i.Level,
       o.PersonID AS OwnerID, o.Name AS Owner, pu.PercentComplete, pu.Status, pu.Note,
       e.Name AS EnteredBy
FROM ProgressUpdates pu
JOIN Initiatives i ON i.InitiativeID = pu.InitiativeID AND i.IsActive = 1
JOIN People o      ON o.PersonID = i.OwnerID
LEFT JOIN People e ON e.PersonID = pu.EnteredByID;
GO
