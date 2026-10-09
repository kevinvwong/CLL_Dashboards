# Capability: rev2-store

## ADDED Requirements

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
- **THEN** each renders successfully with the same logical content as sqlite
  (subject to the Open issues in design.md).

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

### Requirement: gaps are explicit, never silent

Where a screen depends on an SQLite construct with no Rev2 equivalent
(milestones, AppMeta, audit), the change SHALL record the gap and give the screen
a defined interim behaviour, rather than failing silently or guessing.

#### Scenario: priorities screen under mssql

- **GIVEN** milestones have no Rev2 table
- **WHEN** `DB_PROVIDER=mssql`
- **THEN** the milestone-dependent read keeps its defined interim behaviour
  (sqlite-backed) and the gap is recorded in design.md and the change's tasks.

#### Scenario: audit write under mssql before an audit table exists

- **WHEN** a write runs under mssql while no audit target exists
- **THEN** it raises a clear error at the write seam rather than dropping the
  audit row silently.
