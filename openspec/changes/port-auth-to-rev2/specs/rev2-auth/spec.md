# Capability: rev2-auth

## ADDED Requirements

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

### Requirement: the Clerk link is carried on the Rev2 person row

`person_by_clerk_id` and `link_person_to_clerk` SHALL resolve and set the Clerk
link on `person.clerk_user_id` under mssql, and the link SHALL be unique where
present.

#### Scenario: an audited Clerk link resolves

- **WHEN** `link_person_to_clerk` runs under mssql and then
  `person_by_clerk_id` reads it back
- **THEN** the person resolves to the linked record.

#### Scenario: a null link is not a duplicate

- **GIVEN** several people have no Clerk link (`NULL`)
- **THEN** the filtered unique index permits it, as it does for the nullable
  business email (004 pattern).

### Requirement: the local PIN stopgap does not run against the production store

The local PIN stopgap is a development-only seam. Under mssql its credential
read/write SHALL fail loudly and actionably rather than silently appear to work,
and no credential material SHALL be stored in Rev2.

#### Scenario: PIN set/verify on mssql is refused, not ignored

- **WHEN** `set_person_pin` or `verify_person_pin` is called under mssql
- **THEN** it raises a clear error explaining the stopgap is local-only, and no
  credential is written to Rev2.

#### Scenario: Clerk remains the production identity

- **GIVEN** `DB_PROVIDER=mssql` and `AUTH_PROVIDER=clerk`
- **WHEN** a request is authenticated
- **THEN** identity comes from the verified Clerk session and the person is
  resolved from Rev2 — the PIN stopgap is not involved.