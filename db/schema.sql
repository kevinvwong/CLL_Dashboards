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
    -- The register (2026-10-07 canon) carries a named owner and a description
    -- per row; both were absent from the workbook we seeded from.
    OwnerID        INTEGER REFERENCES People(PersonID),
    Description    TEXT,
    -- The only target we hold. The canon workbook carries no target column, and
    -- the prototype's separate `SourceTarget` was always equal to this or null,
    -- so it was dropped as a duplicate (2026-10-07).
    ProposedTarget TEXT,
    TargetStatus   TEXT NOT NULL DEFAULT 'needs_review'
                   CHECK (TargetStatus IN ('source','needs_review')),
    Status         TEXT NOT NULL DEFAULT 'Not started',
    Note           TEXT,
    -- Retire, don't delete (carried from the prototype model at the merge,
    -- 2026-10-07): a retired initiative disappears from every list and card but
    -- its history is kept.
    IsActive       INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1))
);

-- Which priorities a Major Initiative feeds (its `priorities` array).
-- The register states a PRIMARY and a SECONDARY priority per row, so IsPrimary
-- distinguishes them. One primary per initiative is enforced below.
CREATE TABLE MajorInitiativePriorities (
    MajorInitiativeID      INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    PriorityID INTEGER NOT NULL REFERENCES Priorities(PriorityID),
    IsPrimary  INTEGER NOT NULL DEFAULT 0 CHECK (IsPrimary IN (0,1)),
    PRIMARY KEY (MajorInitiativeID, PriorityID)
);
CREATE UNIQUE INDEX UX_MIP_OnePrimary
    ON MajorInitiativePriorities(MajorInitiativeID) WHERE IsPrimary = 1;

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
    -- The team a lead is accountable for (register, 2026-10-07). NULL for the
    -- Dean, who leads none, and for the dashboard admin.
    TeamID       INTEGER REFERENCES Teams(TeamID),
    IsAdmin      INTEGER NOT NULL DEFAULT 0 CHECK (IsAdmin IN (0,1)),  -- dashboard team: edits everything
    IsActive     INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1))
);

-- ---------- The merged initiative model (2026-10-07) -------------------------
--
-- The database used to hold TWO parallel initiative models: the prototype's
-- `Initiatives` (22 sample rows, with the progress diary, tags, links and write
-- paths) and the register's `MajorInitiatives` (the 29 canon rows). The home page
-- showed both counts at once, which read as a contradiction. The register is
-- canon, so the two are MERGED here onto the register's model: the diary and the
-- write paths move onto `MajorInitiatives`, and the five prototype tables
-- (`Initiatives`, `InitiativeGoals`, `InitiativePriorities`, `InitiativeLinks`,
-- `ProgressUpdates`) are dropped.
--
-- The 24 sample diary rows were NOT migrated: every one was about a sample
-- initiative and none named a real Major Initiative.

-- The progress diary, on the 29 Major Initiatives. Append-only, attributed,
-- exactly as the prototype's ProgressUpdates was, but keyed to the register row.
CREATE TABLE MajorInitiativeUpdates (
    UpdateID          INTEGER PRIMARY KEY,
    MajorInitiativeID INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    UpdateDate        TEXT    NOT NULL DEFAULT (date('now')),
    PercentComplete   INTEGER NOT NULL CHECK (PercentComplete BETWEEN 0 AND 100),
    Status            TEXT    NOT NULL DEFAULT 'Not started'
                      CHECK (Status IN ('Not started','On track','At risk','Off track','Complete','Paused')),
    Note              TEXT,
    EnteredByID       INTEGER REFERENCES People(PersonID),
    CreatedAt         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IX_MIU_MI_Date ON MajorInitiativeUpdates(MajorInitiativeID, UpdateDate);

-- The latest diary entry per Major Initiative, for its card and the lists.
CREATE VIEW vw_LatestMajorInitiativeProgress AS
SELECT MajorInitiativeID, UpdateDate, PercentComplete, Status, Note
FROM (
    SELECT u.*, ROW_NUMBER() OVER (PARTITION BY MajorInitiativeID
                                    ORDER BY UpdateDate DESC, UpdateID DESC) AS rn
    FROM MajorInitiativeUpdates u
)
WHERE rn = 1;

-- ---------- Change log ----------

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

-- The change log (AuditLog) had no index at all; it grows with every write and
-- the /changes reader sorts by CreatedAt and drills in by entity.
CREATE INDEX IX_AuditLog_CreatedAt ON AuditLog(CreatedAt DESC);
CREATE INDEX IX_AuditLog_Entity   ON AuditLog(EntityType, EntityKey);

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


-- ---------- The Dean Priorities layer (register, 2026-10-07) -----------------
-- The register's "Dean KPI 26"/"Dean KPI 27" rows: the Dean's own top-level
-- priorities, distinct from the 29 team Major Initiatives. FiscalYear 26 is
-- complete; 27 is in flight. PercentComplete is 0-100 (the register's 0-1 value
-- scaled by 100). Presented in the app as "Dean Priorities", never "KPI".

CREATE TABLE DeanPriorities (
    DeanPriorityID  INTEGER PRIMARY KEY,
    FiscalYear      INTEGER NOT NULL CHECK (FiscalYear IN (26,27)),
    Code            TEXT    NOT NULL UNIQUE,   -- 'D26-1'..'D26-3', 'D27-1'..'D27-8'
    Title           TEXT    NOT NULL,
    Description     TEXT,
    PriorityID      INTEGER REFERENCES Priorities(PriorityID),
    PercentComplete INTEGER NOT NULL DEFAULT 0 CHECK (PercentComplete BETWEEN 0 AND 100),
    Note            TEXT
);

-- The X-matrix: which team Major Initiative contributes to which FY27 Dean item.
CREATE TABLE MajorInitiativeDeanLinks (
    MajorInitiativeID INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    DeanPriorityID    INTEGER NOT NULL REFERENCES DeanPriorities(DeanPriorityID),
    PRIMARY KEY (MajorInitiativeID, DeanPriorityID)
);

-- Co-owners. The register names one owner per row, EXCEPT Learning Futures,
-- whose six rows name two people in one cell ("Meltem Alemdar/Grace Flavin").
-- MajorInitiatives.OwnerID holds the accountable lead (the first-named); this
-- table holds the additional co-owners, so neither person is lost.
CREATE TABLE MajorInitiativeCoOwners (
    MajorInitiativeID INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    PersonID          INTEGER NOT NULL REFERENCES People(PersonID),
    PRIMARY KEY (MajorInitiativeID, PersonID)
);

CREATE VIEW vw_DeanPriorities AS
SELECT d.DeanPriorityID, d.FiscalYear, d.Code, d.Title, d.Description,
       d.PercentComplete, d.Note,
       p.PriorityID, p.Code AS PriorityCode, p.FullTitle AS PriorityTitle,
       p.Colour AS PriorityColour
FROM DeanPriorities d
LEFT JOIN Priorities p ON p.PriorityID = d.PriorityID;

CREATE VIEW vw_MajorInitiativeDeanLinks AS
SELECT kl.MajorInitiativeID, k.Code AS MajorInitiativeCode, k.MIId,
       k.Title AS MajorInitiativeTitle,
       d.DeanPriorityID, d.Code AS DeanCode, d.Title AS DeanTitle
FROM MajorInitiativeDeanLinks kl
JOIN MajorInitiatives k ON k.MajorInitiativeID = kl.MajorInitiativeID
JOIN DeanPriorities d   ON d.DeanPriorityID = kl.DeanPriorityID;


-- ---------- Data checks (merged model, 2026-10-07) ----------------------------
-- The prototype's vw_DataChecks read the dropped tables. These are the same
-- checks on the register's Major Initiatives: each should be tag-complete before
-- the dashboard is trusted.
--
-- "No progress update yet" was dropped 2026-10-07: the register ships no diary,
-- so an initiative with no update is the NORMAL state, not a data error - and the
-- intake importer refuses any import that leaves a check outstanding, so keeping
-- it would have made every import fail. Tag completeness is the real check.

CREATE VIEW vw_DataChecks AS
SELECT k.Code, 'No goal tagged' AS Issue
FROM MajorInitiatives k
WHERE k.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM MajorInitiativeGoals g WHERE g.MajorInitiativeID = k.MajorInitiativeID)
UNION ALL
SELECT k.Code, 'No priority tagged'
FROM MajorInitiatives k
WHERE k.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM MajorInitiativePriorities p WHERE p.MajorInitiativeID = k.MajorInitiativeID);
