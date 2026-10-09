-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, milestone ownership correction
-- ============================================================================
-- Milestones become TEAM-INITIATIVE scoped, matching the app's SQLite schema
-- (2026-10-09). They were keyed to annual_priority here, which put them one
-- level too high in the cascade: column F of the source register ("FY2027
-- Target / Achievement Marks") lives on the register ROW, i.e. on the Team
-- Initiative, not on the annual priority.
--
-- This is the same correction the sqlite side has already made; this file is
-- the other half of it. Without it, the port's milestone reads disagree between
-- stores while everything else agrees, which is precisely the drift the parity
-- tests exist to catch - so build_rev2_seed.py refuses to seed milestones until
-- this has been applied.
--
-- WHAT HAPPENS TO THE EXISTING 18 ROWS
-- ------------------------------------
-- They are DELETED, not re-parented. They are the mock/Wireframe set
-- (dataset_provenance = 'mock'), and re-parenting them is not defensible: a
-- priority is fed by many initiatives, so "which initiative owns this mock
-- milestone" has no answer the data supplies. The real 84 clauses are generated
-- from register column F by db/build_milestone_clauses_seed.py and seeded by
-- db/build_rev2_seed.py; re-run that seed after this migration.
--
-- Idempotent (COL_LENGTH / sys.indexes / sys.foreign_keys guarded).
-- ============================================================================

SET NOCOUNT ON;
GO

-- --- 1. the new columns ----------------------------------------------------
-- initiative_id is added NULLABLE first: a NOT NULL ADD cannot succeed while
-- rows still exist, and it is dropped again below once they are gone. Weight,
-- basis, source and the rewrite flag mirror the sqlite schema so the two stores
-- carry the same rollup inputs.

IF COL_LENGTH('dbo.milestone', 'initiative_id') IS NULL
ALTER TABLE dbo.milestone ADD initiative_id VARCHAR(80) NULL;
GO

IF COL_LENGTH('dbo.milestone', 'weight') IS NULL
ALTER TABLE dbo.milestone ADD weight DECIMAL(6,5) NOT NULL
    CONSTRAINT df_milestone_weight DEFAULT 1.0;
GO

IF COL_LENGTH('dbo.milestone', 'weight_basis') IS NULL
ALTER TABLE dbo.milestone ADD weight_basis VARCHAR(40) NOT NULL
    CONSTRAINT df_milestone_basis DEFAULT 'support-soft';
GO

IF COL_LENGTH('dbo.milestone', 'weight_source') IS NULL
ALTER TABLE dbo.milestone ADD weight_source VARCHAR(20) NOT NULL
    CONSTRAINT df_milestone_source DEFAULT 'inferred';
GO

IF COL_LENGTH('dbo.milestone', 'needs_rewrite') IS NULL
ALTER TABLE dbo.milestone ADD needs_rewrite BIT NOT NULL
    CONSTRAINT df_milestone_rewrite DEFAULT 0;
GO

-- --- 2. the CHECKs on the new columns -------------------------------------
-- Same vocabulary the app enforces (ADR-0002, and the weight contract the
-- rollup depends on). Guarded by name so a re-run does not fail on a duplicate.
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints
               WHERE name = 'ck_milestone_weight_positive')
ALTER TABLE dbo.milestone ADD CONSTRAINT ck_milestone_weight_positive
    CHECK (weight > 0);
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints
               WHERE name = 'ck_milestone_basis')
ALTER TABLE dbo.milestone ADD CONSTRAINT ck_milestone_basis
    CHECK (weight_basis IN ('headline-quant','headline-gate','headline-soft',
                            'support-quant','support-gate','support-soft'));
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints
               WHERE name = 'ck_milestone_source')
ALTER TABLE dbo.milestone ADD CONSTRAINT ck_milestone_source
    CHECK (weight_source IN ('inferred','confirmed'));
GO

-- --- 3. drop the mock rows -------------------------------------------------
-- Only the priority-scoped ones. Anything already carrying an initiative_id was
-- written by a previous run of this migration, or by the corrected seed, and is
-- left alone.
DELETE FROM dbo.milestone WHERE initiative_id IS NULL;
GO

-- --- 4. re-point the key at the initiative ---------------------------------
-- The old UNIQUE (priority_id, name) cannot survive: it enforces the ownership
-- this migration removes. Dropped by name so the file is re-runnable.
IF EXISTS (SELECT 1 FROM sys.key_constraints
           WHERE name = 'uq_milestone_per_priority'
             AND type = 'UQ'
             AND parent_object_id = OBJECT_ID('dbo.milestone'))
ALTER TABLE dbo.milestone DROP CONSTRAINT uq_milestone_per_priority;
GO

-- initiative_id becomes mandatory. This is safe now: step 3 removed every row
-- that lacked one.
IF EXISTS (SELECT 1 FROM sys.columns
           WHERE object_id = OBJECT_ID('dbo.milestone')
             AND name = 'initiative_id' AND is_nullable = 1)
ALTER TABLE dbo.milestone ALTER COLUMN initiative_id VARCHAR(80) NOT NULL;
GO

-- One name per initiative, per initiative. Not per priority: an initiative
-- feeds two priorities, and a name may therefore appear against both.
IF NOT EXISTS (SELECT 1 FROM sys.key_constraints
               WHERE name = 'uq_milestone_per_initiative'
                 AND parent_object_id = OBJECT_ID('dbo.milestone'))
ALTER TABLE dbo.milestone ADD CONSTRAINT uq_milestone_per_initiative
    UNIQUE (initiative_id, name);
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys
               WHERE name = 'fk_milestone_initiative')
ALTER TABLE dbo.milestone ADD CONSTRAINT fk_milestone_initiative
    FOREIGN KEY (initiative_id) REFERENCES dbo.initiative (initiative_id);
GO

-- --- 5. drop the priority column ------------------------------------------
-- Only after the FK to initiative is in place, so the table is never left with
-- neither parent. The old FK and its default go first; SQL Server refuses to
-- drop a column that still participates in a foreign key.
IF EXISTS (SELECT 1 FROM sys.foreign_keys
           WHERE name = 'fk_milestone_priority'
             AND parent_object_id = OBJECT_ID('dbo.milestone'))
ALTER TABLE dbo.milestone DROP CONSTRAINT fk_milestone_priority;
GO

IF EXISTS (SELECT 1 FROM sys.default_constraints dc
           JOIN sys.columns c
             ON c.object_id = dc.parent_object_id
            AND c.column_id = dc.parent_column_id
           WHERE dc.name = 'df_milestone_priority'
             AND c.object_id = OBJECT_ID('dbo.milestone'))
ALTER TABLE dbo.milestone DROP CONSTRAINT df_milestone_priority;
GO

IF COL_LENGTH('dbo.milestone', 'priority_id') IS NOT NULL
ALTER TABLE dbo.milestone DROP COLUMN priority_id;
GO

PRINT 'Milestone re-scoped to the initiative.';
PRINT 'Re-run db/build_rev2_seed.py to seed the 84 real clauses.';
GO
