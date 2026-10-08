-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, team-initiative layer additions
-- ============================================================================
-- Change `rev2-full-reconciliation` (task group 4 of the port). The Rev2
-- `initiative` row carries only identity/description/level/status; the register
-- carries richer columns the team-initiative screens read 29/29 (StrategyAlign,
-- Initiatives, ProposedTarget, TargetStatus, team, source area). This adds them
-- so the team layer runs on Rev2 with true parity, the same pattern as 008.
--
-- All are ADDITIONS to dbo.initiative (and two FK columns), not in the
-- reference; recorded in DEVIATIONS.md. Idempotent (IF COL_LENGTH IS NULL /
-- IF OBJECT_ID IS NULL), applied by apply.py.
-- ============================================================================

SET NOCOUNT ON;
GO

-- team: the register's team (initiative.team_id -> dbo.team). Rev2 already has
-- team from the package; this is the FK on initiative.
IF COL_LENGTH('dbo.initiative', 'team_id') IS NULL
ALTER TABLE dbo.initiative ADD team_id VARCHAR(40) NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_initiative_team')
ALTER TABLE dbo.initiative ADD CONSTRAINT fk_initiative_team
    FOREIGN KEY (team_id) REFERENCES dbo.team(team_id);
GO

-- source area: the register's SourceArea. FK to the 008 lookup.
IF COL_LENGTH('dbo.initiative', 'source_area_id') IS NULL
ALTER TABLE dbo.initiative ADD source_area_id INT NULL;
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_initiative_source_area')
ALTER TABLE dbo.initiative ADD CONSTRAINT fk_initiative_source_area
    FOREIGN KEY (source_area_id) REFERENCES dbo.source_area(source_area_id);
GO

-- strategy alignment (free text, 'Goals 1 + 3: ...'; the register column).
IF COL_LENGTH('dbo.initiative', 'strategy_align') IS NULL
ALTER TABLE dbo.initiative ADD strategy_align NVARCHAR(MAX) NULL;
GO

-- initiatives: the register's free-text 'Initiatives' column (related items).
IF COL_LENGTH('dbo.initiative', 'initiatives_text') IS NULL
ALTER TABLE dbo.initiative ADD initiatives_text NVARCHAR(MAX) NULL;
GO

-- proposed target: the register's free-text ProposedTarget column.
IF COL_LENGTH('dbo.initiative', 'proposed_target') IS NULL
ALTER TABLE dbo.initiative ADD proposed_target NVARCHAR(MAX) NULL;
GO

-- target status: the register's TargetStatus ('needs_review' | 'source').
-- Seed-only vocabulary, no CHECK: the values are register data, and a new
-- register year may add one, so constraining it here would block the next year
-- (the recurring-entity lesson). Kept loose deliberately.
IF COL_LENGTH('dbo.initiative', 'target_status') IS NULL
ALTER TABLE dbo.initiative ADD target_status VARCHAR(40) NULL;
GO

PRINT 'Team-layer columns added to initiative.';
GO
