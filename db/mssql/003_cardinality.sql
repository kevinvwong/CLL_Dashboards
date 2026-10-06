-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL cardinality and non-overlap
-- ============================================================================
-- The package enforces two minimum-cardinality rules with DEFERRABLE INITIALLY
-- DEFERRED constraint triggers, so that an initiative may be inserted and
-- mapped within one transaction and the rule is checked at COMMIT.
--
-- T-SQL has no deferred constraint. DEVIATION (see DEVIATIONS.md): the rule is
-- enforced immediately on every write path, plus a standing integrity report as
-- the backstop for anything that writes around the application. The practical
-- difference is that a transaction may not temporarily hold a violating state
-- and fix it before committing; the workaround is to insert the mapping before
-- activating the initiative, which is the same order the reference's example
-- transaction uses.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- K1. An active initiative must have at least one current goal mapping
-- ---------------------------------------------------------------------------
-- Fires when an initiative becomes Active, and when a goal mapping is removed
-- while the initiative stays Active. Immediate rather than deferred.

CREATE OR ALTER TRIGGER dbo.trg_active_initiative_requires_goal
ON dbo.initiative
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM inserted WHERE status = 'Active' AND active_flag = 1)
        RETURN;

    DECLARE @bad VARCHAR(80);
    SELECT TOP 1 @bad = i.initiative_id
    FROM inserted i
    WHERE i.status = 'Active' AND i.active_flag = 1
      AND NOT EXISTS (
            SELECT 1 FROM dbo.initiative_goal g
            WHERE g.initiative_id = i.initiative_id
              AND (g.effective_end IS NULL OR g.effective_end >= CAST(GETDATE() AS DATE)));

    IF @bad IS NOT NULL
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50010, 'Active initiative must map to at least one current goal.', 1;
    END
END
GO

CREATE OR ALTER TRIGGER dbo.trg_goal_mapping_removal_requires_goal
ON dbo.initiative_goal
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM deleted) RETURN;

    DECLARE @bad VARCHAR(80);
    SELECT TOP 1 @bad = d.initiative_id
    FROM deleted d
    JOIN dbo.initiative i ON i.initiative_id = d.initiative_id
    WHERE i.status = 'Active' AND i.active_flag = 1
      AND NOT EXISTS (
            SELECT 1 FROM dbo.initiative_goal g
            WHERE g.initiative_id = i.initiative_id
              AND (g.effective_end IS NULL OR g.effective_end >= CAST(GETDATE() AS DATE)));

    IF @bad IS NOT NULL
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50011, 'Removing this mapping leaves an active initiative with no goal.', 1;
    END
END
GO

-- ---------------------------------------------------------------------------
-- K2. An active D-1 initiative must support at least one Dean initiative
-- ---------------------------------------------------------------------------
-- Reference: assert_active_d1_has_dean_link(). Independent of K1: satisfying
-- the goal rule does not satisfy this one, and the tests assert that.

CREATE OR ALTER TRIGGER dbo.trg_active_d1_requires_dean_link
ON dbo.initiative
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM inserted
                   WHERE initiative_level = 'D-1' AND status = 'Active' AND active_flag = 1)
        RETURN;

    DECLARE @bad VARCHAR(80);
    SELECT TOP 1 @bad = i.initiative_id
    FROM inserted i
    WHERE i.initiative_level = 'D-1' AND i.status = 'Active' AND i.active_flag = 1
      AND NOT EXISTS (
            SELECT 1
            FROM dbo.initiative_relationship r
            JOIN dbo.initiative parent ON parent.initiative_id = r.to_initiative_id
            WHERE r.from_initiative_id = i.initiative_id
              AND parent.initiative_level = 'Dean'
              AND r.relationship_type IN ('Supports','Contributes To')
              AND (r.effective_end IS NULL OR r.effective_end >= CAST(GETDATE() AS DATE)));

    IF @bad IS NOT NULL
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50012, 'Active D-1 initiative must support at least one Dean initiative.', 1;
    END
END
GO

CREATE OR ALTER TRIGGER dbo.trg_dean_link_removal_requires_link
ON dbo.initiative_relationship
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM deleted) RETURN;

    DECLARE @bad VARCHAR(80);
    SELECT TOP 1 @bad = i.initiative_id
    FROM dbo.initiative i
    WHERE i.initiative_level = 'D-1' AND i.status = 'Active' AND i.active_flag = 1
      AND EXISTS (SELECT 1 FROM deleted d WHERE d.from_initiative_id = i.initiative_id)
      AND NOT EXISTS (
            SELECT 1
            FROM dbo.initiative_relationship r
            JOIN dbo.initiative parent ON parent.initiative_id = r.to_initiative_id
            WHERE r.from_initiative_id = i.initiative_id
              AND parent.initiative_level = 'Dean'
              AND r.relationship_type IN ('Supports','Contributes To')
              AND (r.effective_end IS NULL OR r.effective_end >= CAST(GETDATE() AS DATE)));

    IF @bad IS NOT NULL
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50013, 'Removing this link leaves an active D-1 initiative with no Dean initiative.', 1;
    END
END
GO

-- ---------------------------------------------------------------------------
-- K3. Stewardship periods must not overlap for the same person/entity/role
-- ---------------------------------------------------------------------------
-- Reference: EXCLUDE USING gist with a daterange overlap. T-SQL has no EXCLUDE
-- and no range type (both measured absent on the target), so this is a trigger
-- plus sp_getapplock. THIS IS THE WEAKEST SUBSTITUTE IN THE PORT and is stated
-- plainly rather than claimed equivalent:
--
--   The applock serialises concurrent writers on the same key, so two
--   overlapping assignments cannot both pass the check on the same server.
--   Under a different transaction isolation level a reader could still see a
--   transient violation, and a writer that skips the lock (a bulk load, a
--   manual INSERT) can still create an overlap. The integrity report is the
--   backstop, and the concurrency test in the suite records which behaviour was
--   actually observed rather than asserting equivalence.

CREATE OR ALTER TRIGGER dbo.trg_stewardship_no_overlap
ON dbo.stewardship_assignment
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM inserted) RETURN;

    DECLARE @key NVARCHAR(200), @resource NVARCHAR(255);
    DECLARE @res INT;

    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT DISTINCT CONCAT(entity_type, ':', entity_id, ':', person_id, ':', stewardship_role)
        FROM inserted;
    OPEN cur;
    FETCH NEXT FROM cur INTO @key;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- serialise writers touching this key; the lock is released at commit
        SET @resource = CONCAT('stewardship:', @key);
        EXEC @res = sp_getapplock @Resource = @resource, @LockMode = 'Exclusive',
                                  @LockOwner = 'Transaction', @LockTimeout = 10000;
        IF @res < 0
        BEGIN
            CLOSE cur; DEALLOCATE cur;
            ROLLBACK TRANSACTION;
            THROW 50020, 'Could not serialise stewardship assignment; retry.', 1;
        END

        FETCH NEXT FROM cur INTO @key;
    END
    CLOSE cur; DEALLOCATE cur;

    -- now the overlap check itself, for any row in this statement
    DECLARE @bad VARCHAR(200);
    SELECT TOP 1 @bad = CONCAT(i.entity_type, ' ', i.entity_id)
    FROM inserted i
    JOIN dbo.stewardship_assignment s
      ON  s.entity_type = i.entity_type
      AND s.entity_id   = i.entity_id
      AND s.person_id   = i.person_id
      AND s.stewardship_role = i.stewardship_role
      AND s.stewardship_id  <> i.stewardship_id
      -- half-open intervals [start, end); overlap when each starts before the
      -- other ends, with an open end treated as infinity
      AND i.effective_start < COALESCE(s.effective_end, '9999-12-31')
      AND s.effective_start < COALESCE(i.effective_end, '9999-12-31');

    IF @bad IS NOT NULL
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50021, 'Overlapping stewardship period for the same person, entity and role.', 1;
    END
END
GO
