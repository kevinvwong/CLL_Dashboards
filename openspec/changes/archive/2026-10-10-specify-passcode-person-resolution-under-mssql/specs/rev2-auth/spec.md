# Spec Delta

## MODIFIED Requirements

### Requirement: authentication resolves people and roles on the selected store

The authentication layer SHALL resolve people, active status and role membership
from the configured store, so an authenticated request works under either
`DB_PROVIDER` with the app's key shape and identical role semantics.

#### Scenario: a signed-in person resolves on mssql

- **GIVEN** `DB_PROVIDER=mssql` and a person carrying a Clerk session
- **WHEN** the request resolves the current person
- **THEN** it reads `dbo.person` and returns the app's key shape
  (`PersonID`, `Name`, `Title`), not a driver error.

#### Scenario: role-based guards agree across stores

- **WHEN** `is_admin`, `is_executive_sponsor`, `is_data_owner`, `is_operator`
  and `has_capability` run under each provider for the same person
- **THEN** each answers identically, because roles come from the same reconciled
  role store (`role` + `person_role`) on both engines.

#### Scenario: the person picker lists the active people

- **WHEN** the sign-in surface lists people under mssql
- **THEN** `active_people` returns the Rev2 active people, and `person_exists`
  resolves an id on the store in use.

#### Scenario: a passcode-selected person resolves under mssql

- **GIVEN** `DB_PROVIDER=mssql`, `AUTH_PROVIDER=local` (the deployed
  configuration), and a session authenticated by the shared passcode with a
  person selected from the picker
- **WHEN** the request resolves the current person
- **THEN** it reads `dbo.person` through the store seam for the selected
  `PersonID` and returns the app's key shape, with no sqlite fallback — the
  same resolution the Clerk path performs, from the store in use.
