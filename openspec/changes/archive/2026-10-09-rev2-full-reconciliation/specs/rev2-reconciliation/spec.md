# Capability: rev2-reconciliation

## ADDED Requirements

### Requirement: Rev2 carries the app's milestone layer

The Rev2 store SHALL hold the app's per-year priority milestones in a
`milestone` table keyed to the `annual_priority` instance, preserving the
milestone status vocabulary.

#### Scenario: milestones keyed to the year's priority

- **GIVEN** milestones exist for `P01` in FY2027
- **THEN** `milestone.priority_id` references the `annual_priority` row for
  (`priority_code='P01'`, `planning_period='FY2027'`), not a year's code in
  another period.

#### Scenario: milestone vocabulary preserved

- **THEN** `milestone.status` is constrained to ('Met','In progress','Not
  started','Missed'), matching the SQLite CHECK (ADR-0002).

### Requirement: Rev2 carries the app's config and audit layers

The Rev2 store SHALL hold `app_meta` (the engine-agnostic config the app reads)
and a real append-only `audit_log` (the change-management record every write
emits), so no read or write falls back to SQLite for these.

#### Scenario: AppMeta served from Rev2

- **WHEN** `DB_PROVIDER=mssql` and `current_plan_year()` /
  `dataset_provenance()` run
- **THEN** they read from Rev2 `app_meta`, with no sqlite fallback.

#### Scenario: audited write persists an audit row

- **WHEN** any audited write runs under `DB_PROVIDER=mssql`
- **THEN** a row is inserted into `audit_log` in the same transaction, and the
  prior `adopt-rev2-store` "error at the seam" behaviour is retired.

### Requirement: Rev2 carries the role and team metadata the app surfaces

The Rev2 store SHALL hold `role`, `person_role` and `source_area` mirroring the
app's `Roles`/`PeopleRoles`/`SourceAreas`, FK to Rev2 `person`.

#### Scenario: role membership resolvable

- **WHEN** the app asks whether a person is an admin under mssql
- **THEN** the answer comes from `person_role`+`role` for that person's Rev2 id,
  matching what SQLite's `PeopleRoles`+`Roles` return.

### Requirement: re-seed is reproducible and leaves the store consistent

Applying `008` and the extended seed SHALL be idempotent, reproducible
(`build_rev2_seed.py --check` clean), and leave `vw_integrity_report` clean.

#### Scenario: counts land

- **THEN** `cllrev2` holds 18 milestones, 3 app_meta rows, 7 roles, 22
  person_roles and 5 source_areas.
