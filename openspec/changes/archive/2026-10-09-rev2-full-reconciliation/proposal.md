# Proposal: Complete the Rev2 reconciliation (carry the four layers Rev2 lacks)

## Why

`adopt-rev2-store` ports the app onto Rev2 *as it exists*. But a measured
reconciliation (2026-10-08) shows the shared portfolio data is in sync while
four layers of the app's model have **no Rev2 equivalent at all**:

- **Milestones** (18 rows) — the checkable events per plan-year priority that
  drive the priorities screen and the meeting agenda.
- **AppMeta** (3 rows) — the engine-agnostic config the app reads
  (`current_plan_year`, `dataset_provenance`), which the port currently falls
  back to *sqlite* for even under `DB_PROVIDER=mssql`.
- **AuditLog** — the change-management record every write produces; with no
  Rev2 audit target, a ported write must error rather than drop the record.
- **Roles / PeopleRoles** (7 / 22 rows) — the application's role vocabulary the
  auth seam reads (`People.IsAdmin` is derived per role), plus **Teams** and
  **SourceAreas** metadata the team-initiative screens carry.

Without these, "run on Rev2" is permanently partial: the priorities screen, the
person/role surfaces, and every audited write still depend on SQLite. This change
adds the missing Rev2 tables and extends the seed to fill them, so the port can
cover the whole surface. It sits between `adopt-rev2-store`'s seam (done) and its
write ports (which need a real audit table to land).

## What changes

- **New Rev2 migration `db/mssql/008_app_layer.sql`**, applied batch-by-batch
  through the existing `db/mssql/apply.py` and added to its batch list. Tables:
  - `app_meta (key, value)` — mirrors `AppMeta`.
  - `audit_log (audit_id identity, created_at, person_id, action, entity_type,
    entity_key, details, reason, source, correlation_id)` — mirrors `AuditLog`,
    person FK to Rev2 `person`. Append-only.
  - `role (role_id, name unique, description)` and `person_role (person_id,
    role_id)` — mirror `Roles`/`PeopleRoles`, FK to Rev2 `person`.
  - `milestone (milestone_id identity, priority_id FK -> annual_priority,
    name, status CHECK(Met/In progress/Not started/Missed), planned_date,
    date_met, owner_label, evidence_url, sort_order, active_flag,
    UNIQUE(priority_id, name))` — mirrors `Milestones`, keyed to the Rev2 annual
    priority instance. ADR-0002 vocabulary preserved verbatim.
  - `source_area (source_area_id, name unique)` — mirrors `SourceAreas`
    (Teams already exist as Rev2 `team`).
- **Seed extension** in `db/build_rev2_seed.py`: emit `app_meta`, `audit_log`
  (none yet — schema only), `role`/`person_role`, `source_area`, `milestone`,
  resolving each milestone's SQLite `Priorities.PriorityID` `(PlanYear, Code)` to
  Rev2 `annual_priority.priority_id` `PRI-<Code>-FY<year>`.
- **Re-apply to the live `cllrev2`** and re-seed; verify counts (18 milestones,
  3 app_meta, 7 roles, 22 person_roles, 5 source_areas) land.

## Non-goals

- **Not changing the existing `001..007` port** or its read models; this is an
  additive `008`.
- **Not altering `adopt-rev2-store`'s read ports** beyond closing its four
  recorded Open issues: the AppMeta sqlite fallback is replaced by a real Rev2
  read, and the audit "error at the seam" becomes a real insert.
- **No UI changes.**

## Success

`cllrev2` holds milestones, AppMeta, audit, roles and source areas; the seed is
reproducible (`--check` clean); the port can read every screen from Rev2 and
write with a durable audit record; and the reconciliation is recorded as
"shared data verified identical + the four coverage gaps closed", not as a
suspected content drift.
