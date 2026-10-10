# Design: specify-passcode-person-resolution-under-mssql

## Decision 1 — MODIFIED, not ADDED

The behaviour being pinned is not new. `current_person` resolves the
passcode-selected person through `port.auth_person` on the store in use, exactly
as the Clerk branch resolves `person_by_clerk_id`. Nothing is being added; a
scenario is being supplied for an existing requirement.

So the requirement is MODIFIED and its existing three scenarios are carried
verbatim. Using ADDED for a scenario belonging to an existing requirement would
either duplicate the requirement or leave the original without it.

## Decision 2 — the scenario asserts the deployed path, not a new one

The GIVEN names `AUTH_PROVIDER=local` explicitly, because that is what makes the
scenario different from the Clerk one and worth writing: it is the configuration
every deployed environment actually runs (DEPLOY.md, identity section). A
scenario that omitted it would be ambiguous about which path it covers and could
be satisfied by the Clerk branch.

It also asserts **no sqlite fallback**, because that is the property a future
refactor is most likely to break — reintroducing a fallback would leave both
engines reading their own store while quietly answering from the wrong one.
`test_store_parity.py` already asserts this shape for `_appmeta`; the same
property for person resolution is what this pins.

## Decision 3 — scope stays at the spec

This adds a scenario to a spec, which is a statement of required behaviour. It
does not add a test. The distinction matters: a spec change says the behaviour
must hold, a test change proves it does. `test_store_parity.py` is the natural
home for an executable version, but adding one is a test change with its own
blink radius and belongs in its own change.

The tasks therefore include a verification task — confirming the scenario's claim
is already true on both stores — rather than an implementation task. If the
behaviour turned out not to hold, that would be a finding, not something to fix
inside this change.

## What the audit found elsewhere

The change that prompted this was a staleness sweep across all 15 requirements
in `rev2-auth`, `rev2-reconciliation` and `rev2-store`. It found **no stale
claim**: every cited view exists (7/7), every cited count matches the live store
(84 milestones, 3 app_meta, 7 roles, 22 person_roles, 5 source_areas, 0 audit
rows), every cited function exists (23/23), `vw_primary_reporting_owner` is
genuinely filtered by `ownership_role`/`primary_flag`/`effective_end`, SQLite's
`People` carries no credential column, `set_person_pin`/`verify_person_pin` are
gone, and all 61 `initiative_relationship` rows are D-1 → Dean `Supports`.

Two false positives were caught by reading the definition rather than the shape:
`vw_primary_reporting_owner` does not *expose* `ownership_role`, but it is
filtered by it, which is what the spec claims. Recorded here so the next audit
does not repeat the check.

## Risk

Low. Spec-only, and the scenario describes behaviour that already exists and is
already exercised by the passcode path in the local suite (under sqlite). The
only way this change is wrong is if the behaviour does not hold under mssql —
which task 2.1 checks before anything is synced.
