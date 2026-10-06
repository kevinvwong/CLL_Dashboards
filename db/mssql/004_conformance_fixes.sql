-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL conformance fixes
-- ============================================================================
-- Discovered by testing against the real target, not by reading. Each one is a
-- place where the reference PostgreSQL DDL and T-SQL disagree about something
-- that is invisible until data arrives.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- F1. NULL uniqueness: many people may lack an email address
-- ---------------------------------------------------------------------------
-- Reference: `business_email varchar(320) unique`
-- PostgreSQL treats NULLs as DISTINCT, so any number of people may have no
-- email. A plain UNIQUE constraint in T-SQL treats NULLs as EQUAL, so only one
-- person in the whole table could have a NULL email - found when the second
-- test person without an address was rejected with
--   Violation of UNIQUE KEY constraint 'uq_person_email'
-- The reference's intent is "emails, where present, are unique". A filtered
-- unique index says exactly that on T-SQL.

IF EXISTS (SELECT 1 FROM sys.key_constraints
           WHERE name = 'uq_person_email' AND parent_object_id = OBJECT_ID('dbo.person'))
    ALTER TABLE dbo.person DROP CONSTRAINT uq_person_email;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'uq_person_email_present')
    CREATE UNIQUE INDEX uq_person_email_present
        ON dbo.person (business_email)
        WHERE business_email IS NOT NULL;
GO

-- The same NULL-as-equal trap applies anywhere the reference relies on
-- PostgreSQL's NULL-distinct behaviour for a nullable unique column. Audited
-- across the port:
--   initiative.initiative_code  NOT NULL  -> unaffected
--   initiative_goal PK          NOT NULL  -> unaffected
--   goal.goal_number            NOT NULL  -> unaffected
--   metric.metric_code          NOT NULL  -> unaffected
--   metric_version (metric_id, version_number) NOT NULL -> unaffected
--   priority_definition.priority_code          NOT NULL -> unaffected
--   annual_priority (priority_code, planning_period) NOT NULL -> unaffected
-- business_email is the only nullable unique column in the model, so this is
-- the only site that needed the fix.

PRINT 'Conformance fixes applied.';
GO
