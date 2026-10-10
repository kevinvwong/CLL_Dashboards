# Tasks: retire-the-closed-rev2-gaps

**Planning note:** this is a spec-only change. Three of the four tasks below
are verification and syncing; there is no application, migration or route work,
and no task touches code.

## 1. Sync

- [x] 1.1 Apply the delta to `openspec/specs/rev2-store/spec.md`: remove the requirement *"gaps are explicit, never silent"* with its two scenarios, and drop the "(subject to the Open issues in design.md)" parenthetical from *"DB_PROVIDER selects a working store"*'s *mssql renders every screen* scenario. (verify: `openspec validate --specs` passes; the main spec keeps 7 requirements and carries no delta operation headers.)
- [x] 1.2 Archive the change with `/opsx-archive`, which merges the delta into the main spec and moves it out of `changes/`.

## 2. Confirm the retirement is safe

- [x] 2.1 (verify) no test asserts the removed requirement: `grep -r "gaps are explicit" tests/ app/` returns nothing.
- [x] 2.2 (verify) the three gaps the requirement described are genuinely closed on the live store, re-reading the DDL rather than trusting this design's table:
  - `dbo.milestone` exists with `initiative_id` NOT NULL and 84 rows
  - `dbo.app_meta` exists and `port._appmeta` reads it under mssql with no sqlite fallback
  - `dbo.audit_log` exists from `008_app_layer.sql`
  Run against `cllrev2` via `db/mssql/apply.py`'s credential path; do not print credentials.
- [x] 2.3 (verify) the surviving self-contradiction is really gone: after syncing, `rev2-store` must not simultaneously say audit has no Rev2 table and that `recent_changes` reads `audit_log`. (`grep -n "audit" openspec/specs/rev2-store/spec.md` and read both hits.)

## 3. Gate

- [x] 3.1 `python -m pytest -q` Ã¢â‚¬â€ exit 0, no regression (the change is spec-only, so this is a guard, not a workload).
- [x] 3.2 Regenerate `docs/ops/PROGRESS_LOG.md` (`--check` clean) and commit it with the change.
- [x] 3.3 `openspec validate --strict` passes for the archived change and `--specs` passes for the main specs.
