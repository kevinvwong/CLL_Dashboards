# Tasks

Open questions in design.md do not block groups 1-8; sample data stands in. Group 10 needs the data-policy answer before live data goes on the deployed site. The live environment is Azure App Service (changed from a Hetzner VPS on 2026-10-05); see design.md decisions 11-14.

## 1. Project setup (Tue Oct 6)

- [x] 1.1 Add `requirements.txt`: fastapi, uvicorn[standard], jinja2, python-multipart, itsdangerous, openpyxl, pytest, httpx
- [x] 1.2 Add `.env.example` with APP_PASSCODE, APP_SECRET, DB_PATH, BACKUP_DIR, PORT
- [x] 1.3 `app/config.py` loads settings from env or `.env`
- [x] 1.4 `app/db.py`: connection with foreign keys on, WAL, busy timeout 5000 ms, rows as dicts
- [x] 1.5 Vendor `htmx.min.js` into `app/static/`
- [x] 1.6 `tests/conftest.py`: fixture builds a fresh sample database per test and a logged-in TestClient per person
- [x] 1.7 Check: `python db/build_db.py` reports 0 issues; `uvicorn app.main:app` serves the app

*Verified 2026-10-05. This task was previously checked without being run: `build_db.py` reports 0 issues across 8 tables, and `uvicorn` was confirmed serving over real HTTP (303 to `/login`, `/healthz` returning `ok`, and a full passcode + person login reaching the home page with 11 tiles). The wording said "placeholder page"; `/` now renders the real home screen from task 3.3.*

## 2. Access gate (Tue Oct 6)

- [x] 2.1 Middleware: no passcode cookie redirects to `/login`; static files exempt
- [x] 2.2 `/login` and `/whoami` pages; signed cookies; header shows current person with Switch link
- [x] 2.3 `app/auth.py` helpers: `current_person()`, `can_update(code)`, `can_edit_details(code)`, `is_admin()`
- [x] 2.4 Check: tests for redirect without passcode, redirect without person, and successful entry

*Note 2026-10-05: `is_dean()` was added alongside the listed helpers. `design.md` decision 5 defines the Dean as `ReportsToID IS NULL` **and** owning Dean-level initiatives, and the second clause is load-bearing — Kevin is also top-level (`ReportsToID IS NULL`) and would be granted Dean powers by the first clause alone. Covered by `test_top_level_admin_is_not_the_dean`.*

## 3. Base layout and home (Tue Oct 6)

- [x] 3.1 `base.html`: header, nav (Home, Meeting, Checks), `<dialog>` for modals, print stylesheet
- [x] 3.2 `style.css`: tiles, list rows, status-colored bars, divider, badges
- [x] 3.3 Home route: goal and priority tiles with active initiative counts
- [x] 3.4 Check: test `/` shows 5 goal tiles and 6 priority tiles with counts

*Note 2026-10-05: `app/queries.py` was added for the home screen. No view covers "initiative count per goal/priority", and putting SQL in the route would be the only alternative; `repo.py` (task 6.1) will be the write-side counterpart. Task 3.1's nav links to `/meeting` and `/checks`, which do not exist until group 8 — they currently 404.*

## 4. Goal and priority lists (Wed Oct 7)

- [x] 4.1 Shared `list.html` fed by `vw_GoalInitiatives` or `vw_PriorityInitiatives`
- [x] 4.2 Dean rows, divider, D-1 grouped by owner; primary badge; "No update yet" state
- [x] 4.3 Header with counts by status; no aggregate percent
- [x] 4.4 Rows open the card via HTMX; owner names link to person cards
- [x] 4.5 Check: tests for ordering, divider, badge, empty state, absence of aggregate percent

*Two findings recorded 2026-10-05 while implementing this group:*

- **The list views expose `Owner` as a name and no `OwnerID`**, so linking an owner to `/people/{id}` (task 4.4) requires a name-to-ID lookup in `queries.people_ids_by_name()`. That is only safe while `People.Name` is distinct, and a duplicate name would link to the wrong person silently. Worth adding `OwnerID` to both views — same class of gap as the missing `InitiativeID` in the T-SQL mirror.
- **The sample data cannot produce the "No update yet" empty state.** Every active initiative has a diary entry, and `vw_DataChecks` lists "No progress update yet" as an issue and currently reports none, so the state is unreachable from the seed. The check therefore deletes the diary for one initiative inside the test's private database copy. The same applies to task 5.4's "Needs update" flag for a *missing* update.

## 5. Initiative and person cards (Wed Oct 7)

- [x] 5.1 Initiative route returns fragment or full page by `HX-Request`
- [x] 5.2 Sections: details, tags, Feeds or Fed by from `vw_InitiativeConnections`, latest progress, diary newest first
- [x] 5.3 Every connected item links to its screen; Feeds item swaps the modal content
- [x] 5.4 Person card from `vw_PersonInitiatives` with "Needs update" flag for missing or over-14-day updates
- [x] 5.5 Check: tests for Dean card (Fed by), D-1 card (Feeds), full-page URL, stale flag

*Two decisions recorded 2026-10-05 while implementing this group:*

- **The staleness threshold is 20 days, not 14.** This task said "over-14-day"; the `person-card` spec says "WHEN an initiative's latest update is 20 days old". The spec wins, because it is the requirement this task derives from, and it is the more conservative reading. `queries.STALE_DAYS` holds the value and the check pins it behaviourally by ageing an update 25 days and then 10. **If 14 was the intent, change the spec and the constant together** — they currently agree on 20.
- **`vw_InitiativeConnections` was extended** with `PercentComplete` and `Status`. The `initiative-card` spec requires a Dean card's "Fed by" list to carry owner *and latest progress*, which the view did not provide. Added to both `db/schema.sql` and `db/schema.mssql.sql`; all seven views re-verified column-identical between the two.
- **`vw_GoalInitiatives`, `vw_PriorityInitiatives`, `vw_PersonInitiatives` and `vw_RecentUpdates` gained `InitiativeID`, and the first three plus the connections view gained `OwnerID`.** This removes the name-based person lookup that task 4.4 had needed. Both schema files updated together and re-verified.

## 6. Progress updates (Wed Oct 7)

- [x] 6.1 `app/repo.py` with transactional write helper and constraint-error mapping
- [x] 6.2 Update form fragment: slider with live percent, status select, note limited to 500 characters
- [x] 6.3 POST appends to `ProgressUpdates` with EnteredByID; re-renders card and refreshes the list row
- [x] 6.4 Server-side permission check (owner, Dean, admin); button hidden otherwise
- [x] 6.5 Check: tests for append-only, invalid percent, 403 for non-owner, no Dean rollup

*Note 2026-10-05:* the "refreshes the list row" part is implemented by returning the re-rendered card plus an `HX-Trigger: initiativeUpdated` header, and re-fetching the whole list rather than patching a single row. Patching one row would risk losing the Dean/D-1 ordering, the divider, or the primary badge, since the row partial does not know its position. `repo.update_initiative_details` was added ahead of task 8.1 because 6.1 asks for the transactional write helper and mapping, and having one established path was cheaper than writing a second one in 8.1.

## 7. Demo with sample data (Thu Oct 8)

- [x] 7.1 Full test suite green
- [x] 7.2 Walk: login → pick Bill → Research goal → D-A card → Fed by ELIZ-1 → Elizabeth's card → switch to Elizabeth → add update → list shows new bar
- [ ] 7.3 Capture feedback from the team as follow-up items

*7.1 and 7.2 verified 2026-10-05: 87 tests pass, and the whole walk was executed against a real `uvicorn` server over HTTP (login, passcode, person picker, home tiles, goal list, D-A card with Fed by, ELIZ-1 card with Feeds, person switch, update form, POST, and the list re-fetch showing the new 55% bar with the at-risk colour). 7.3 needs people in a room and is deliberately left open.*

## 8. Admin editing, meeting page, intake (Thu Oct 8 - Fri Oct 9)

- [x] 8.1 Edit details (owner or admin) with AuditLog row
- [x] 8.2 Edit tags: checkbox lists for goals and priorities, radio for primary; replace in one transaction
- [x] 8.3 Edit links: checkbox list of Dean initiatives (D-1 cards only)
- [x] 8.4 Create initiative and retire initiative; edit goal and priority descriptions
- [x] 8.5 `/meeting` from `vw_RecentUpdates` and latest-status query: attention list, changes grouped by owner, date picker, print CSS
- [x] 8.6 `/checks` page listing `vw_DataChecks` with links
- [x] 8.7 `scripts/make_template.py`: Initiatives sheet with dropdowns and X columns, plus Goals, Priorities, People sheets
- [x] 8.8 `scripts/import_xlsx.py`: temp-copy load, upsert by Code, retire missing, run checks, report by sheet row, atomic swap only with zero errors
- [x] 8.9 Check: tests for 403 on admin routes, primary-tag error message, audit rows, meeting window, clean and failing imports, diary preserved after re-import

## 9. Hardening and Azure App Service deploy (Fri Oct 9)

*Group 9 was "Hardening and VPS deploy" and was replanned 2026-10-05. Only the tasks whose content was VPS-specific were replaced; every platform-independent hardening task was carried over unchanged. `deploy/`, `scripts/`, and `compose.yaml` were never created, so nothing was deleted.*

- [x] 9.1 `APP_ENV` setting; "LOCAL" banner; Secure cookies when live; **enable `httpsOnly` on the live web app (currently `false` — see design.md decision 14)**
- [x] 9.2 Login lockout (in-memory counter per IP), `X-Robots-Tag` header, `robots.txt`, `/healthz` — *carried over unchanged*
- [x] 9.3 `scripts/backup.py` with 14-copy retention; run at startup and daily in a background task; also callable before imports — *carried over, but note Azure SQL (Track 1) supplies its own backup/PITR and this task is then deleted rather than ported*
- [ ] 9.4 `Dockerfile` (python:3.12-slim, non-root user) retained for local dev only; **drop** `compose.yaml` and its `127.0.0.1:8085` port mapping, named volume, and `/healthz` compose healthcheck — replaced by 9.4a
- [ ] 9.4a **BLOCKED 2026-10-06** Live deploy via `az webapp deploy` (zip with forward-slash entries; Oryx builds deps when `SCM_DO_BUILD_DURING_DEPLOYMENT=true`), then restart; assert `/healthz` returns 200 — *replaces the old `deploy/deploy.sh` ssh path*
- [ ] 9.5 ~~Reverse proxy: add a site block for the subdomain to the existing proxy, or add a Caddy service with automatic HTTPS~~ **CANCELLED 2026-10-05** — TLS terminates at the platform; no proxy to configure
- [ ] 9.6 ~~`deploy/deploy.sh`: ssh, `git pull`, `docker compose up -d --build`, curl `/healthz`, print result~~ **REPLACED by 9.4a** — no SSH host
- [ ] 9.7 ~~`scripts/pull_live.sh`: copy newest VPS backup to `./cll_live_copy.db`~~ **CANCELLED 2026-10-05** — retrieving a copy is now a Kudu/SCM download of the backup file; no script needed for a prototype
- [ ] 9.8 First deploy with sample data; set a strong `APP_PASSCODE` and random `APP_SECRET` as App Service app settings — *secret storage retargeted from a VPS `.env` file*
- [ ] 9.9 Check: tests for lockout, noindex, healthz outside gate, local banner; from a phone off Wi-Fi, the site loads over HTTPS and asks for the passcode

## 10. Live data and first meeting (Fri Oct 9 - Wed Oct 14)

- [ ] 10.1 Confirm data-policy answer (design.md Open Questions); if not cleared, keep the live site on sample data and run meetings locally — **the live site is on a personal `Azure for Students` subscription, so this question is unresolved as of 2026-10-05 and no real data may land until it is**
- [ ] 10.2 Send `intake_template.xlsx` to Elizabeth, Tim, and Mario (and other D-1 owners) on Fri Oct 9
- [ ] 10.3 Mon Oct 12: upload the filled template to the live instance via the Kudu/SCM file API and run the importer; clear `/checks` to zero errors — *was: `scp` to `/data/inbox/` and `docker compose exec` in the container*
- [ ] 10.4 Send the URL, passcode (separately), and a two-line how-to to owners; ask for first updates before Wed Oct 14
- [ ] 10.5 Check: Dean opens `/meeting` on Wed Oct 14 and sees updates from every owner

*Open questions recorded 2026-10-05 while building 8.5 and 8.6:*

- **The attention list excludes `Off track`.** The `meeting-view` spec defines it as "WHEN an initiative's latest status is *At risk* THEN it appears in the attention list", so that is what was built - even though a stalled initiative seems more deserving of attention than a merely shaky one. Pinned by `test_off_track_is_not_in_the_attention_list` so that changing it is deliberate. **If `Off track` (and possibly `Paused`) belong, amend the spec, not just the query.**
- **`vw_RecentUpdates` had a comment that lied.** It claimed to filter to a date range and sort newest-first, and did neither. The comment in both `db/schema.sql` and `db/schema.mssql.sql` now states that the window and the ordering are the caller's job, which is what lets the one view serve any meeting window.

*Two gaps found and closed while building 8.7 and 8.8 (2026-10-05). Both were
chicken-and-egg deadlocks that made the intake feature unusable as specified:*

- **The workbook had no way to express links.** `vw_DataChecks` flags "D-1 initiative not linked to any Dean initiative" and the importer refuses any import that leaves a check outstanding. So a workbook that created a new D-1 initiative could never import. Added a **`Feeds`** column carrying the Dean codes, with a dropdown of active Dean initiatives.
- **The workbook had no way to express a first progress update.** `vw_DataChecks` also flags "No progress update yet", so a brand-new initiative failed the same gate. Added **`Percent`** and **`Status`** columns; a filled-in pair creates the initiative's opening diary entry.

Neither column is in the task text or the `data-intake` spec, which describes the
template only as "dropdowns and X columns". **The `data-intake` spec should be
amended to describe them.**

---

## Deploy state, 2026-10-06 (honest record)

`wrangler`-free Azure deploy of the full app was attempted against
`cll-dash-proto-kwong27`. **The deploy reports success but the new code is
not being served, and the cause is not yet established.**

What is known:

- The zip is correct: 30 entries, forward slashes only, no `__pycache__`,
  and its `app/main.py` contains both `access_gate` and `robots_txt`.
- `az webapp log deployment show` reports **Deployment successful**, with no
  rsync errors and no "failed to stat" in any of the 23 logged deployments.
- The site nevertheless serves the **old** placeholder HTML - a string that
  exists only in the earlier abandoned `fastapi-container/app/main.py`.
- `/healthz` and `/robots.txt` return **404**, which the new code defines, so
  the new code is definitively not live. An explicit `az webapp restart`
  did not change this.
- A `/healthz` marker (`DEPLOY_MARKER`, echoed as `ok <marker>`) was added so
  this question is answerable over plain HTTP without shell access.
- The Kudu VFS API returns **401**: the credentials
  `az webapp deployment list-publishing-credentials` returns are 8 characters
  long, which is not a real App Service publishing credential. So the
  instance's filesystem cannot be read to diagnose this, and `az webapp ssh`
  is unavailable on the free tier.

Leading hypothesis, **not verified**: App Service's incremental OneDeploy is
not replacing the already-present `app/` files, so the previous deployment's
copy survives. Clearing it needs either filesystem access (blocked) or a new
web app.

**Not claimed as done.** 9.4a and 9.8 stay open until a probe of the live
site shows `ok <marker>` and a 303 from `/` to `/login`.