# Roles are local rows, not identity-provider groups

**Status:** added 2026-10-07

Authorization today is `People.IsAdmin` — a column anyone could self-select
through the picker — plus the string convention `Title == 'Dean'`. `Title` is
free text, so "dean" is a substring match, not a role; and `TeamInitiatives`
ownership is a data relationship, not a permission.

**Decision:** introduce `Roles` and `PeopleRoles` (e.g. `admin`, `dean`,
`team_lead`, `viewer`) and make `guards.py` read them. Users and their roles are
provisioned **locally by an admin in the app**, not synced from Entra or Clerk.
`People.IsAdmin` is kept as a deprecated mirror until the guards are migrated,
then dropped.

## Consequences
- The identity provider answers "who are you"; the app answers "what may you
  do". This keeps the app usable with any provider, including the local
  stopgap, and keeps group management editable without tenant access.
- An Entra or Clerk **group claim**, if ever adopted, *maps onto* these rows
  rather than replacing them — so the local model is not throwaway.
- Do not reintroduce a permission check that reads `Title` or a raw `IsAdmin`
  once the guards are migrated.
