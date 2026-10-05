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
11. **Two environments, one codebase.**
    - *Local (MacBook):* `uvicorn app.main:app --reload` with sample data, no Docker (8GB RAM). `.env` sets `APP_ENV=local`.
    - *Live (Hetzner VPS):* Docker Compose service `cll-dashboard` running uvicorn with 2 workers, `APP_ENV=live`. Database and backups on a named volume mounted at `/data`. The VPS already runs other containers, so the app binds only to `127.0.0.1:8085` and sits behind the existing reverse proxy, or behind a Caddy container if none exists, which handles HTTPS on a subdomain.
12. **Source of truth is the VPS.** Live data is imported and edited only on the VPS. `scripts/pull_live.sh` copies the newest VPS backup to the laptop (as `cll_live_copy.db`) for debugging; nothing pushes a database up. Code moves by git: push to GitHub, then `deploy/deploy.sh` SSHes in, pulls, rebuilds, restarts, and checks `/healthz`.
13. **Import on the VPS.** Copy the filled template up with `scp`, then run `docker compose exec cll-dashboard python scripts/import_xlsx.py /data/inbox/<file>.xlsx`. The importer takes a backup first.
14. **Hardening for a public VPS:** HTTPS only; cookies `Secure`, `HttpOnly`, `SameSite=Lax`; login lockout after 10 failed passcode attempts per IP in 15 minutes; `X-Robots-Tag: noindex` and a disallow-all `robots.txt`; `/healthz` is the only route outside the gate and returns no data.

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
- [Internal planning data on a personal VPS outside Georgia Tech] → Passcode, HTTPS, noindex, no personal data beyond names; confirm acceptability before live data (Open Questions). Fallback: run locally during meetings and import owner updates from the template.
- [VPS outage before a meeting] → Daily backups plus `pull_live.sh` let the meeting run from the laptop copy.
- [Leaders submit inconsistent names] → Template uses dropdowns and X columns generated from the database.
- [Bill expects rollups] → No aggregate percent anywhere; only counts by status.
- [SQLite write contention] → WAL mode and busy timeout; expected load is under 10 users.

## Open Questions

- Is hosting initiative names, descriptions, and leader names on a personal Hetzner VPS acceptable under Georgia Tech data policy for this prototype? Who confirms (Cassie, CLL IT)?
- Subdomain to use and whether the VPS already has a reverse proxy (Caddy, Traefik, nginx) to reuse.
- Full names and descriptions for goals 2-5; final wording of goal 4 ("Learner impact" is a placeholder).
- Remaining D-1 owners beyond Elizabeth, Tim, and Mario, and which dashboard team members are admins.
- Initiative code format (proposed: `D-A` for Dean, `ELIZ-1` for D-1).
- Whether retreat priority descriptions are final.
