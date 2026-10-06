-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL port
-- ============================================================================
-- Target : Azure SQL Database (serverless General Purpose, GP_S_Gen5)
-- Source : ../rev2/package_04_baseline.sql and ../rev2/package_09_rev2_migration.sql
--          transcribed verbatim from CLL_Strategy_Portfolio_Enterprise_Package_v1.0.zip
--
-- ADR-021 designates the PostgreSQL DDL a REFERENCE IMPLEMENTATION and requires
-- the target platform to receive equivalent constraints, with every semantic
-- deviation documented. This file is that port, and the deviations it carries
-- are listed in DEVIATIONS.md beside it. Read that before changing a constraint
-- here, because three of them are substitutes rather than translations.
--
-- Deliberate changes from the reference, all recorded:
--   D7  vocabularies resolved to reversible defaults
--   D9  validation_event added (the package cannot record who validated what)
--   D3  substitutes for mechanisms T-SQL does not provide
--
-- Idempotent: safe to run more than once.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- 1. Canonical strategy
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.source_record', 'U') IS NULL
CREATE TABLE dbo.source_record (
    source_id       VARCHAR(40)  NOT NULL CONSTRAINT pk_source_record PRIMARY KEY,
    source_type     VARCHAR(40)  NOT NULL,
    source_name     VARCHAR(255) NOT NULL,
    source_locator  VARCHAR(255) NULL,
    authority_level VARCHAR(40)  NOT NULL,
    notes           NVARCHAR(MAX) NULL
);
GO

IF OBJECT_ID('dbo.goal', 'U') IS NULL
CREATE TABLE dbo.goal (
    goal_id              VARCHAR(10)  NOT NULL CONSTRAINT pk_goal PRIMARY KEY,
    -- Canonical goal number. Constrained 1..5 because Strategy 2035 defines
    -- exactly five, and this number IS the goal's identity.
    goal_number          SMALLINT     NOT NULL CONSTRAINT uq_goal_number UNIQUE
                                      CONSTRAINT ck_goal_number CHECK (goal_number BETWEEN 1 AND 5),
    short_label          VARCHAR(80)  NOT NULL,
    canonical_title      NVARCHAR(MAX) NOT NULL,
    canonical_description NVARCHAR(MAX) NULL,
    source_id            VARCHAR(40)  NOT NULL CONSTRAINT fk_goal_source REFERENCES dbo.source_record(source_id),
    display_order        SMALLINT     NOT NULL,
    active_flag          BIT          NOT NULL CONSTRAINT df_goal_active DEFAULT 1
);
GO

IF OBJECT_ID('dbo.strategic_objective', 'U') IS NULL
CREATE TABLE dbo.strategic_objective (
    objective_id       VARCHAR(20)  NOT NULL CONSTRAINT pk_strategic_objective PRIMARY KEY,
    goal_id            VARCHAR(10)  NOT NULL CONSTRAINT fk_objective_goal REFERENCES dbo.goal(goal_id),
    objective_sequence SMALLINT     NOT NULL,
    canonical_text     NVARCHAR(MAX) NOT NULL,
    source_id          VARCHAR(40)  NOT NULL CONSTRAINT fk_objective_source REFERENCES dbo.source_record(source_id),
    active_flag        BIT          NOT NULL CONSTRAINT df_objective_active DEFAULT 1,
    CONSTRAINT uq_objective_sequence UNIQUE (goal_id, objective_sequence)
);
GO

-- Portfolio: a navigational lens over goals (ADR-002). Rev2 migration.
IF OBJECT_ID('dbo.portfolio', 'U') IS NULL
CREATE TABLE dbo.portfolio (
    portfolio_id VARCHAR(40)  NOT NULL CONSTRAINT pk_portfolio PRIMARY KEY,
    portfolio_name VARCHAR(200) NOT NULL,
    description  NVARCHAR(MAX) NULL,
    source_id    VARCHAR(40)  NULL CONSTRAINT fk_portfolio_source REFERENCES dbo.source_record(source_id),
    validation_status VARCHAR(40) NOT NULL CONSTRAINT df_portfolio_validation DEFAULT 'Needs Review',
    active_flag  BIT NOT NULL CONSTRAINT df_portfolio_active DEFAULT 1
);
GO

IF OBJECT_ID('dbo.portfolio_goal', 'U') IS NULL
CREATE TABLE dbo.portfolio_goal (
    portfolio_id VARCHAR(40) NOT NULL CONSTRAINT fk_portfolio_goal_pf REFERENCES dbo.portfolio(portfolio_id),
    goal_id      VARCHAR(10) NOT NULL CONSTRAINT fk_portfolio_goal_goal REFERENCES dbo.goal(goal_id),
    CONSTRAINT pk_portfolio_goal PRIMARY KEY (portfolio_id, goal_id)
);
GO

-- ---------------------------------------------------------------------------
-- 4. Targets (Rev2 migration). Separate from Objective and from Metric.
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.target', 'U') IS NULL
CREATE TABLE dbo.target (
    target_id          VARCHAR(40)  NOT NULL CONSTRAINT pk_target PRIMARY KEY,
    target_name        VARCHAR(255) NOT NULL,
    target_value_text  VARCHAR(200) NULL,
    measure_context    VARCHAR(255) NULL,
    unit               VARCHAR(80)  NULL,
    target_timeframe   VARCHAR(80)  NULL,
    source_id          VARCHAR(40)  NULL CONSTRAINT fk_target_source REFERENCES dbo.source_record(source_id),
    validation_status  VARCHAR(40)  NOT NULL CONSTRAINT df_target_validation DEFAULT 'Needs Review'
);
GO

IF OBJECT_ID('dbo.objective_target', 'U') IS NULL
CREATE TABLE dbo.objective_target (
    objective_id VARCHAR(20) NOT NULL CONSTRAINT fk_objtarget_objective REFERENCES dbo.strategic_objective(objective_id),
    target_id    VARCHAR(40) NOT NULL CONSTRAINT fk_objtarget_target REFERENCES dbo.target(target_id),
    CONSTRAINT pk_objective_target PRIMARY KEY (objective_id, target_id)
);
GO

IF OBJECT_ID('dbo.objective_initiative', 'U') IS NULL
CREATE TABLE dbo.objective_initiative (
    objective_id  VARCHAR(20) NOT NULL CONSTRAINT fk_objinit_objective REFERENCES dbo.strategic_objective(objective_id),
    initiative_id VARCHAR(80) NOT NULL,
    relationship_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_objinit_rel CHECK (relationship_type IN ('Primary','Secondary','Contributing')),
    validation_status VARCHAR(40) NOT NULL CONSTRAINT df_objinit_validation DEFAULT 'Needs Review',
    CONSTRAINT pk_objective_initiative PRIMARY KEY (objective_id, initiative_id)
);
GO

-- ---------------------------------------------------------------------------
-- 5. Cycles and Priorities
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.planning_cycle', 'U') IS NULL
CREATE TABLE dbo.planning_cycle (
    planning_cycle_id VARCHAR(40) NOT NULL CONSTRAINT pk_planning_cycle PRIMARY KEY,
    cycle_name        VARCHAR(120) NOT NULL,
    cycle_start       DATE NULL,
    cycle_end         DATE NULL,
    CONSTRAINT ck_planning_cycle_dates CHECK (cycle_end IS NULL OR cycle_start IS NULL OR cycle_end >= cycle_start)
);
GO

IF OBJECT_ID('dbo.priority_definition', 'U') IS NULL
CREATE TABLE dbo.priority_definition (
    priority_id   VARCHAR(40)  NOT NULL CONSTRAINT pk_priority_definition PRIMARY KEY,
    priority_code VARCHAR(20)  NOT NULL,
    priority_name VARCHAR(120) NOT NULL,
    active_flag   BIT          NOT NULL CONSTRAINT df_priority_def_active DEFAULT 1,
    CONSTRAINT uq_priority_code UNIQUE (priority_code)
);
GO

IF OBJECT_ID('dbo.annual_priority', 'U') IS NULL
CREATE TABLE dbo.annual_priority (
    priority_id     VARCHAR(20)  NOT NULL CONSTRAINT pk_annual_priority PRIMARY KEY,
    priority_code   VARCHAR(20)  NOT NULL,
    priority_name   VARCHAR(120) NOT NULL,
    description     NVARCHAR(MAX) NULL,
    planning_period VARCHAR(40)  NOT NULL,
    source_id       VARCHAR(40)  NULL CONSTRAINT fk_priority_source REFERENCES dbo.source_record(source_id),
    display_order   SMALLINT     NOT NULL,
    active_flag     BIT          NOT NULL CONSTRAINT df_annual_priority_active DEFAULT 1,
    CONSTRAINT uq_priority_code_period UNIQUE (priority_code, planning_period)
);
GO

IF OBJECT_ID('dbo.priority_cycle', 'U') IS NULL
CREATE TABLE dbo.priority_cycle (
    priority_cycle_id VARCHAR(60) NOT NULL CONSTRAINT pk_priority_cycle PRIMARY KEY,
    priority_id       VARCHAR(40) NOT NULL CONSTRAINT fk_priority_cycle_definition REFERENCES dbo.priority_definition(priority_id),
    planning_cycle_id VARCHAR(40) NOT NULL CONSTRAINT fk_priority_cycle_planning REFERENCES dbo.planning_cycle(planning_cycle_id),
    cycle_description NVARCHAR(MAX) NULL,
    display_order     SMALLINT NOT NULL CONSTRAINT df_priority_cycle_order DEFAULT 0
);
GO

-- ---------------------------------------------------------------------------
-- 6. Teams and people
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.team', 'U') IS NULL
CREATE TABLE dbo.team (
    team_id     VARCHAR(40)  NOT NULL CONSTRAINT pk_team PRIMARY KEY,
    team_name   VARCHAR(200) NOT NULL,
    description NVARCHAR(MAX) NULL,
    active_flag BIT NOT NULL CONSTRAINT df_team_active DEFAULT 1
);
GO

IF OBJECT_ID('dbo.person', 'U') IS NULL
CREATE TABLE dbo.person (
    person_id      VARCHAR(80)  NOT NULL CONSTRAINT pk_person PRIMARY KEY,
    display_name   VARCHAR(200) NOT NULL,
    business_email VARCHAR(320) NULL CONSTRAINT uq_person_email UNIQUE,
    working_title  VARCHAR(200) NULL,
    team_id        VARCHAR(40)  NULL CONSTRAINT fk_person_team REFERENCES dbo.team(team_id),
    active_flag    BIT NOT NULL CONSTRAINT df_person_active DEFAULT 1
);
GO

-- ---------------------------------------------------------------------------
-- 7. Initiative
-- ---------------------------------------------------------------------------
-- D7 #5: level vocabulary resolved to Dean and D-1 only, matching the project
-- config and the implementation checklist. The reference permits four.
-- D7 #3: progress_method resolved to 'Owner Estimate' and 'Metric Derived'.
-- Note this table holds progress_value and status as a CACHE. The authoritative
-- current state is derived from initiative_update (design.md D2); nothing keeps
-- these two in step, so they must be written together by the application.

IF OBJECT_ID('dbo.initiative', 'U') IS NULL
CREATE TABLE dbo.initiative (
    initiative_id   VARCHAR(80)  NOT NULL CONSTRAINT pk_initiative PRIMARY KEY,
    initiative_code VARCHAR(40)  NOT NULL CONSTRAINT uq_initiative_code UNIQUE,
    initiative_name VARCHAR(255) NOT NULL,
    description     NVARCHAR(MAX) NOT NULL,
    initiative_level VARCHAR(30) NOT NULL
        CONSTRAINT ck_initiative_level CHECK (initiative_level IN ('Dean','D-1')),
    initiative_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_initiative_type CHECK (initiative_type IN ('Initiative','Project','Program','Capability','TBD')),
    status VARCHAR(30) NOT NULL
        CONSTRAINT ck_initiative_status CHECK (status IN ('Proposed','Active','On Hold','Completed','Retired')),
    progress_value DECIMAL(5,2) NULL
        CONSTRAINT ck_initiative_progress CHECK (progress_value IS NULL OR progress_value BETWEEN 0 AND 100),
    progress_method VARCHAR(30) NULL
        CONSTRAINT ck_initiative_progress_method CHECK (progress_method IS NULL OR progress_method IN ('Owner Estimate','Metric Derived')),
    start_date  DATE NULL,
    target_date DATE NULL,
    source_id   VARCHAR(40) NULL CONSTRAINT fk_initiative_source REFERENCES dbo.source_record(source_id),
    validation_status VARCHAR(40) NOT NULL CONSTRAINT df_initiative_validation DEFAULT 'Needs Review',
    active_flag BIT NOT NULL CONSTRAINT df_initiative_active DEFAULT 1,
    created_at  DATETIME2 NOT NULL CONSTRAINT df_initiative_created DEFAULT SYSDATETIME(),
    updated_at  DATETIME2 NOT NULL CONSTRAINT df_initiative_updated DEFAULT SYSDATETIME()
);
GO

-- ---------------------------------------------------------------------------
-- 8. Relationships
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.initiative_goal', 'U') IS NULL
CREATE TABLE dbo.initiative_goal (
    initiative_id VARCHAR(80) NOT NULL CONSTRAINT fk_initgoal_initiative REFERENCES dbo.initiative(initiative_id),
    goal_id       VARCHAR(10) NOT NULL CONSTRAINT fk_initgoal_goal REFERENCES dbo.goal(goal_id),
    relationship_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_initgoal_rel CHECK (relationship_type IN ('Primary','Secondary','Contributing')),
    rationale NVARCHAR(MAX) NULL,
    validation_status VARCHAR(40) NOT NULL CONSTRAINT df_initgoal_validation DEFAULT 'Needs Review',
    effective_start DATE NULL,
    effective_end   DATE NULL,
    CONSTRAINT pk_initiative_goal PRIMARY KEY (initiative_id, goal_id),
    CONSTRAINT ck_initgoal_dates CHECK (effective_end IS NULL OR effective_start IS NULL OR effective_end >= effective_start)
);
GO

IF OBJECT_ID('dbo.initiative_priority', 'U') IS NULL
CREATE TABLE dbo.initiative_priority (
    initiative_id VARCHAR(80) NOT NULL CONSTRAINT fk_initpri_initiative REFERENCES dbo.initiative(initiative_id),
    priority_id   VARCHAR(20) NOT NULL CONSTRAINT fk_initpri_priority REFERENCES dbo.annual_priority(priority_id),
    relationship_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_initpri_rel CHECK (relationship_type IN ('Primary','Supporting')),
    rationale NVARCHAR(MAX) NULL,
    validation_status VARCHAR(40) NOT NULL CONSTRAINT df_initpri_validation DEFAULT 'Needs Review',
    effective_start DATE NULL,
    effective_end   DATE NULL,
    CONSTRAINT pk_initiative_priority PRIMARY KEY (initiative_id, priority_id),
    CONSTRAINT ck_initpri_dates CHECK (effective_end IS NULL OR effective_start IS NULL OR effective_end >= effective_start)
);
GO

IF OBJECT_ID('dbo.initiative_priority_cycle', 'U') IS NULL
CREATE TABLE dbo.initiative_priority_cycle (
    initiative_id     VARCHAR(80) NOT NULL CONSTRAINT fk_initpric_initiative REFERENCES dbo.initiative(initiative_id),
    priority_cycle_id VARCHAR(60) NOT NULL CONSTRAINT fk_initpric_cycle REFERENCES dbo.priority_cycle(priority_cycle_id),
    relationship_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_initpric_rel CHECK (relationship_type IN ('Primary','Supporting')),
    CONSTRAINT pk_initiative_priority_cycle PRIMARY KEY (initiative_id, priority_cycle_id)
);
GO

-- D7 #2: relationship vocabulary resolved to the five the reference actually
-- permits. The migration narrates ten but never issues the ALTER; adopting the
-- narrated five would have been adopting a constraint that does not exist.
IF OBJECT_ID('dbo.initiative_relationship', 'U') IS NULL
CREATE TABLE dbo.initiative_relationship (
    from_initiative_id VARCHAR(80) NOT NULL CONSTRAINT fk_initrel_from REFERENCES dbo.initiative(initiative_id),
    to_initiative_id   VARCHAR(80) NOT NULL CONSTRAINT fk_initrel_to REFERENCES dbo.initiative(initiative_id),
    relationship_type  VARCHAR(30) NOT NULL
        CONSTRAINT ck_initrel_type CHECK (relationship_type IN ('Supports','Enables','Depends On','Contributes To','Replaces')),
    weight DECIMAL(7,4) NULL,
    effective_start DATE NULL,
    effective_end   DATE NULL,
    CONSTRAINT pk_initiative_relationship PRIMARY KEY (from_initiative_id, to_initiative_id, relationship_type),
    CONSTRAINT ck_initrel_not_self CHECK (from_initiative_id <> to_initiative_id),
    CONSTRAINT ck_initrel_dates CHECK (effective_end IS NULL OR effective_start IS NULL OR effective_end >= effective_start)
);
GO

IF OBJECT_ID('dbo.initiative_owner', 'U') IS NULL
CREATE TABLE dbo.initiative_owner (
    initiative_id VARCHAR(80) NOT NULL CONSTRAINT fk_initowner_initiative REFERENCES dbo.initiative(initiative_id),
    person_id     VARCHAR(80) NOT NULL CONSTRAINT fk_initowner_person REFERENCES dbo.person(person_id),
    -- D7 #1: 'Accountable Owner' stored; 'Accountable Executive' is a display
    -- alias. 'Operational Lead' (named in ADR-006) is deferred; it appears in no
    -- SQL file in the package.
    ownership_role VARCHAR(30) NOT NULL
        CONSTRAINT ck_initowner_role CHECK (ownership_role IN ('Accountable Owner','Reporting Owner','Sponsor','Contributor')),
    primary_flag BIT NOT NULL CONSTRAINT df_initowner_primary DEFAULT 0,
    effective_start DATE NOT NULL,
    effective_end   DATE NULL,
    CONSTRAINT pk_initiative_owner PRIMARY KEY (initiative_id, person_id, ownership_role, effective_start),
    CONSTRAINT ck_initowner_dates CHECK (effective_end IS NULL OR effective_end >= effective_start)
);
GO

-- ---------------------------------------------------------------------------
-- 9. Stewardship
-- ---------------------------------------------------------------------------
-- D7 #4: 'Data Product' removed. The reference permits it but no data_product
-- table exists in the package, so the value could never be satisfied.

IF OBJECT_ID('dbo.stewardship_assignment', 'U') IS NULL
CREATE TABLE dbo.stewardship_assignment (
    stewardship_id VARCHAR(80) NOT NULL CONSTRAINT pk_stewardship PRIMARY KEY,
    entity_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_stewardship_entity CHECK (entity_type IN ('Initiative','Metric','Target')),
    entity_id VARCHAR(80) NOT NULL,
    person_id VARCHAR(80) NOT NULL CONSTRAINT fk_stewardship_person REFERENCES dbo.person(person_id),
    stewardship_role VARCHAR(30) NOT NULL
        CONSTRAINT ck_stewardship_role CHECK (stewardship_role IN ('Business Steward','Data Steward','Technical Steward')),
    effective_start DATE NOT NULL,
    effective_end   DATE NULL,
    CONSTRAINT ck_stewardship_dates CHECK (effective_end IS NULL OR effective_end >= effective_start)
);
GO

-- ---------------------------------------------------------------------------
-- 10. Metrics
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.metric', 'U') IS NULL
CREATE TABLE dbo.metric (
    metric_id   VARCHAR(80)  NOT NULL CONSTRAINT pk_metric PRIMARY KEY,
    metric_code VARCHAR(40)  NOT NULL CONSTRAINT uq_metric_code UNIQUE,
    metric_name VARCHAR(255) NOT NULL,
    definition  NVARCHAR(MAX) NULL,
    unit        VARCHAR(80)  NULL,
    calculation_method NVARCHAR(MAX) NULL,
    data_source NVARCHAR(MAX) NULL,
    reporting_frequency VARCHAR(80) NULL,
    data_steward VARCHAR(200) NULL,
    baseline_value VARCHAR(120) NULL,
    target_value   VARCHAR(120) NULL,
    target_date    DATE NULL,
    current_value  VARCHAR(120) NULL,
    validation_status VARCHAR(40) NOT NULL CONSTRAINT df_metric_validation DEFAULT 'Needs Review'
);
GO

IF OBJECT_ID('dbo.metric_version', 'U') IS NULL
CREATE TABLE dbo.metric_version (
    metric_version_id VARCHAR(80) NOT NULL CONSTRAINT pk_metric_version PRIMARY KEY,
    metric_id         VARCHAR(80) NOT NULL CONSTRAINT fk_metric_version_metric REFERENCES dbo.metric(metric_id),
    version_number    INT NOT NULL,
    definition        NVARCHAR(MAX) NULL,
    calculation_method NVARCHAR(MAX) NULL,
    unit              VARCHAR(80) NULL,
    authoritative_source_id VARCHAR(40) NULL CONSTRAINT fk_metric_version_source REFERENCES dbo.source_record(source_id),
    effective_start  DATE NOT NULL,
    effective_end    DATE NULL,
    CONSTRAINT uq_metric_version_number UNIQUE (metric_id, version_number),
    CONSTRAINT ck_metric_version_dates CHECK (effective_end IS NULL OR effective_end >= effective_start)
);
GO

IF OBJECT_ID('dbo.initiative_metric', 'U') IS NULL
CREATE TABLE dbo.initiative_metric (
    initiative_id VARCHAR(80) NOT NULL CONSTRAINT fk_initmetric_initiative REFERENCES dbo.initiative(initiative_id),
    metric_version_id VARCHAR(80) NOT NULL CONSTRAINT fk_initmetric_version REFERENCES dbo.metric_version(metric_version_id),
    relationship_type VARCHAR(30) NOT NULL,
    weight DECIMAL(7,4) NULL,
    CONSTRAINT pk_initiative_metric PRIMARY KEY (initiative_id, metric_version_id)
);
GO

IF OBJECT_ID('dbo.goal_metric', 'U') IS NULL
CREATE TABLE dbo.goal_metric (
    goal_id   VARCHAR(10) NOT NULL CONSTRAINT fk_goalmetric_goal REFERENCES dbo.goal(goal_id),
    metric_version_id VARCHAR(80) NOT NULL CONSTRAINT fk_goalmetric_version REFERENCES dbo.metric_version(metric_version_id),
    relationship_type VARCHAR(30) NOT NULL,
    CONSTRAINT pk_goal_metric PRIMARY KEY (goal_id, metric_version_id)
);
GO

IF OBJECT_ID('dbo.target_metric', 'U') IS NULL
CREATE TABLE dbo.target_metric (
    target_id  VARCHAR(40) NOT NULL CONSTRAINT fk_targetmetric_target REFERENCES dbo.target(target_id),
    metric_version_id VARCHAR(80) NOT NULL CONSTRAINT fk_targetmetric_version REFERENCES dbo.metric_version(metric_version_id),
    relationship_type VARCHAR(30) NOT NULL
        CONSTRAINT ck_targetmetric_rel CHECK (relationship_type IN ('Primary','Supporting')),
    CONSTRAINT pk_target_metric PRIMARY KEY (target_id, metric_version_id)
);
GO

-- ---------------------------------------------------------------------------
-- 11. Updates (append-only, ADR-010)
-- ---------------------------------------------------------------------------

IF OBJECT_ID('dbo.initiative_update', 'U') IS NULL
CREATE TABLE dbo.initiative_update (
    update_id   VARCHAR(80) NOT NULL CONSTRAINT pk_initiative_update PRIMARY KEY,
    initiative_id VARCHAR(80) NOT NULL CONSTRAINT fk_update_initiative REFERENCES dbo.initiative(initiative_id),
    update_date DATETIME2 NOT NULL CONSTRAINT df_update_date DEFAULT SYSDATETIME(),
    updated_by_person_id VARCHAR(80) NULL CONSTRAINT fk_update_person REFERENCES dbo.person(person_id),
    narrative   NVARCHAR(MAX) NOT NULL,
    progress_value DECIMAL(5,2) NULL
        CONSTRAINT ck_update_progress CHECK (progress_value IS NULL OR progress_value BETWEEN 0 AND 100),
    status_at_update VARCHAR(30) NULL,
    risks_or_barriers NVARCHAR(MAX) NULL,
    next_step NVARCHAR(MAX) NULL
);
GO

-- ---------------------------------------------------------------------------
-- 12. validation_event -- ADDITION, not in the reference (design.md D9)
-- ---------------------------------------------------------------------------
-- The package has no table that can record who validated a record or when; all
-- 27 tables were checked and validation_status is a bare varchar with no
-- attribution. The provenance spec requires an attributable confirmation, so
-- this table is added. validation_status on each record remains the current
-- state; this is the history behind it. Append-only.

IF OBJECT_ID('dbo.validation_event', 'U') IS NULL
CREATE TABLE dbo.validation_event (
    validation_event_id VARCHAR(80) NOT NULL CONSTRAINT pk_validation_event PRIMARY KEY,
    entity_type VARCHAR(40) NOT NULL,
    entity_id   VARCHAR(80) NOT NULL,
    prior_status VARCHAR(40) NULL,
    new_status   VARCHAR(40) NOT NULL,
    actor_person_id VARCHAR(80) NULL CONSTRAINT fk_validation_person REFERENCES dbo.person(person_id),
    acted_at DATETIME2 NOT NULL CONSTRAINT df_validation_acted DEFAULT SYSDATETIME(),
    note NVARCHAR(MAX) NULL
);
GO

PRINT 'Rev2 base tables created.';
GO
