# Tasks

Open questions in design.md do not block groups 1-8; sample data stands in. Group 10 needs the data-policy answer before live data goes on the VPS.

## 1. Project setup (Tue Oct 6)

- [x] 1.1 Add `requirements.txt`: fastapi, uvicorn[standard], jinja2, python-multipart, itsdangerous, openpyxl, pytest, httpx
- [x] 1.2 Add `.env.example` with APP_PASSCODE, APP_SECRET, DB_PATH, BACKUP_DIR, PORT
- [x] 1.3 `app/config.py` loads settings from env or `.env`
- [x] 1.4 `app/db.py`: connection with foreign keys on, WAL, busy timeout 5000 ms, rows as dicts
- [x] 1.5 Vendor `htmx.min.js` into `app/static/`
- [x] 1.6 `tests/conftest.py`: fixture builds a fresh sample database per test and a logged-in TestClient per person
- [x] 1. 7 Check : `python db/build_db.py` reports 0 issues ; `uvicorn app.main:app` serves a placeholder page

## 2. Access gate (Tue Oct 6)

- [ ] 2.1 Middleware: no passcode cookie redirects to `/login`; static files exempt
- [ ] 2.2 `/login` and `/whoami` pages; signed cookies; header shows current person with Switch link
- [ ] 2.3 `app/auth.py` helpers: `current_person()`, `can_update(code)`, `can_edit_details(code)`, `is_admin()`
- [ ] 2.4 Check: tests for redirect without passcode, redirect without person, and successful entry

## 3. Base layout and home (Tue Oct 6)

- [ ] 3.1 `base.html`: header, nav (Home, Meeting, Checks), `<dialog>` for modals, print stylesheet
- [ ] 3.2 `style.css`: tiles, list rows, status-colored bars, divider, badges
- [ ] 3.3 Home route: goal and priority tiles with active initiative counts
- [ ] 3.4 Check: test `/` shows 5 goal tiles and 6 priority tiles with counts

## 4. Goal and priority lists (Wed Oct 7)

- [ ] 4.1 Shared `list.html` fed by `vw_GoalInitiatives` or `vw_PriorityInitiatives`
- [ ] 4.2 Dean rows, divider, D-1 grouped by owner; primary badge; "No update yet" state
- [ ] 4.3 Header with counts by status; no aggregate percent
- [ ] 4.4 Rows open the card via HTMX; owner names link to person cards
- [ ] 4.5 Check: tests for ordering, divider, badge, empty state, absence of aggregate percent

## 5. Initiative and person cards (Wed Oct 7)

- [ ] 5.1 Initiative route returns fragment or full page by `HX-Request`
- [ ] 5.2 Sections: details, tags, Feeds or Fed by from `vw_InitiativeConnections`, latest progress, diary newest first
- [ ] 5.3 Every connected item links to its screen; Feeds item swaps the modal content
- [ ] 5.4 Person card from `vw_PersonInitiatives` with "Needs update" flag for missing or over-14-day updates
- [ ] 5.5 Check: tests for Dean card (Fed by), D-1 card (Feeds), full-page URL, stale flag

## 6. Progress updates (Wed Oct 7)

- [ ] 6.1 `app/repo.py` with transactional write helper and constraint-error mapping
- [ ] 6.2 Update form fragment: slider with live percent, status select, note limited to 500 characters
- [ ] 6.3 POST appends to `ProgressUpdates` with EnteredByID; re-renders card and refreshes the list row
- [ ] 6.4 Server-side permission check (owner, Dean, admin); button hidden otherwise
- [ ] 6.5 Check: tests for append-only, invalid percent, 403 for non-owner, no Dean rollup

## 7. Demo with sample data (Thu Oct 8)

- [ ] 7.1 Full test suite green
- [ ] 7.2 Walk: login → pick Bill → Research goal → D-A card → Fed by ELIZ-1 → Elizabeth's card → switch to Elizabeth → add update → list shows new bar
- [ ] 7.3 Capture feedback from the team as follow-up items

## 8. Admin editing, meeting page, intake (Thu Oct 8 - Fri Oct 9)

- [ ] 8.1 Edit details (owner or admin) with AuditLog row
- [ ] 8.2 Edit tags: checkbox lists for goals and priorities, radio for primary; replace in one transaction
- [ ] 8.3 Edit links: checkbox list of Dean initiatives (D-1 cards only)
- [ ] 8.4 Create initiative and retire initiative; edit goal and priority descriptions
- [ ] 8.5 `/meeting` from `vw_RecentUpdates` and latest-status query: attention list, changes grouped by owner, date picker, print CSS
- [ ] 8.6 `/checks` page listing `vw_DataChecks` with links
- [ ] 8.7 `scripts/make_template.py`: Initiatives sheet with dropdowns and X columns, plus Goals, Priorities, People sheets
- [ ] 8.8 `scripts/import_xlsx.py`: temp-copy load, upsert by Code, retire missing, run checks, report by sheet row, atomic swap only with zero errors
- [ ] 8.9 Check: tests for 403 on admin routes, primary-tag error message, audit rows, meeting window, clean and failing imports, diary preserved after re-import

## 9. Hardening and VPS deploy (Fri Oct 9)

- [ ] 9.1 `APP_ENV` setting; "LOCAL" banner; Secure cookies when live
- [ ] 9.2 Login lockout (in-memory counter per IP), `X-Robots-Tag` header, `robots.txt`, `/healthz`
- [ ] 9.3 `scripts/backup.py` with 14-copy retention; run at startup and daily in a background task; also callable before imports
- [ ] 9.4 `Dockerfile` (python:3.12-slim, non-root user) and `compose.yaml` (service `cll-dashboard`, `127.0.0.1:8085:8000`, volume `cll-data:/data`, `restart: unless-stopped`, healthcheck on `/healthz`)
- [ ] 9.5 Reverse proxy: add a site block for the subdomain to the existing proxy, or add a Caddy service with automatic HTTPS
- [ ] 9.6 `deploy/deploy.sh`: ssh, `git pull`, `docker compose up -d --build`, curl `/healthz`, print result
- [ ] 9.7 `scripts/pull_live.sh`: copy newest VPS backup to `./cll_live_copy.db`
- [ ] 9.8 First deploy with sample data; set a strong `APP_PASSCODE` and random `APP_SECRET` in the VPS `.env`
- [ ] 9.9 Check: tests for lockout, noindex, healthz outside gate, local banner; from a phone off Wi-Fi, the site loads over HTTPS and asks for the passcode

## 10. Live data and first meeting (Fri Oct 9 - Wed Oct 14)

- [ ] 10.1 Confirm data-policy answer (design.md Open Questions); if not cleared, keep the VPS on sample data and run meetings locally
- [ ] 10.2 Send `intake_template.xlsx` to Elizabeth, Tim, and Mario (and other D-1 owners) on Fri Oct 9
- [ ] 10.3 Mon Oct 12: `scp` filled template to `/data/inbox/`, run importer in the container, clear `/checks` to zero errors
- [ ] 10.4 Send the URL, passcode (separately), and a two-line how-to to owners; ask for first updates before Wed Oct 14
- [ ] 10.5 Check: Dean opens `/meeting` on Wed Oct 14 and sees updates from every owner
