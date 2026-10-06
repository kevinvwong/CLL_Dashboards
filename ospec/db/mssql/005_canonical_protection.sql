-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL canonical protection and misc
-- ============================================================================
-- Two reference rules that the first pass of the port missed. Both were found by
-- checking the live database for the object rather than by reading the port.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- P1. Canonical goals and strategic objectives resist hard deletion
-- ---------------------------------------------------------------------------
-- Reference: 04_Strategy_Portfolio_Schema_with_Constraints.sql item 11,
-- "Protect canonical Goals and Strategic Objectives from hard deletion".
-- Retirement is expressed by active_flag = 0, not by removing the row.
--
-- The FIRST PASS OF THIS PORT OMITTED THIS ENTIRELY. Caught by querying
-- sys.triggers for the goal and strategic_objective tables and finding none.

CREATE OR ALTER TRIGGER dbo.trg_block_canonical_goal_delete
ON dbo.goal
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted)
        THROW 50030, 'Canonical goals cannot be hard deleted; retire the goal by clearing active_flag instead.', 1;
END
GO

CREATE OR ALTER TRIGGER dbo.trg_block_objective_delete
ON dbo.strategic_objective
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM deleted)
        THROW 50031, 'Canonical strategic objectives cannot be hard deleted; retire the objective by clearing active_flag instead.', 1;
END
GO

-- ---------------------------------------------------------------------------
-- P2. A metric may have only one current version
-- ---------------------------------------------------------------------------
-- Reference: ADR-005 / the migration's
--   create unique index uq_metric_current_version
--     on metric_version(metric_id) where effective_end is null;
-- The first pass created uq_metric_version_number (version numbers unique) but
-- NOT this rule, so two open-ended versions of the same metric could coexist.
-- Caught by listing the indexes on metric_version and finding only two.

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'uq_metric_current_version')
    CREATE UNIQUE INDEX uq_metric_current_version
        ON dbo.metric_version (metric_id)
        WHERE effective_end IS NULL;
GO

PRINT 'Canonical protection and metric-version rules applied.';
GO
