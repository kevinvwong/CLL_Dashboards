# Tasks: adopt-rev2-store

Order: 0 gates the rest (no port on an unverified schema); 1 is the dialect
plumbing everything uses; 2-5 are reads by screen group; 6 is the write seam;
7 is the gate. Each task commits independently and leaves `DB_PROVIDER=sqlite`
fully green.

## 0. Verify the live Rev2 schema before building on it

- [x] 0.1 Run `db/mssql/007_integrity_report.sql` against `cllrev2` via `DB_PROVIDER=mssql`; confirm it reports the expected state (no missing/extra objects). (0 defects — clean; vw_integrity_report present)
- [x] 0.2 Confirm every read model in `006_read_models.sql` exists on the live DB and projects the columns the port will read (list `vw_*` and compare). Record any drift as an Open issue, do not fix the live schema here. (all 11 views present, none missing/extra; card-view columns verified)
- [x] 0.3 Grep the live DB row counts (`initiative`, `goal`, `annual_priority`, `initiative_update`, `person`, `initiative_relationship`, …) and confirm they match the seed commit's claim (40 initiatives, 96 goal links, 62 priority links, 61 relationships). (exact match; initiative_update=0 — no diary seeded)

## 1. Dialect seam (plumbing only — no behaviour change)

- [x] 1.1 Add an `engine` tag to the connection (sqlite/mssql) so each read/write asks the connection, not `Config()`, which formulation to use. (`db.engine(conn)` — a `getattr(conn,'engine','sqlite')`; sqlite conn untouched)
- [x] 1.2 Add a tiny placeholder/dialect helper used by ported queries (e.g. `?`→`%s`, `date('now')`→T-SQL). Document it in `app/db.py` as the single place dialect differences live. (`db.DIALECT` + `db.dialect(conn)`; `app/port.py` is the single home for dual-engine SQL bodies)
- [x] 1.3 Add the `pymssql` error → `repo.RuleError` mapping at the write seam so mssql constraint failures raise actionable messages. (verify: sqlite suite green; a mssql smoke connect succeeds) (`repo._friendly_mssql` + dual-path `write()`; only integrity failures map, other errors propagate — verified by test_a_body_that_raises_mid_write_rolls_back)
- [x] 1.4 Confirm the sqlite suite (644) still passes with the seam in place but no query yet ported. (644 passed, 1 skipped; required killing the local uvicorn first so the reproducible-build test could rewrite the DB)

## 2. Home + taxonomy reads

- [x] 2.1 `goal_tiles` — goals + per-goal initiative count (Rev2: `goal` LEFT JOIN `initiative_goal`/`initiative`). (parity: counts 18/7/11/12/10 identical on both stores)
- [x] 2.2 `priority_tiles` — annual priorities + governed fields + count (Rev2: `annual_priority`). (code-keyed parity; PriorityName projected to the short name via canon.short_for_code; Rev2 has no Measure/Target/Cadence/Owner/Colour columns → None, UI falls back to canon)
- [x] 2.3 `blueprint_priorities` — composed over `priority_tiles` + canon; confirm colour/owner fields map. (no port code; verified composition works on both)
- [x] 2.4 `coverage_summary` — derived from 2.1/2.2; parity test. (no port code; verified 11/11 = 100% on both stores)
- [x] 2.5 `goal_by_number` / `priority_by_name`; `current_plan_year` / `plan_years` / `dataset_provenance` (AppMeta — keeps sqlite per Open issue 2, via `connect(provider="sqlite")` so the fallback never re-enters an mssql connection). (PlanYear projected to int 2027 from 'FY2027')
- [x] 2.6 **parity test** for this group. (tests/test_store_parity.py: 5 tests, all pass; skipped when MSSQL_* unset)

## 3. Cascade + index reads

- [x] 3.1 `goal_rows` — via `vw_goal_initiatives`. (parity: goals 1-5 identical)
- [x] 3.2 `priority_rows` — via `vw_priority_initiatives`. (canon.code resolves the short-name arg to a code; PriorityName/PlanYear normalized to app shape)
- [x] 3.3 `all_initiatives` — initiative list + collected goal/priority names. (vw_initiative_summary; tag dicts keyed by the row's InitiativeID so the caller joins identically)
- [x] 3.4 `all_people` — people + counts. (IsAdmin derived from person_role/PlatformAdmin to match auth.is_admin; PERS-N projected back to the app's int PersonID; a P11 TechnicalAdmin-is-not-admin nuance was caught by the parity test)
- [x] 3.5 **parity test** for the cascade screens. (5 new tests; vw_initiative_summary doesn't project active_flag — it pre-filters — so the port dropped the outer predicate)

## 4. Team-initiative layer reads

- [ ] 4.1 `team_overview`, `team_initiative_cards`, `goal_team_initiatives`, `team_detail`, `team_initiative_detail`.
- [ ] 4.2 `search` (the four per-kind queries) — translate LIKE expressions.
- [ ] 4.3 **parity test** for the team-initiative screens.

## 5. Card reads

- [ ] 5.1 `initiative_card` — details + goal/priority tags + contributes-to connections (`initiative_relationship`) + latest + diary (`initiative_update`).
- [ ] 5.2 `person_card` — via `vw_person_portfolio` (a person owning nothing still resolves).
- [ ] 5.3 `priority_detail`, `priority_outcomes` (milestone read stays sqlite per Open issue 1 — recorded, with a clear interim path), `tag_edit_options`, `link_edit_options`.
- [ ] 5.4 Meeting reads (`meeting_updates`, `update_deltas`, `attention_list`) — only if they reuse an already-ported read model; otherwise out of scope while MEETING_ENABLED=0. Record which.
- [ ] 5.5 **parity test** for initiative and person cards.

## 6. Writes

- [ ] 6.1 `add_progress_update` → `INSERT initiative_update` (resolve initiative id from the public `MI-###` / `initiative_code`).
- [ ] 6.2 `create/retire/restore` → `initiative` (`active_flag` for retire/restore).
- [ ] 6.3 `update_initiative_details` → `UPDATE initiative` (name/description).
- [ ] 6.4 `replace_tags` → replace `initiative_goal` + `initiative_priority` rows.
- [ ] 6.5 `replace_links` → replace `initiative_relationship` rows (D-1 → Dean).
- [ ] 6.6 `update_entry_description` → `UPDATE goal` / `UPDATE annual_priority`.
- [ ] 6.7 Audit rows → per Open issue 3, raise a clear error at the seam until the Rev2 audit target is decided; never drop silently. Record the decision task as follow-up.
- [ ] 6.8 **parity test**: write on mssql, confirm the card reflects it identically to a sqlite write. (verify: `RuleError` messages identical on both engines)

## 7. Gate + docs

- [ ] 7.1 Full sqlite suite (644) green.
- [ ] 7.2 Full Rev2 parity suite green against live `cllrev2`.
- [ ] 7.3 `openspec validate --strict` passes for this change.
- [ ] 7.4 Regenerate `docs/ops/PROGRESS_LOG.md` and assert it is current (`--check`).
- [ ] 7.5 Add one line to `docs/ops/DEPLOY.md` recording that flipping the store is a `DB_PROVIDER` env var, and that promoting Rev2 to the authoritative source remains a separate business-validation decision.
