-- =====================================================================
-- SAMPLE DATA ONLY — fake initiatives for testing the dashboard.
-- Replace with live data from the intake spreadsheet.
-- Rows reference each other by Code/name so the file is easy to edit.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Goals (confirm FullName wording from the Strategy 2035 PDF)
INSERT INTO Goals (GoalNumber, ShortName, FullName) VALUES
 (1, 'Academic',       'Catalyze a learning society and build a home for transformative learning'),
 (2, 'Extension',      NULL),
 (3, 'Research',       NULL),
 (4, 'Learner impact', NULL),
 (5, 'Operational',    NULL);

-- 2027 annual priorities
INSERT INTO Priorities (PriorityName, PlanYear) VALUES
 ('Culture',2027),('Scale',2027),('Identity',2027),
 ('Innovation',2027),('Pathways',2027),('Data',2027);

-- People
INSERT INTO People (PersonID, Name, Title, ReportsToID) VALUES
 (1, 'Bill',      'Dean', NULL),
 (2, 'Elizabeth', NULL, 1),
 (3, 'Tim',       NULL, 1),
 (4, 'Mario',     NULL, 1);

-- Dashboard team admins (no initiatives; can edit everything)
INSERT INTO People (PersonID, Name, Title, ReportsToID, IsAdmin) VALUES
 (5, 'Kevin', 'Associate Director, Strategic Operations', NULL, 1);

-- Initiatives (names are placeholders)
INSERT INTO Initiatives (Code, InitiativeName, Level, OwnerID) VALUES
 ('D-A','Dean A (sample): Transparent ROI reporting','Dean',1),
 ('D-B','Dean B (sample): Scale online credentials','Dean',1),
 ('D-C','Dean C (sample): Consulting arm launch','Dean',1),
 ('D-D','Dean D (sample): Research partnerships','Dean',1),
 ('D-E','Dean E (sample): Learner pathways redesign','Dean',1),
 ('D-F','Dean F (sample): Culture and identity','Dean',1),
 ('ELIZ-1','Financial and operational dashboards (sample)','D-1',2),
 ('ELIZ-2','Ops LLM agent (sample)','D-1',2),
 ('ELIZ-3','Workflow centralization (sample)','D-1',2),
 ('ELIZ-4','Brand and identity refresh (sample)','D-1',2),
 ('ELIZ-5','Consulting service catalog (sample)','D-1',2),
 ('TIM-1','Tim initiative 1 (sample)','D-1',3),
 ('TIM-2','Tim initiative 2 (sample)','D-1',3),
 ('TIM-3','Tim initiative 3 (sample)','D-1',3),
 ('TIM-4','Tim initiative 4 (sample)','D-1',3),
 ('TIM-5','Tim initiative 5 (sample)','D-1',3),
 ('TIM-6','Tim initiative 6 (sample)','D-1',3),
 ('MAR-1','Mario initiative 1 (sample)','D-1',4),
 ('MAR-2','Mario initiative 2 (sample)','D-1',4),
 ('MAR-3','Mario initiative 3 (sample)','D-1',4),
 ('MAR-4','Mario initiative 4 (sample)','D-1',4),
 ('MAR-5','Mario initiative 5 (sample)','D-1',4);

-- Goal tags: (Code, GoalShortName, IsPrimary)
WITH t(c,g,p) AS (VALUES
 ('D-A','Research',1),('D-A','Operational',0),
 ('D-B','Academic',1),('D-B','Extension',0),
 ('D-C','Operational',1),('D-C','Research',0),
 ('D-D','Research',1),
 ('D-E','Learner impact',1),('D-E','Academic',0),
 ('D-F','Operational',1),('D-F','Academic',0),
 ('ELIZ-1','Operational',1),('ELIZ-1','Research',0),
 ('ELIZ-2','Operational',1),
 ('ELIZ-3','Operational',1),
 ('ELIZ-4','Operational',1),('ELIZ-4','Academic',0),
 ('ELIZ-5','Operational',1),
 ('TIM-1','Academic',1),('TIM-2','Academic',1),('TIM-3','Extension',1),
 ('TIM-4','Learner impact',1),('TIM-5','Academic',1),('TIM-6','Extension',1),
 ('MAR-1','Academic',1),('MAR-2','Learner impact',1),('MAR-3','Academic',1),
 ('MAR-4','Research',1),('MAR-5','Academic',1)
)
INSERT INTO InitiativeGoals (InitiativeID, GoalID, IsPrimary)
SELECT i.InitiativeID, g.GoalID, t.p
FROM t
JOIN Initiatives i ON i.Code = t.c
JOIN Goals g       ON g.ShortName = t.g;

-- Priority tags: (Code, PriorityName, IsPrimary)
WITH t(c,pr,p) AS (VALUES
 ('D-A','Data',1),('D-B','Scale',1),('D-B','Pathways',0),
 ('D-C','Innovation',1),('D-D','Innovation',1),('D-D','Data',0),
 ('D-E','Pathways',1),('D-F','Culture',1),('D-F','Identity',0),
 ('ELIZ-1','Data',1),('ELIZ-2','Innovation',1),('ELIZ-3','Scale',1),
 ('ELIZ-4','Identity',1),('ELIZ-5','Innovation',1),
 ('TIM-1','Scale',1),('TIM-2','Pathways',1),('TIM-3','Scale',1),
 ('TIM-4','Pathways',1),('TIM-5','Innovation',1),('TIM-6','Identity',1),
 ('MAR-1','Scale',1),('MAR-2','Pathways',1),('MAR-3','Innovation',1),
 ('MAR-4','Data',1),('MAR-5','Culture',1)
)
INSERT INTO InitiativePriorities (InitiativeID, PriorityID, IsPrimary)
SELECT i.InitiativeID, pr.PriorityID, t.p
FROM t
JOIN Initiatives i ON i.Code = t.c
JOIN Priorities pr ON pr.PriorityName = t.pr AND pr.PlanYear = 2027;

-- Links: D-1 initiative feeds Dean initiative(s)
WITH t(c,d) AS (VALUES
 ('ELIZ-1','D-A'),('ELIZ-1','D-C'),('ELIZ-2','D-C'),('ELIZ-3','D-F'),
 ('ELIZ-4','D-F'),('ELIZ-5','D-C'),
 ('TIM-1','D-B'),('TIM-2','D-E'),('TIM-3','D-B'),('TIM-4','D-E'),
 ('TIM-5','D-B'),('TIM-6','D-B'),
 ('MAR-1','D-B'),('MAR-2','D-E'),('MAR-3','D-B'),('MAR-4','D-D'),('MAR-5','D-F')
)
INSERT INTO InitiativeLinks (InitiativeID, DeanInitiativeID)
SELECT c.InitiativeID, d.InitiativeID
FROM t
JOIN Initiatives c ON c.Code = t.c
JOIN Initiatives d ON d.Code = t.d;

-- Progress diary (two entries on a few to show history)
WITH t(c,dt,pct,st,note,by) AS (VALUES
 ('D-A','2026-09-21',20,'On track','Scoping ROI measures with finance.','Bill'),
 ('D-A','2026-10-05',30,'On track','Dashboard requirements agreed.','Bill'),
 ('D-B','2026-10-05',45,'On track','Two new credential tracks approved.','Bill'),
 ('D-C','2026-10-05',15,'At risk','Waiting on service catalog.','Bill'),
 ('D-D','2026-10-05',10,'On track','Initial partner meetings held.','Bill'),
 ('D-E','2026-10-05',25,'On track','Pathway map drafted.','Bill'),
 ('D-F','2026-10-05',35,'On track','Retreat follow-ups underway.','Bill'),
 ('ELIZ-1','2026-09-28',2,'On track','Ideation session held.','Elizabeth'),
 ('ELIZ-1','2026-10-05',10,'On track','Data model drafted; first dashboard due Oct 16.','Elizabeth'),
 ('ELIZ-2','2026-10-05',5,'Not started','Use cases being collected.','Elizabeth'),
 ('ELIZ-3','2026-10-05',20,'On track','Inventory of current workflows started.','Elizabeth'),
 ('ELIZ-4','2026-10-05',30,'On track','Draft brand guide in review.','Elizabeth'),
 ('ELIZ-5','2026-10-05',10,'At risk','Scope depends on reorg.','Elizabeth'),
 ('TIM-1','2026-10-05',40,'On track','Sample update.','Tim'),
 ('TIM-2','2026-10-05',25,'On track','Sample update.','Tim'),
 ('TIM-3','2026-10-05',60,'On track','Sample update.','Tim'),
 ('TIM-4','2026-10-05',15,'Off track','Sample update.','Tim'),
 ('TIM-5','2026-10-05',50,'On track','Sample update.','Tim'),
 ('TIM-6','2026-10-05',5,'Not started','Sample update.','Tim'),
 ('MAR-1','2026-10-05',35,'On track','Sample update.','Mario'),
 ('MAR-2','2026-10-05',20,'At risk','Sample update.','Mario'),
 ('MAR-3','2026-10-05',55,'On track','Sample update.','Mario'),
 ('MAR-4','2026-10-05',10,'On track','Sample update.','Mario'),
 ('MAR-5','2026-10-05',30,'On track','Sample update.','Mario')
)
INSERT INTO ProgressUpdates (InitiativeID, UpdateDate, PercentComplete, Status, Note, EnteredByID)
SELECT i.InitiativeID, t.dt, t.pct, t.st, t.note, p.PersonID
FROM t
JOIN Initiatives i ON i.Code = t.c
JOIN People p      ON p.Name = t.by;
