# Design: rev2-full-reconciliation

## Context

The reconciliation (measured 2026-10-08) split cleanly: the D-1/Dean portfolio
the two stores share is byte-identical (0 title/owner/link diffs; the seed
generator reports `current`), while four app layers have no Rev2 table. The
decision is to close the coverage gap with an additive migration, not to re-seed
what already agrees.

## Decisions

### R1 — milestones belong to the Rev2 annual priority *instance*

SQLite keys `Milestones.PriorityID` to the priority *row*, which is already
`(PlanYear, Code)`-scoped (the 2026-10-08 multi-year fix). Rev2 has the same
split: `priority_definition` (reusable, by code) + `annual_priority` (per
`planning_period`). The port keys `milestone.priority_id` to the
`annual_priority` instance, so `P01`-FY2027's milestones never attach to another
year's `P01`. The seed resolves the mapping from the SQLite priority's
`(PlanYear, Code)` to Rev2's `PRI-<Code>-FY<year>`.

### R2 — audit is a real append-only table, not `validation_event`

Rev2's `validation_event` records validation-status transitions (the ADR-021 D9
addition), with an actor and a prior/new status. The app's `AuditLog` records
broad change-management (`action`, `entity_type`, `entity_key`, before/after
JSON, `reason`, `source`, `correlation_id`) — a different contract with no
prior/new status and free-text entity keys. Reusing `validation_event` would
force-fit the audit rows and lose the JSON/details. A dedicated `audit_log`
table preserves the app's shape one-for-one.

### R3 — new IDs are auto-generated; person/entity keys stay strings

Rev2 PKs are `VARCHAR` with no identity. For tables the app writes new rows into
(`audit_log`, `milestone`), the migration uses `INT IDENTITY` so the write path
does not generate string ids. `person_id`/`entity_key`/codes stay strings,
joining to Rev2 `person.person_id` (`PERS-N`) and `initiative_code`.

### R4 — additive, idempotent, recorded in DEVIATIONS

`008_app_layer.sql` follows the `001..007` pattern: `IF OBJECT_ID(...) IS NULL`
guards, batch-separated by GO, applied through `apply.py`. Because these tables
are project additions (not in the Rev2 package), each is recorded in
`db/mssql/DEVIATIONS.md` as an addition, same as D9's `validation_event`.

## Data volumes (from the live reconciliation)

| layer | sqlite rows | Rev2 target |
|---|---|---|
| Milestones | 18 | `milestone` 18 |
| AppMeta | 3 | `app_meta` 3 |
| AuditLog | 0 | `audit_log` 0 (schema only) |
| Roles / PeopleRoles | 7 / 22 | `role` 7 / `person_role` 22 |
| SourceAreas | 5 | `source_area` 5 |
| TeamInitiativeUpdates | 0 | `initiative_update` (already exists) |

## Risks

- **Cardinality triggers (`003`)**: new tables must not trip the K1/K2 rules;
  milestones/audit/etc. are not initiatives, so they do not. Verified by
  re-running `007_integrity_report.sql` after re-seed.
- **`People.IsAdmin`**: in SQLite it is a stored column; the role seams derive it
  per request from `PeopleRoles`+`Roles`. The port maps `People.PersonID` ->
  `PERS-N` and checks `person_role` at auth time (auth port is a separate later
  task; this change only lands the tables).
