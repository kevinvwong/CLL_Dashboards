# Roles and signing in

## Signing in

The dashboard is behind a shared passcode. You then pick your name, and — if an
administrator has set one for you — enter your **PIN**. The PIN ties your session
to you, so no one else can become you by choosing your name.

## Roles

Authorization is held in the app, as *roles* on your account, not in an external
directory. A role says what you may do here; your name says who you are.

| Role | Meaning |
|---|---|
| `viewer` | may read every page |
| `team_lead` | accountable for a team; updates its initiatives |
| `dean` | updates any initiative and the Dean layer |
| `admin` | the dashboard team: edits everything, manages users |

A person may hold more than one role. Roles are managed locally by an admin, so
they keep working whichever sign-in method is used.

## Setting a PIN (administrators)

An administrator sets a person's PIN from the app. Once a PIN is set, the shared
passcode alone is no longer enough to become that person. Until PINs are rolled
out, the name picker still works — so rolling out PINs is what closes the gap
person by person.

Next: [Mock data vs confirmed data](/guide/mock-vs-confirmed).
