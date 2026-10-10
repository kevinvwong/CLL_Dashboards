# rev2-store Specification

## Purpose

The app talks to its data through one seam (`app/port.py`), so the same screens
and writes run against the local SQLite file during development and against the
production Rev2 SQL Server without any per-screen branching.

This capability is what makes the production migration a configuration change
rather than a rewrite, and it is also what makes the store differences
*checkable*: the parity suite asserts the two providers return identical results,
so a divergence is a test failure rather than something a board discovers.

## Requirements

### Requirement: DB_PROVIDER selects a working store

The application SHALL select its data store from `DB_PROVIDER` (`sqlite` |
`mssql`) at a single seam (`app/db.py connect()`), and SHALL render every screen
and accept every write identically under either provider.

#### Scenario: default stays sqlite, unchanged

- **GIVEN** `DB_PROVIDER` is unset or `sqlite`
- **WHEN** the app serves any screen or write
- **THEN** it behaves byte-for-byte as before this change, and the existing
  sqlite test suite passes unmodified.

#### Scenario: mssql renders every screen

- **GIVEN** `DB_PROVIDER=mssql` and `MSSQL_*` point at the live `cllrev2`
- **WHEN** every screen is requested
- **THEN** each renders successfully with the same logical content as sqlite.

#### Scenario: a single, named dialect seam

- **GIVEN** any read or write function
- **THEN** its engine choice is made at one seam (the connection's engine tag),
  and no route handler or template contains an engine-conditional.

### Requirement: reads produce identical results across providers

Each ported read in `app/queries.py` SHALL return the same keys and values on
mssql as on sqlite for the same logical data, by aliasing on select where the two
schemas name a field differently.

#### Scenario: card parity

- **GIVEN** an initiative present in both stores
- **WHEN** `initiative_card` is called under each provider
- **THEN** the returned details, tags, connections, latest progress and diary are
  equal (same keys and values).

#### Scenario: read models are the source for matching cards

- **GIVEN** the goal, priority or person card
- **WHEN** read under `DB_PROVIDER=mssql`
- **THEN** its rows come from the corresponding Rev2 read model
  (`vw_goal_initiatives` / `vw_priority_initiatives` / `vw_person_portfolio`),
  so the documented Rev2 contract and the app agree by construction.

#### Scenario: current progress is derived

- **WHEN** any read needs an initiative's current progress or status
- **THEN** it is taken from the latest update (`vw_latest_update` /
  `vw_initiative_current`), never from a stored cache column.

#### Scenario: the full-page card renders its header once

- **GIVEN** the full-page team-initiative route requested directly (not as an
  HTMX fragment)
- **WHEN** the page renders
- **THEN** the initiative's code, level, name and description each appear
  **exactly once**, the page's `h1` precedes the content it titles, and the Dean
  initiatives it contributes to are listed once — sourced from the shared card
  fragment, which carries the linkable codes, rather than a second names-only
  copy appended below.

#### Scenario: the drawer fragment keeps its own header

- **GIVEN** the same route requested with `HX-Request` so the bare fragment is
  returned for the drawer
- **WHEN** the fragment renders
- **THEN** it still carries its own code, title and close control, because the
  drawer has no page heading to inherit.

### Requirement: the current owner is the primary Reporting Owner

Where a read needs an initiative's owner, the mssql formulation SHALL use
`vw_primary_reporting_owner` (`ownership_role='Reporting Owner'`,
`primary_flag=1`, `effective_end IS NULL`).

#### Scenario: a person owning nothing still resolves

- **WHEN** `person_card` is read under mssql for a person with no active
  ownership
- **THEN** they still resolve to a meaningful row (anchored on `person`,
  work LEFT JOINed), as `vw_person_portfolio` guarantees.

### Requirement: writes stay append-only, transactional, and actionable

Each write in `app/repo.py` SHALL run as one transaction under either provider,
remain append-only, and map integrity failures to the same actionable `RuleError`
messages on both engines.

#### Scenario: progress update parity

- **WHEN** `add_progress_update` runs under each provider for the same initiative
- **THEN** one `initiative_update` row is appended in each, and the card's
  current progress reflects it identically.

#### Scenario: retire/restore parity

- **WHEN** `retire_initiative` / `restore_initiative` run under mssql
- **THEN** the initiative's `active_flag` flips and it disappears from / returns
  to every list and card, as on sqlite.

#### Scenario: constraint error is still human-readable

- **WHEN** a write violates a rule under mssql (e.g. percent out of range)
- **THEN** the raised `RuleError` carries the same message as under sqlite.

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
