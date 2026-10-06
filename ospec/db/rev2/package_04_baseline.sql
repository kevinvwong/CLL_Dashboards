-- ============================================================================
-- CLL Strategy Portfolio - Revision 2 BASELINE
-- ============================================================================
-- TRANSCRIBED VERBATIM from the source package. Do not edit to fix behaviour:
-- this file is the reference the T-SQL port is measured against. The port lives
-- in ../mssql/ and is where defaults and deviations are applied.
--
-- Source : 04_Strategy_Portfolio_Schema_with_Constraints.sql
-- Package: CLL_Strategy_Portfolio_Enterprise_Package_v1.0.zip
-- Archive SHA256: EB71B8BCA667420F78E3289C4D2AB4DD341482CDAA464E7E1050E30A1251E08E
-- Package SHA256 of this file: D1B9EBBE889AFFA2A1DB95448C9F3ABA9A9CCF3E47F36907E733EB777EF7A44A
-- Baseline date  : 2026-10-05
-- Architecture   : Revision 2, Governance Review Baseline
-- Dialect        : PostgreSQL (self-declared reference implementation, ADR-021)
-- Tables         : 15
--
-- ============================================================================
-- CONTRADICTIONS IN THE SOURCE PACKAGE - RESOLVED BY REVERSIBLE DEFAULT
-- ============================================================================
-- The package disagrees with itself in five places. This transcription keeps
-- the package's PostgreSQL forms exactly as delivered; the defaults below are
-- applied in the T-SQL port under ../mssql/, and recorded in the change's
-- design.md D7 with the cost of reversing each one.
--
-- 1. OWNERSHIP ROLE NAMING
--      ADR-006 (12_Architecture_Decision_Record.md) names eight roles
--      including 'Accountable Executive' and 'Operational Lead'.
--      THIS FILE constrains initiative_owner.ownership_role to four:
--      ('Accountable Owner','Reporting Owner','Sponsor','Contributor').
--      'Operational Lead' appears nowhere in either SQL file.
--      DEFAULT: 'Accountable Owner' stored, 'Accountable Executive' as a
--      display alias, 'Operational Lead' deferred.
--      REVERSAL: one CHECK constraint.
--
-- 2. RELATIONSHIP TYPES
--      09_Revision2_Migration.sql narrates an expansion to ten types
--      (adding Delivers, Funds, Consumes, Influences, Measures) but issues no
--      ALTER widening the CHECK.
--      THIS FILE constrains initiative_relationship.relationship_type to five:
--      ('Supports','Enables','Depends On','Contributes To','Replaces').
--      DEFAULT: the five this file actually permits.
--      REVERSAL: widen one CHECK; no data change.
--
-- 3. PROGRESS METHOD VOCABULARY
--      09_Revision2_Migration.sql replaces the check with six values:
--      ('Manual','Owner Estimate','Milestone','Metric','Weighted Metric',
--      'Portfolio').
--      03_Strategy_Portfolio_Data_Package.xlsx ControlledVocab permits three:
--      ('Owner Estimate','Metric Derived','Milestone Derived').
--      Only 'Owner Estimate' survives both. 'Metric Derived' becomes 'Metric';
--      'Weighted Metric' is added although ADR-013 defers weighted rollups.
--      DEFAULT: 'Owner Estimate' and 'Metric Derived'.
--      REVERSAL: one CHECK on initiative.progress_method.
--
-- 4. STEWARDSHIP ENTITY TYPE
--      09_Revision2_Migration.sql permits entity_type 'Data Product', but no
--      data_product table exists in either file (27 tables, checked).
--      DEFAULT: remove the value; nothing exists to steward.
--      REVERSAL: remove one value from a CHECK.
--
-- 5. INITIATIVE LEVEL VOCABULARY
--      THIS FILE permits four (Dean, D-1, Team, Enterprise).
--      05_Handoff_and_Implementation_Checklist.docx assumes two.
--      01_Executive_Handoff_Brief.docx names three.
--      DEFAULT: 'Dean' and 'D-1' only, matching the project config.
--      REVERSAL: one CHECK on initiative.initiative_level.
--
-- A sixth gap, not a contradiction: the package cannot record WHO validated a
-- record or WHEN, which the change's provenance spec requires. See design.md
-- D9; a validation_event table is added in the T-SQL port.
-- ============================================================================

-- Strategy Portfolio Database baseline schema
-- Platform-neutral PostgreSQL-style DDL; adapt data types and filtered indexes for target platform.

create table source_record (
  source_id varchar(40) primary key,
  source_type varchar(40) not null,
  source_name varchar(255) not null,
  source_locator varchar(255),
  authority_level varchar(40) not null,
  notes text
);

create table goal (
  goal_id varchar(10) primary key,
  goal_number smallint not null unique check (goal_number between 1 and 5),
  short_label varchar(80) not null,
  canonical_title text not null,
  canonical_description text,
  source_id varchar(40) not null references source_record(source_id),
  display_order smallint not null,
  active_flag boolean not null default true
);

create table strategic_objective (
  objective_id varchar(20) primary key,
  goal_id varchar(10) not null references goal(goal_id),
  objective_sequence smallint not null,
  canonical_text text not null,
  source_id varchar(40) not null references source_record(source_id),
  active_flag boolean not null default true,
  unique(goal_id, objective_sequence)
);

create table annual_priority (
  priority_id varchar(20) primary key,
  priority_code varchar(20) not null,
  priority_name varchar(120) not null,
  description text,
  planning_period varchar(40) not null,
  source_id varchar(40) references source_record(source_id),
  display_order smallint not null,
  active_flag boolean not null default true,
  unique(priority_code, planning_period)
);

create table team (
  team_id varchar(40) primary key,
  team_name varchar(200) not null,
  description text,
  active_flag boolean not null default true
);

create table person (
  person_id varchar(80) primary key,
  display_name varchar(200) not null,
  business_email varchar(320) unique,
  working_title varchar(200),
  team_id varchar(40) references team(team_id),
  active_flag boolean not null default true
);

create table initiative (
  initiative_id varchar(80) primary key,
  initiative_code varchar(40) not null unique,
  initiative_name varchar(255) not null,
  description text not null,
  initiative_level varchar(30) not null check (initiative_level in ('Dean','D-1','Team','Enterprise')),
  initiative_type varchar(30) not null check (initiative_type in ('Initiative','Project','Program','Capability','TBD')),
  status varchar(30) not null check (status in ('Proposed','Active','On Hold','Completed','Retired')),
  progress_value numeric(5,2) check (progress_value is null or (progress_value between 0 and 100)),
  progress_method varchar(30) check (progress_method is null or progress_method in ('Owner Estimate','Metric Derived','Milestone Derived')),
  start_date date,
  target_date date,
  source_id varchar(40) references source_record(source_id),
  validation_status varchar(40) not null default 'Needs Review',
  active_flag boolean not null default true,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
);

create table initiative_goal (
  initiative_id varchar(80) not null references initiative(initiative_id),
  goal_id varchar(10) not null references goal(goal_id),
  relationship_type varchar(30) not null check (relationship_type in ('Primary','Secondary','Contributing')),
  rationale text,
  validation_status varchar(40) not null default 'Needs Review',
  effective_start date,
  effective_end date,
  primary key (initiative_id, goal_id)
);

create table initiative_priority (
  initiative_id varchar(80) not null references initiative(initiative_id),
  priority_id varchar(20) not null references annual_priority(priority_id),
  relationship_type varchar(30) not null check (relationship_type in ('Primary','Supporting')),
  rationale text,
  validation_status varchar(40) not null default 'Needs Review',
  effective_start date,
  effective_end date,
  primary key (initiative_id, priority_id)
);

create table initiative_relationship (
  from_initiative_id varchar(80) not null references initiative(initiative_id),
  to_initiative_id varchar(80) not null references initiative(initiative_id),
  relationship_type varchar(30) not null check (relationship_type in ('Supports','Enables','Depends On','Contributes To','Replaces')),
  weight numeric(7,4),
  effective_start date,
  effective_end date,
  primary key (from_initiative_id, to_initiative_id, relationship_type),
  check (from_initiative_id <> to_initiative_id)
);

create table initiative_owner (
  initiative_id varchar(80) not null references initiative(initiative_id),
  person_id varchar(80) not null references person(person_id),
  ownership_role varchar(30) not null check (ownership_role in ('Accountable Owner','Reporting Owner','Sponsor','Contributor')),
  primary_flag boolean not null default false,
  effective_start date not null,
  effective_end date,
  primary key (initiative_id, person_id, ownership_role, effective_start)
);

create table initiative_update (
  update_id varchar(80) primary key,
  initiative_id varchar(80) not null references initiative(initiative_id),
  update_date timestamp not null default current_timestamp,
  updated_by_person_id varchar(80) references person(person_id),
  narrative text not null,
  progress_value numeric(5,2) check (progress_value is null or progress_value between 0 and 100),
  status_at_update varchar(30),
  risks_or_barriers text,
  next_step text
);

create table metric (
  metric_id varchar(80) primary key,
  metric_code varchar(40) not null unique,
  metric_name varchar(255) not null,
  definition text,
  unit varchar(80),
  calculation_method text,
  data_source text,
  reporting_frequency varchar(80),
  data_steward varchar(200),
  baseline_value varchar(120),
  target_value varchar(120),
  target_date date,
  current_value varchar(120),
  validation_status varchar(40) not null default 'Needs Review'
);

create table initiative_metric (
  initiative_id varchar(80) not null references initiative(initiative_id),
  metric_id varchar(80) not null references metric(metric_id),
  relationship_type varchar(30) not null,
  weight numeric(7,4),
  primary key (initiative_id, metric_id)
);

create table goal_metric (
  goal_id varchar(10) not null references goal(goal_id),
  metric_id varchar(80) not null references metric(metric_id),
  relationship_type varchar(30) not null,
  primary key (goal_id, metric_id)
);

-- Target-platform implementation note:
-- Add a filtered/partial unique index to enforce one current primary reporting owner per initiative.
-- Example for PostgreSQL:
create unique index uq_current_primary_owner
  on initiative_owner (initiative_id)
  where primary_flag = true and effective_end is null;

create index ix_initiative_goal_goal on initiative_goal(goal_id);
create index ix_initiative_priority_priority on initiative_priority(priority_id);
create index ix_owner_person on initiative_owner(person_id);
create index ix_update_initiative_date on initiative_update(initiative_id, update_date desc);

-- ============================================================================
-- RELATIONSHIP-CONSTRAINT ENFORCEMENT EXAMPLES (PostgreSQL)
-- ============================================================================
-- These examples supplement the baseline DDL. Apply after the base tables exist.
-- Where a rule depends on multiple rows or tables, use deferred constraint
-- triggers so a transaction can complete all related inserts before validation.

-- 1. Cardinality: prevent duplicate many-to-many links.
-- Already enforced by composite primary keys. Equivalent explicit examples:
-- alter table initiative_goal
--   add constraint uq_initiative_goal unique (initiative_id, goal_id);
-- alter table initiative_priority
--   add constraint uq_initiative_priority unique (initiative_id, priority_id);

-- 2. Cardinality: exactly one current primary reporting owner per initiative.
-- Conditional uniqueness is enforced with a partial unique index.
create unique index if not exists uq_initiative_current_primary_reporting_owner
  on initiative_owner (initiative_id)
  where primary_flag = true
    and ownership_role = 'Reporting Owner'
    and effective_end is null;

-- 3. Temporal integrity for effective-dated relationships.
alter table initiative_owner
  add constraint ck_initiative_owner_date_order
  check (effective_end is null or effective_end >= effective_start);

alter table initiative_goal
  add constraint ck_initiative_goal_date_order
  check (effective_end is null or effective_start is null or effective_end >= effective_start);

alter table initiative_priority
  add constraint ck_initiative_priority_date_order
  check (effective_end is null or effective_start is null or effective_end >= effective_start);

alter table initiative_relationship
  add constraint ck_initiative_relationship_date_order
  check (effective_end is null or effective_start is null or effective_end >= effective_start);

-- 4. Prevent overlapping ownership periods for the same role/person/initiative.
-- Requires the btree_gist extension for equality support in an exclusion constraint.
create extension if not exists btree_gist;

alter table initiative_owner
  add constraint ex_initiative_owner_no_overlap
  exclude using gist (
    initiative_id with =,
    person_id with =,
    ownership_role with =,
    daterange(effective_start, coalesce(effective_end, 'infinity'::date), '[]') with &&
  );

-- 5. Enforce relationship semantics by initiative level.
-- D-1 initiatives may support Dean initiatives. Other relationship types remain
-- available for same-level or cross-level dependency/enabling links.
create or replace function enforce_initiative_relationship_levels()
returns trigger
language plpgsql
as $$
declare
  from_level varchar(30);
  to_level varchar(30);
begin
  if new.from_initiative_id = new.to_initiative_id then
    raise exception 'An initiative cannot relate to itself: %', new.from_initiative_id;
  end if;

  select initiative_level into from_level
  from initiative where initiative_id = new.from_initiative_id;

  select initiative_level into to_level
  from initiative where initiative_id = new.to_initiative_id;

  if new.relationship_type in ('Supports','Contributes To')
     and not (from_level = 'D-1' and to_level = 'Dean') then
    raise exception 'Supports/Contributes To must map D-1 -> Dean. Received % -> %',
      from_level, to_level;
  end if;

  return new;
end;
$$;

create trigger trg_enforce_initiative_relationship_levels
before insert or update on initiative_relationship
for each row execute function enforce_initiative_relationship_levels();

-- 6. Prevent cycles in hierarchical initiative links.
-- The recursive CTE starts from the proposed destination and follows existing
-- hierarchical links. If it can reach the proposed source, the insert would
-- create a cycle.
create or replace function prevent_initiative_relationship_cycle()
returns trigger
language plpgsql
as $$
declare
  creates_cycle boolean;
begin
  if new.relationship_type not in ('Supports','Contributes To','Enables') then
    return new;
  end if;

  with recursive descendants AS (
    select ir.to_initiative_id
    from initiative_relationship ir
    where ir.from_initiative_id = new.to_initiative_id
      and ir.relationship_type in ('Supports','Contributes To','Enables')
      and (ir.effective_end is null or ir.effective_end >= current_date)

    union

    select ir.to_initiative_id
    from initiative_relationship ir
    join descendants d on ir.from_initiative_id = d.to_initiative_id
    where ir.relationship_type in ('Supports','Contributes To','Enables')
      and (ir.effective_end is null or ir.effective_end >= current_date)
  )
  select exists (
    select 1 from descendants where to_initiative_id = new.from_initiative_id
  ) into creates_cycle;

  if creates_cycle then
    raise exception 'Relationship would create an initiative cycle: % -> %',
      new.from_initiative_id, new.to_initiative_id;
  end if;

  return new;
end;
$$;

create trigger trg_prevent_initiative_relationship_cycle
before insert or update on initiative_relationship
for each row execute function prevent_initiative_relationship_cycle();

-- 7. Minimum cardinality: every active initiative must have at least one
-- current Goal mapping. This is cross-table logic and therefore uses a deferred
-- constraint trigger. The trigger is fired by changes to initiative_goal.
create or replace function assert_active_initiative_has_goal(p_initiative_id varchar)
returns void
language plpgsql
as $$
begin
  if exists (
      select 1 from initiative i
      where i.initiative_id = p_initiative_id
        and i.active_flag = true
        and i.status = 'Active'
    )
    and not exists (
      select 1 from initiative_goal ig
      where ig.initiative_id = p_initiative_id
        and (ig.effective_end is null or ig.effective_end >= current_date)
    ) then
      raise exception 'Active initiative % must have at least one current Goal mapping',
        p_initiative_id;
  end if;
end;
$$;

create or replace function check_goal_minimum_from_mapping()
returns trigger
language plpgsql
as $$
begin
  perform assert_active_initiative_has_goal(coalesce(new.initiative_id, old.initiative_id));
  return null;
end;
$$;

create constraint trigger ctrg_active_initiative_goal_minimum
  after insert or update or delete on initiative_goal
  deferrable initially deferred
  for each row execute function check_goal_minimum_from_mapping();

-- Companion trigger catches an initiative being activated without a Goal map.
create or replace function check_goal_minimum_from_initiative()
returns trigger
language plpgsql
as $$
begin
  perform assert_active_initiative_has_goal(new.initiative_id);
  return null;
end;
$$;

create constraint trigger ctrg_active_initiative_goal_on_status
  after insert or update of status, active_flag on initiative
  deferrable initially deferred
  for each row execute function check_goal_minimum_from_initiative();

-- 8. Minimum cardinality: an active D-1 initiative must support at least one
-- current Dean initiative.
create or replace function assert_active_d1_has_dean_link(p_initiative_id varchar)
returns void
language plpgsql
as $$
begin
  if exists (
      select 1 from initiative i
      where i.initiative_id = p_initiative_id
        and i.initiative_level = 'D-1'
        and i.active_flag = true
        and i.status = 'Active'
    )
    and not exists (
      select 1
      from initiative_relationship ir
      join initiative parent_i on parent_i.initiative_id = ir.to_initiative_id
      where ir.from_initiative_id = p_initiative_id
        and parent_i.initiative_level = 'Dean'
        and ir.relationship_type in ('Supports','Contributes To')
        and (ir.effective_end is null or ir.effective_end >= current_date)
    ) then
      raise exception 'Active D-1 initiative % must support at least one Dean initiative',
        p_initiative_id;
  end if;
end;
$$;

create or replace function check_d1_dean_minimum_from_relationship()
returns trigger
language plpgsql
as $$
begin
  perform assert_active_d1_has_dean_link(coalesce(new.from_initiative_id, old.from_initiative_id));
  return null;
end;
$$;

create constraint trigger ctrg_active_d1_dean_minimum
  after insert or update or delete on initiative_relationship
  deferrable initially deferred
  for each row execute function check_d1_dean_minimum_from_relationship();

-- 9. Minimum cardinality: active D-1 initiatives have one current primary
-- reporting owner. The partial unique index above enforces the maximum of one;
-- this deferred trigger enforces the minimum of one.
create or replace function assert_active_d1_has_primary_owner(p_initiative_id varchar)
returns void
language plpgsql
as $$
begin
  if exists (
      select 1 from initiative i
      where i.initiative_id = p_initiative_id
        and i.initiative_level = 'D-1'
        and i.active_flag = true
        and i.status = 'Active'
    )
    and not exists (
      select 1 from initiative_owner io
      where io.initiative_id = p_initiative_id
        and io.ownership_role = 'Reporting Owner'
        and io.primary_flag = true
        and io.effective_end is null
    ) then
      raise exception 'Active D-1 initiative % must have one current primary Reporting Owner',
        p_initiative_id;
  end if;
end;
$$;

create or replace function check_primary_owner_minimum()
returns trigger
language plpgsql
as $$
begin
  perform assert_active_d1_has_primary_owner(coalesce(new.initiative_id, old.initiative_id));
  return null;
end;
$$;

create constraint trigger ctrg_active_d1_primary_owner_minimum
  after insert or update or delete on initiative_owner
  deferrable initially deferred
  for each row execute function check_primary_owner_minimum();

-- 10. Append-only initiative updates.
create or replace function block_initiative_update_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'initiative_update is append-only; insert a superseding update instead';
end;
$$;

create trigger trg_block_initiative_update_change
before update or delete on initiative_update
for each row execute function block_initiative_update_mutation();

-- 11. Protect canonical Goals and Strategic Objectives from hard deletion.
create or replace function block_canonical_delete()
returns trigger
language plpgsql
as $$
begin
  raise exception 'Canonical strategy records cannot be deleted; set active_flag = false if superseded';
end;
$$;

create trigger trg_block_goal_delete
before delete on goal
for each row execute function block_canonical_delete();

create trigger trg_block_objective_delete
before delete on strategic_objective
for each row execute function block_canonical_delete();

-- 12. Example transaction: activate a D-1 initiative while satisfying all
-- deferred minimum-cardinality rules in a single transaction.
begin;

insert into initiative (
  initiative_id, initiative_code, initiative_name, description,
  initiative_level, initiative_type, status, progress_method,
  validation_status, active_flag
) values (
  'INIT-D1-001', 'D1-001', 'Dashboarding',
  'Create operational, financial, and Strategy 2035 reporting views.',
  'D-1', 'Initiative', 'Proposed', 'Owner Estimate',
  'Leadership Confirmed', true
);

insert into initiative_goal (
  initiative_id, goal_id, relationship_type, validation_status, effective_start
) values
  ('INIT-D1-001', 'G4', 'Contributing', 'Leadership Confirmed', current_date),
  ('INIT-D1-001', 'G5', 'Primary', 'Leadership Confirmed', current_date);

insert into initiative_priority (
  initiative_id, priority_id, relationship_type, validation_status, effective_start
) values
  ('INIT-D1-001', 'P6', 'Primary', 'Leadership Confirmed', current_date),
  ('INIT-D1-001', 'P2', 'Supporting', 'Leadership Confirmed', current_date);

insert into initiative_relationship (
  from_initiative_id, to_initiative_id, relationship_type, effective_start
) values
  ('INIT-D1-001', 'INIT-DEAN-001', 'Supports', current_date);

insert into initiative_owner (
  initiative_id, person_id, ownership_role, primary_flag, effective_start
) values
  ('INIT-D1-001', 'PERSON-001', 'Reporting Owner', true, current_date);

update initiative
set status = 'Active', updated_at = current_timestamp
where initiative_id = 'INIT-D1-001';

commit;

-- 13. Operational integrity report: records requiring remediation.
-- This can be scheduled as a monitoring query even when database rules are
-- temporarily relaxed during migration.
with current_goal as (
  select distinct initiative_id
  from initiative_goal
  where effective_end is null or effective_end >= current_date
),
current_dean_link as (
  select distinct ir.from_initiative_id as initiative_id
  from initiative_relationship ir
  join initiative parent_i on parent_i.initiative_id = ir.to_initiative_id
  where parent_i.initiative_level = 'Dean'
    and ir.relationship_type in ('Supports','Contributes To')
    and (ir.effective_end is null or ir.effective_end >= current_date)
),
current_primary_owner as (
  select initiative_id, count(*) as owner_count
  from initiative_owner
  where ownership_role = 'Reporting Owner'
    and primary_flag = true
    and effective_end is null
  group by initiative_id
)
select
  i.initiative_code,
  i.initiative_name,
  case when cg.initiative_id is null then 'Missing Goal mapping' end as goal_issue,
  case when i.initiative_level = 'D-1' and cdl.initiative_id is null
       then 'Missing Dean initiative link' end as dean_link_issue,
  case when i.initiative_level = 'D-1' and coalesce(cpo.owner_count, 0) <> 1
       then 'Must have exactly one current primary Reporting Owner' end as owner_issue
from initiative i
left join current_goal cg on cg.initiative_id = i.initiative_id
left join current_dean_link cdl on cdl.initiative_id = i.initiative_id
left join current_primary_owner cpo on cpo.initiative_id = i.initiative_id
where i.active_flag = true
  and i.status = 'Active'
  and (
    cg.initiative_id is null
    or (i.initiative_level = 'D-1' and cdl.initiative_id is null)
    or (i.initiative_level = 'D-1' and coalesce(cpo.owner_count, 0) <> 1)
  );


-- 14. Companion activation trigger for D-1 minimum cardinalities.
-- The relationship-table and ownership-table triggers protect changes to those
-- tables. This trigger also protects a Proposed D-1 initiative when its status
-- is changed to Active.
create or replace function check_d1_minima_from_initiative()
returns trigger
language plpgsql
as $$
begin
  perform assert_active_d1_has_dean_link(new.initiative_id);
  perform assert_active_d1_has_primary_owner(new.initiative_id);
  return null;
end;
$$;

create constraint trigger ctrg_active_d1_minima_on_status
  after insert or update of status, active_flag, initiative_level on initiative
  deferrable initially deferred
  for each row execute function check_d1_minima_from_initiative();
