# Azure Stack Requirements — CLL Initiative Dashboard

**Prepared:** 2026-10-07
**Service:** Dean's Wednesday leadership-meeting dashboard (CLL Initiative Dashboard)
**Current live footprint:** App Service `clldashproto2kwong27` on plan `cll-dash-proto-plan` (F1 Free), resource group `rg-cll-dash-proto`, region `westus`, on a personal *Azure for Students* subscription.

> **Blocking context (from `docs/ops/LAUNCH_RECORD.md`):** the current F1 Free plan is stopped by its own quota (`WPStopRequests` 80/15) and returns 403 to all users; the service also sits outside the Georgia Tech tenant, which GT has not cleared for hosting. **Both conditions must be resolved by this provisioning request.** Nothing here is approved to carry real institutional data until the data-policy question is closed.

---

## 1. Azure Web App

| Item | Value |
|---|---|
| **Runtime stack** | **Python 3.12** (Linux). Confirmed by `pyproject.toml` (`requires-python = ">=3.12"`), `Dockerfile` (`python:3.12-slim`), and CI (`.github/workflows/docker.yml`). |
| **Framework** | FastAPI + Uvicorn, served in production by a Gunicorn ASGI worker. |
| **Build** | Oryx build from the deploy zip; `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, install from `requirements.txt`. |
| **Startup command** | `gunicorn --bind=0.0.0.0:8000 --timeout 600 -k uvicorn.workers.UvicornWorker app.main:app` — App Service's default **sync/WSGI** worker will return HTTP 500 against this ASGI app. |
| **Recommended plan tier** | **Basic B1** to leave the free tier immediately; **Standard S1** for launch (see justification). |
| **Deployment slots** | **1 staging + 1 production** (requires Standard or Premium). |
| **Estimated users** | ~40 registered (4 teams, 6 owners, Dean, admin); **≤10 concurrent** at a leadership meeting. Size for ~25 concurrent. |

### Plan-tier justification

- **F1 Free is disqualified.** `alwaysOn` is unavailable and the 15-per-hour stop-request cap stops the *whole shared plan*, so the app cannot stay up. A paid tier both enables `alwaysOn` and removes the cap.
- **B1 (Basic, Linux)** is the minimum that fixes the outage: `alwaysOn`, always-available, no stop-request cap. Suitable for the demo/sample-data phase.
- **S1 (Standard, Linux)** is the recommended **launch** tier: adds **deployment slots** (the runbook's rollback relies on deployment history), higher autoscale headroom, and 5 staging slots. This is proportionate for an institutional service. **P0v3 (Premium v3)** is an alternative if stronger isolation/faster cold start is required, at higher cost.
- The app is stateless apart from the database file; it scales horizontally once the DB moves to Azure SQL (see §2).

### Required app settings (keys only)

| Key | Purpose | Notes |
|---|---|---|
| `APP_PASSCODE` | Shared access passcode | **Secret → Key Vault.** From `.env` today. |
| `APP_SECRET` | Signs session cookies (itsdangerous) | **Secret → Key Vault.** Rotating it invalidates all sessions. |
| `APP_ENV` | `live` forces Secure cookies | Set to `live`. |
| `DB_PATH` | SQLite path — **superseded by the Azure SQL connection string** once migrated | See §2. |
| `BACKUP_DIR` | Backup output path | Currently `./backups`. |
| `PORT` | Listen port | Injected by App Service. |
| `DEPLOY_MARKER` | Revision marker echoed by `/healthz` | Set per deploy (runbook step 2). |
| `MEETING_ENABLED` | Re-enables the iced `/meeting` route | Off by default. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | Enables Oryx install | `true`. |
| `WEBSITES_ENABLE_APP_SERVICE_STORAGE` | Only if persistent local disk is retained | Prefer Azure SQL over local disk. |
| **Azure SQL connection string** | New — replaces `DB_PATH` | **Secret → Key Vault.** See §2. |

> Note: App Service's built-in Linux Python runtime requires a **startup file** (`--startup-file`), and `az webapp deploy` exits `1` even on success — the runbook's `/healthz` marker poll is the real verdict.

---

## 2. Azure SQL / Database

| Item | Value |
|---|---|
| **Engine** | **Azure SQL Database** (T-SQL / SQL Server). The repo has already ported to T-SQL: `db/mssql/001`–`007`, a 27-table Revision 2 model with constraints, cardinality rules, canonical-protection triggers and read models. `db/mssql/001_rev2_tables.sql` names the target explicitly: **Serverless General Purpose, `GP_S_Gen5`**. |
| **Recommended tier** | **Basic (5 DTU, 2 GB)** for the current sample-data phase; **Serverless GP_S_Gen5_1 (auto-pause)** as the repo's stated target; **Standard S1 / GP_Gen5_2** if real institutional data and guaranteed latency are required. |
| **Estimated storage** | Current SQLite DB is **216 KB, 17 tables, 13 views**. Real portfolio data is on the order of tens of MB at most. **Allocate 2 GB (Basic includes it).** |
| **Backup retention** | Azure SQL default PITR is 7 days. **Request 35-day PITR**, plus a **long-term retention (LTR) policy** for institutional records. |
| **Geo-redundancy** | **Not required** for a single-region internal tool. Enable **read-access geo-redundant backup (RA-GRS)** if off-region DR is mandated. |
| **Region** | **East US / East US 2** — the current `westus` is arbitrary; GT is in Atlanta. Co-locate DB and Web App in one region to avoid egress latency. |

### Why Azure SQL is genuinely required (not optional)

The deploy **zip replaces `/home/site/wwwroot`**, and nothing recreates the SQLite file at startup — shipping a zip without `cll_initiatives.db` took the live site down with `database unreachable` (recorded in `DEVIATIONS.md` and the runbook). A file-backed DB under `wwwroot` is **destroyed by every deploy**. Real data requires an external database. The Revision 2 T-SQL port (27 tables, 40 acceptance tests, 38 constraint mechanisms all covered) is already validated against a live Azure SQL instance, so the schema work is done and tested.

> **Residual deviations to accept (documented in `db/mssql/DEVIATIONS.md`):** two constraints are **weaker** in T-SQL than the PostgreSQL reference — deferred/`DEFERRABLE` cardinality checks (immediate triggers + integrity report instead) and `EXCLUDE USING gist` period non-overlap (`sp_getapplock` trigger instead). These are recorded, not hidden.

### Code prerequisites for the SQL migration (owned by this project)

`requirements.txt` currently ships **no SQL driver** and **no Azure identity library** — the T-SQL port was validated with `pymssql` only inside `db/mssql/tests/`. Before the app can read Azure SQL, the runtime gains either **`pyodbc`** (with the MS ODBC Driver for SQL Server on the Linux image) or **`pymssql`**, plus **`azure-identity`** for managed-identity access. This is a code change on the project's side; it does **not** block provisioning and is listed so the resource request and the roadmap agree.

---

## 3. Supporting Resources

| Resource | Needed? | Detail |
|---|---|---|
| **Blob Storage** | **Optional / minimal** | Static assets ship inside the app package and are served from the App Service filesystem — no blob needed for the app. A **small storage account (<1 GB)** is worth adding **only** to offload DB backups and export files (`BACKUP_DIR`, xlsx intake). |
| **Key Vault** | **Yes** | Secrets: `APP_PASSCODE`, `APP_SECRET`, and the **Azure SQL connection string**. Replace the current `.env`/app-settings plaintext with Key Vault references. |
| **Application Insights / Log Analytics** | **Yes** | No telemetry exists today; `/healthz` is the only signal. Add App Insights for request/failure tracking and a Log Analytics workspace for retention. Low volume, low cost. |
| **Azure Monitor Action Group** | **Yes** | App Insights without an action group sends alerts nowhere. One action group routes failure/health alerts to the CLL team (GT email or Teams). $0. |
| **Entra ID App Registration** | **No for the current code — request it anyway** | The app authenticates with a **shared passcode + person picker** signed by `itsdangerous`; it does not use Entra ID today. Institutional SSO is the expected end-state, the registration is **$0**, and taking it now lets the SSO code change proceed without a second procurement. |
| **System-assigned Managed Identity** | **Recommended** | Removes passwords from the app entirely: the Web App reads Key Vault and authenticates to Azure SQL via its managed identity (AAD token auth). Requires **Entra ID auth enabled on Azure SQL** and an AAD admin. $0. |
| **Custom domain + Managed Certificate** | **Recommended** | A GT service should present `*.gatech.edu`, not `*.azurewebsites.net`. The App Service **Managed Certificate is free**; the **DNS record is a GT OIT lead-time item**. $0 (cert). |
| **Static assets / CDN** | **No** | Assets total **~400 KB** (vendored `htmx.min.js` 50 KB, one 59 KB stylesheet, self-hosted woff2 fonts, GT logo SVG). htmx is vendored **by design** so the app works with no CDN access. No CDN required. |

---

## 4. Networking

- **Endpoint:** **Public**, HTTPS-only (TLS 1.2+), with a **restricted inbound allow-list**. The app currently answers a public URL; for institutional data, restrict to the GT network / VPN ranges, or add **VNet integration + Private Endpoint** for the DB.
- **Outbound:** **None.** No external APIs, no third-party services — confirmed by code search (no `requests`/`httpx`/`fetch` in `app/`; `httpx` is a test-only dependency). The only outbound dependency is **Azure SQL**, which should be reached over a **Private Endpoint** (`Public network access = Disabled`) if real data is hosted.
- **CORS:** **None configured** — same-origin only. No cross-origin origins to declare.
- **Inbound auth:** custom passcode gate (30-day signed cookie), login lockout after 10 failures/15 min, `X-Robots-Tag: noindex` on every response, and `robots.txt` disallow-all.

---

## 5. Summary Table

| Resource Name | Type | Tier | Monthly Est. Cost (USD) | Required By |
|---|---|---|---|---|
| `cll-dash-prod-plan` | App Service Plan (Linux) | **Standard S1** (Basic B1 interim) | S1 ~$70 · B1 ~$13 | **Before 2026-10-16** (unblock outage) |
| `cll-dash-prod-app` | App Service (Web App) | n/a (on plan) | included | Before 2026-10-16 |
| `cll-dash-prod-app/staging` | Deployment Slot | n/a (5 free with S1) | included | At launch |
| `cll-sql-prod` | Azure SQL logical server | n/a | included | For real-data launch |
| `cll-dash-prod-db` | Azure SQL Database | **Serverless GP_S_Gen5_1** (auto-pause) · Basic interim | ~$5–50 (usage-based) | For real-data launch |
| `cll-dash-kv` | Azure Key Vault | Standard | <$1 (per-op) | Before 2026-10-16 |
| `cll-dash-ai` | Application Insights | Pay-as-you-go | ~$0–5 (low volume) | At launch |
| `cll-dash-logs` | Log Analytics Workspace | Pay-as-you-go | ~$2–10 | At launch |
| `clldashstorage` | Storage Account (optional) | Standard LRS | <$1 | Optional |
| `cll-dash-identity` | Entra ID App Registration + Enterprise App | — | $0 | **Request now** (SSO lands later) |
| `cll-dash-prod-app` (identity) | System-assigned Managed Identity | — | $0 | With the app |
| `cll-dash-prod-app` (domain) | Custom domain + App Service Managed Certificate | — | $0 (cert) | DNS by GT OIT |
| `cll-dash-alerts` | Azure Monitor Action Group | — | $0 | At launch |
| *(none)* | CDN / Static assets | — | $0 | Not required |

**Estimated total: ~$80–140/month** (Standard S1 + serverless SQL + Key Vault + monitoring), or **~$20–35/month** on the Basic interim tier.

> **Cost figures are indicative** (pay-as-you-go, Linux, USD, East US; region and any education/enterprise agreement will change them). Confirm against the GT Azure agreement before submission.

---

## Items requiring a human decision before this request is final

1. **Tenant & subscription** — must move to the **Georgia Tech tenant**; personal-subscription hosting of institutional planning data is **not cleared** (LAUNCH_RECORD §6.3).
2. **Tier choice** — B1 (demo) vs S1 (launch with slots).
3. **Region** — confirm East US / East US 2 rather than the current `westus`.
4. **SQL tier** — Basic (fixed, cheapest) vs Serverless (repo's stated target, auto-pauses).
5. **Networking posture** — public + IP allow-list, or private endpoint for the DB.
6. **SSO** — keep the app's passcode gate, or fund an Entra ID integration (code change).
7. **Auth posture for SQL** — password in Key Vault, or **managed identity (passwordless)** with Entra auth enabled on the database. The latter is recommended and is why the App Registration is requested now.
8. **Custom domain** — confirm the GT hostname (`*.gatech.edu`) and raise the **DNS record with GT OIT** early; it is the longest-lead item after the tenant move.

**What this document is based on:** `pyproject.toml`, `requirements.txt`, `Dockerfile`, `.env.example`, `app/config.py`, `app/main.py`, `app/auth.py`, `scripts/backup.py`, `db/mssql/001`–`007`, `db/mssql/tests/`, `db/mssql/DEVIATIONS.md`, `db/rev2/PROVENANCE.md`, `docs/ops/DEPLOY.md`, `docs/ops/LAUNCH_RECORD.md`, `.github/workflows/docker.yml`, and a live count of `cll_initiatives.db` (17 tables, 13 views, 216 KB).
