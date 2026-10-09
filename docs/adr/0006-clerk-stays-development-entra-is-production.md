# Clerk stays a development adapter; Entra is the production identity provider

**Status:** accepted (2026-10-08) — amended 2026-10-08 for provisioning timing

> **Timing note (2026-10-08).** Full provisioning is fast-tracked and expected
> **2026-10-09**. The local-passcode interim is therefore likely to be *days*, not
> months, and Entra may be live almost immediately. The decision below is
> unaffected — it still means no Clerk production spend — but read the
> consequences accordingly: the identity work is not worth building out against a
> window this short. The genuine long pole is the **Entra app registration**,
> because that needs GT tenant action rather than local work; everything else can
> follow it quickly.
>
> **Amended 2026-10-09:** the per-person PIN was **removed from the application**,
> so the consequences below that describe PINs no longer apply. What survives is
> the decision itself and its timing. The self-assertion exposure the PIN was
> introduced to close is therefore now carried by the passcode and the network
> boundary alone — which is an accepted trade for a fast-tracked internal tool,
> not an oversight, and Entra removes it properly.

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
shared passcode, then the person picker — from now until Entra is provisioned.
Clerk is retained as a **development** adapter only. The `clerk` value of
`AUTH_PROVIDER` stays supported and covered by `tests/test_clerk_auth.py` so the
seam stays proven, but no deployed host points at a Clerk instance.

## Consequences

- **No cost is incurred for identity** between now and Entra.
- **Anyone holding the passcode can become anyone**, including the
  `PlatformAdmin`. The per-person PIN that closed this was removed on
  2026-10-09, so for the remaining life of the stopgap the passcode and the
  network boundary are the only controls. That is an accepted trade for an
  internal fast-tracked tool, not an oversight — and it is the strongest
  practical argument for getting Entra provisioned rather than extending the
  stopgap.
- No per-person secret is stored in either data store, so moving between SQLite
  and Rev2 changes nothing about authentication.
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