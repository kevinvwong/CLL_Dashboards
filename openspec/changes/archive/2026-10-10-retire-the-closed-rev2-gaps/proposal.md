# Proposal: Retire the Rev2 gap requirement the reconciliation already closed

## Why

`openspec/specs/rev2-store/spec.md` carries a requirement, **"gaps are explicit,
never silent"**, that states milestones, AppMeta and audit have **no Rev2
equivalent** and that the priorities screen must fall back to a sqlite-backed
interim. All three gaps were closed by `rev2-full-reconciliation`
(`008_app_layer.sql`, `011_milestone_initiative.sql`).

The spec catalogue is what a future contributor reads to decide whether an area
is safe to touch. A requirement asserting a gap that closed two changes ago is
worse than no requirement: it invites someone to "restore" an interim behaviour
that was deliberately removed, or to treat the port as permanently partial. The
same spec already contradicts itself — requirement "the change log reads the
Rev2 audit store" says `recent_changes` **SHALL** read `audit_log` "(reconciled
in `008`)", while this one says no audit target exists.

## What Changes

- **REMOVED** — the requirement *"gaps are explicit, never silent"* from
  `rev2-store`, with its two scenarios (priorities screen under mssql, audit
  write under mssql). **This is a spec-only change: no code, schema or route
  changes.** The behaviour the requirement described no longer exists to change.
- **MODIFIED** — *"DB_PROVIDER selects a working store"*, dropping the stale
  parenthetical "(subject to the Open issues in design.md)" from its
  *mssql renders every screen* scenario. Those Open issues were
  `adopt-rev2-store`'s, and `rev2-full-reconciliation` closed them; the
  parenthetical now points at a resolved condition.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rev2-store`: removes a requirement that records gaps `rev2-full-reconciliation`
  closed, and retires the dangling Open-issues cross-reference.

## Impact

- **Specs only.** `openspec/specs/rev2-store/spec.md` (8 requirements → 7);
  no application, migration or route is touched.
- The `rev2-reconciliation` spec already requires Rev2 to carry the milestone,
  config and audit layers; this change removes the `rev2-store` requirement that
  denied it. The two specs stop contradicting each other.
- No test changes. Nothing in the suite asserts this requirement — a spec-level
  requirement has no executable form once the interim it described is gone.
