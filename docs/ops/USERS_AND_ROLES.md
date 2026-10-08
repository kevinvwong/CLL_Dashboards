# CLL Dashboard — Users, Roles & Clerk Provisioning

**Recorded:** 2026-10-08
**Source of truth:** the application's `People`, `Roles` and `PeopleRoles`
tables (seeded by `db/build_milestones_seed.py`). This document mirrors them for
review; the database decides.

## The roster

| Person | GT username | Email | Application roles | Functional role |
|---|---|---|---|---|
| Kevin Wong | kwong318 | kwong318@gatech.edu | PlatformAdmin, Operator, Viewer | Strategic Operations — primary developer & administrator |
| Cassie Parkin | cparkin6 | cparkin6@gatech.edu | PlatformAdmin, Operator, Viewer | Strategic Operations |
| Chris Reyes | creyes39 | creyes39@gatech.edu | PlatformAdmin, Operator, Viewer | Strategic Operations |
| DeMarco Williams | dwilliams406 | dwilliams406@gatech.edu | PlatformAdmin, Operator, Viewer | Strategic Operations |
| Elizabeth Smith | esmith460 | esmith460@gatech.edu | DataOwner, Viewer | Data Owner / Portfolio Governor |
| Bill Gaudelli | wgaudelli3 | wgaudelli3@gatech.edu | ExecutiveSponsor, Viewer | Dean / Executive Sponsor |
| Grace Flavin | eflavin6 | eflavin6@gatech.edu | Viewer | Leadership Viewer (Contributor later) |
| Mario Herane | mherane3 | mherane3@gatech.edu | Viewer | Leadership Viewer (Contributor later) |
| Meltem Alemdar | ma128 | ma128@gatech.edu | Viewer | Leadership Viewer (Contributor later) |
| Tim Jacobbe | tjacobbe3 | tjacobbe3@gatech.edu | Viewer | Leadership Viewer (Contributor later) |
| Mike Sewell | msewell7 | msewell7@gatech.edu | TechnicalAdmin, Viewer | OIT Technical Contact |

A person may hold more than one role; the app presents the **union** of the
authorized functions. The roles are **not a hierarchy** (DR-23): each carries a
different authority (technical, operational, data-governance, strategic
decision, contribution, consumption).

## Role definitions

| App role | Holders | Meaning |
|---|---|---|
| `PlatformAdmin` | Kevin, Cassie, Chris, DeMarco | Technical/application administration and approved access administration |
| `Operator` | Kevin, Cassie, Chris, DeMarco | Routine initiative/data maintenance, meeting preparation, workflow processing, implementation of approved decisions |
| `DataOwner` | Elizabeth | Governs portfolio data: definitions, ownership, approvals, exceptions, contributor access |
| `ExecutiveSponsor` | Bill | Portfolio-wide read plus explicitly authorized executive actions; **no** general initiative-update authority |
| `Viewer` | everyone | Read-only portfolio, initiative details, history, published meeting information |
| `Contributor` | *none initially* | Future: submit updates to assigned initiatives, without publishing/governance authority |
| `TechnicalAdmin` | Mike | OIT/Azure infrastructure support; separate from business/application governance |

The Dean's `ExecutiveSponsor` role explicitly **excludes** general `may_update`
and routine initiative editing (DR-23). Executive actions — approve, return,
defer, escalate, resolve, request information/recommendation, record direction,
set executive priority, controlled override, watchlist, meeting-agenda actions —
are separately authorized workflow actions, not data edits.

Contributors, when activated, **retain** their `Viewer` capability; Contributor
adds assigned-update capabilities rather than replacing read access.

## Clerk provisioning

- **Identity provider:** Clerk, application `app_3KPot74L7qbEcADeZzaSQerlWfg`,
  dev instance, Microsoft (Entra) SSO.
- **Users:** all 11 exist in Clerk with username + email. Sign-in is via
  Microsoft SSO, which Clerk matches to a user **by email** — so the roster's GT
  email is the identity key. Kevin signs in as
  `kevin.wong@lifetimelearning.gatech.edu`.
- **Aliases (two addresses per person):** a GT person often has two addresses —
  a username form (`<username>@gatech.edu`) and an alias
  (e.g. `first.last@lifetimelearning.gatech.edu`), and Microsoft SSO returns ONE
  of them. Clerk auto-links an SSO sign-in only when the returned address matches
  a **verified** email already on the user. So each person should carry **both**
  addresses, both verified: if only the username is on file and the person signs
  in with their alias, Clerk creates a *second* user instead of linking. Add the
  second address with
  `python scripts/add_clerk_email.py <clerk_user_id> <alias>`. (Kevin carries
  both.)
- **Link to the app:** each Clerk user id is stored in `People.ClerkUserID`
  (set locally by `scripts/link_clerk_user.py`). Clerk ids are per-environment, so
  they are **not committed** — the committed database carries none.
- **Groups:** one Clerk organization, "Georgia Institute of Technology". Its
  **development-instance membership limit is 5** (a plan-level cap, not the org
  `max_allowed_memberships` setting), so not all 11 are org members. This does
  **not** affect access: roles live in the application (ADR-0005), and the app
  does not read Clerk org claims.

## Re-provisioning

1. Create the users in Clerk with their username + email (SSO matches on email).
2. Add each person's alias as a second **verified** email
   (`python scripts/add_clerk_email.py <clerk_user_id> <alias>`), so whichever
   address Microsoft returns links to the same user.
3. Link each to their person: `python scripts/link_clerk_user.py <clerk_user_id> <person_id>`
   (`clerk users list --app <app_id>` shows the ids).
4. Roles come from the seed; adjust the roster in `db/build_milestones_seed.py`
   and rebuild (`python db/build_db.py`).
