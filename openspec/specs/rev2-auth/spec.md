# rev2-auth Specification

## Purpose

Authentication resolves a person and their role membership from whichever store
is configured, so an authenticated request behaves identically under either
`DB_PROVIDER`.

The identity *mechanism* is deliberately boring right now: a single shared
passcode followed by a person picker, with no per-person secret stored anywhere.
That is an accepted interim risk recorded in ADR-0006, not a designed property -
anyone holding the passcode can select any person, including `PlatformAdmin`. GT
Entra is the actual destination for production identity. This capability exists
to pin the property that makes the interim state acceptable at all: the app
holds no per-person credential to leak.

## Requirements

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

### Requirement: the shared passcode is the stopgap, and it stores no per-person secret

Identity in every deployed environment is a single shared passcode followed by a
person picker. It SHALL NOT store, hash, or compare any per-person credential, and
no credential material SHALL be stored in Rev2.

> **Re-scoped 2026-10-09.** This requirement previously read "the local PIN
> stopgap does not run against the production store" and specified
> `set_person_pin` / `verify_person_pin` refusing under mssql. That behaviour was
> **deleted outright** rather than disabled: the per-person PIN, its schema
> column, its hashing helpers, its routes and its tests are all gone.
>
> The requirement is retained, not deleted, because the *property* it protects is
> still the reason this auth design is acceptable for a governing board: **the
> app holds no per-person secret at all.** Under the old shape the safety
> argument was "the PIN never reaches the production store." Under the current
> shape it is stronger and simpler — there is nothing to leak, anywhere. Losing
> the requirement would lose that argument.
>
> Keeping the refusal scenario would have published a requirement describing
> functions that no longer exist; it is dropped rather than left to mislead a
> future reader about the auth surface.

#### Scenario: no per-person credential is stored anywhere

- **GIVEN** the schema for either provider
- **THEN** the `People` table carries no credential column, and the store exposes
  no set-or-verify-per-person credential function.

#### Scenario: anyone with the shared passcode may select any person

- **GIVEN** a session authenticated by the shared passcode
- **WHEN** the user selects a person from the picker
- **THEN** any active person may be selected, including `PlatformAdmin`.

> This is an **accepted interim risk**, not a designed property. It is recorded
> in ADR-0006 and is why GT Entra provisioning is the actual destination for
> production identity. Recorded here so that a future reader does not mistake it
> for intended behaviour and preserve it on purpose.

#### Scenario: Clerk remains available as a development-only adapter

- **GIVEN** `DB_PROVIDER=mssql` and `AUTH_PROVIDER=clerk`
- **WHEN** a request is authenticated
- **THEN** identity comes from the verified Clerk session and the person is
  resolved from Rev2 — the shared passcode is not involved.

> **Renamed and re-scoped 2026-10-08** (ADR-0006). This scenario previously read
> "Clerk remains the **production** identity", which recorded a decision that has
> since been reversed on cost grounds: no Clerk production instance is being
> purchased, and every deployed environment runs `AUTH_PROVIDER=local` until
> Entra is provisioned into the GT tenant. The *behaviour* above is unchanged and
> still correct — Clerk remains a supported adapter, used for development. What
> changed is the claim about which provider production runs, so the requirement
> now says what is true: available, and not production.
