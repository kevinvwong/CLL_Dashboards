# Proposal: Port the authentication surface to Rev2

## Why

The Rev2 store port is complete for the read and write data surfaces
(`adopt-rev2-store`, `rev2-remaining-surfaces`, `rev2-full-reconciliation`), but
the **authentication layer** still bypasses the seam: `app/auth.py` issues
SQLite-shaped SQL directly (`People`, `PeopleRoles`, `Roles`, `?` placeholders).
Under `DB_PROVIDER=mssql` even logging in 500s — the port does not actually let
the app *run* on Rev2, and the deploy runbook's "one env var" claim is false for
any authenticated request.

Auth is the last un-ported surface. It has one genuine modeling fork: the **local
PIN credential** (`People.Credential`) and the **Clerk link** (`People.ClerkUserID`)
have no Rev2 column on `person`. The role stores, by contrast, were reconciled in
`rev2-full-reconciliation` (`role`/`person_role`), so the permission surface ports
cleanly.

**Decision (2026-10-08): the local PIN stopgap is dev-only and does NOT port.**
Rev2 carries the Clerk link only; there is no credential column and no secret in
Rev2 at all. Rationale: the stopgap exists for local development, production runs
Clerk (ADR-0004), and a PBKDF2 hash is still a secret material worth keeping out of
the production data store. Under mssql the PIN set/verify paths raise a clear,
actionable error instead of silently degrading. The alternative considered —
adding `person.credential_hash`/`clerk_user_id` columns (010_auth.sql) — was
rejected in favour of not carrying the secret.

## What changes

- **Reads → Rev2 `person`.** `person_exists`, `current_person`'s person lookup,
  `active_people`, and `get_initiative` read `dbo.person` (active, by `PERS-N`
  or the int the cookie carries) and `dbo.initiative`. The app-facing dict keeps
  the app's key names (`PersonID` int, `Name`, `Title`).
- **Roles → `person_role` + `role`.** `roles_of`, `_role_ids`, `is_admin`,
  `is_executive_sponsor`, `is_operator`, `is_data_owner`, `has_capability` resolve
  from the reconciled role store, identical semantics.
- **Clerk link only.** `person_by_clerk_id` / `link_person_to_clerk` need
  `person.clerk_user_id`, added by a one-column additive `010_auth.sql` with a
  filtered unique index (`WHERE clerk_user_id IS NOT NULL`, the same pattern 004
  used for the nullable email). The Clerk link is an *identifier*, not a secret,
  so it belongs on `person`.
- **PIN refused on mssql.** `person_credential` / `set_person_pin` /
  `verify_person_pin` raise a clear RuleError under mssql (dev-only seam), so the
  stopgap can never appear to work against the production store.
- Wire `auth.py` to route these through `app/port.py` per engine, exactly as the
  data surfaces do. The Clerk adapter (`clerk_auth.py`, which talks to Clerk's API,
  not the DB) is unchanged; only the local-person resolution moves stores.

## Non-goals

- **No auth model change.** The seams stay: `AUTH_PROVIDER` (local/clerk), ADR-0004,
  and the local-stopgap PIN. This ports the storage, not the design.
- **No permission model change.** DR-05/DR-23 role/capability semantics are
  preserved exactly; only where the rows live changes.
- **The PIN stopgap stays sqlite-only** (the decision above); it is not
  "reimplemented" on Rev2.
- **No UI changes**; sign-in surfaces are untouched.

## Success

Under `DB_PROVIDER=mssql`, the authenticated request path — Clerk identity
resolution, person lookup, role-based guards, and Clerk linking — works on Rev2
with the same messages and permissions as sqlite; a PIN attempt under mssql
fails loudly rather than silently; the parity suite covers the auth reads; the
sqlite suite stays green.
