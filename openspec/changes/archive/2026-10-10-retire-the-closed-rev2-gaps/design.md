# Design: retire-the-closed-rev2-gaps

## Decision 1 — REMOVED, not MODIFIED

The obvious alternative is to MODIFIED the requirement into something that is
still true — "if a gap exists, it SHALL be recorded" — and keep the heading.

That is the wrong move here, and it is worth being explicit about why. The
requirement was written **for a change, not for a capability**. Its subject is
the transitional state of the Rev2 port, and it exists to say "while these gaps
are open, do not hide them". Once the gaps close, the requirement's subject is
gone, and a rewritten version ("gaps SHALL be recorded") is a standing *policy*
that no longer matches anything the port does. It would also be untestable:
the scenarios it carries assert the *absence* of Rev2 tables, which is exactly
what must not survive.

So the requirement is REMOVED with a Reason and a Migration, and the delta
carries no replacement. A reader arriving after this change sees the port with
no gaps rather than a policy for managing one.

## Decision 2 — the internal contradiction is the strongest evidence

The change is not justified by "the requirement is old". `rev2-store` already
contains both halves of a contradiction:

- *"gaps are explicit, never silent"* — no audit target exists, so an audited
  write under mssql raises at the seam.
- *"the change log reads the Rev2 audit store"* — `recent_changes` SHALL read
  `audit_log`, "(reconciled in `008`)".

Both cannot be true. The second is the accurate one (verified: `dbo.audit_log`
exists from `008`, and `rev2-full-reconciliation` task 3.2 pointed
`repo._audit` at it), so the first is what goes. A spec that disagrees with
itself cannot be used to decide whether an area is safe to touch, which is the
only thing a spec catalogue is for.

## Decision 3 — the stale Open-issues parenthetical goes with it

The `DB_PROVIDER` scenario qualified "same logical content as sqlite" with
"(subject to the Open issues in design.md)". Those were `adopt-rev2-store`'s
recorded Open issues, and `rev2-full-reconciliation`'s proposal states it closes
them. The parenthetical now points at a resolved condition, so the qualification
is removed rather than updated to name a new one — there is nothing to qualify.

This is a MODIFIED rather than REMOVED because the requirement itself is still
the capability's contract and its other two scenarios are unaffected.

## What was verified before proposing this

The requirement was checked against the live `cllrev2` store and the code, not
against memory:

| Claim in the requirement | Verified state |
|---|---|
| milestones have no Rev2 table | `dbo.milestone` exists, 84 rows across 29 D-1 initiatives, keyed to `initiative_id` |
| AppMeta falls back to sqlite | `dbo.app_meta` exists (3 rows); `port._appmeta` branches on `engine()` with no sqlite fallback |
| no audit target under mssql | `dbo.audit_log` exists (`008`) |
| the milestone read is interim sqlite-backed | `port.milestones_for_year` joins `initiative_priority`, de-duplicated at read time |

Every module and function name the `rev2-store` spec cites was also confirmed to
still exist (`app/queries.py`, `app/repo.py`, `app/port.py`, and all six read
functions plus the writes), so no other requirement is naming a deleted surface.

## Risk

Low, and entirely documentary. Nothing in the test suite asserts this
requirement — a spec requirement describing an interim has no executable form
once the interim is gone — so removing it cannot turn a test red. The only way
this change can go wrong is if a gap the requirement described is still open and
was missed during the audit; the table above is the check against that.
