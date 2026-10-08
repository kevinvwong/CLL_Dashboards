# Azure Stack Requirements — CLL Initiative Dashboard

**Prepared:** 2026-10-08
**Service:** Dean's weekly leadership-meeting dashboard (CLL Initiative Dashboard)
**Requesting:** two environments — **production and development** — for a new
service to be built on the Georgia Tech tenant.

> This is a forward-looking build request. It describes what the service needs,
> not any existing deployment. Region, subscription and tenant are for GT A&I /
> OIT to confirm (see *Items requiring a decision*).

---

## 1. What the service is

A Python web application for the College of Lifetime Learning. It presents the
College's strategy portfolio — the 29 Team Initiatives, six annual priorities,
five Strategy 2035 goals, four teams, and the Dean's own initiatives — read from
a database, behind authenticated access. It supports the Dean's weekly
leadership meetings and strategic decision-making, and carries an in-app guide.

Runtime and framework are fixed by the application:

| Item | Value |
|---|---|
| **Runtime stack** | **Python 3.12**, Linux |
| **Framework** | FastAPI + Uvicorn, served in production by a Gunicorn ASGI worker |
| **Build** | Oryx build from the deploy archive; `SCM_DO_BUILD_DURING_DEPLOYMENT=true`, install from `requirements.txt` |
| **Startup command** | `gunicorn --bind=0.0.0.0:8000 --timeout 600 -k uvicorn.workers.UvicornWorker app.main:app` — App Service's default **sync/WSGI** worker returns HTTP 500 against this ASGI app |
| **Estimated users** | ~40 registered (4 teams, 6 owners, Dean, admin); **≤10 concurrent** at a leadership meeting. Size for ~25 concurrent. |

### Required application settings (keys only)

| Key | Purpose | Notes |
|---|---|---|
| `CLERK_SECRET_KEY` | Identity provider backend secret (server-side only) | **Secret → Key Vault.** The app verifies sign-in tokens; institutional SSO is provided through this identity provider. |
| `CLERK_PUBLISHABLE_KEY` | Identity provider publishable key (public) | Non-secret; set as a plain app setting. |
| `CLERK_AUTHORIZED_PARTY` | Origin(s) allowed to mint a session | Set to the service's own host. |
| `AUTH_PROVIDER` | Selects the authentication adapter | `clerk` in every provisioned environment. |
| `APP_SECRET` | Signs session cookies | **Secret → Key Vault.** Rotating it invalidates all sessions. |
| `APP_ENV` | `live` forces Secure cookies | Set to `live`. |
| `DOCS_PATH` | Root for the rendered in-app guide | `./docs`. |
| `DB_PATH` | SQLite path — **superseded by the managed database connection** | Retained only as a local-dev fallback. |
| **Azure SQL connection string** | The managed database connection | **Secret → Key Vault** (or a managed-identity connection with no secret; see §3). |
| `DEPLOY_MARKER` | Revision marker echoed by `/healthz` | Set per deploy. |
| `MEETING_ENABLED` | Enables an optional meeting surface | Off by default. |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | Enables Oryx install | `true`. |

> App Service's built-in Linux Python runtime requires a **startup file**
> (`--startup-file`), and `az webapp deploy` exits `1` even on success — the
> `/healthz` marker poll is the real deploy verdict.

---

## 2. The two environments

The service is built with a **production** and a **development** environment,
each self-contained, sharing only the monitoring workspace and the alert group.

| Resource | Development | Production |
|---|---|---|
| **Resource group** | `rg-cll-dash-dev` | `rg-cll-dash-prod` |
| **App Service Plan** (Linux) | **Basic B1** | **Standard S1** |
| **Azure SQL Database** | **Basic (5 DTU)** | **Serverless General Purpose `GP_S_Gen5_1`** (auto-pause) |
| **Azure Key Vault** | `cll-dash-dev-kv` (Standard) | `cll-dash-prod-kv` (Standard) |
| **Application Insights** | `cll-dash-dev-ai` | `cll-dash-prod-ai` |

**Plan-tier rationale.**

- **Production — Standard S1.** Adds **deployment slots** (needed for a safe
  release/rollback path), higher autoscale headroom and 5 staging slots. A
  production web app benefits from slots so a new revision can be warmed before
  it takes live traffic.
- **Development — Basic B1.** An always-on, always-available tier without
  production's slot and scale requirements. Adequate for integration testing.
- **P0v3 (Premium v3)** is an alternative for either if stronger isolation or
  faster cold start is required, at higher cost.

**Database-tier rationale.**

- **Production — Serverless GP_S_Gen5_1.** Auto-pauses when idle (low cost for an
  internal tool with a weekly usage rhythm) and scales compute on demand. This is
  the target tier named in the schema's own port notes (`db/mssql/`).
- **Development — Basic.** Cheapest fixed tier; the workload is a fraction of
  production's.
- **Standard S1 / GP_Gen5_2** if guaranteed latency (no cold resume) is required
  for production.

---

## 3. Database

| Item | Value |
|---|---|
| **Engine** | **Azure SQL Database** (T-SQL / SQL Server) |
| **Backup retention** | Request **35-day point-in-time restore** (default is 7) plus a **long-term retention (LTR)** policy for institutional records |
| **Geo-redundancy** | Not required for a single-region internal tool; enable read-access geo-redundant backup (RA-GRS) only if off-region DR is mandated |
| **High availability** | Single-region; Business Critical not required |

**Why a managed database is required (not optional).** An App Service deploy
replaces the site's file system, and the application does not recreate a
file-backed database at startup. The service therefore requires a database
**external to the app package** and reachable independently of a deploy. Azure
SQL provides that, plus backups, point-in-time restore and access control that a
bundled file cannot.

**Code prerequisite (owned by this project, not by A&I):** the runtime gains a
SQL driver (`pyodbc`, with the MS ODBC Driver for SQL Server on the Linux image,
or `pymssql`) and, for passwordless access, `azure-identity`. This does not block
provisioning and is listed so the resource request and the roadmap agree.

---

## 4. Supporting resources

| Resource | Needed? | Detail |
|---|---|---|
| **Azure Key Vault** (per environment) | **Yes** | Holds the identity-provider secret, the session-signing secret and the database connection string. App settings reference Key Vault rather than holding plaintext. |
| **Application Insights** (per environment) | **Yes** | Request/failure tracking and dependency telemetry, in addition to the app's `/healthz` endpoint. |
| **Log Analytics workspace** (shared) | **Yes** | The retention and privacy boundary for the telemetry above. One workspace shared by both environments. |
| **Azure Monitor Action Group** (shared) | **Yes** | Application Insights alerts route here; without it, alerts go nowhere. Routes failure/health alerts to the CLL team (GT email or Teams). $0. |
| **Blob Storage** | **Optional / minimal** | Static assets ship inside the app package and are served from the App Service file system — no blob needed for the app. A small storage account (<1 GB) is worth adding only to offload database backups and export files. |
| **Static assets / CDN** | **No** | Assets total ~400 KB (a vendored ~50 KB htmx, one ~59 KB stylesheet, self-hosted woff2 fonts, an SVG logo). The script library is vendored by design so the app works with no CDN. |

---

## 5. Identity and access

| Item | Detail | Cost |
|---|---|---|
| **Entra ID App Registration + Enterprise Application** | Registered in the GT tenant for the service. Institutional sign-in is provided through the identity provider wired to this registration. **Entra holds the six coarse application roles and emits them in the `roles` claim; the application consumes that claim, while finer-grained assignments (which initiative, approvals) remain application data.** What GT Identity owns (role definitions, membership) versus what the app owns is a scoping question, not an assumption. | $0 |
| **Application roles** (six, capability-oriented) | `Administrator`, `ExecutiveSponsor`, `DataOwner`, `Operator`, `Contributor`, `Viewer`. These are **not a hierarchy** (DR-05/DR-23): each carries a different authority — technical, strategic-decision, data-governance, operational, contribution, consumption. The Executive Sponsor (the Dean) holds portfolio-wide read plus executive-action authority but **no** routine data-maintenance authority. See the App Registration row above for the provider/app ownership boundary. | $0 |
| **Role-assignment licensing** | Application roles are a **core Entra feature ($0)** to define. Whether GT's tenant requires a **premium tier to assign groups to app roles** is to be confirmed with GT Identity. Assigning **users** directly does not raise this question; **group-based** assignment depends on tenant policy. | TBC |
| **System-assigned Managed Identity** (per Web App) | Lets each web app read Key Vault and authenticate to Azure SQL **without a password** (Entra token auth), removing the connection-string secret entirely. One per environment. | $0 |
| **Entra ID admin + app identity on Azure SQL** (AAD-only auth) | The managed identity is granted database access; SQL password authentication is disabled. Required for passwordless DB access. | $0 |
| **RBAC assignments for the CLL team** | Azure role assignments so named CLL staff can administer and monitor the service (e.g. Contributor on the resource groups, Monitoring Reader on the shared workspace, Key Vault secrets access as appropriate). These are Azure-plane roles, distinct from the **application** roles above. Exact roles and principals to be confirmed with A&I at scoping. | $0 |

---

## 6. Networking

- **Endpoint:** **Public**, HTTPS-only (TLS 1.2+), with a **restricted inbound
  allow-list** (GT network / VPN ranges).
- **Outbound:** the service calls **Azure SQL** and the **identity provider**
  only. No other external APIs.
- **Database access:** reach the database over a **Private Endpoint**
  (`Public network access = Disabled`) if the data classification requires it;
  otherwise a firewall allow-list.
- **Custom domain (production):** a GT service should present `*.gatech.edu`, not
  `*.azurewebsites.net`. The **App Service Managed Certificate is free** and
  auto-renewing; the **DNS record is a GT OIT lead-time item**.
- **CORS:** none — same-origin only.

---

## 7. Summary

| Resource | Type | Tier | Required by |
|---|---|---|---|
| `cll-dash-prod-plan` | App Service Plan (Linux) | Standard S1 | Production launch |
| `cll-dash-prod-app` | Web App | on plan | Production launch |
| `cll-dash-prod-app/staging` | Deployment Slot | free with S1 | Release/rollback path |
| `cll-dash-prod-sql` / `cll-dash-prod-db` | Azure SQL server / database | Serverless GP_S_Gen5_1 | Production launch |
| `cll-dash-prod-kv` | Key Vault | Standard | Production launch |
| `cll-dash-prod-ai` | Application Insights | Pay-as-you-go | Production launch |
| `cll-dash-dev-plan` | App Service Plan (Linux) | Basic B1 | Development |
| `cll-dash-dev-app` | Web App | on plan | Development |
| `cll-dash-dev-sql` / `cll-dash-dev-db` | Azure SQL server / database | Basic | Development |
| `cll-dash-dev-kv` | Key Vault | Standard | Development |
| `cll-dash-dev-ai` | Application Insights | Pay-as-you-go | Development |
| `cll-dash-logs` | Log Analytics workspace (shared) | Pay-as-you-go | At launch |
| `cll-dash-alerts` | Azure Monitor Action Group (shared) | — | At launch |
| `clldashstorage` | Storage account (optional) | Standard LRS | Optional |
| `cll-dash-identity` | Entra ID App Registration + Enterprise App | — | **Request now** |
| `cll-dash-{dev,prod}-app` (identity) | System-assigned Managed Identity | — | With each web app |
| `cll-dash-prod-app` (domain) | Custom domain + Managed Certificate | — | DNS by GT OIT |
| *(none)* | CDN / Static assets | — | Not required |

**Estimated total: ~$100–185/month** for both environments (prod S1 + serverless
SQL + dev B1 + Basic SQL + two Key Vaults + monitoring). Development alone is
estimated at ~$20–35/month; production at ~$80–140/month.

> Cost figures are indicative (pay-as-you-go, Linux, USD, East US). Region and
> any education/enterprise agreement will change them. Confirm against the GT
> Azure agreement before submission.

---

## Items requiring a decision

1. **Subscription, tenant and region** — to be confirmed by GT A&I / OIT. The
   service proposes **East US 2** (nearest Azure region to Atlanta) but the region
   is OIT's to select.
2. **SQL tier** — Serverless (auto-pause, the stated target) vs a fixed tier for
   guaranteed latency.
3. **Networking posture** — public + IP allow-list, or a private endpoint for the
   database, per the data classification.
4. **Custom domain** — confirm the GT hostname (`*.gatech.edu`) and raise the
   **DNS record with GT OIT** early; it is the longest-lead external item.
5. **RBAC scope** — confirm the roles and CLL principals for the team's
   assignments (§5).

**What this document is based on:** the application's declared runtime
(`pyproject.toml`, `requirements.txt`, `Dockerfile`), its configuration surface
(`app/config.py`), and the T-SQL schema port under `db/mssql/`.
