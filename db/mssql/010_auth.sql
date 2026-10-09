-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, auth additions
-- ============================================================================
-- Change `port-auth-to-rev2`. The authentication layer resolves people and
-- roles from the configured store. Roles already exist (008: role/person_role);
-- the Clerk identity link does not, so it is added here as a single nullable
-- column on `person`.
--
-- The Clerk link is an IDENTIFIER, not a secret, so it belongs on the person
-- row. There is deliberately no credential column: the shared passcode is an
-- environment setting and no per-person secret is stored in either store.
--
-- Unique where present (a filtered index), the same pattern 004 used for the
-- nullable business_email: many people may be unlinked, but two may not share
-- one Clerk id.
--
-- Idempotent (COL_LENGTH / sys.indexes guarded); applied by apply.py.
-- ============================================================================

SET NOCOUNT ON;
GO

IF COL_LENGTH('dbo.person', 'clerk_user_id') IS NULL
ALTER TABLE dbo.person ADD clerk_user_id VARCHAR(128) NULL;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
               WHERE name = 'uq_person_clerk_user' AND object_id = OBJECT_ID('dbo.person'))
CREATE UNIQUE INDEX uq_person_clerk_user ON dbo.person (clerk_user_id)
    WHERE clerk_user_id IS NOT NULL;
GO

PRINT 'Auth additions created.';
GO