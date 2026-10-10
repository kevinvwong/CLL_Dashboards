# Proposal: Specify the passcode person resolution under mssql

## Why

`rev2-auth`'s stated purpose is that "an authenticated request behaves
identically under either `DB_PROVIDER`". Its scenarios do not prove that.

The capability has one scenario asserting a person resolves from Rev2 —
*"a signed-in person resolves on mssql"* — and its GIVEN is **a person carrying
a Clerk session**. Clerk is development-only (ADR-0006): every deployed
environment runs `AUTH_PROVIDER=local`, the shared passcode plus person picker.
So the only scenario proving cross-provider equivalence for person resolution
covers the path that does not run in production, and the path that does run has
no scenario at all.

This is a coverage gap, not a defect. `current_person` does resolve the
passcode-selected person through the store seam (`port.auth_person`), so the
behaviour the spec should be pinning already exists. What is missing is the
scenario that would fail if someone broke it — which matters most for the
deployed path, because that is the one a board would hit if Rev2 is promoted.

## What Changes

- **MODIFIED** — *"authentication resolves people and roles on the selected
  store"* in `rev2-auth`, adding a scenario that resolves a
  passcode-authenticated person under `DB_PROVIDER=mssql` and
  `AUTH_PROVIDER=local`.
- No application, schema or route change. `port.auth_person` already serves
  both engines; this change pins the behaviour the spec was silent about.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rev2-auth`: adds the missing scenario for the deployed authentication path,
  so the capability's stated cross-provider equivalence is actually demonstrated
  rather than asserted only of the Clerk development path.

## Impact

- **Specs only.** `openspec/specs/rev2-auth/spec.md`, one scenario added to an
  existing requirement.
- No test changes. `tests/test_store_parity.py` already compares both stores;
  a parity assertion over `current_person` could be added later if the team
  wants executable coverage, but that is a test change and out of scope here.
