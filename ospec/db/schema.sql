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
    UNIQUE (PriorityName, PlanYear)
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
SELECT g.GoalNumber, g.ShortName AS Goal, i.Level, i.Code, i.InitiativeName,
       p.Name AS Owner, ig.IsPrimary, lp.PercentComplete, lp.Status
FROM InitiativeGoals ig
JOIN Goals g       ON g.GoalID = ig.GoalID
JOIN Initiatives i ON i.InitiativeID = ig.InitiativeID AND i.IsActive = 1
JOIN People p      ON p.PersonID = i.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;

-- Priority list / priority card: same shape, other entry point
CREATE VIEW vw_PriorityInitiatives AS
SELECT pr.PriorityName AS Priority, pr.PlanYear, i.Level, i.Code, i.InitiativeName,
       p.Name AS Owner, ip.IsPrimary, lp.PercentComplete, lp.Status
FROM InitiativePriorities ip
JOIN Priorities pr ON pr.PriorityID = ip.PriorityID
JOIN Initiatives i ON i.InitiativeID = ip.InitiativeID AND i.IsActive = 1
JOIN People p      ON p.PersonID = i.OwnerID
LEFT JOIN vw_LatestProgress lp ON lp.InitiativeID = i.InitiativeID;

-- Initiative card: what it feeds (up) and what feeds it (down)
CREATE VIEW vw_InitiativeConnections AS
SELECT l.DeanInitiativeID AS InitiativeID, 'Fed by' AS Direction,
       c.Code, c.InitiativeName, pc.Name AS Owner
FROM InitiativeLinks l
JOIN Initiatives c ON c.InitiativeID = l.InitiativeID
JOIN People pc     ON pc.PersonID = c.OwnerID
UNION ALL
SELECT l.InitiativeID, 'Feeds', d.Code, d.InitiativeName, pd.Name
FROM InitiativeLinks l
JOIN Initiatives d ON d.InitiativeID = l.DeanInitiativeID
JOIN People pd     ON pd.PersonID = d.OwnerID;

-- Person card: everything a person owns, with latest progress
CREATE VIEW vw_PersonInitiatives AS
SELECT p.PersonID, p.Name AS Owner, i.Level, i.Code, i.InitiativeName,
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
CREATE VIEW vw_RecentUpdates AS
SELECT pu.UpdateDate, pu.CreatedAt, i.Code, i.InitiativeName, i.Level,
       o.Name AS Owner, pu.PercentComplete, pu.Status, pu.Note,
       e.Name AS EnteredBy
FROM ProgressUpdates pu
JOIN Initiatives i ON i.InitiativeID = pu.InitiativeID AND i.IsActive = 1
JOIN People o      ON o.PersonID = i.OwnerID
LEFT JOIN People e ON e.PersonID = pu.EnteredByID;
