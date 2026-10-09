# Proposal: Port the remaining active surfaces to Rev2

## Why

`adopt-rev2-store` ported the seam and the principal reads and writes, and its
parity tests prove every *ported* function returns identical results on both
stores. But a direct audit of `app/queries.py` after the write port landed shows
six active surfaces still execute the SQLite schema's SQL and would 500 under
`DB_PROVIDER=mssql`:

- `initiative_signals` — the home page's current-progress strip.
- `relationships_for` — the cascade's "contributes to" rows.
- `dean_initiatives` and `team_initiative_dean_links` — the `/dean-priorities` layer.
- `recent_changes` — `/changes`, reading the change log (now `audit_log` on Rev2,
  post-reconciliation).
- `data_checks` — `/checks`, the data-quality view.

The prior change's parity tests passed precisely because they never called these.
This follow-on closes the surface so the deploy runbook's claim — "flipping the
store is one `DB_PROVIDER` env var" — is actually true.

## What changes

- Port the six functions in `app/port.py`, each returning the app's existing key
  shape, and wire them in `app/queries.py`:
  - `initiative_signals` → `vw_initiative_summary` (+ Reporting Owner), latest
    update derived (`vw_latest_update`).
  - `relationships_for` → `initiative_relationship` (D-1 `Supports`/`Contributes To`
    → Dean), keyed by the public `MI-###`.
  - `dean_initiatives` → `initiative` where `initiative_level='Dean'`, with its
    priority edge (`initiative_priority`) and the D-1 roll-up from
    `initiative_relationship`.
  - `team_initiative_dean_links` → `initiative_relationship` joined to the Dean row.
  - `data_checks` → `initiative` NOT EXISTS `initiative_goal` /
    `initiative_priority` (the same two checks `vw_DataChecks` encodes).
  - `recent_changes` → `audit_log` joined to `person`.
- Extend `tests/test_store_parity.py` to cover all six, so the surface is proven
  end-to-end rather than per-function.

## Non-goals

- The meeting surface (`meeting_updates`, `update_deltas`, `attention_list`,
  `meeting` route) stays ICED (`MEETING_ENABLED=0`, recorded in
  `adopt-rev2-store` task 5.4). It is untouched here; re-enabling it is a
  separate decision.
- `blueprint_priorities`, `coverage_summary`, and the pure-Python groupers
  (`split_for_list`, `group_rows`, `status_counts`, `rollup_label`) are
  engine-agnostic compositions over already-ported reads; unchanged.
- No UI or schema changes. Dean progress is independently computed in the app
  (not a rolled-up aggregate, per the standing "no aggregate parent progress"
  rule) and is left NULL on Rev2's `initiative` row exactly as the card reads
  imply; the Dean page's `percent_complete` reads NULL there too, matching the
  no-self-reported-Dean-diary reality.

## Success

Under `DB_PROVIDER=mssql`, every route renders live data with no app-model SQL
left in the read path, and the parity suite proves the six surfaces match sqlite
exactly; the sqlite suite stays green.
