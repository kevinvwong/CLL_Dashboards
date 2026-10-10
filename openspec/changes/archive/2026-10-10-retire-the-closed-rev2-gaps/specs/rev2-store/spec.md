# Spec Delta

## REMOVED Requirements

### Requirement: gaps are explicit, never silent

**Reason**: The requirement records three gaps in the Rev2 store — milestones,
AppMeta, audit — and prescribes an interim behaviour for each. All three were
closed by `rev2-full-reconciliation`: `008_app_layer.sql` created
`dbo.app_meta` and `dbo.audit_log` (and `role`/`person_role`/`source_area`), and
`011_milestone_initiative.sql` created `dbo.milestone` keyed to the initiative.
Retiring it removes a requirement that asserts the port is permanently partial,
and removes the contradiction with this capability's own requirement "the change
log reads the Rev2 audit store", which already requires `recent_changes` to read
`audit_log` "(reconciled in `008`)".

**Migration**: None required — no application, schema or route behaviour is
affected. `port._appmeta` reads `dbo.app_meta` on both engines with no sqlite
fallback; `port.milestones_for_year` is fully ported through
`initiative_priority`; `recent_changes` reads `dbo.audit_log`. Consumers of the
old interim behaviour have none.

## MODIFIED Requirements

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
