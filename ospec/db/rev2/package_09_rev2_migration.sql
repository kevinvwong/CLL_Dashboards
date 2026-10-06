-- ============================================================================
-- CLL Strategy Portfolio - Revision 2 MIGRATION
-- ============================================================================
-- TRANSCRIBED VERBATIM from the source package. See the baseline header for
-- provenance and the contradiction list.
--
-- Source : 09_Strategy_Portfolio_Revision2_Migration.sql
-- Package SHA256 of this file: 6D7C20A7C4163CAC4A14FC8B3433208E9EBB118D315572215E773FC3F986A317
-- Tables added: 12
-- ============================================================================

-- Revision 2 migration: receiving-team changes
create table portfolio (
  portfolio_id varchar(40) primary key,
  portfolio_name varchar(160) not null unique,
  description text,
  active_flag boolean not null default true
);
create table portfolio_goal (
  portfolio_id varchar(40) not null references portfolio(portfolio_id),
  goal_id varchar(10) not null references goal(goal_id),
  relationship_type varchar(30) not null default 'Primary',
  primary key (portfolio_id, goal_id)
);
create table target (
  target_id varchar(40) primary key,
  target_name varchar(255) not null,
  target_value_text varchar(255) not null,
  unit varchar(80),
  target_date date,
  source_id varchar(40) references source_record(source_id),
  validation_status varchar(40) not null default 'Needs Review',
  active_flag boolean not null default true
);
create table objective_target (
  objective_id varchar(20) not null references strategic_objective(objective_id),
  target_id varchar(40) not null references target(target_id),
  relationship_type varchar(30) not null default 'Primary',
  primary key (objective_id,target_id)
);
create table objective_initiative (
  objective_id varchar(20) not null references strategic_objective(objective_id),
  initiative_id varchar(80) not null references initiative(initiative_id),
  relationship_type varchar(30) not null check (relationship_type in ('Primary','Secondary','Contributing')),
  weight numeric(7,4),
  validation_status varchar(40) not null default 'Needs Review',
  effective_start date,
  effective_end date,
  primary key (objective_id,initiative_id)
);
create table planning_cycle (
  planning_cycle_id varchar(40) primary key,
  cycle_name varchar(80) not null unique,
  cycle_start date,
  cycle_end date,
  active_flag boolean not null default true,
  check (cycle_end is null or cycle_start is null or cycle_end >= cycle_start)
);
create table priority_definition (
  priority_id varchar(40) primary key,
  priority_name varchar(120) not null unique,
  description text,
  active_flag boolean not null default true
);
create table priority_cycle (
  priority_cycle_id varchar(60) primary key,
  priority_id varchar(40) not null references priority_definition(priority_id),
  planning_cycle_id varchar(40) not null references planning_cycle(planning_cycle_id),
  cycle_description text,
  display_order smallint not null,
  active_flag boolean not null default true,
  unique(priority_id,planning_cycle_id)
);
create table initiative_priority_cycle (
  initiative_id varchar(80) not null references initiative(initiative_id),
  priority_cycle_id varchar(60) not null references priority_cycle(priority_cycle_id),
  relationship_type varchar(30) not null check (relationship_type in ('Primary','Supporting')),
  rationale text,
  validation_status varchar(40) not null default 'Needs Review',
  effective_start date,
  effective_end date,
  primary key (initiative_id,priority_cycle_id)
);
create table metric_version (
  metric_version_id varchar(80) primary key,
  metric_id varchar(80) not null references metric(metric_id),
  version_number integer not null,
  definition text not null,
  calculation_method text not null,
  unit varchar(80),
  data_source text,
  reporting_frequency varchar(80),
  effective_start date not null,
  effective_end date,
  unique(metric_id,version_number),
  check (effective_end is null or effective_end >= effective_start)
);
create unique index uq_metric_current_version on metric_version(metric_id) where effective_end is null;
create table target_metric (
  target_id varchar(40) not null references target(target_id),
  metric_version_id varchar(80) not null references metric_version(metric_version_id),
  relationship_type varchar(30) not null check (relationship_type in ('Primary','Supporting')),
  primary key (target_id,metric_version_id)
);
create table stewardship_assignment (
  stewardship_id varchar(80) primary key,
  entity_type varchar(30) not null check (entity_type in ('Initiative','Metric','Target','Data Product')),
  entity_id varchar(80) not null,
  person_id varchar(80) not null references person(person_id),
  stewardship_role varchar(30) not null check (stewardship_role in ('Business Steward','Data Steward','Technical Steward')),
  effective_start date not null,
  effective_end date,
  check (effective_end is null or effective_end >= effective_start)
);
create extension if not exists btree_gist;
alter table stewardship_assignment add constraint ex_stewardship_no_overlap exclude using gist (
  entity_type with =, entity_id with =, person_id with =, stewardship_role with =,
  daterange(effective_start,coalesce(effective_end,'infinity'::date),'[]') with &&
);
alter table initiative drop constraint if exists initiative_progress_method_check;
-- Target-platform note: replace the original progress_method check with:
alter table initiative add constraint ck_progress_method_v2 check (
 progress_method is null or progress_method in ('Manual','Owner Estimate','Milestone','Metric','Weighted Metric','Portfolio')
);
-- Relationship-type trigger/function must accept expanded semantic list:
-- Supports, Enables, Depends On, Contributes To, Replaces, Delivers, Funds,
-- Consumes, Influences, Measures. Preserve D-1 -> Dean direction checks only for
-- Supports and Contributes To.
create or replace view strategy_traceability_matrix as
select p.portfolio_name, g.goal_id, g.canonical_title, so.objective_id,
       so.canonical_text, t.target_id, t.target_value_text,
       i.initiative_code, i.initiative_name, mv.metric_version_id,
       m.metric_name, per.display_name as primary_reporting_owner
from goal g
left join portfolio_goal pg on pg.goal_id=g.goal_id
left join portfolio p on p.portfolio_id=pg.portfolio_id
left join strategic_objective so on so.goal_id=g.goal_id
left join objective_target ot on ot.objective_id=so.objective_id
left join target t on t.target_id=ot.target_id
left join objective_initiative oi on oi.objective_id=so.objective_id
left join initiative i on i.initiative_id=oi.initiative_id
left join initiative_metric im on im.initiative_id=i.initiative_id
left join metric_version mv on mv.metric_id=im.metric_id and mv.effective_end is null
left join metric m on m.metric_id=mv.metric_id
left join initiative_owner io on io.initiative_id=i.initiative_id and io.primary_flag=true and io.ownership_role='Reporting Owner' and io.effective_end is null
left join person per on per.person_id=io.person_id;
