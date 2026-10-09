# Roles and signing in

## Signing in

The dashboard is behind a shared passcode. Once you have it, you pick your name
and you are signed in as that person.

## Roles

Authorization is held in the app, as *roles* on your account, not in an external
directory. A role says what you may do here; your name says who you are.

| Role | Meaning |
|---|---|
| `Viewer` | may read every page |
| `Operator` | updates the initiatives a team owns |
| `Contributor` | adds updates, without changing the register itself |
| `DataOwner` | curates the data definitions and their provenance |
| `ExecutiveSponsor` | portfolio-wide read, plus the executive decisions |
| `PlatformAdmin` | the dashboard team: edits everything, manages people |
| `TechnicalAdmin` | infrastructure support |

A person may hold more than one role, and the roles are not a hierarchy — each
carries a different kind of authority. The Executive Sponsor (the Dean) holds
portfolio-wide read and executive-action authority but **no** routine
data-maintenance authority.

Roles are managed inside the app by a `PlatformAdmin`, so they keep working
whichever sign-in method is in use.

Next: [Mock data vs confirmed data](/guide/mock-vs-confirmed).