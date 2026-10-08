# Capability: rev2-store

## ADDED Requirements

### Requirement: every active read surface runs on the selected store

No active UI surface SHALL execute app-model (SQLite) SQL when `DB_PROVIDER=mssql`.
Each remaining read (`initiative_signals`, `relationships_for`, `dean_initiatives`,
`team_initiative_dean_links`, `data_checks`, `recent_changes`) SHALL source from
the Rev2 schema and read models and return the app's existing key set.

#### Scenario: surfaces render on mssql

- **GIVEN** `DB_PROVIDER=mssql` and the reconciled `cllrev2`
- **WHEN** the home, cascade, `/dean-priorities`, `/checks` and `/changes`
  surfaces render
- **THEN** none of them raises an app-model "no such table/view" error, and each
  returns the same logical content as sqlite.

#### Scenario: parity on the remaining surfaces

- **WHEN** each of the six functions runs under both providers against the
  reconciled seed
- **THEN** the returned rows agree (same keys and values), proven by the parity
  suite — not only the previously-ported functions.

### Requirement: the Dean layer is sourced from initiative_relationship

The `/dean-priorities` read (`dean_initiatives`, `team_initiative_dean_links`)
SHALL resolve each Dean initiative and its D-1 roll-up from `initiative` +
`initiative_relationship` on mssql, matching the merged model's direction
(a D-1 contributes to the Dean rows it supports).

#### Scenario: roll-up names the contributing D-1 initiatives

- **WHEN** a Dean FY27 row is read under mssql
- **THEN** it lists the D-1 initiatives it contributes to, in the same shape as
  sqlite's `vw_DeanInitiatives` roll-up.

### Requirement: the change log reads the Rev2 audit store

On mssql, `recent_changes` SHALL read `audit_log` (reconciled in `008`), so the
`/changes` screen reflects the store the app is actually writing to.

#### Scenario: an audited write appears in /changes on mssql

- **WHEN** a write runs under `DB_PROVIDER=mssql` and `/changes` renders
- **THEN** the new change appears, sourced from `audit_log`.

#### Scenario: empty audit log renders, not errors

- **GIVEN** the reconciled seed has no audit rows yet
- **THEN** `/changes` under mssql returns an empty list rather than failing.
