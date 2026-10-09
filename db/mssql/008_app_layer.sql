-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, app-layer additions
-- ============================================================================
-- Change `rev2-full-reconciliation`. The Rev2 package (000..007) models the
-- canonical strategy and the portfolio, but not four layers the running app
-- carries in SQLite. This adds them so the whole app surface can run on Rev2
-- (see the change proposal). All are ADDITIONS, not in the reference; each is
-- recorded in DEVIATIONS.md alongside the port's other documented deviations.
--
-- Idempotent (IF OBJECT_ID ... IS NULL); applied by apply.py batch-by-batch.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- app_meta: engine-agnostic key/value config (mirrors SQLite AppMeta).
-- current_plan_year, dataset_provenance. Rev2 has no equivalent, so the port
-- was falling back to sqlite for these; this removes the fallback.
-- ---------------------------------------------------------------------------
IF OBJECT_ID('dbo.app_meta', 'U') IS NULL
CREATE TABLE dbo.app_meta (
    [key]    VARCHAR(80)  NOT NULL CONSTRAINT pk_app_meta PRIMARY KEY,
    [value]  NVARCHAR(MAX) NULL
);
GO

-- ---------------------------------------------------------------------------
-- audit_log: the append-only change-management record every write emits
-- (mirrors SQLite AuditLog). person_id joins to Rev2 person. NOT
-- validation_event - that records status transitions; this records actions,
-- with free-text entity keys, before/after JSON and request correlation.
-- ---------------------------------------------------------------------------
IF OBJECT_ID('dbo.audit_log', 'U') IS NULL
CREATE TABLE dbo.audit_log (
    audit_id     INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_audit_log PRIMARY KEY,
    created_at   DATETIME2 NOT NULL CONSTRAINT df_audit_created DEFAULT SYSUTCDATETIME(),
    person_id    VARCHAR(80) NULL,   -- 'PERS-N'; no FK, an audit may outlive the person
    action       VARCHAR(80) NOT NULL,
    entity_type  VARCHAR(40) NOT NULL,
    entity_key   VARCHAR(120) NOT NULL,
    details      NVARCHAR(MAX) NULL,
    reason       NVARCHAR(MAX) NULL,
    source       VARCHAR(200) NULL,
    correlation_id VARCHAR(80) NULL
);
GO

-- ---------------------------------------------------------------------------
-- role / person_role: the application's role vocabulary the auth seam reads
-- (mirrors SQLite Roles/PeopleRoles). person_id joins to Rev2 person.
-- ---------------------------------------------------------------------------
IF OBJECT_ID('dbo.role', 'U') IS NULL
CREATE TABLE dbo.role (
    role_id     INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_role PRIMARY KEY,
    name        VARCHAR(80) NOT NULL CONSTRAINT uq_role_name UNIQUE,
    description NVARCHAR(MAX) NULL
);
GO

IF OBJECT_ID('dbo.person_role', 'U') IS NULL
CREATE TABLE dbo.person_role (
    person_id VARCHAR(80) NOT NULL CONSTRAINT fk_personrole_person REFERENCES dbo.person(person_id),
    role_id   INT NOT NULL CONSTRAINT fk_personrole_role REFERENCES dbo.role(role_id),
    CONSTRAINT pk_person_role PRIMARY KEY (person_id, role_id)
);
GO

-- ---------------------------------------------------------------------------
-- source_area: the five source areas the team-initiative screens carry
-- (mirrors SQLite SourceAreas). A lookup; nothing else FKs to it here.
-- ---------------------------------------------------------------------------
IF OBJECT_ID('dbo.source_area', 'U') IS NULL
CREATE TABLE dbo.source_area (
    source_area_id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_source_area PRIMARY KEY,
    name           VARCHAR(200) NOT NULL CONSTRAINT uq_source_area_name UNIQUE
);
GO

-- ---------------------------------------------------------------------------
-- milestone: a checkable event with a status (mirrors SQLite Milestones).
-- INT IDENTITY so the app appends without generating a string id.
--
-- SUPERSEDED BY 011_milestone_initiative.sql. It was created keyed to
-- annual_priority, which put milestones one level too high in the cascade: the
-- source register's column F lives on the Team Initiative row. 011 adds
-- initiative_id (NOT NULL, FK to dbo.initiative), drops the priority key, and
-- moves UNIQUE to (initiative_id, name). This table is left as-is for a fresh
-- install, which 011 then re-points; the two files must be applied in order.
-- ---------------------------------------------------------------------------
IF OBJECT_ID('dbo.milestone', 'U') IS NULL
CREATE TABLE dbo.milestone (
    milestone_id INT IDENTITY(1,1) NOT NULL CONSTRAINT pk_milestone PRIMARY KEY,
    priority_id  VARCHAR(20) NOT NULL CONSTRAINT fk_milestone_priority REFERENCES dbo.annual_priority(priority_id),
    name         NVARCHAR(255) NOT NULL,
    status       VARCHAR(20) NOT NULL CONSTRAINT df_milestone_status DEFAULT 'Not started'
                 CONSTRAINT ck_milestone_status CHECK (status IN ('Met','In progress','Not started','Missed')),
    planned_date DATE NULL,
    date_met     DATE NULL,
    owner_label  VARCHAR(200) NULL,
    evidence_url VARCHAR(400) NULL,
    sort_order   INT NOT NULL CONSTRAINT df_milestone_sort DEFAULT 0,
    active_flag  BIT NOT NULL CONSTRAINT df_milestone_active DEFAULT 1,
    CONSTRAINT uq_milestone_per_priority UNIQUE (priority_id, name)
);
GO

PRINT 'App-layer additions created.';
GO
