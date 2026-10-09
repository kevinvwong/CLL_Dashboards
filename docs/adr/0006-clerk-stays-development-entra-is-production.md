# Clerk stays a development adapter; Entra is the production identity provider

**Status:** accepted (2026-10-08) — amended 2026-10-08 for provisioning timing

> **Timing note (2026-10-08).** Full provisioning is fast-tracked and expected
> **2026-10-09**. The local-passcode interim is therefore likely to be *days*, not
> months, and Entra may be live almost immediately. The decision below is
> unaffected — it still means no Clerk production spend — but read the
> consequences accordingly: the PIN guidance matters for the live VPS host *now*,
> and it is not worth building further stopgap investment against a window this
> short. The genuine long pole is the **Entra app registration**, because that
> needs GT tenant action rather than local work; everything else can follow it
> quickly.

ADR-0004 made authentication a swappable seam and anticipated "a Clerk/Entra
token adapter later" without choosing between them. This records the choice,
which is driven by cost rather than preference: **a Clerk production instance is
not being purchased.** Clerk's free tier does not cover production users, and
buying the paid tier to bridge to Entra would mean paying, for a few months, for
a provider we are deliberately replacing. So the interim provider is the one
that is already built and already deployed.

Entra stays blocked for a different and unrelated reason: the Azure host is a
personal `Azure for Students` subscription whose tenant is **outside Georgia
Tech** (`LAUNCH_RECORD.md:30`), so a GT-tenant app registration cannot be
provisioned there. That unblocks when the project is provisioned into the GT
tenant — not before, and not by paying Clerk.

**Decision:** every deployed environment runs `AUTH_PROVIDER=local` — the
shared passcode, the admin-only person picker, and per-person PINs — from now
until Entra is provisioned. Clerk is retained as a **development** adapter only.
The `clerk` value of `AUTH_PROVIDER` stays supported and covered by
`tests/test_clerk_auth.py` so the seam stays proven, but no deployed host points
at a Clerk instance.

## Consequences

- **No cost is incurred for identity** between now and Entra.
- The person picker is the production sign-in path, so per-person PINs are what
  close the self-assertion hole (ADR-0004). **A PIN must be set for the
  PlatformAdmin at minimum** — without one, anyone holding the passcode can
  become the admin. Note that on the VPS host no PIN is currently set
  (`People.Credential` is empty), because no one has ever completed sign-in.
- PINs are **not** available on the Rev2/Azure SQL store — no credential is
  stored there (`db/mssql/DEVIATIONS.md`, entry 010). Staying on
  `AUTH_PROVIDER=local` is therefore also what keeps the PIN gate available; a
  Rev2 deployment would have the passcode picker with no PIN to close it.
- Swapping to Entra is an env var plus one adapter, per ADR-0004. It is not a
  route rewrite, and the rest of the app never learns which provider is in use.
- `People.ClerkUserID` and the linking scripts stay in place so the Clerk dev
  roster in `docs/ops/USERS_AND_ROLES.md` remains usable for local development.

## What this decision is not

It is not a claim that Clerk dev sign-in works in production. It does not: the
VPS host is pointed at a Clerk **development** instance and sign-in there never
completes, which is why its `AuditLog` and `TeamInitiativeUpdates` tables are
both empty. An earlier version of `docs/ops/DEPLOY.md` asserted that
"production identity is Clerk"; that was never true of Azure (which has always
run the passcode) and is not true of the VPS host either. The correction is
recorded inline there.