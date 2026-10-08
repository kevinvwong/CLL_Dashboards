# Tasks: rev2-full-reconciliation

## 1. Migration

- [x] 1.1 Write `db/mssql/008_app_layer.sql`: `app_meta`, `audit_log`, `role`, `person_role`, `source_area`, `milestone` (INT IDENTITY PKs for the two the app appends to; VARCHAR keys for the rest; FK to Rev2 `person`). Idempotent, GO-batched.
- [x] 1.2 Register `008` in `db/mssql/apply.py`'s batch list.
- [x] 1.3 Record the additions in `db/mssql/DEVIATIONS.md` (same convention as D9's `validation_event`).

## 2. Seed

- [x] 2.1 Extend `db/build_rev2_seed.py` to emit `app_meta`, `role`/`person_role`, `source_area`, and `milestone` (resolving SQLite `(PlanYear,Code)` -> `PRI-<Code>-FY<year>`; `audit_log` schema only).
- [x] 2.2 `python db/build_rev2_seed.py` and confirm `--check` clean (reproducible).
- [x] 2.3 Apply `008` + re-seed to live `cllrev2` via `DB_PROVIDER=mssql` + apply.py.
- [x] 2.4 (verify) counts land: 18 milestones, 3 app_meta, 7 roles, 22 person_roles, 5 source_areas; `vw_integrity_report` stays clean.

## 3. Close the adopt-rev2-store Open issues this removes

- [x] 3.1 Switch `port._appmeta` from the sqlite fallback to the Rev2 `app_meta` read; drop the `provider="sqlite"` fallback for it. Update the two parity tests.
- [x] 3.2 Point `repo._audit` at Rev2 `audit_log` under mssql (remove the task-6.7 "raise at the seam" interim). 
- [x] 3.3 Note in `adopt-rev2-store/design.md` Open issues 1-3 are now resolved by this change (milestones/appmeta/audit have tables; the priorities-screen milestone read can port).

## 4. Gate

- [x] 4.1 sqlite suite green (no regression).
- [x] 4.2 A parity test asserts milestone set + app_meta values equal on both stores.
- [x] 4.3 `openspec validate --strict` passes for both changes.
- [x] 4.4 Regenerate `docs/ops/PROGRESS_LOG.md`; `git checkout -- cll_initiatives.db` if the reproduce test dirtied it.
