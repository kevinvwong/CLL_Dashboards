# Design

## Context

Schema, sample data, and build script exist in `db/` and are tested. Views map one-to-one to screens: `vw_GoalInitiatives`, `vw_PriorityInitiatives`, `vw_InitiativeConnections`, `vw_PersonInitiatives`, `vw_LatestProgress`, `vw_RecentUpdates`, `vw_DataChecks`. Development happens on a 2019 Intel MacBook with 8GB RAM. Users: the Dean, 3+ D-1 leaders, and the dashboard team (admins).

## Goals / Non-Goals

**Goals:**
- Usable by the Dean and leaders from their own computers within one week.
- Keep business rules in SQL so they carry over to Microsoft tools.
- One view per screen; no duplicated query logic.

**Non-Goals:**
- SSO, fine-grained permissions, accessibility audit, front-end build pipeline.

## Decisions

1. **Server-rendered HTML with HTMX.** One route plus one template per screen; no SPA, no bundler. HTMX vendored into `app/static/` so the app works without CDN access.
2. **SQLite with `PRAGMA foreign_keys = ON`, WAL mode, and a 5-second busy timeout** per connection. Handles a handful of concurrent users. SQL Server in Docker rejected (memory).
3. **Raw SQL against views, no ORM.** The views are the contract for the later Power BI build.
4. **Writes go through one module (`app/repo.py`)** that runs inside a transaction, maps SQLite constraint errors to friendly messages, and writes the AuditLog row.
5. **Access:** shared passcode (env `APP_PASSCODE`) checked by middleware; then a person picker. Both stored in cookies signed with `APP_SECRET` via itsdangerous. Permission checks run on the server for every POST: owner, Dean (`ReportsToID IS NULL` and has Dean initiatives), or admin.
6. **Modal initiative card** loaded by HTMX into a `<dialog>`; `/initiatives/{code}` also renders as a full page.
7. **Progress bar color** from latest status: On track green, At risk amber, Off track red, Not started and Paused gray, Complete dark green. Length from percent.
8. **Ordering in lists:** Dean initiatives by code, divider, D-1 grouped by owner name then code. Primary tags show a badge.
9. **Importer is all-or-nothing** into a temp copy of the database, then an atomic file swap. It upserts by `Code`, so existing `ProgressUpdates` survive. Initiatives missing from the file are retired, not deleted.
10. **Backups:** `scripts/backup.py` uses SQLite's online backup API to write `backups/cll_YYYYMMDD.db`, keeps 14. Run at app startup and daily from a background task.
11. **Two environments, one codebase.** — *Live half REVERSED 2026-10-05.*
    - *Local (MacBook):* `uvicorn app.main:app --reload` with sample data, no Docker (8GB RAM). `.env` sets `APP_ENV=local`. **Unchanged.**
    - *Live (was: Hetzner VPS):* was Docker Compose service `cll-dashboard` running uvicorn with 2 workers, `APP_ENV=live`, database and backups on a named volume at `/data`, binding `127.0.0.1:8085` behind an existing reverse proxy or a Caddy container for HTTPS on a subdomain.
    - *Live (now: Azure App Service):* Linux, Python 3.12, F1 free tier, region `northcentralus`. Code deploys as a zip and Oryx builds dependencies at deploy time. **Reason:** the project is being redesigned into the Microsoft ecosystem (Azure SQL + Entra ID), and Georgia Tech provisioning takes longer than the prototype deadline. **What survives unchanged:** `APP_ENV=live` itself. The reverse-proxy, Caddy, `127.0.0.1:8085`, and named-volume concerns are moot because TLS terminates at the platform and persistence moves off the app's local disk (see Track 1, Azure SQL).
12. **Source of truth is the live deployed instance** — *REVERSED 2026-10-05.* *Was: "Source of truth is the VPS."* Live data is imported and edited only in the live environment, and nothing pushes a database up over it — **that safety property is unchanged.** What changed is the mechanism: `scripts/pull_live.sh` (copy the newest VPS backup to the laptop) and `deploy/deploy.sh` (ssh, `git pull`, `docker compose up -d --build`) no longer have a target. Code still moves by git; the deploy step becomes `az webapp deploy` plus a restart, and the post-deploy `/healthz` check survives unchanged.
13. **Import runs against the live instance** — *REVERSED 2026-10-05.* *Was: "Import on the VPS" — `scp` the filled template up, then `docker compose exec cll-dashboard python scripts/import_xlsx.py /data/inbox/<file>.xlsx`.* Now: the filled template is uploaded through the Kudu/SCM file API and the importer is invoked in the running instance. `scp` and `docker compose exec` have no target. **Unchanged:** the importer takes a backup before importing, and decision 9's temp-copy-then-atomic-swap discipline still governs.
14. **Hardening for a public endpoint** — *NOT reversed, only retargeted.* *Was: "Hardening for a public VPS."* The list is platform-independent and all of it still applies: HTTPS only; cookies `Secure`, `HttpOnly`, `SameSite=Lax`; login lockout after 10 failed passcode attempts per IP in 15 minutes; `X-Robots-Tag: noindex` and a disallow-all `robots.txt`; `/healthz` is the only route outside the gate and returns no data. **Open item:** `httpsOnly` was `false` on the live site as of 2026-10-05 and must be enabled before any real data lands — tracked in task 9.1.
15. **Production data target is Azure SQL (T-SQL); SQLite is local development only.** *Added 2026-10-05.* A T-SQL mirror of the schema exists and was verified table-for-table and view-for-view against `db/schema.sql`: 9 tables, 7 views, every column matched. Consequences for earlier decisions:
    - **Amends D2.** The SQLite pragmas (`foreign_keys`, `journal_mode=WAL`, `busy_timeout`) are a local-dev concern only. In T-SQL the same rules are declarative: `CHECK (Level IN ('Dean','D-1'))`, `CHECK (PercentComplete BETWEEN 0 AND 100)`, filtered unique indexes `UX_IG_OnePrimary` / `UX_IP_OnePrimary ... WHERE IsPrimary = 1` for "at most one primary tag", and `trg_Links_LevelCheck` for the D-1 to Dean rule. This retires the constraint-error mapping D4 described; the database refuses the write instead of the app catching it.
    - **Supersedes D10.** `scripts/backup.py` and its 14-copy retention are deleted, not ported. Azure SQL point-in-time restore replaces them.
    - **Amends D11.** "Two environments, one codebase" now spans two *dialects*, not just two hosts. The T-SQL file must be kept in sync with `db/schema.sql`; divergence is a build failure, not a surprise.
    - **Upholds D3.** The views remain the contract. That is the reason Azure SQL was chosen over the Dataverse/SharePoint target previously recorded in `db/README.md`: Dataverse has no SQL views and would have required re-expressing every rule as a Power Automate check.
    - **Auth is Entra ID via managed identity.** No SQL authentication password exists anywhere, which removes the `APP_SECRET`-shaped problem from the data layer.
    - **Target SKU:** Azure SQL Database, serverless, auto-pause, so a prototype idle most of the week is not billed continuously.
    - **Not yet done:** there is no T-SQL equivalent of `seed_sample.sql`, so view parity cannot be verified against real rows until one exists. This does not block the prototype.

### Routes

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET/POST | `/login` | anyone | Passcode page |
| GET/POST | `/whoami` | passcode | Person picker |
| GET | `/` | all | Goal and priority tiles |
| GET | `/goals/{n}` | all | Goal list |
| GET | `/priorities/{id}` | all | Priority list |
| GET | `/initiatives/{code}` | all | Initiative card (fragment when `HX-Request`) |
| GET | `/people/{id}` | all | Person card |
| GET | `/meeting?since=YYYY-MM-DD` | all | Meeting page |
| GET | `/checks` | all | Data checks |
| POST | `/initiatives/{code}/updates` | owner, Dean, admin | Append progress update |
| POST | `/initiatives/{code}/details` | owner, admin | Edit name, description |
| POST | `/initiatives/{code}/tags` | admin | Replace goal and priority tags |
| POST | `/initiatives/{code}/links` | admin | Replace Dean links |
| POST | `/initiatives/{code}/retire` | admin | Retire |
| POST | `/initiatives` | admin | Create |
| POST | `/goals/{n}`, `/priorities/{id}` | admin | Edit descriptions |

### Screen sketches

```
HOME
[ Goals (Strategy 2035) ]            [ 2027 Priorities ]
[1 Academic 9] [2 Extension 4] ...    [Culture 3] [Scale 7] [Identity 3] ...

GOAL LIST: 3 Research                 On track 5 · At risk 1 · No update 2
Description text...
Bill   D-A Transparent ROI reporting  [######----] 30% On track  (primary)
Bill   D-D Research partnerships      [#---------] 10% On track
------------------------------------- D-1 -------------------------------
Elizabeth  ELIZ-1 Dashboards          [#---------] 10% On track
Mario      MAR-4  ...                 [#---------] 10% On track

INITIATIVE CARD (modal)
ELIZ-1 Financial and operational dashboards     D-1 · Owner: Elizabeth
Description...
Goals: Operational (primary), Research    Priorities: Data (primary)
Feeds: D-A Transparent ROI reporting · D-C Consulting arm launch
Latest: 10% On track · Oct 5        [Update]  [Edit]*
Diary: Oct 5 10% On track  "Data model drafted..."
       Sep 28 2% On track  "Ideation session held."
```

## Risks / Trade-offs

- [Passcode plus picker lets a user pick someone else] → Audit log records the picked person; acceptable for an internal prototype; replaced by Microsoft auth at migration.
- [Internal planning data on a personal subscription outside Georgia Tech] → **Recharacterised 2026-10-05.** The live environment is Azure App Service on Kevin's own `Azure for Students` subscription, so moving off the Hetzner VPS did **not** resolve this risk — it relocated it. Mitigations unchanged: passcode, HTTPS, noindex, no personal data beyond names; confirm acceptability before live data (Open Questions). Fallback: run locally during meetings and import owner updates from the template. Moving to the Georgia Tech tenant is the actual fix and is Track 1.
- [Live-instance outage before a meeting] → **Recharacterised 2026-10-05.** No VPS to go down. Daily backups still let the meeting run from the laptop copy, but `pull_live.sh` no longer exists; retrieving a copy is now a Kudu/SCM download of the backup file.
- [Leaders submit inconsistent names] → Template uses dropdowns and X columns generated from the database.
- [Bill expects rollups] → No aggregate percent anywhere; only counts by status.
- [SQLite write contention] → WAL mode and busy timeout; expected load is under 10 users.

## Open Questions

- **Partially answered 2026-10-05:** Is hosting initiative names, descriptions, and leader names acceptable under Georgia Tech data policy for this prototype? Who confirms (Cassie, CLL IT)? The Hetzner VPS is gone, but the live environment is still a *personal* Azure subscription, so the question stands and is now the blocker for putting real data on the live site. Interim position: the deployed prototype carries **sample seed data only**, which keeps it out of scope of the question.
- **Obsolete 2026-10-05:** Subdomain to use and whether the VPS already has a reverse proxy (Caddy, Traefik, nginx) to reuse. No VPS, no reverse proxy, no subdomain decision — the endpoint is a `*.azurewebsites.net` host that can be renamed later.
- **New, 2026-10-05:** Should the live prototype stay on the `Azure for Students` subscription, or move to a Georgia Tech tenant subscription once provisioning completes? This decides whether `APP_PASSCODE`/`APP_SECRET` handling stays as-is or is replaced by Entra ID auth in Track 1.
- Full names and descriptions for goals 2-5; final wording of goal 4 ("Learner impact" is a placeholder).
- Remaining D-1 owners beyond Elizabeth, Tim, and Mario, and which dashboard team members are admins.
- Initiative code format (proposed: `D-A` for Dean, `ELIZ-1` for D-1).
- Whether retreat priority descriptions are final.
