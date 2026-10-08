# Roles are local rows, not identity-provider groups

**Status:** added 2026-10-07

Authorization today is `People.IsAdmin` — a column anyone could self-select
through the picker — plus the string convention `Title == 'Dean'`. `Title` is
free text, so "dean" is a substring match, not a role; and `TeamInitiatives`
ownership is a data relationship, not a permission.

**Decision:** introduce `Roles` and `PeopleRoles` and make `guards.py` read them.
Users and their roles are provisioned **locally by an admin in the app**, not
synced from Entra or Clerk. `People.IsAdmin` is kept as a deprecated mirror until
the guards are migrated, then dropped.

**The role set is the DR-05 model (six capability-oriented roles):**
`Administrator`, `ExecutiveSponsor`, `DataOwner`, `Operator`, `Contributor`,
`Viewer`. The earlier placeholder names (`admin`, `dean`, `team_lead`, `viewer`)
are still recognised as aliases during the migration.

The roles are **not a hierarchy** (DR-23). Each carries a different authority —
technical, operational, data-governance, strategic-decision, contribution,
consumption — and the app asks capability questions (`has_capability`,
`can_update`, `can_edit_details`) rather than identity questions. In particular
the Executive Sponsor (the Dean) holds portfolio-wide read and executive-action
authority but **no** routine update authority: `may_update` must never accept
`is_dean` alone.

## Consequences
- The identity provider answers "who are you"; the app answers "what may you
  do". This keeps the app usable with any provider, including the local
  stopgap, and keeps group management editable without tenant access.
- An Entra or Clerk **group claim**, if ever adopted, *maps onto* these rows
  rather than replacing them — so the local model is not throwaway.
- Do not reintroduce a permission check that reads `Title` or a raw `IsAdmin`
  once the guards are migrated.
- Do not collapse the six capabilities into a single rank, and do not let
  executive authority imply data-maintenance authority (DR-23).
