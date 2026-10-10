# Capability: rev2-reconciliation

## MODIFIED Requirements

### Requirement: Rev2 carries the app's milestone layer

The Rev2 store SHALL hold the app's per-year milestones in a `milestone` table
keyed to the TEAM INITIATIVE (`initiative_id` FK -> `dbo.initiative`), never to
an annual priority, and SHALL carry the weight columns the attainment rollup
reads. The priority a milestone appears against is derived at read time by
joining `initiative_priority`.

#### Scenario: milestones keyed to the year's priority

- **GIVEN** milestones exist for `P01` in FY2027
- **THEN** they are **not** keyed to an annual priority — `priority_id` no
  longer exists on `dbo.milestone` — and each row's `initiative_id` references
  the `dbo.initiative` row (`initiative_level='D-1'`) that owns the register row.
  `P01`'s milestone list is derived at read time by joining
  `initiative_priority`, de-duplicated.

#### Scenario: milestone vocabulary preserved

- **THEN** `milestone.status` is constrained to ('Met','In progress','Not
  started','Missed'), matching the SQLite CHECK (ADR-0002).

#### Scenario: rollup inputs match the app's schema

- **THEN** `weight`, `weight_basis`, `weight_source` and `needs_rewrite` are
  present with the SQLite CHECKs (`weight > 0`; `weight_basis` IN
  ('headline-quant','headline-gate','headline-soft','support-quant',
  'support-gate','support-soft'); `weight_source` IN ('inferred','confirmed')),
  so both stores carry identical rollup inputs.

#### Scenario: an initiative feeding two priorities stores its milestones once

- **GIVEN** an initiative feeds both `P02` and `P04`
- **THEN** its milestone set is stored **once**, and the priority-level expansion
  happens at read time by joining `initiative_priority`, de-duplicated so a
  milestone is not counted into both priorities twice.

### Requirement: re-seed is reproducible and leaves the store consistent

Applying `008` + `011` and the extended seed SHALL be idempotent, reproducible
(`build_rev2_seed.py --check` clean), and leave `vw_integrity_report` clean. A
milestone read SHALL return the same rows in the same **sequence** on both
stores, which constrains the seed's insert order.

#### Scenario: counts land

- **THEN** `cllrev2` holds 84 milestones across 29 D-1 initiatives, 3 app_meta
  rows, 7 roles, 22 person_roles and 5 source_areas.

#### Scenario: the two stores agree on sequence, not just content

- **WHEN** `port.milestones_for_year` runs under sqlite and under mssql for the
  same plan year
- **THEN** each priority's milestone list is identical in name, status **and
  order**, not merely as a set.

## ADDED Requirements

### Requirement: Milestone ordering parity does not depend on a store-local id

SQLite tie-breaks a priority's milestones on `MilestoneID` (a rowid following
the register's clause order); Rev2 tie-breaks on `milestone_id` (an `INT
IDENTITY` assigned by the seed's insert order). Neither id is derivable from the
data, so the two stores agreeing on an ordered result SHALL require the seed to
insert milestones in the app's `MilestoneID` order. Ordering parity is a property
of the **seed**, not of the read query, and SHALL be documented wherever the seed
is generated.

#### Scenario: seed inserts in MilestoneID order

- **WHEN** `db/build_rev2_seed.py` emits the milestone section
- **THEN** milestones are ordered by `m.MilestoneID`, so the Rev2 `IDENTITY`
  assignment follows the same sequence as SQLite's rowids and the two `ORDER BY`s
  coincide.

#### Scenario: identical data in a different sequence is a tie-break defect

- **GIVEN** the same milestone names and statuses are present on both stores but
  in a different order
- **THEN** the defect is in the ordering tie-break or the seed's insert order —
  **not** in the migration or the data — and the diagnostic is to diff
  `(id, sort_order, name)` from both stores before changing either.

#### Scenario: re-running the seed does not repair a wrong order

- **GIVEN** milestones already exist on the store with ids assigned in a stale
  order
- **THEN** re-running the idempotent seed leaves them in place, so the rows must
  be deleted and re-inserted for a new insert order to take effect (`dbo.milestone`
  has no inbound FKs — verify first).
