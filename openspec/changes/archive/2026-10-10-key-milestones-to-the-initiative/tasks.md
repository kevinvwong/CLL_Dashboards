# Tasks: key-milestones-to-the-initiative

**Recorded as complete: this change documents work already implemented and
verified (migration `011` applied to live `cllrev2` 2026-10-09, both parity tests
green, full suite exit 0).** The tasks are the work as it was carried out, so the
change can be archived honestly.

## 1. Migration

- [x] 1.1 Write `db/mssql/011_milestone_initiative.sql`: add `initiative_id` (nullable, then NOT NULL), the four rollup columns with SQLite's CHECKs, move UNIQUE from `(priority_id, name)` to `(initiative_id, name)`, FK to `dbo.initiative`, and drop `priority_id` + its FK and default **last**. Idempotent, GO-batched.
- [x] 1.2 Delete the 18 unscoped rows (`DELETE ... WHERE initiative_id IS NULL`) rather than re-parenting them; the mock set has no defensible initiative.
- [x] 1.3 Register `011` **last** in `db/mssql/apply.py`'s `ORDER`, and update its docstring and `--help` from `001..007` to `001..011`.
- [x] 1.4 (verify) applied to live `cllrev2`: 18/18 batches, 0 failures; `initiative_id` NOT NULL, `uq_milestone_per_initiative` and `fk_milestone_initiative` present, all four CHECKs present, and `priority_id` / `fk_milestone_priority` / `uq_milestone_per_priority` gone.
- [x] 1.5 Record the deviation in `db/mssql/DEVIATIONS.md` (011 section) and mark `008_app_layer.sql`'s table as superseded by `011`.

## 2. Seed

- [x] 2.1 Re-key `db/build_rev2_seed.py`'s milestone section to `initiative_id` (`INI-<MIId>`), emitted once per initiative, carrying the weight columns.
- [x] 2.2 Point `build_rev2_seed.py`'s D-1 activation read at `vw_TeamInitiativeStatus` (status is derived).
- [x] 2.3 Order the milestone `INSERT`s by `m.MilestoneID` so the Rev2 `IDENTITY` assignment follows the register clause order — the tie-break both stores' `ORDER BY`s can agree on.
- [x] 2.4 (verify) `python db/build_rev2_seed.py` and `--check` clean (reproducible).
- [x] 2.5 Apply the regenerated seed to live `cllrev2` (84 rows across 29 initiatives, 0 null weights, 12 needs_rewrite), deleting the old rows first because the idempotent guards would otherwise leave the stale order in place.

## 3. Ports

- [x] 3.1 Re-point `app/port.py`'s three mssql branches (`milestones_for_year`, `priority_outcomes`, `telemetry`) through `initiative_priority`, de-duplicated at read time.
- [x] 3.2 Add the missing `NeedsRewrite` count to telemetry's mssql branch so the indicator no longer differs between stores.
- [x] 3.3 Correct `db/README.md`: the T-SQL equivalent of `seed_sample.sql` now exists (`db/seed_rev2.sql`) and the views are verified against real rows.

## 4. Ordering parity

- [x] 4.1 (verify) diagnose the P01 failure by dumping `(id, sort_order, name)` from both stores and diffing the sequences — same 15 names, same statuses, different order.
- [x] 4.2 Confirm the cause is the tie-break, not the data or the migration: `MilestoneID 7,10,38,40,70` on sqlite vs `33,48,51,95,97` on mssql for the same five rows, and `milestone_id` is `INT IDENTITY` per the `008` DDL (not VARCHAR, despite port.py's comment).
- [x] 4.3 Document the constraint in `db/build_rev2_seed.py`, `db/mssql/DEVIATIONS.md` and this change's design.md, so a future regeneration that sorts differently fails with identical data rather than silently.
- [x] 4.4 (verify) ordering invariant holds for all six priorities (P01 15, P02 27, P03 20, P04 39, P05 20, P06 26 — identical names, counts and sequences).

## 5. Gate

- [x] 5.1 Full suite green (pytest exit 0) with both parity tests passing against the live store.
- [x] 5.2 `openspec validate --specs` passes after the delta is synced into the main specs.
- [x] 5.3 Regenerate `docs/ops/PROGRESS_LOG.md` (`--check` clean).
