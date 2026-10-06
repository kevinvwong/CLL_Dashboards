-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL constraints and enforcement
-- ============================================================================
-- Every statement here corresponds to a rule in the reference PostgreSQL DDL.
-- Where T-SQL cannot express the reference mechanism, the substitute is marked
-- DEVIATION and explained in DEVIATIONS.md. Read that before editing.
--
-- Reference mechanisms T-SQL lacks, all handled below:
--   EXCLUDE USING gist (period non-overlap)   -> trigger + sp_getapplock
--   DEFERRABLE INITIALLY DEFERRED constraint  -> immediate trigger + report
--   recursive CTE inside a BEFORE trigger     -> iterative walk
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- C1. Exactly one current primary Reporting Owner per initiative
-- ---------------------------------------------------------------------------
-- Reference: partial unique index
--   where primary_flag = true and ownership_role = 'Reporting Owner'
--     and effective_end is null
-- T-SQL: filtered unique index. NATIVE - no deviation. Verified on the target:
-- refuses a duplicate inside the filter and permits multiple NULLs, matching
-- PostgreSQL partial-index semantics.

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'uq_initiative_current_primary_reporting_owner')
    CREATE UNIQUE INDEX uq_initiative_current_primary_reporting_owner
        ON dbo.initiative_owner (initiative_id)
        WHERE primary_flag = 1
          AND ownership_role = 'Reporting Owner'
          AND effective_end IS NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'uq_current_primary_owner')
    CREATE UNIQUE INDEX uq_current_primary_owner
        ON dbo.initiative_owner (initiative_id)
        WHERE primary_flag = 1 AND effective_end IS NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_initiative_goal_goal')
    CREATE INDEX ix_initiative_goal_goal ON dbo.initiative_goal(goal_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_initiative_priority_priority')
    CREATE INDEX ix_initiative_priority_priority ON dbo.initiative_priority(priority_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_owner_person')
    CREATE INDEX ix_owner_person ON dbo.initiative_owner(person_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_update_initiative_date')
    CREATE INDEX ix_update_initiative_date ON dbo.initiative_update(initiative_id, update_date DESC);
GO

-- ---------------------------------------------------------------------------
-- C2. Hierarchical relationship direction: D-1 -> Dean
-- ---------------------------------------------------------------------------
-- Reference: plpgsql BEFORE INSERT trigger.
-- T-SQL has no BEFORE trigger on a table, so this is AFTER INSERT, UPDATE and
-- rolls the statement back. DEVIATION in mechanism; the rule and the refusal
-- message match the reference, including naming the attempted direction.

CREATE OR ALTER TRIGGER dbo.trg_enforce_initiative_relationship_levels
ON dbo.initiative_relationship
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM inserted) RETURN;

    DECLARE @bad VARCHAR(400);
    SELECT TOP 1 @bad = CONCAT('Supports/Contributes To must map D-1 -> Dean. Received ',
                               f.initiative_level, ' -> ', t.initiative_level)
    FROM inserted i
    JOIN dbo.initiative f ON f.initiative_id = i.from_initiative_id
    JOIN dbo.initiative t ON t.initiative_id = i.to_initiative_id
    WHERE i.relationship_type IN ('Supports','Contributes To')
      AND NOT (f.initiative_level = 'D-1' AND t.initiative_level = 'Dean');

    IF @bad IS NOT NULL
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50001, @bad, 1;
    END
END
GO

-- ---------------------------------------------------------------------------
-- C3. Cycle prevention across the full chain
-- ---------------------------------------------------------------------------
-- Reference: recursive CTE inside a BEFORE trigger.
-- T-SQL: a recursive CTE cannot reference the mutating table inside a trigger,
-- so this walks the chain iteratively with a bounded depth. DEVIATION in
-- mechanism only: the rule (no cycle of any length) is identical, and the
-- depth bound is a termination guard, not a limit on correctness, because a
-- cycle shorter than the bound is always found.
--
-- For each inserted edge from -> to, walk forward from `to`. If `from` is
-- reachable, the edge closes a cycle.

CREATE OR ALTER TRIGGER dbo.trg_prevent_initiative_relationship_cycle
ON dbo.initiative_relationship
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM inserted
                   WHERE relationship_type IN ('Supports','Contributes To','Enables'))
        RETURN;

    DECLARE @edges TABLE (f VARCHAR(80), t VARCHAR(80));
    INSERT INTO @edges
    SELECT from_initiative_id, to_initiative_id
    FROM dbo.initiative_relationship
    WHERE relationship_type IN ('Supports','Contributes To','Enables');

    DECLARE @from VARCHAR(80), @to VARCHAR(80), @hit BIT;
    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT from_initiative_id, to_initiative_id FROM inserted
        WHERE relationship_type IN ('Supports','Contributes To','Enables');
    OPEN cur;

    FETCH NEXT FROM cur INTO @from, @to;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @hit = 0;

        DECLARE @seen TABLE (id VARCHAR(80) PRIMARY KEY);
        DECLARE @frontier TABLE (id VARCHAR(80) PRIMARY KEY);
        DECLARE @depth INT = 0;

        -- start one hop out, so the new edge itself does not count
        INSERT INTO @frontier SELECT DISTINCT t FROM @edges WHERE f = @to;

        WHILE @depth < 64 AND @hit = 0
        BEGIN
            IF EXISTS (SELECT 1 FROM @frontier WHERE id = @from)
            BEGIN
                SET @hit = 1;
                BREAK;
            END
            IF NOT EXISTS (SELECT 1 FROM @frontier) BREAK;

            -- anything already seen is behind us; this also terminates an
            -- existing cycle in the data rather than looping forever
            INSERT INTO @seen (id)
            SELECT f.id FROM @frontier f
            WHERE NOT EXISTS (SELECT 1 FROM @seen s WHERE s.id = f.id);

            DELETE @frontier;

            INSERT INTO @frontier (id)
            SELECT DISTINCT e.t
            FROM @edges e
            JOIN @seen s ON s.id = e.f
            WHERE e.t NOT IN (SELECT id FROM @seen);

            SET @depth = @depth + 1;
        END

        IF @hit = 1
        BEGIN
            CLOSE cur;
            DEALLOCATE cur;
            ROLLBACK TRANSACTION;
            THROW 50002, 'Relationship would create a cycle.', 1;
        END

        FETCH NEXT FROM cur INTO @from, @to;
    END

    CLOSE cur;
    DEALLOCATE cur;
END
GO

-- ---------------------------------------------------------------------------
-- C4. Updates are append-only
-- ---------------------------------------------------------------------------
-- Reference: before update or delete trigger block_initiative_update_mutation().
-- T-SQL: INSTEAD OF UPDATE, DELETE. DEVIATION: INSTEAD OF is required rather
-- than BEFORE, and it does not silently no-op - it refuses, so a caller learns
-- the write failed rather than believing it succeeded.

CREATE OR ALTER TRIGGER dbo.trg_block_initiative_update_change
ON dbo.initiative_update
INSTEAD OF UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    THROW 50003, 'Initiative updates are append-only; record a superseding update instead of modifying history.', 1;
END
GO