# Stack specification — CLL Initiative Dashboard

**Purpose of this document.** A single, accurate description of the technology
stack, its components and configuration, so a new engineer can provision it
from scratch or take over its operation. It is a *description of what is*, not a
plan: where something is wrong or fragile it says so under known issues.

**Verified** against the running system on 2026-10-08. Facts are cited; nothing
here is aspirational.

---

## 1. What the application is

A server-rendered web dashboard for the Georgia Tech College of Lifetime
Learning (CLL): the Dean's weekly leadership-meeting view of the College's
strategy portfolio. It presents the 29 Team Initiatives, the six annual
priorities, five Strategy 2035 goals, four teams and the Dean's own initiatives,
all read from one SQLite database, behind a shared access gate.

- **Read-mostly.** Owners append progress to their own initiatives; everyone
  signed in reads the whole portfolio.
- **Single-tenant, single-instance, internal.** Not designed for public traffic
  or horizontal scaling.

---

## 2. The stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Language | Python | 3.12 (dev: 3.12.10) | `requires-python >=3.12` in `pyproject.toml` |
| Web framework | FastAPI | 0.135.1 | ASGI; `app.main:app` |
| ASGI server | Uvicorn | 0.41.0 | `uvicorn[standard]`; `UvicornWorker` under gunicorn in production |
| Process manager | Gunicorn | (see `requirements.txt`) | Production startup command, below |
| Templating | Jinja2 | 3.1.6 | `Jinja2Templates`, directory `app/templates` |
| HTML safety | markupsafe | (Jinja2 dependency) | `Markup` for the icon filters |
| Database | SQLite | stdlib `sqlite3` | One file, `cll_initiatives.db`; WAL mode |
| Front-end | HTMX (vendored) | `app/static/htmx.min.js` | No CDN; no build step |
| CSS | Hand-written | `app/static/style.css`, `print.css` | Design tokens in `:root` |
| Icons | Inline SVG | `app/identity.py` | `currentColor`; no icon font |
| Forms / multipart | python-multipart | 0.0.22 | |
| Cookies / signing | itsdangerous | 2.2.0 | `URLSafeTimedSerializer`, signed with `APP_SECRET` |
| Config loading | python-dotenv | 1.2.2 | `.env` |
| Excel (intake) | openpyxl | 3.1.5 | `scripts/make_template.py`, `import_xlsx.py` |
| In-app docs | Python-Markdown | 3.10.2 | renders `docs/**/*.md` |
| HTML sanitiser | bleach | 6.4.0 | sanitises rendered markdown |
| Doc manifest | PyYAML | 6.0.3 | `docs/guide.yaml` |
| Auth provider (optional) | clerk-backend-api | 7.0.0 | verifies Clerk session tokens (ADR-0004) |
| Tests | pytest | 9.1.1 | config in `pyproject.toml` |
| Test HTTP client | httpx | 0.28.1 | via Starlette `TestClient` |
| Lint | Ruff | (dev) | config in `pyproject.toml` |

Runtime dependencies are declared in **`requirements.txt`** (the single source;
the Dockerfile and App Service both install from it). `pyproject.toml` also
lists a `dependencies` table *for tooling only* — see known issues.

**No front-end build tooling.** No npm, no bundler. Templates are server-rendered
and HTMX drives the interactive parts.

---

## 3. Repository layout

```
.
├── app/                     the FastAPI application package (import path app.main:app)
│   ├── main.py              routes, template context, filters, error pages (~983 lines)
│   ├── queries.py           all reads; one function per screen (~1136 lines)
│   ├── repo.py              all writes (one transaction per write) (~330 lines)
│   ├── auth.py              access gate, cookies, PIN credential, roles (~297 lines)
│   ├── guards.py            server-side permission checks (403, not just hidden buttons)
│   ├── status.py            status vocabularies, slugs, glyphs
│   ├── identity.py          goal/team colour tokens and inline SVG icons
│   ├── docs.py              the in-app guide (markdown -> sanitised HTML)
│   ├── priorities.py        canonical priority names/titles
│   ├── config.py            the one config loader (reads .env / environment)
│   ├── db.py                the one connection factory (paths, pragmas, row factory)
│   ├── oct16_data.py        the static build memo (generated; not on the primary page)
│   ├── templates/           39 Jinja2 templates
│   └── static/              style.css, print.css, htmx.min.js, brand/
├── db/                      schema.sql, seed*.sql, build_db.py, seed generators,
│                            schema.mssql.sql (superseded), rev2/ (superseded)
├── scripts/                 build_deploy_zip.py, build_progress_log.py,
│                            make_template.py, import_xlsx.py, backup.py, ...
├── tests/                   the pytest suite (~46 files)
├── docs/                    guide.yaml + guide/, ops/, specs/, source/, adr/, agents/
├── cll_initiatives.db       the committed sample database (a build artefact)
├── requirements.txt         runtime dependencies
├── pyproject.toml           pytest + ruff config
├── run-dashboard.cmd        one-command local launcher (Windows)
├── Dockerfile, docker-compose.yml
└── README.md, AGENTS.md, CLAUDE.md, CONTEXT.md
```

---

## 4. Data model

One SQLite database, `cll_initiatives.db` (196,608 bytes as committed).
**17 tables, 9 views.**

**Tables:** `Goals`, `Priorities`, `Teams`, `SourceAreas`, `TeamInitiatives`,
`TeamInitiativePriorities`, `TeamInitiativeGoals`, `TeamInitiativeUpdates`
(the progress diary), `People`, `Milestones`, `DeanInitiatives`,
`TeamInitiativeDeanLinks`, `TeamInitiativeCoOwners`, `Roles`, `PeopleRoles`,
`AppMeta` (provenance + current plan year), `AuditLog` (the change log).

**Views:** `vw_TeamInitiatives`, `vw_TeamInitiativePriorities`,
`vw_TeamInitiativeGoals`, `vw_TeamSummary`, `vw_LatestTeamInitiativeProgress`,
`vw_DeanInitiatives`, `vw_TeamInitiativeDeanLinks`,
`vw_PriorityMilestoneProgress`, `vw_DataChecks`.

**Key modelling decisions** (recorded as ADRs in `docs/adr/`):
- A **Priority** is identified by `(PlanYear, Code)` — the six recur each year
  (ADR-0001, ADR-0002). Milestones reference `Priorities.PriorityID`.
- **Three status vocabularies stay distinct:** initiative, milestone, outcome
  (ADR-0002).
- **Identity colour is a CSS token keyed by id**, not a database column
  (ADR-0003).
- **Authentication** is a swappable adapter behind one `authenticate()` seam
  (ADR-0004); **roles are local rows** (ADR-0005).

**The database is built, not authored.** `python db/build_db.py` runs
`schema.sql` then the seed files, in order: `seed_sample.sql`,
`seed_team_layer.sql`, `seed_canon_links.sql`, `seed_register.sql`,
`seed_milestones.sql`. The build is **reproducible**: two consecutive builds
produce a byte-identical file (asserted by `tests/test_register_seed.py`). The
committed `.db` is that artefact and **must be regenerated whenever the schema
changes** — see the guard test in §8.

---

## 5. Configuration

All configuration is read by `app/config.py` from the environment (or a `.env`
file), and is the only place a setting is named.

| Setting | Purpose | Dev (`.env`) | Production (App Service) |
|---|---|---|---|
| `APP_PASSCODE` | the shared access passcode | required | set as app setting |
| `APP_SECRET` | signs the session cookies | required | set as app setting |
| `APP_ENV` | `local` or `live`; drives Secure cookies | `local` | `live` |
| `DB_PATH` | the SQLite file | `./cll_initiatives.db` | `./cll_initiatives.db` |
| `BACKUP_DIR` | where `backup.py` writes | `./backups` | (unused live) |
| `PORT` | local port | `8000` | (App Service uses `WEBSITES_PORT`) |
| `MEETING_ENABLED` | un-ices the meeting surface | unset (off) | unset (off) |
| `DOCS_PATH` | docs root for the in-app guide | `./docs` | `./docs` |
| `AUTH_PROVIDER` | `local` or `clerk` (ADR-0004) | `local` | `local` |
| `CLERK_SECRET_KEY` | Clerk backend secret (server-side only) | unset | only if `AUTH_PROVIDER=clerk` |
| `CLERK_PUBLISHABLE_KEY` | Clerk publishable key (public) | unset | only if `AUTH_PROVIDER=clerk` |
| `CLERK_AUTHORIZED_PARTY` | origin(s) allowed to mint a session | localhost defaults | the live origin |
| `CLERK_FRONTEND_API` | optional override; derived from the publishable key | unset | unset |
| `DEPLOY_MARKER` | which build is serving; echoed by `/healthz` | unset (`dev`) | set per deploy |
| `GIT_COMMIT` | short commit, shown in the header stamp | unset | set per deploy |

`.env.example` documents the keys with no values. **`.env` is gitignored and
holds the real dev secrets.**

**Secrets policy:** credentials live only in `.env` (dev) and App Service
settings (production). They are never committed. See the security section (§9).

---

## 6. Provisioning from scratch

### 6.1 Local development

```
git clone <repo>
cd CLL_Dashboards
python -m venv .venv && .venv\Scripts\activate    # Windows
python -m pip install -r requirements.txt
copy .env.example .env                              # then set APP_PASSCODE + APP_SECRET
python db/build_db.py                               # writes ./cll_initiatives.db
```

Run it:

```bat
run-dashboard.cmd            :: resolves its own location, port 8000
```

or by hand from the repo root (the working directory matters — `DB_PATH`
defaults to `./cll_initiatives.db`):

```powershell
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. Sign in with the passcode, then pick a person.

### 6.2 Production (Azure App Service, Linux)

Resources in subscription `92fa8183-a01a-4e33-92e6-c5a053273fb6`:

| Resource | Name | Notes |
|---|---|---|
| Resource group | `rg-cll-dash-proto` | North Central US |
| App Service plan | `cll-dash-proto-plan` | **F1 (Free), Linux** — see §7 |
| Web app | `clldashproto2kwong27` | `kind: app,linux`, `PYTHON\|3.12` |
| URL | `https://clldashproto2kwong27.azurewebsites.net` | |

App Service settings that must be present:

```
APP_ENV=live
DB_PATH=./cll_initiatives.db
DOCS_PATH=./docs
APP_PASSCODE=<secret>
APP_SECRET=<secret>
DEPLOY_MARKER=<set per deploy>
GIT_COMMIT=<short sha, set per deploy>
SCM_DO_BUILD_DURING_DEPLOYMENT=true
WEBSITES_PORT=8000
```

Startup command (the one App Service setting whose flag name is misleading —
it is `--startup-file`, not `--startup-command`):

```
gunicorn --bind=0.0.0.0:8000 --timeout 600 -k uvicorn.workers.UvicornWorker app.main:app
```

The `uvicorn.workers.UvicornWorker` class is **required** for FastAPI (an ASGI
app); the default gunicorn sync worker is WSGI and returns 500.

Rough create sequence (adapt names; the CLI is the `az` wrapper noted in
`docs/ops/DEPLOY.md`):

```powershell
az group create -n rg-cll-dash-proto -l northcentralus
az appservice plan create -n cll-dash-proto-plan -g rg-cll-dash-proto --sku B1 --is-linux
az webapp create -n clldashproto2kwong27 -g rg-cll-dash-proto `
  --plan cll-dash-proto-plan --runtime "PYTHON|3.12"
az webapp config set -n clldashproto2kwong27 -g rg-cll-dash-proto `
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 600 -k uvicorn.workers.UvicornWorker app.main:app"
az webapp config appsettings set -n clldashproto2kwong27 -g rg-cll-dash-proto --settings `
  APP_ENV=live DB_PATH=./cll_initiatives.db DOCS_PATH=./docs `
  SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_PORT=8000 `
  APP_PASSCODE=<secret> APP_SECRET=<secret>
```

Then deploy per §7.1.

---

## 7. Deploy

### 7.1 The procedure

The full runbook is `docs/ops/DEPLOY.md`. In brief:

1. **Build the archive** — `python scripts/build_deploy_zip.py`. It writes
   `deploy.zip`, asserts the database and required files are present, and prints
   an entry count and a **backslash count that must be 0** (Linux Kudu cannot
   stat Windows-style separators).
2. **Set the revision marker and commit** — app settings `DEPLOY_MARKER=<label>-
   <UTC timestamp>Z` and `GIT_COMMIT=<short sha>`.
3. **Deploy** — `az webapp deploy --type zip --src-path deploy.zip`. **This
   command blocks while polling but the deploy succeeds**, and it exits non-zero
   on success. Run it detached and do not trust its exit code.
4. **Verify** — poll `GET /healthz` until it reports the marker just set. *That
   observation, not the command's exit code, is the verdict.* The header stamp on
   any page also shows `<commit> · deployed <time> UTC`.

What the archive contains: `app/**`, `requirements.txt`, `cll_initiatives.db`,
the `db/` files needed to rebuild it, and `docs/` (for the in-app guide).
Excluded: `.env`, `__pycache__/`, `.git/`, tests, and any secret-shaped file.

### 7.2 The `az` wrapper

On Windows `az` is a `.cmd` shim that re-parses arguments (a pipe becomes a
literal `|`). Call the underlying interpreter directly:

```
& "C:\Users\kwong318\aztools\azure-cli\python.exe" -IBm azure.cli <command>
```

---

## 8. Testing and CI

- **Run the suite:** `python -m pytest` from the repo root (config in
  `pyproject.toml`). ~620 tests, 1 skipped (the axe suite skips when no local
  server is up).
- **Stop the local server before running the suite.** A running `uvicorn` holds
  `cll_initiatives.db`, so `tests/test_register_seed.py::test_build_is_reproducible`
  fails spuriously (the build cannot replace a file another process has open).
- **Accessibility:** `tests/test_a11y_axe.py` runs axe-core against a live local
  server; it is skipped offline. Run it after a UI change.
- **Progress log:** `docs/ops/PROGRESS_LOG.md` is generated from git history by
  `scripts/build_progress_log.py`; `tests/test_progress_log.py` fails if it is
  stale. Regenerate it in the same commit as any work (`--check` asserts it is
  current).

### Guard for the committed database

The `.db` is a committed build artefact. If the schema changes and the db is not
rebuilt, the app reads columns that do not exist. `tests/test_committed_db_is_current.py`
opens the committed db directly and asserts it matches what the app expects
(view has `PriorityID`, `current_plan_year` set, milestones key on `PriorityID`).
This exists because a schema change shipped without a rebuild and caused a live
500.

---

## 9. Security posture — and known issues

The application is **internal and behind a shared passcode**. It is not
hardened for public exposure. Known, unresolved items:

1. **Secrets.** `APP_PASSCODE` and `APP_SECRET` live in App Service settings and
   `.env`. Historically a `docker-compose.yml` and commits carried a
   value-shaped passcode/secret; **rotate these and purge them from git
   history** if that has not been done. Treat any value that has appeared in a
   log, transcript or commit as compromised.
2. **Authentication is a stopgap, with Clerk available behind the seam.** The
   default is a shared passcode + a person picker; a PIN closes the
   self-assertion hole for people who have one set. Setting `AUTH_PROVIDER=clerk`
   switches to Clerk session-token verification (ADR-0004), mapping a Clerk user
   to a `People.ClerkUserID`. Entra remains blocked (the host subscription is
   outside the GT tenant). `authenticate()` is the seam either provider slots
   into.
3. **Roles are app-local** (ADR-0005), seeded from the register; there is no
   user administration UI beyond setting a PIN.
4. **No monitoring or alerting.** The only endpoint is `GET /healthz`
   (200 + marker; 503 if the database is unreachable).
5. **SQLite, single instance.** One file on one instance; concurrent writes are
   serialised. Fine for this load; not for scale.

---

## 10. Known issues and technical debt

| Issue | Impact | Where |
|---|---|---|
| **F1 free tier quota** | `WP stop requests` capped at **15/hour**; every deploy, start and idle shutdown counts. Crossing it stops the *whole plan* (403, `state: QuotaExceeded`) until the hourly reset. Deploys and uptime are unreliable. | `docs/ops/DEPLOY.md` |
| **`pyproject.toml` dependency list is stale** | It omits `Markdown`, `bleach`, `PyYAML`; a tool that installs from it (not `requirements.txt`) gets a broken app. | `pyproject.toml` |
| **`db/schema.mssql.sql` predates the register model** | It still describes the old prototype schema; the documented SQL Server port is far behind. | `db/schema.mssql.sql` |
| **`db/rev2/` and `db/mssql/`** | Superseded ("Revision 2") models, kept as records, not the target. | `db/rev2`, `db/mssql` |
| **No CI pipeline** | The suite runs locally; nothing enforces it on push. | `.github/` |
| **Test run dirties the tracked db** | The app opens the tracked `.db`, changing 4 bytes (WAL flag/counter) at offsets 18,19,27,95. Restore with `git checkout -- cll_initiatives.db` **only when the committed db is already current** — see the trap below. | — |

### The one deploy trap to know

**Never run `git checkout -- cll_initiatives.db` between building and packaging
the archive.** The committed db is a build output; checking it out reverts a
fresh rebuild to a stale one and ships a database whose schema doesn't match the
code. This caused a live 500 on 2026-10-08. Build the db, then package — do not
"clean up" the working copy in between.

---

## 11. Handoff checklist

- [ ] Access to the Azure subscription and `rg-cll-dash-proto` granted.
- [ ] `APP_PASSCODE` / `APP_SECRET` rotated and delivered out-of-band.
- [ ] `.env` created locally from `.env.example`.
- [ ] `python db/build_db.py` runs and is reproducible (build twice, compare hashes).
- [ ] `python -m pytest` is green (stop the local server first).
- [ ] Decide the **App Service tier** (F1 vs B1) before any launch needing more
      than one deploy in an hour.
- [ ] Read `docs/ops/DEPLOY.md` (deploy + rollback), `CONTEXT.md` (domain
      vocabulary), and `docs/adr/` (the decisions).
- [ ] Confirm the **data provenance** expected: seeded `mock` vs imported
      `confirmed` (shown on `/outcomes`).
