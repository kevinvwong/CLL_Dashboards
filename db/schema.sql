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
    PlanYear     INTEGER NOT NULL,   -- the plan year this priority belongs to
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
    -- The reported outcome state for this priority (workbook A-05/A-06). NULL
    -- until an owner states it; the app renders "not yet reported", never a
    -- guessed value. Its own vocabulary, distinct from initiative and milestone
    -- status (ADR-0002): 'On track','At risk','Behind','Not started'.
    Status       TEXT,
    LastUpdated  TEXT,      -- ISO date the state was last confirmed
    -- A PRIORITY IS IDENTIFIED BY (YEAR, CODE), not by code alone: the same six
    -- recur every plan year, so 'P01' names a priority and the year names which
    -- plan. Keying on code alone (the earlier UNIQUE(Code)) made a 2028 'P01'
    -- unstorable - the multi-year fix (2026-10-08).
    UNIQUE (PlanYear, Code),
    UNIQUE (PriorityName, PlanYear)
);

-- ---------- Milestones (enhancement work, 2026-10-07) -------------------------
-- A Milestone is a concrete, checkable event that evidences a PRIORITY. It hangs
-- off Priorities, not Team Initiatives: the Outcomes view is one card per
-- priority and its "milestones reached / planned" figure is defined per outcome,
-- so the edge points at the priority (ADR-0001). The fields are the workbook's
-- own requirement rows A-07..A-17 (Oct16_Wireframe_Data_Lists.xlsx, "Option A
-- Data"), and every one is populated by the intake, never by hand.
CREATE TABLE Milestones (
    MilestoneID  INTEGER PRIMARY KEY,
    -- Keyed to the PRIORITY ROW, not its code: a milestone belongs to one
    -- year's priority, and the code 'P01' recurs each year (multi-year fix,
    -- 2026-10-08).
    PriorityID   INTEGER NOT NULL REFERENCES Priorities(PriorityID),
    Name         TEXT    NOT NULL,      -- a checkable event, not an activity
    -- A milestone's own status vocabulary (ADR-0002): an event is Met or Missed;
    -- it is never "On track" and never "Complete".
    Status       TEXT    NOT NULL DEFAULT 'Not started'
                 CHECK (Status IN ('Met','In progress','Not started','Missed')),
    PlannedDate  TEXT,                  -- ISO date the milestone is due
    DateMet      TEXT,                  -- ISO date achieved, when Met
    OwnerLabel   TEXT,                  -- who is responsible, as named
    EvidenceURL  TEXT,                  -- approving doc / minutes / release note
    SortOrder    INTEGER NOT NULL DEFAULT 0,
    IsActive     INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1)),
    UNIQUE (PriorityID, Name)
);

-- Milestones reached / planned per priority, for the Outcomes cards and the
-- rings. LEFT JOIN so a priority with no milestones yet still appears, reading
-- 0 of 0 rather than vanishing. Keyed by PriorityID, so each year's priorities
-- report their own milestones.
CREATE VIEW vw_PriorityMilestoneProgress AS
SELECT p.PriorityID AS PriorityID,
       p.Code AS PriorityCode,
       p.PlanYear AS PlanYear,
       p.FullTitle AS PriorityTitle,
       COUNT(m.MilestoneID) AS Planned,
       SUM(CASE WHEN m.Status = 'Met' THEN 1 ELSE 0 END) AS Reached
FROM Priorities p
LEFT JOIN Milestones m ON m.PriorityID = p.PriorityID AND m.IsActive = 1
GROUP BY p.PriorityID, p.Code, p.PlanYear, p.FullTitle;

-- ---------- Dataset provenance -----------------------------------------------
-- Whether the data is a seeded MOCK or imported-and-confirmed. The UI reads this
-- to label the Outcomes page. Mock data is allowed only as a seed, and this row
-- is what keeps a mock from being presented as real: the seed writes 'mock', the
-- importer writes 'confirmed', and data_status() reads provenance, never content
-- (the enhancement plan, D5).
CREATE TABLE AppMeta (
    Key   TEXT PRIMARY KEY,
    Value TEXT
);

-- ---------- Organizational layer (blueprint-redesign scope correction) -------
-- The Dean's prototype carries a layer beneath the six priorities: four
-- organizational TEAMS, and 29 Team Initiatives grouped by FIVE source areas. Our
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

-- The 29 Team Initiatives. `TeamID` is the team accountable; `SourceAreaID` is the
-- workbook area they came from; the two are different axes.
CREATE TABLE TeamInitiatives (
    TeamInitiativeID          INTEGER PRIMARY KEY,
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

-- Which priorities a Team Initiative feeds (its `priorities` array).
-- The register states a PRIMARY and a SECONDARY priority per row, so IsPrimary
-- distinguishes them. One primary per initiative is enforced below.
CREATE TABLE TeamInitiativePriorities (
    TeamInitiativeID      INTEGER NOT NULL REFERENCES TeamInitiatives(TeamInitiativeID),
    PriorityID INTEGER NOT NULL REFERENCES Priorities(PriorityID),
    IsPrimary  INTEGER NOT NULL DEFAULT 0 CHECK (IsPrimary IN (0,1)),
    PRIMARY KEY (TeamInitiativeID, PriorityID)
);
CREATE UNIQUE INDEX UX_MIP_OnePrimary
    ON TeamInitiativePriorities(TeamInitiativeID) WHERE IsPrimary = 1;

-- Which Strategy 2035 goals a Team Initiative aligns to, parsed from the
-- canon workbook's `Strategy Alignment` column. This is the MI -> Goal edge that
-- register states and the schema did not hold.
CREATE TABLE TeamInitiativeGoals (
    TeamInitiativeID  INTEGER NOT NULL REFERENCES TeamInitiatives(TeamInitiativeID),
    GoalID INTEGER NOT NULL REFERENCES Goals(GoalID),
    PRIMARY KEY (TeamInitiativeID, GoalID)
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
    -- The Clerk user id (e.g. 'user_...') that maps a Clerk identity to this
    -- person (Clerk integration, 2026-10-08). People carry no email, so this is
    -- the explicit link; an admin sets it. NULL means Clerk cannot yet map this
    -- person, and they are not reachable through the Clerk provider (ADR-0004).
    ClerkUserID  TEXT UNIQUE,
    IsActive     INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1))
);

-- ---------- The merged initiative model (2026-10-07) -------------------------
--
-- The database used to hold TWO parallel initiative models: the prototype's
-- `Initiatives` (22 sample rows, with the progress diary, tags, links and write
-- paths) and the register's `TeamInitiatives` (the 29 canon rows). The home page
-- showed both counts at once, which read as a contradiction. The register is
-- canon, so the two are MERGED here onto the register's model: the diary and the
-- write paths move onto `TeamInitiatives`, and the five prototype tables
-- (`Initiatives`, `InitiativeGoals`, `InitiativePriorities`, `InitiativeLinks`,
-- `ProgressUpdates`) are dropped.
--
-- The 24 sample diary rows were NOT migrated: every one was about a sample
-- initiative and none named a real Team Initiative.

-- The progress diary, on the 29 Team Initiatives. Append-only, attributed,
-- exactly as the prototype's ProgressUpdates was, but keyed to the register row.
CREATE TABLE TeamInitiativeUpdates (
    UpdateID          INTEGER PRIMARY KEY,
    TeamInitiativeID INTEGER NOT NULL REFERENCES TeamInitiatives(TeamInitiativeID),
    UpdateDate        TEXT    NOT NULL DEFAULT (date('now')),
    PercentComplete   INTEGER NOT NULL CHECK (PercentComplete BETWEEN 0 AND 100),
    Status            TEXT    NOT NULL DEFAULT 'Not started'
                      CHECK (Status IN ('Not started','On track','At risk','Off track','Complete','Paused')),
    Note              TEXT,
    EnteredByID       INTEGER REFERENCES People(PersonID),
    CreatedAt         TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IX_MIU_MI_Date ON TeamInitiativeUpdates(TeamInitiativeID, UpdateDate);

-- The latest diary entry per Team Initiative, for its card and the lists.
CREATE VIEW vw_LatestTeamInitiativeProgress AS
SELECT TeamInitiativeID, UpdateDate, PercentComplete, Status, Note
FROM (
    SELECT u.*, ROW_NUMBER() OVER (PARTITION BY TeamInitiativeID
                                    ORDER BY UpdateDate DESC, UpdateID DESC) AS rn
    FROM TeamInitiativeUpdates u
)
WHERE rn = 1;

-- ---------- Local roles (auth hardening, 2026-10-07) -------------------------
-- Authorization is app-local, not from an identity provider's groups (ADR-0005).
-- A person is WHO they are (the provider answers that); a role is WHAT they may
-- do here. The provider may change (local credential now, Clerk/Entra later)
-- without touching these rows.
CREATE TABLE Roles (
    RoleID      INTEGER PRIMARY KEY,
    Name        TEXT NOT NULL UNIQUE,   -- 'admin','dean','team_lead','viewer'
    Description TEXT
);

CREATE TABLE PeopleRoles (
    PersonID INTEGER NOT NULL REFERENCES People(PersonID),
    RoleID   INTEGER NOT NULL REFERENCES Roles(RoleID),
    PRIMARY KEY (PersonID, RoleID)
);

-- ---------- Change log ----------

-- Who changed what (edits to initiatives, tags, links, descriptions)
CREATE TABLE AuditLog (
    AuditID       INTEGER PRIMARY KEY,
    CreatedAt     TEXT    NOT NULL DEFAULT (datetime('now')),
    PersonID      INTEGER REFERENCES People(PersonID),
    Action        TEXT    NOT NULL,     -- e.g. 'update_initiative', 'add_goal_tag', 'remove_link'
    EntityType    TEXT    NOT NULL,     -- 'Initiative','Goal','Priority','Link','Tag'
    EntityKey     TEXT    NOT NULL,     -- Code or ID
    Details       TEXT,                 -- JSON of before/after
    -- Change-management fields (2026-10-07): why a change was made, where the
    -- request came from, and an id to correlate the changes of one request. All
    -- optional, so every existing writer keeps working.
    Reason        TEXT,                 -- why this change was made
    Source        TEXT,                 -- the request's origin (e.g. a ticket id)
    CorrelationID TEXT                  -- groups the changes of one request
);

-- The change log (AuditLog) had no index at all; it grows with every write and
-- the /changes reader sorts by CreatedAt and drills in by entity.
CREATE INDEX IX_AuditLog_CreatedAt ON AuditLog(CreatedAt DESC);
CREATE INDEX IX_AuditLog_Entity   ON AuditLog(EntityType, EntityKey);

-- ---------- Read models for the organizational layer -------------------------
-- One view per screen, matching the existing convention. These expose the
-- 29 Team Initiatives with their team, source area, and what they feed.

CREATE VIEW vw_TeamInitiatives AS
SELECT k.TeamInitiativeID, k.Code, k.Title, k.StrategyAlign, k.Initiatives,
       k.ProposedTarget, k.TargetStatus,
       k.Status, k.Note,
       t.TeamID, t.Name AS Team,
       sa.SourceAreaID, sa.Name AS SourceArea
FROM TeamInitiatives k
LEFT JOIN Teams t       ON t.TeamID = k.TeamID
LEFT JOIN SourceAreas sa ON sa.SourceAreaID = k.SourceAreaID;

-- Which priorities each Team Initiative feeds, one row per link.
CREATE VIEW vw_TeamInitiativePriorities AS
SELECT kp.TeamInitiativeID, k.Code AS TeamInitiativeCode, k.Title AS TeamInitiativeTitle,
       p.PriorityID, p.PriorityName, p.Code AS PriorityCode,
       p.FullTitle AS PriorityTitle, p.Colour AS PriorityColour
FROM TeamInitiativePriorities kp
JOIN TeamInitiatives k       ON k.TeamInitiativeID = kp.TeamInitiativeID
JOIN Priorities p     ON p.PriorityID = kp.PriorityID;

-- Team rollup: how many Team Initiatives each team carries, and how many review.
CREATE VIEW vw_TeamSummary AS
SELECT t.TeamID, t.Name AS Team, t.Description,
       COUNT(k.TeamInitiativeID) AS TeamInitiativeCount,
       SUM(CASE WHEN k.TargetStatus = 'needs_review' THEN 1 ELSE 0 END) AS NeedsReview
FROM Teams t
LEFT JOIN TeamInitiatives k ON k.TeamID = t.TeamID
GROUP BY t.TeamID, t.Name, t.Description;


-- The MI -> Goal edge, one row per link, for the goal page and MI page.
CREATE VIEW vw_TeamInitiativeGoals AS
SELECT kg.TeamInitiativeID, k.Code AS TeamInitiativeCode, k.MIId, k.Title AS TeamInitiativeTitle,
       g.GoalID, g.GoalNumber, g.ShortName AS GoalShort
FROM TeamInitiativeGoals kg
JOIN TeamInitiatives k ON k.TeamInitiativeID = kg.TeamInitiativeID
JOIN Goals g    ON g.GoalID = kg.GoalID;


-- ---------- The Dean Initiatives layer (register, 2026-10-07) -----------------
-- The register's "Dean KPI 26"/"Dean KPI 27" rows: the Dean's own top-level
-- priorities, distinct from the 29 team Team Initiatives. FiscalYear 26 is
-- complete; 27 is in flight. PercentComplete is 0-100 (the register's 0-1 value
-- scaled by 100). Presented in the app as "Dean Initiatives", never "KPI".

CREATE TABLE DeanInitiatives (
    DeanInitiativeID  INTEGER PRIMARY KEY,
    -- A 2-digit fiscal year. FY26/FY27 are the seeded years; the range is open
    -- so later years are storable without another migration (multi-year fix,
    -- 2026-10-08).
    FiscalYear      INTEGER NOT NULL CHECK (FiscalYear BETWEEN 26 AND 99),
    Code            TEXT    NOT NULL UNIQUE,   -- 'D26-1'..'D26-3', 'D27-1'..'D27-8'
    Title           TEXT    NOT NULL,
    Description     TEXT,
    PriorityID      INTEGER REFERENCES Priorities(PriorityID),
    PercentComplete INTEGER NOT NULL DEFAULT 0 CHECK (PercentComplete BETWEEN 0 AND 100),
    Note            TEXT
);

-- The X-matrix: which team Team Initiative contributes to which FY27 Dean item.
CREATE TABLE TeamInitiativeDeanLinks (
    TeamInitiativeID INTEGER NOT NULL REFERENCES TeamInitiatives(TeamInitiativeID),
    DeanInitiativeID    INTEGER NOT NULL REFERENCES DeanInitiatives(DeanInitiativeID),
    PRIMARY KEY (TeamInitiativeID, DeanInitiativeID)
);

-- Co-owners. The register names one owner per row, EXCEPT Learning Futures,
-- whose six rows name two people in one cell ("Meltem Alemdar/Grace Flavin").
-- TeamInitiatives.OwnerID holds the accountable lead (the first-named); this
-- table holds the additional co-owners, so neither person is lost.
CREATE TABLE TeamInitiativeCoOwners (
    TeamInitiativeID INTEGER NOT NULL REFERENCES TeamInitiatives(TeamInitiativeID),
    PersonID          INTEGER NOT NULL REFERENCES People(PersonID),
    PRIMARY KEY (TeamInitiativeID, PersonID)
);

CREATE VIEW vw_DeanInitiatives AS
SELECT d.DeanInitiativeID, d.FiscalYear, d.Code, d.Title, d.Description,
       d.PercentComplete, d.Note,
       p.PriorityID, p.Code AS PriorityCode, p.FullTitle AS PriorityTitle,
       p.Colour AS PriorityColour
FROM DeanInitiatives d
LEFT JOIN Priorities p ON p.PriorityID = d.PriorityID;

CREATE VIEW vw_TeamInitiativeDeanLinks AS
SELECT kl.TeamInitiativeID, k.Code AS TeamInitiativeCode, k.MIId,
       k.Title AS TeamInitiativeTitle,
       d.DeanInitiativeID, d.Code AS DeanCode, d.Title AS DeanTitle
FROM TeamInitiativeDeanLinks kl
JOIN TeamInitiatives k ON k.TeamInitiativeID = kl.TeamInitiativeID
JOIN DeanInitiatives d   ON d.DeanInitiativeID = kl.DeanInitiativeID;


-- ---------- Data checks (merged model, 2026-10-07) ----------------------------
-- The prototype's vw_DataChecks read the dropped tables. These are the same
-- checks on the register's Team Initiatives: each should be tag-complete before
-- the dashboard is trusted.
--
-- "No progress update yet" was dropped 2026-10-07: the register ships no diary,
-- so an initiative with no update is the NORMAL state, not a data error - and the
-- intake importer refuses any import that leaves a check outstanding, so keeping
-- it would have made every import fail. Tag completeness is the real check.

CREATE VIEW vw_DataChecks AS
SELECT COALESCE(k.MIId, k.Code) AS Code, 'No goal tagged' AS Issue
FROM TeamInitiatives k
WHERE k.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM TeamInitiativeGoals g WHERE g.TeamInitiativeID = k.TeamInitiativeID)
UNION ALL
SELECT COALESCE(k.MIId, k.Code), 'No priority tagged'
FROM TeamInitiatives k
WHERE k.IsActive = 1
  AND NOT EXISTS (SELECT 1 FROM TeamInitiativePriorities p WHERE p.TeamInitiativeID = k.TeamInitiativeID);
