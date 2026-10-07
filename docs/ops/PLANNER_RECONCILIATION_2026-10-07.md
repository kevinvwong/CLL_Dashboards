# Planner reconciliation — 2026-10-07

Applies the review of the open platform tasks, **verified against the repository**.
Microsoft Planner is not reachable from here; this file is the copy-paste-ready
change set. It records one rename and confirms every other task stays open.

## What changes

| # | Action | Task |
|---|---|---|
| 1 | **Rename** | "Stand up the portfolio registry and intake approval workflow" → **"Add governed intake approval workflow to the canonical portfolio registry"** |

Nothing else changes. Every task below stays **open**, with its existing bucket
and priority.

## Why the rename

The registry foundation already exists: `SourceAreas`, `Teams`, the register
import (`db/build_register_seed.py`), the intake path (`scripts/import_xlsx.py`),
and the merged read/write model. The unresolved part is the **governed approval
workflow** on top of it, not standing the registry up. The old title overstates
what remains.

## Confirmations (no edit needed)

### Security — keep all three open, distinct
- **Harden credential handling and protect untracked folders** — the archive
  guard (`scripts/build_deploy_zip.py:49`) refuses a secret-shaped *file*, but the
  **tracked literals in `docker-compose.yml`** and the two un-ignored directories
  remain. Open.
- **Rotate exposed application credentials** — no evidence of rotation. Open.
- **Coordinate credential-history remediation** — `.env` is in history
  (`4ee6d3e`, `9436720`). Open.
The guard is real but does **not** substitute for these; they are distinct.

### Entra identity and authorization — keep all seven open
The commit "sign in with the canonical owner names" (`ee5a3d3`) is a **test
rename** (`auth.py` and `queries.py`, one line each, plus 24 test files), not
identity work. No Entra/OIDC/MSAL code exists. All seven stay open.
- Entra group overage: keep **predicted** until the identity design proves the condition applies.

### Administration, CRUD, governance, audit — keep all six open
Admin-related routes exist (`admin_for` / `admin_only` guards, `/changes`,
`/entries/{kind}/{key}/edit`), but there is **no administration of users or
group-to-role mappings**, no steward/validation/period/evidence metadata, no
change reason/source/correlation id, **no restore path** (only `IsActive`, always
filtered to 1), and no concurrency control on import. Keep open.
- Concurrent-import duplicate prevention: keep **predicted / validation** until real import behavior confirms the need.
- Administration task: read as *extending* the existing admin capability, not creating it.

### Production data and infrastructure — keep all six open
The prototype has a deploy runbook, an exercised rollback, backup retention, a
data-swap path, reproducible local db construction, and archive checks. None of
those is a **versioned production schema migration, Azure SQL migration,
institutional provisioning, full restore against the target, App Insights with
alerts, or a production support runbook**. Keep open.

### Operating governance and product expansion — keep all three open
- Portfolio registry: **renamed** (above).
- KPI ingestion and executive reporting: open — the app has no KPI/measure table
  (`Measure` is a free-text column on `Priorities` only) and the Outcomes page is
  generated, hardcoded data (`CONFIRMED = False`), not a live measure.
- Recurring access review: keep **predicted**.

### Board readiness — keep all ten open, and report separately
The deliverable and the data-swap path were built, but the log does not show the
walkthrough, leadership approval, rehearsal, final package, or the October 16
event occurred. Keep open; report these apart from the post-October platform
roadmap.

## The one framing worth stating plainly

Every identity, authorization, audit, and administration task is open for a
single root reason: **the app is behind a shared passcode with a self-asserted
person picker** (`app/auth.py`), so `IsAdmin` is a value anyone can select for
themselves. That is why "admin routes exist" does not mean "administration
exists". This is the through-line of the whole roadmap, not a gap in it.

## Retraction

An earlier draft of this reconciliation proposed that "Academic Affairs" was a
stale label needing reconciliation with the register. **That was wrong.** The
canon workbook uses `Academic Affairs` for 9 rows, and the DB's five source areas
match it exactly. No reconciliation is needed. Recorded here so the wrong
reading is not repeated.
