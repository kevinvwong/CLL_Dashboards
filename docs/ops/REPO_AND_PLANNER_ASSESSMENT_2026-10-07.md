# CLL Dashboard — Repo & Planner Assessment

**Assessment date / revision:** `2026-10-07`, HEAD `86bf60d`, branch `main`.
**Scope:** the CLL Initiative Dashboard codebase and the Microsoft Planner plan that
manages its delivery. Read-only. No production data, Azure, identity, or Planner
change was made.
**Evidence rule:** every claim below cites a file, a test, or a commit. Where a
conclusion could not be verified it is labelled **unverified**. Planner task
status was *not* trusted; it was reconciled against the repository.

> **Credential note.** Two credential locations were found and are reported by
> **location and remediation category only**. No value is reproduced anywhere in
> this document. See §4.

---

## 1. Executive summary

The repository is a **well-tested, single-tenant SQLite prototype** that has grown
well past "prototype" in its **domain modelling** but has not yet grown into its
**platform layer**. Concretely:

- **Strong:** the data model, the register-canon reconciliation, the read/write
  separation (`queries.py` / `repo.py`), the guard seam, and an unusually large
  test suite (**551 passing**, 52 files, 7,312 lines) for a prototype. Change
  logging and a change-log reader exist. The database builds reproducibly.
- **Weak, and the real risk:** **authentication is a shared passcode plus a
  self-asserted person picker** — any holder of one passcode can *be* any person,
  including the Dean or the admin. There is **no Entra ID integration, no user
  groups, no roles beyond one boolean, and no server-enforced per-user scope**.
- **A live credential leak** exists in tracked files and in git history (§4).

**Planner reconciliation headline:** of the 35 Planner tasks, a substantial block
are **functionally complete in the repository but marked "Not started"** — the
prototype is developed, branded, canon-loaded, deployed, and reviewed. The tasks
that are *genuinely* open are the platform ones: **Entra auth, roles/permissions,
administration, and operational readiness**.

**Recommended posture:** treat October 16 as a **frozen demonstration** (the app
already does what the demo needs), and treat the Entra/roles/admin/ops work as a
**separately-sequenced post-October platform programme**. One small slice
(§17) is safe to do now.

---

## 2. Repository architecture summary

| Layer | What exists | Evidence |
|---|---|---|
| Language / runtime | Python 3.12 | `pyproject.toml`, `.github/workflows/docker.yml` |
| Web framework | FastAPI + Uvicorn/Gunicorn | `requirements.txt`, `app/main.py` |
| Templating | Jinja2 (36 templates) | `app/templates/` |
| Interactivity | HTMX (vendored `htmx.min.js`) | `app/static/htmx.min.js` |
| Data store | **SQLite**, single file, committed | `cll_initiatives.db`, `db/schema.sql` |
| AuthN | **Shared passcode → person picker → signed cookies** | `app/auth.py` |
| AuthZ | One boolean (`IsAdmin`) + `is_dean` + owner match | `app/auth.py:172-215`, `app/guards.py` |
| Config | `.env` via `python-dotenv` | `app/config.py` |
| Deployment | Azure App Service; zip deploy | `docs/ops/DEPLOY.md`, `scripts/build_deploy_zip.py` |
| CI | GitHub Actions: pytest + docker smoke | `.github/workflows/docker.yml` |
| Tests | pytest, 52 files, **551 passed / 1 skipped** | run this session |
| Logging | **None** (no structured logs, no app telemetry) | no logger config found |
| Monitoring | `/healthz` only | `app/main.py`, provisioning doc |
| Audit | `AuditLog` table + `/changes` admin page | `db/schema.sql:204`, `app/repo.py:359` |
| Backup | `scripts/backup.py` (SQLite online-backup API) | `scripts/backup.py` |
| Rollback | `docs/ops/DEPLOY.md` §5 (revision + db restore) | `docs/ops/DEPLOY.md` |

**Module sizes (lines):** `queries.py` 1228, `main.py` 960, `oct16_data.py` 453,
`repo.py` 367 (well under the 200-line heuristic, two modules are large but
single-responsibility), `auth.py` 264, `guards.py` 120, `status.py` 132,
`priorities.py` 102.

**Data model (16 objects, `db/schema.sql`):** `Goals` (5), `Priorities` (6),
`Teams` (4), `SourceAreas` (5), `People` (7), `TeamInitiatives` (29),
`TeamInitiativeGoals`, `TeamInitiativePriorities`, `TeamInitiativeUpdates` (the
diary), `TeamInitiativeDeanLinks`, `TeamInitiativeCoOwners`, `DeanInitiatives`
(11), `AuditLog`, plus seven `vw_*` read views.

**Supersession marker:** `db/schema.sql:1-36` and `db/schema.mssql.sql:1-14` both
declare themselves **"SUPERSEDED 2026-10-06 by Revision 2 (db/rev2/, db/mssql/)"**.
Both `db/rev2/` and `db/mssql/` **exist**. This is a fork in the record: the
running app uses the *prototype* schema while a *Revision 2* model is present but
**not wired into the app** (verified: no import of `rev2` in `app/`).

**Untracked, un-ignored directories:** `fastapi-container/` and `source/` are
present on disk, **not tracked, and not matched by `.gitignore`** (verified with
`git check-ignore`). They are a stage-the-wrong-files risk for the next `git add`.

---

## 3. Current implementation inventory

Status vocabulary: **Verified complete / Partially implemented / Present but
unverified / Not implemented / Blocked / Obsolete**.

| Capability | Status | Evidence |
|---|---|---|
| 5 goals + 6 priorities + 4 teams + 29 Team Initiatives seeded from the register | **Verified complete** | `db/build_register_seed.py`, `db/seed_register.sql`, 551 tests |
| Register-canon reconciliation by name (not position) | **Verified complete** | `db/build_canon_links.py`, `tests/test_canon_links.py` |
| Dean Initiatives layer (11) w/ percent-complete | **Verified complete** | `db/schema.sql:267`, `app/queries.py` |
| Team→Dean roll-up edge (61 links) | **Verified complete** | `tests/test_dean_layer.py`, `/dean-initiatives` |
| Progress diary (append-only, attributed) | **Verified complete** | `TeamInitiativeUpdates`, `app/repo.py:109` |
| Change log **write** (audited mutations) | **Verified complete** | `app/repo.py:359`, `tests/test_change_log.py` |
| Change log **read** (`/changes`, admin-only) | **Verified complete** | `app/main.py` `changes_route` |
| Server-side authorization guards (403 not hidden button) | **Verified complete** | `app/guards.py`, `tests/test_guards.py` |
| Admin CRUD: create / retire / edit details / tags / links / goal+priority descriptions | **Verified complete** | `app/repo.py`, `tests/test_admin.py` (31 pass) |
| XLSX intake importer + template generator | **Verified complete** | `scripts/import_xlsx.py`, `scripts/make_template.py`, `tests/test_intake.py` |
| Accessible UI (axe-clean, keyboard, 320–1440px) | **Verified complete** | `tests/test_a11y_axe.py`, `tests/test_goal_labels.py` |
| Deployment (zip) + rollback runbook | **Verified complete** | `docs/ops/DEPLOY.md`, marker deployed |
| Backup / restore (SQLite) | **Verified complete** | `scripts/backup.py`, `tests/` |
| **Entra ID authentication** | **Not implemented** | no MSAL/OIDC/EasyAuth reference in `app/` |
| **User groups / roles / RBAC** | **Not implemented** | only `People.IsAdmin`; no roles table |
| **Record-level / org-scope permissions** | **Not implemented** | `can_*` is owner-or-admin only |
| **Administration UI** (users, roles, reference data) | **Not implemented** | no `/admin`; person picker is the only "admin" |
| **Structured logging / App Insights** | **Not implemented** | no logger; provisioning doc confirms "no telemetry" |
| **Alerts / action group** | **Not implemented** | provisioning request lists it as future |
| **Azure SQL migration** | **Not implemented** (ready resource exists) | `docs/ops/AZURE_PROVISIONING.md`; app is SQLite |
| **Managed identity / Key Vault** | **Not implemented** | provisioning request lists as future |
| **Duplicate-prevention beyond UNIQUE / optimistic locking / versioning** | **Not implemented** | no version column; `write()` uses BEGIN IMMEDIATE only |
| **Soft-delete for all entities except TeamInitiatives** | **Partially implemented** | only `TeamInitiatives.IsActive` |
| **Data-governance metadata** (steward, validation status, period, evidence) | **Not implemented** | no such columns |
| **CI dependency/vulnerability scanning** | **Not implemented** | `.github/workflows/docker.yml` has none |
| Revision 2 schema (`db/rev2/`, `db/mssql/`) | **Obsolete / unwired** | present on disk, referenced by nothing in `app/` |

---

## 4. Security findings

Ordered by severity. **Locations only; no values reproduced.**

### S1 — CRITICAL: credentials committed in a tracked file
- **Location:** `docker-compose.yml`, keys `APP_PASSCODE` and `APP_SECRET`.
- **Evidence:** static sweep found value-shaped literals (lengths 25 and 30) at
  `docker-compose.yml:16-17`; the file **is tracked** (`git ls-files`).
- **Category:** secret-in-source. **Remediation:** rotate both values, move them
  to environment/Key Vault, replace with `${VAR}` references, then purge history.

### S2 — HIGH: `.env` was committed historically
- **Location:** commits `4ee6d3e` ("Initial commit…") and `9436720`.
- **Evidence:** `git log --all -- .env` returns both commits; `.env` is untracked
  today (`.gitignore` covers it) but its values persist in history.
- **Category:** secret-in-history. **Remediation:** rotate; history rewrite or
  git-filter/BFG if the values were real.

### S3 — HIGH: no institutional authentication; identity is self-asserted
- **Location:** `app/auth.py` (whole module), picker in `app/main.py`.
- **Evidence:** access is `APP_PASSCODE` then `POST /whoami {person_id}`; the
  person cookie is signed but the *choice* is user-supplied. There is **zero**
  Entra/OIDC/MSAL/EasyAuth code (sweep returned nothing in `app/`).
- **Consequence:** one shared secret confers **all identities**; the audit log's
  actor is only as trustworthy as that picker.
- **Remediation:** Entra ID sign-in (app registration + `oid` claim as the key;
  the provisioning request already anticipates this as a future need).

### S4 — MEDIUM: lockout is in-memory and single-instance
- **Location:** `app/auth.py:227-263`.
- **Evidence:** `_failures = defaultdict(list)`; docstring explicitly says
  in-memory by design. Resets on restart; not shared across instances.
- **Remediation:** accept for the demo; replace with Entra (which removes the
  passcode surface) or a shared counter if the passcode survives.

### S5 — MEDIUM: no token/session revocation; 30-day cookie
- **Location:** `app/auth.py:30` (`COOKIE_MAX_AGE` 30 days).
- **Evidence:** signed cookie, no server-side session store, no revocation list.
- **Remediation:** short-lived Entra tokens once SSO lands.

### S6 — LOW: no security scanning in CI; no TLS/header controls in app
- **Evidence:** `.github/workflows/docker.yml` runs pytest + docker only; no
  dependency audit. TLS is terminated by App Service (platform), not the app.

---

## 5. Data-governance findings

- **No steward / validation-status / reporting-period / evidence metadata** on any
  entity. The register's own "Named Owner" is held as `People`, but there is no
  data-steward concept (G1).
- **`AuditLog` is thin for compliance** (`db/schema.sql:204`): actor, timestamp,
  action, entity, and a JSON `Details` string exist — but no **reason/source**, no
  **correlation/request id**, no **immutable storage**, no **retention policy**.
  (The `EntityType` derivation bug was found and fixed during this session; the
  map is now explicit — `app/repo.py:_ACTION_ENTITY`.)
- **Soft-delete only on `TeamInitiatives`**; other entities have no archive
  path (G2/§6). Restoration is not implemented.
- **Data-quality checks are minimal** (`vw_DataChecks`): only "no goal tagged" and
  "no priority tagged". No freshness, orphan, or duplicate checks (G3, G4).
- **Two schema generations coexist** (`schema.sql` vs `db/rev2/`), each labelled
  superseded relative to the other — a governance ambiguity that needs a single
  named target (G5).
- **A known faithful-to-source gap:** `MI-017` has no Dean link because the
  register marks none — recorded, not a defect (G6); `MI-026`-style row numbering
  reuses per-team numbers, so `MI-###` is an **invented key** with no register
  counterpart (G7, verified: 0 `MI-` cells in the register).

---

## 6. Operational-readiness findings

| Area | State | Evidence |
|---|---|---|
| Hosting | Personal `Azure for Students`, F1 plan, `northcentralus` | `docs/ops/AZURE_PROVISIONING_REQUEST.md` |
| Availability | Free-tier **stop-quota** (80/15) → 403 to all users observed | provisioning request; DEPLOY.md §4 |
| Monitoring | **None** — `/healthz` is the only signal | provisioning doc; no logger |
| Alerts | **None** (no action group) | provisioning request lists as future |
| Env separation | Weak: `APP_ENV` string only; no separate stage | `app/config.py` |
| Secrets | In app settings + the leak (§4) | DEPLOY.md §Prerequisites |
| Managed identity | Not used | not referenced |
| DB security | SQLite file, no network layer; Azure SQL future | `db.py` |
| TLS/HTTPS | Platform-provided on App Service | not in app |
| Backup | SQLite dated copies, keep 14 | `scripts/backup.py` |
| Migrations | **None** — `build_db.py` drops and rebuilds | `db/build_db.py` |
| Rollback | Documented and exercised (revision + db) | `docs/ops/DEPLOY.md` §5, §Record |
| Release safety | Zip replace (no slots) | DEPLOY.md §3 |
| CI gates | Tests + docker probe only | `.github/workflows/docker.yml` |
| Cost visibility | Not instrumented | — |
| Runbook | Exists and is unusually good | `docs/ops/DEPLOY.md` |

---

## 7. Planner reconciliation summary

All 35 Planner tasks read **Not started**. Repository evidence says this is
**wrong for a large block**. Summary by bucket:

| Bucket | Tasks | Verdict |
|---|---|---|
| Scope | 3 | 1 done, 1 blocked-external, 1 partial |
| Analysis/Requirements | 6 | mostly **done** in the register work |
| Design | 3 | largely **done** (design docs exist) |
| Development | 8 | mixed: 4 done, 4 not started |
| Testing | 3 | 1 done, 2 need splitting |
| Pilot & Deployment | 12 | several done; Board-material tasks not in repo |

Full per-task mapping in §8–§10.

---

## 8. Closed-task candidates

Each: existing task → evidence → confidence → gap → recommendation.

| # | Existing Planner task | Evidence (files / tests / commit) | Confidence | Remaining gap | Recommend |
|---|---|---|---|---|---|
| C1 | Validate Strategy 2035 goals and descriptions | `db/canonical_goals.py`, `tests/test_goal_correctness.py`, `tests/test_canon_links.py` | **High** | none | **Close** |
| C2 | Validate full names and descriptions for the six annual priorities | `app/priorities.py`, `tests/test_priority_definitions.py` (pins all six) | **High** | none | **Close** |
| C3 | Review and validate initiatives | `db/build_register_seed.py` (29 rows), `tests/test_register_seed.py` | **High** | register approval confirmed 2026-10-07 | **Close** |
| C4 | Map people to initiatives | owners 29/29 + co-owners (`TeamInitiativeCoOwners`) | **High** | real names pending Oct 9 (external) | **Close** (owner-data task splits out — see P?) |
| C5 | Reconcile dashboard fields with the Dean's prototype | `docs/specs/2026-10-06-blueprint-redesign-design.md`, `docs/source/DEAN_DECISIONS.md`, 551 tests | **High** | the prototype→register merge superseded the framing | **Close** (or **Supersede**) |
| C6 | Develop prototype based on specifications | whole `app/` tree, deployed markers | **High** | none | **Close** |
| C7 | Apply CLL and Georgia Tech brand assets | `docs/specs/hive/`, `app/static/fonts/`, `app/static/brand/`, `tests/test_visual_system.py` | **High** | none | **Close** |
| C8 | Incorporate canonical data into the prototype | `db/seed_register.sql`, `tests/test_register_seed.py` | **High** | none | **Close** |
| C9 | Document authoritative data sources, owners, and gaps | `docs/source/AUTHORITATIVE_SOURCE.md`, `CONTEXT.md`, `db/README.md` | **Medium** | "owners" per-row partly external | **Close**, split the external part |
| C10 | Review the live prototype and consolidate change requests | `docs/specs/cll-dashboard-analysis-2026-10-06.md`, `…rereview-2026-10-07.md`, `analysis-fix-workflow.md` | **High** | none | **Close** |
| C11 | Verify authenticated access to the deployed prototype | marker `labels-20261007T123612Z` live; login tested | **High** | it authenticated via **passcode**, not Entra | **Close**, add a new Entra task |
| C12 | Deploy major prototype updates to Azure | markers in `LAUNCH_RECORD.md`, `DEPLOY.md` | **High** | superseded by the local=dev/Azure=prod policy | **Close**; **retire** "Deploy software" (see D) |
| C13 | Develop dashboard change logging | `repo.py:359`, `tests/test_change_log.py`, `/changes` | **Medium** | write+read exist; compliance gaps in §5 | **Close** with a follow-on governance task |
| C14 | Implement dashboard data-update functions | `repo.py`, `tests/test_updates.py`, `tests/test_write_path.py` | **High** | none for the diary/edit paths | **Close** |
| C15 | Conduct needs analysis | register + `docs/source/DEAN_DECISIONS.md` + reviews | **Medium** | no single "needs analysis" artefact | **Verify manually** |

---

## 9. Current tasks requiring updates

| # | Existing task | Status (evidence) | Problem with the title | Recommendation |
|---|---|---|---|---|
| U1 | Determine project scope | **partially done** — demo scope clear, platform scope explicit | too broad; no acceptance | **Rename** to *"Confirm October 16 demonstration scope and out-of-scope platform work"*; add criteria |
| U2 | Confirm Azure subscription and account path with IT | **blocked-external** | fine title | **Keep open**; label *Blocked*; the provisioning request exists |
| U3 | Confirm the October 16 Board outcome and MVP scorecard | **not found in repo** | broad | **Keep**; add: scorecard fields, fallback triggers |
| U4 | Draft preliminary software specifications | **done in substance** (two design specs + plans) | vague | **Rename** *"Consolidate specifications: register data model + app architecture"*; link specs |
| U5 | Complete detailed Academic Affairs wording and label review | **partial** — labels renamed (Team/Dean Initiative) | "Academic Affairs" is a stale register area | **Rename** to current vocabulary; verify remaining wording |
| U6 | Implement Entra authentication and user groups | **not implemented** | fine but huge | **Split** into registration, sign-in, claim→role mapping, tests |
| U7 | Resolve open content, ownership, and data-quality decisions | **partial** | lumps three decisions | **Split** into content, ownership (external), data-quality |
| U8 | Conduct user testing | **partial** — browser reviews exist | vague | **Rename** *"Run a scripted Board walkthrough with 3 named reviewers"*; define script |
| U9 | Conduct testing | **done** (551 pass) but title vacuous | redundant with CI | **Retire**; replace with named suites (authz matrix, E2E) |
| U10 | Obtain leadership review and approve the rehearsal version | **not found** | broad | **Keep**; add sign-off artefact |
| U11 | Obtain user feedback | **partial** | vacuous | **Merge** into U8 |
| U12 | Deploy software | **obsolete** | duplicates C12 | **Retire** (superseded) |
| U13 | Notify reviewers when major deployment updates are ready | process, not code | — | **Keep**; low value; consider merging |
| U14 | Prepare Board talking points and demonstration flow | **not found** | fine | **Keep**; add deliverable path |
| U15 | Prepare fallback screenshots of the final dashboard | **not found** | fine | **Keep**; add criteria |

---

## 10. Future tasks

Grouped as requested. Each carries the full task schema in §16.

**Authentication & identity:** Entra app registration; sign-in/logout; `oid`→People
mapping; session/token handling; local-dev auth strategy; remove passcode.

**Authorization & permissions:** roles model; group→role mapping; org-scope
(own-team) permissions; default-deny; access review; break-glass admin.

**Administration:** admin landing; user/role management; reference-data admin;
review/approval queue; safe deactivate/restore.

**CRUD & lifecycle:** add soft-delete + restore for goals/priorities/people/
DeanInitiatives; optimistic locking/version column; duplicate detection.

**Governance & data quality:** steward + validation status + reporting period +
evidence columns; freshness/orphan/duplicate checks; curated-vs-validated labels.

**Audit & compliance:** reason/source + correlation id on `AuditLog`; retention;
redaction; export; immutable storage option.

**Testing:** authorization-matrix suite; Entra sign-in E2E; migration test;
backup/restore test; deployment smoke on the target env.

**Azure operations:** institutional subscription migration; managed identity +
Key Vault; Azure SQL migration + migrations tooling; App Insights + alerts; slots.

**Docs & support:** production runbook; support ownership; training/knowledge
transfer.

**Product/UX:** freshness ("last updated"); provenance labels; export/print.

**Integrations & reporting:** KPI measures ingest; executive reporting.

**Post-Oct portfolio management:** project/portfolio registry; KPI governance;
intake/approval workflow; portfolio reviews.

---

## 11. Predicted tasks (predictions, NOT approved scope)

| # | Predicted task | Trigger / evidence | Confidence | When to validate | If ignored |
|---|---|---|---|---|---|
| P1 | Rotate and purge the leaked credentials | §4 S1/S2 | **High** | now | continued exposure |
| P2 | Coordinate Entra app registration + consent | provisioning request names it; S3 | **High** | now | blocks all auth work |
| P3 | Resolve group-claim size / membership lookup | typical Entra; ≥200 groups possible | **Medium** | at SSO design | sign-in defects |
| P4 | Migrate seed & reference data to Azure SQL | `schema.mssql.sql` exists, unwired | **High** | at SQL cut-over | data split-brain |
| P5 | Schema migration + rollback tooling | only `build_db.py` (drop/rebuild) | **High** | at SQL cut-over | no safe schema change |
| P6 | Deduplicate records after import | `import_xlsx.py` upserts by code only | **Medium** | after first real import | duplicate rows |
| P7 | Remove legacy passcode path | S3 | **High** | at SSO cut-over | two auth paths |
| P8 | Environment-specific config cleanup | `APP_ENV` string only | **Medium** | at staging creation | prod/dev confusion |
| P9 | Define an access-review process | RBAC lands | **Medium** | post-RBAC | stale entitlements |
| P10 | Admin recovery / break-glass workflow | RBAC lands | **Medium** | post-RBAC | lockout |
| P11 | Audit-log retention policy | §5 | **Medium** | post-audit work | unbounded growth / privacy |
| P12 | Data-owner onboarding | register owners external | **Medium** | Oct 9+ | no accountability |
| P13 | Monitoring/alert tuning | App Insights lands | **Low** | post-monitoring | alert noise |
| P14 | Backup restore validation | `backup.py` untested end-to-end | **Medium** | before prod | untested restore |
| P15 | Production support runbook | DEPLOY.md is deploy-only | **High** | before prod | no support model |
| P16 | Technical-debt: retire `db/rev2` or adopt it | two conflicting schemas | **Medium** | now | governance ambiguity |

---

## 12. Duplicate, vague, or superseded tasks

- **Retire:** "Deploy software" (duplicate of "Deploy major prototype updates to
  Azure"; superseded by the local=dev policy).
- **Retire:** "Conduct testing" (vacuous; the suite is the gate).
- **Merge:** "Obtain user feedback" → "Conduct user testing".
- **Supersede:** "Reconcile dashboard fields with the Dean's prototype" — the
  register merge replaced the prototype as canon.
- **Split:** "Implement Entra authentication and user groups"; "Resolve open
  content, ownership, and data-quality decisions".
- **Rename:** "Develop code" → the specific implementation outcomes in §16.
- **Ambiguous scope:** "Determine project scope" — demo vs platform must separate.

---

## 13. Proposed textual dependency map

Predecessor → successor. "proposed" where the link is inferred, not certain.

```
[Register canon approved]  (closed)
   │
   ├─✓ C1..C14 closed candidates
   │
[U3 Confirm Oct-16 Board outcome & MVP scorecard]  (no predecessor)
   │
   ├─→ [U14 Board talking points] ─→ [U15 Fallback screenshots] ─→ [U8 Walkthrough]
   │                                                                     │
   │                                                              [U10 Rehearsal approval]
   │
[P1 Rotate/purge leaked credentials]  (no predecessor — do first)
   │
   └─→ [P2 Entra app registration + consent]  (Blocked: GT Identity)
            │
            ├─→ [F-A1 Entra sign-in & logout]
            │        │
            │        ├─→ [F-A2 oid → People mapping]
            │        │        │
            │        │        └─→ [P7 Remove passcode path]  (proposed)
            │        │
            │        └─→ [F-B1 Roles model] ─→ [F-B2 Group→role mapping]
            │                                     │
            │                                     ├─→ [P9 Access review]
            │                                     └─→ [P10 Break-glass]
            │
            └─→ [F-Ops1 Institutional subscription + managed identity] (Blocked: A&I)
                     │
                     └─→ [F-Ops2 Key Vault]  (parallel w/ P4)
                              │
                              └─→ [F-Ops3 Azure SQL migration] (needs P4, P5)
                                       │
                                       └─→ [F-Ops4 App Insights + alerts] (parallel)

[F-C1 Soft-delete + restore]  (parallel with all auth work)
[F-G1 Governance metadata columns]  (parallel)
[F-T1 Authorization-matrix tests]  (needs F-B1)
[P5 Migration/rollback tooling]  (needs F-Ops3 decision; blocks F-Ops3)
[P15 Support runbook]  (needs F-Ops1; blocks production go-live)
```

---

## 14. Recommended delivery phases

- **Phase 0 — now (safety + demo freeze):** P1 (secrets), freeze the demo, add
  Board materials tasks (U14/U15). *No platform work.*
- **Phase 1 — post-Oct (identity):** P2 → F-A1 → F-A2 → F-B1 → F-B2 → P7.
- **Phase 2 — governance & data:** F-C1, F-G1, audit enhancements (§5), F-T1.
- **Phase 3 — operations:** F-Ops1..4, P5, P14, P15.
- **Phase 4 — portfolio maturity:** registry, KPI governance, intake workflow.

---

## 15. Risks and unresolved decisions

**Risks**
- **R1 (High):** credentials committed + in history (§4). Owner: project.
- **R2 (High):** identity is self-asserted; audit actor untrustworthy (§4 S3).
- **R3 (High):** F1 stop-quota → 403 outage; availability is quota-bound.
- **R4 (Medium):** two schema generations, each marked superseded.
- **R5 (Medium):** no migrations/rollback for schema.
- **R6 (Medium):** no monitoring/alerts.

**Unresolved decisions (do NOT treat as approved scope)**
- **D-1:** Adopt Revision 2 (`db/rev2/`) or delete it? *Currently ambiguous.*
- **D-2:** SQLite vs Azure SQL for the production target.
- **D-3:** Is the passcode gate acceptable on Oct 16, or is Entra a demo blocker?
- **D-4:** Which subscription/tenant hosts production (external gate).
- **D-5:** Role vocabulary (who may edit what) — not yet defined.
- **D-6:** Real owner names (external, Oct 9) and the register's `MI-017` gap.

---

## 16. Copy-paste-ready Planner task backlog

Full task objects are in the JSON block at the end. This is the human-readable
short list, with predecessors. Buckets reused from the current plan unless noted.

**Immediate (Phase 0)**
1. *Rotate and purge the credentials committed in `docker-compose.yml`* —
   Scope + Security. No predecessor. Enables: everything identity.
2. *Confirm the October 16 Board outcome and MVP scorecard* — Scope.
3. *Write the Board talking points and demonstration flow* — Pilot & Deployment.
   Pred: #2. Enables: #5.
4. *Capture fallback screenshots of the final dashboard* — Pilot & Deployment.
   Pred: #3. Parallel: #5.
5. *Run a scripted Board walkthrough and capture follow-up actions* — Testing.
   Pred: #3.
6. *Obtain final approval for the Board package* — Pilot & Deployment. Pred: #3,#4,#5.

**Identity (Phase 1)** — each with predecessors `#1`, then chained
7. *Register the Entra app and record the tenant/redirect configuration* — Dev.
   Blocked: GT Identity.
8. *Implement Entra sign-in and sign-out, replacing the person picker* — Dev.
   Pred: #7.
9. *Map the Entra `oid` claim to `People` and enforce it server-side* — Dev. Pred: #8.
10. *Define the roles model (viewer / team-editor / admin)* — Design. Pred: #1.
11. *Map Entra groups to roles and enforce default-deny server-side* — Dev. Pred: #10.
12. *Retire the shared-passcode access path* — Dev. Pred: #9, #11.

**Governance & lifecycle (Phase 2)**
13. *Add soft-delete and restore for goals, priorities, people and Dean Initiatives*
14. *Add steward, validation status, reporting period and evidence metadata* —
    Data governance.
15. *Extend the change log with reason/source and a request correlation id*.
16. *Build the authorization-matrix test suite (allowed and denied per role)* —
    Testing. Pred: #11.

**Operations (Phase 3)**
17. *Provision production on the GT subscription with managed identity and Key Vault*.
18. *Add Application Insights and one alert action group*.
19. *Migrate the data layer to Azure SQL with a reversible migration and rollback*.
20. *Validate a full backup/restore against the production target*.
21. *Write the production support runbook (monitoring, on-call, incident steps)*.

**Predictions (backlog / risk register — not approved scope)**
22. *Resolve Entra group-claim size or membership-lookup issues* (predicted).
23. *Deduplicate records created by concurrent or repeated imports* (predicted).
24. *Define an access-review process* (predicted).
25. *Decide the fate of the Revision 2 schema* (predicted).

---

## 17. Recommended next implementation slice

**Title:** *Harden the repository against the committed credentials and stop the
next `git add` from sweeping untracked folders.*

**Why this one first.** It is the only item that is both **safe** (no behaviour
change, no Azure/identity/database change) and **urgent** (a live leak). It is
small, reviewable, and unblocks Phase 1 without touching the frozen demo.

**Scope**
1. Replace the literals in `docker-compose.yml` with `${APP_PASSCODE}` /
   `${APP_SECRET}` references (values now read from the environment; the file
   becomes safe to track).
2. Add `.gitignore` entries for `fastapi-container/` and `source/` (verified
   currently untracked **and** un-ignored).
3. Add a short `docs/ops/SECURITY.md` recording: the two leak locations, the
   rotation requirement, and the history-rewrite requirement (no values).
4. Add a test-guard: a scan that fails if a tracked file matches the credential
   patterns from §4 (so this cannot recur).

**Out of scope:** history rewrite (needs a coordinated, destructive step the
user must approve); Azure/Entra; the demo.

**Acceptance criteria**
- `docker-compose.yml` contains no literal secret; it references environment vars.
- `git check-ignore fastapi-container source` returns both paths.
- A new test fails when a credential-shaped literal is reintroduced in a tracked
  file, and passes on the current tree.
- `docs/ops/SECURITY.md` names both leak locations and the rotation/purge need.

**Validation**
- Run the full suite: expect **552 passed** (551 + the new guard).
- Run the tracked-file secret sweep from this assessment: expect no hits.

**Security considerations:** rotation and history purge are *required* and are
explicitly deferred to a user-approved step; the slice only removes the literals
from the working tree.

**Governance considerations:** records the leak in the ops docs so the rotation is
traceable.

**Rollback:** revert the commit; no runtime behaviour changes.

**Evidence that lets the related Planner task close:** the sweep test is green
and `SECURITY.md` exists. (The leak is *mitigated in the tree*; it is fully closed
only after rotation + history purge, which is a separate, user-approved task.)

---

## JSON

```json
{
  "assessmentDate": "2026-10-07",
  "repositorySummary": {
    "head": "86bf60d",
    "branch": "main",
    "language": "Python 3.12",
    "framework": "FastAPI + Jinja2 + HTMX",
    "dataStore": "SQLite (committed file)",
    "testFiles": 52,
    "testLines": 7312,
    "testsPassing": 551,
    "testsSkipped": 1,
    "authentication": "shared passcode + self-asserted person picker (no Entra)",
    "authorization": "single IsAdmin boolean + owner match + is_dean",
    "monitoring": "none (healthz only)",
    "ci": "GitHub Actions: pytest + docker smoke; no security scanning",
    "deployment": "Azure App Service zip deploy, personal Student subscription",
    "credentialLeak": "docker-compose.yml (tracked) + .env in history (4ee6d3e, 9436720) — values redacted"
  },
  "closedTaskCandidates": [
    {"title": "Validate Strategy 2035 goals and descriptions", "existingPlannerTask": "Validate Strategy 2035 goals and descriptions", "lifecycle": "closedCandidate", "evidence": ["db/canonical_goals.py", "tests/test_goal_correctness.py", "tests/test_canon_links.py"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Validate the six annual priority names and descriptions", "existingPlannerTask": "Validate full names and descriptions for the six annual priorities", "lifecycle": "closedCandidate", "evidence": ["app/priorities.py", "tests/test_priority_definitions.py"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Validate the 29 Team Initiatives against the register", "existingPlannerTask": "Review and validate initiatives", "lifecycle": "closedCandidate", "evidence": ["db/build_register_seed.py", "tests/test_register_seed.py"], "completionConfidence": "high", "remainingGap": "register approval confirmed 2026-10-07", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Map people to initiatives", "existingPlannerTask": "Map people to initiatives", "lifecycle": "closedCandidate", "evidence": ["TeamInitiatives.OwnerID 29/29", "TeamInitiativeCoOwners"], "completionConfidence": "high", "remainingGap": "real names external (Oct 9)", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Develop the working prototype from the specifications", "existingPlannerTask": "Develop prototype based on specifications", "lifecycle": "closedCandidate", "evidence": ["app/ (11 modules)", "deployed markers"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Development", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Apply CLL and Georgia Tech brand assets", "existingPlannerTask": "Apply CLL and Georgia Tech brand assets", "lifecycle": "closedCandidate", "evidence": ["docs/specs/hive/", "app/static/fonts/", "app/static/brand/", "tests/test_visual_system.py"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Development", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Incorporate canonical data into the prototype", "existingPlannerTask": "Incorporate canonical data into the prototype", "lifecycle": "closedCandidate", "evidence": ["db/seed_register.sql", "tests/test_register_seed.py"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Development", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Review the live prototype and consolidate change requests", "existingPlannerTask": "Review the live prototype and consolidate change requests", "lifecycle": "closedCandidate", "evidence": ["docs/specs/cll-dashboard-analysis-2026-10-06.md", "docs/specs/cll-rereview-2026-10-07.md"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Verify access to the deployed prototype", "existingPlannerTask": "Verify authenticated access to the deployed prototype", "lifecycle": "closedCandidate", "evidence": ["marker labels-20261007T123612Z live"], "completionConfidence": "high", "remainingGap": "authenticated by passcode, not Entra", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close; add an Entra task"},
    {"title": "Implement dashboard progress-update functions", "existingPlannerTask": "Implement dashboard data-update functions", "lifecycle": "closedCandidate", "evidence": ["app/repo.py:109", "tests/test_updates.py", "tests/test_write_path.py"], "completionConfidence": "high", "remainingGap": "none", "recommendedBucket": "Development", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"},
    {"title": "Implement the change log (write + admin reader)", "existingPlannerTask": "Implement dashboard change logging", "lifecycle": "closedCandidate", "evidence": ["app/repo.py:359", "tests/test_change_log.py", "app/main.py /changes"], "completionConfidence": "medium", "remainingGap": "no reason/source, no correlation id, no retention", "recommendedBucket": "Development", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close; open a governance follow-on"},
    {"title": "Deploy prototype updates to Azure and verify the marker", "existingPlannerTask": "Deploy major prototype updates to Azure", "lifecycle": "closedCandidate", "evidence": ["docs/ops/LAUNCH_RECORD.md", "docs/ops/DEPLOY.md"], "completionConfidence": "high", "remainingGap": "superseded by local=dev/Azure=prod checkpoint policy", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "recommendation": "Close"}
  ],
  "currentTaskUpdates": [
    {"title": "Confirm the October 16 demonstration scope and out-of-scope platform work", "existingPlannerTask": "Determine project scope", "lifecycle": "current", "recommendedBucket": "Scope", "recommendedStatus": "InProgress", "recommendedPriority": "Urgent", "evidence": ["docs/ops/LAUNCH_RECORD.md", "docs/ops/DEPLOY.md"], "problemOrOutcome": "Scope mixes the demo with the platform programme; separate them", "acceptanceCriteria": ["a one-page statement of demo scope and explicit out-of-scope platform items"]},
    {"title": "Confirm the Azure subscription and account path with IT", "existingPlannerTask": "Confirm Azure subscription and account path with IT", "lifecycle": "current", "recommendedBucket": "Scope", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "evidence": ["docs/ops/AZURE_PROVISIONING_REQUEST.md"], "risksOrBlockers": ["Blocked: external (A&I)"]},
    {"title": "Confirm the October 16 Board outcome and MVP scorecard", "existingPlannerTask": "Confirm the October 16 Board outcome and MVP scorecard", "lifecycle": "current", "recommendedBucket": "Scope", "recommendedStatus": "InProgress", "recommendedPriority": "Urgent", "evidence": [], "acceptanceCriteria": ["named Board outcome and the fields shown on the scorecard"]},
    {"title": "Consolidate the specifications: register data model and app architecture", "existingPlannerTask": "Draft preliminary software specifications", "lifecycle": "current", "recommendedBucket": "Design", "recommendedStatus": "Completed", "recommendedPriority": "Medium", "evidence": ["docs/specs/2026-10-07-register-canon-and-dean-layer-design.md", "docs/specs/2026-10-06-interconnection-redesign-design.md"], "recommendation": "Rename; link the existing specs"},
    {"title": "Register the Entra app and record the tenant and redirect configuration", "existingPlannerTask": "Implement Entra authentication and user groups", "lifecycle": "current", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "evidence": ["docs/ops/AZURE_PROVISIONING_REQUEST.md"], "predecessors": ["Rotate and purge the committed credentials"], "risksOrBlockers": ["Blocked: GT Identity"]},
    {"title": "Resolve open content decisions (wording and labels)", "existingPlannerTask": "Resolve open content, ownership, and data-quality decisions", "lifecycle": "current", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "InProgress", "recommendedPriority": "Medium", "evidence": ["CONTEXT.md"], "scope": ["content only"]},
    {"title": "Resolve open ownership decisions with the register owners", "existingPlannerTask": "Resolve open content, ownership, and data-quality decisions", "lifecycle": "current", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium", "risksOrBlockers": ["external: real names pending"]},
    {"title": "Resolve open data-quality decisions", "existingPlannerTask": "Resolve open content, ownership, and data-quality decisions", "lifecycle": "current", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium", "evidence": ["vw_DataChecks"]},
    {"title": "Run a scripted Board walkthrough with three named reviewers", "existingPlannerTask": "Conduct user testing", "lifecycle": "current", "recommendedBucket": "Testing", "recommendedStatus": "InProgress", "recommendedPriority": "Important", "evidence": ["docs/specs/cll-rereview-2026-10-07.md"], "acceptanceCriteria": ["a written script and captured follow-up actions"]},
    {"title": "Obtain final approval for the Board package", "existingPlannerTask": "Obtain final approval for the Board package", "lifecycle": "current", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent"},
    {"title": "Prepare Board talking points and the demonstration flow", "existingPlannerTask": "Prepare Board talking points and demonstration flow", "lifecycle": "current", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent"},
    {"title": "Prepare fallback screenshots of the final dashboard", "existingPlannerTask": "Prepare fallback screenshots of the final dashboard", "lifecycle": "current", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent"}
  ],
  "futureTasks": [
    {"title": "Implement Entra sign-in and sign-out, replacing the person picker", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "securityConsiderations": ["validate issuer/audience/expiry", "tenant restriction"], "predecessors": ["Register the Entra app and record the tenant and redirect configuration"]},
    {"title": "Map the Entra oid claim to People and enforce it server-side", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "governanceConsiderations": ["oid is the immutable key; never key on email/name"]},
    {"title": "Define the roles model (viewer, team-editor, admin)", "lifecycle": "future", "recommendedBucket": "Design", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent"},
    {"title": "Map Entra groups to roles and enforce default-deny server-side", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "securityConsiderations": ["least privilege", "default deny", "403 not hidden control"]},
    {"title": "Retire the shared-passcode access path", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Important", "predecessors": ["Implement Entra sign-in and sign-out, replacing the person picker"]},
    {"title": "Add soft-delete and restore for goals, priorities, people and Dean Initiatives", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Important"},
    {"title": "Add steward, validation status, reporting period and evidence metadata", "lifecycle": "future", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "NotStarted", "recommendedPriority": "Important"},
    {"title": "Extend the change log with reason or source and a request correlation id", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Important"},
    {"title": "Build the authorization-matrix test suite (allowed and denied per role)", "lifecycle": "future", "recommendedBucket": "Testing", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent"},
    {"title": "Provision production on the GT subscription with managed identity and Key Vault", "lifecycle": "future", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "risksOrBlockers": ["external: A&I provisioning"]},
    {"title": "Add Application Insights and one alert action group", "lifecycle": "future", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "NotStarted", "recommendedPriority": "Important"},
    {"title": "Migrate the data layer to Azure SQL with a reversible migration and rollback", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Important", "predecessors": ["Provision production on the GT subscription with managed identity and Key Vault"]},
    {"title": "Validate a full backup and restore against the production target", "lifecycle": "future", "recommendedBucket": "Testing", "recommendedStatus": "NotStarted", "recommendedPriority": "Important"},
    {"title": "Write the production support runbook (monitoring, on-call, incident steps)", "lifecycle": "future", "recommendedBucket": "Pilot & Deployment", "recommendedStatus": "NotStarted", "recommendedPriority": "Important"},
    {"title": "Build the KPI measures ingest and executive reporting", "lifecycle": "future", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium"},
    {"title": "Stand up the portfolio registry and intake approval workflow", "lifecycle": "future", "recommendedBucket": "Design", "recommendedStatus": "NotStarted", "recommendedPriority": "Low"}
  ],
  "predictedTasks": [
    {"title": "Rotate and purge the credentials committed in docker-compose.yml", "lifecycle": "predicted", "recommendedBucket": "Scope", "recommendedStatus": "NotStarted", "recommendedPriority": "Urgent", "evidence": ["docker-compose.yml:16-17", "git log --all -- .env"], "predictionConfidence": "high", "predictionTrigger": "static secret sweep found tracked value-shaped literals; .env in history", "risksOrBlockers": ["requires a user-approved destructive history rewrite"]},
    {"title": "Resolve Entra group-claim size or membership-lookup issues", "lifecycle": "predicted", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium", "predictionConfidence": "medium", "predictionTrigger": "group-based authorization at scale", "risksOrBlockers": ["group overage >200"]},
    {"title": "Deduplicate records created by repeated or concurrent imports", "lifecycle": "predicted", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium", "evidence": ["scripts/import_xlsx.py upserts by code only"], "predictionConfidence": "medium", "predictionTrigger": "first real import round"},
    {"title": "Decide the fate of the superseded Revision 2 schema", "lifecycle": "predicted", "recommendedBucket": "Design", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium", "evidence": ["db/schema.sql:1-36", "db/rev2/", "db/mssql/"], "predictionConfidence": "medium", "predictionTrigger": "two schema generations, each marked superseded"},
    {"title": "Define an access-review process", "lifecycle": "predicted", "recommendedBucket": "Analysis/Software requirements", "recommendedStatus": "NotStarted", "recommendedPriority": "Low", "predictionConfidence": "medium", "predictionTrigger": "RBAC lands"},
    {"title": "Add a schema-migration and rollback tool", "lifecycle": "predicted", "recommendedBucket": "Development", "recommendedStatus": "NotStarted", "recommendedPriority": "Medium", "evidence": ["db/build_db.py (drop and rebuild only)"], "predictionConfidence": "high", "predictionTrigger": "any schema change or SQL migration"}
  ],
  "duplicatesOrSuperseded": [
    {"task": "Deploy software", "verdict": "Retire", "reason": "duplicate of 'Deploy major prototype updates to Azure'; superseded by the local=dev / Azure=prod checkpoint policy"},
    {"task": "Conduct testing", "verdict": "Retire", "reason": "vacuous; the CI suite is the gate"},
    {"task": "Obtain user feedback", "verdict": "Merge", "reason": "into 'Conduct user testing'"},
    {"task": "Reconcile dashboard fields with the Dean's prototype", "verdict": "Supersede", "reason": "the register merge replaced the prototype as canon"},
    {"task": "Implement Entra authentication and user groups", "verdict": "Split", "reason": "registration, sign-in, claim mapping, tests"},
    {"task": "Resolve open content, ownership, and data-quality decisions", "verdict": "Split", "reason": "three distinct decisions"},
    {"task": "Develop code", "verdict": "Rename", "reason": "replace with specific implementation outcomes"}
  ],
  "risks": [
    {"id": "R1", "severity": "high", "summary": "Credentials committed in docker-compose.yml and preserved in git history"},
    {"id": "R2", "severity": "high", "summary": "Identity is self-asserted; the audit actor is untrustworthy"},
    {"id": "R3", "severity": "high", "summary": "F1 stop-quota causes 403 to all users; availability is quota-bound"},
    {"id": "R4", "severity": "medium", "summary": "Two schema generations, each marked superseded"},
    {"id": "R5", "severity": "medium", "summary": "No schema migration or rollback tooling"},
    {"id": "R6", "severity": "medium", "summary": "No monitoring or alerting"}
  ],
  "unresolvedDecisions": [
    {"id": "D-1", "decision": "Adopt or delete the Revision 2 schema (db/rev2/)"},
    {"id": "D-2", "decision": "SQLite or Azure SQL for the production target"},
    {"id": "D-3", "decision": "Is the passcode gate acceptable on October 16, or is Entra a demo blocker"},
    {"id": "D-4", "decision": "Which subscription and tenant host production (external)"},
    {"id": "D-5", "decision": "The role vocabulary: who may edit what"},
    {"id": "D-6", "decision": "Real owner names and the register's MI-017 gap (external)"}
  ],
  "recommendedNextSlice": [
    {
      "title": "Harden the repository against the committed credentials and stop the next git add from sweeping untracked folders",
      "lifecycle": "current",
      "existingPlannerTask": "",
      "recommendedBucket": "Scope",
      "recommendedStatus": "InProgress",
      "recommendedPriority": "Urgent",
      "evidence": ["docker-compose.yml:16-17", "git log --all -- .env", "git check-ignore fastapi-container source (no match)"],
      "problemOrOutcome": "A tracked file contains literal credentials and two untracked directories are not ignored",
      "scope": ["replace docker-compose literals with environment references", "gitignore fastapi-container/ and source/", "add docs/ops/SECURITY.md naming both leak locations", "add a credential-pattern test guard"],
      "outOfScope": ["git history rewrite (user-approved, separate)", "Azure/Entra changes", "the frozen demo"],
      "acceptanceCriteria": ["docker-compose.yml has no literal secret", "git check-ignore returns both dirs", "a new guard test fails on a reintroduced literal and passes now", "SECURITY.md names both leaks"],
      "validation": ["full suite expects 552 passed", "tracked-file secret sweep returns no hits"],
      "securityConsiderations": ["rotation and history purge required and deferred to a user-approved step"],
      "governanceConsiderations": ["records the leak so rotation is traceable"],
      "predecessors": [],
      "enables": ["Register the Entra app and record the tenant and redirect configuration"],
      "parallelWith": ["Confirm the October 16 Board outcome and MVP scorecard"],
      "blocks": [],
      "risksOrBlockers": [],
      "suggestedLabels": ["security", "phase-0", "bounded"],
      "predictionConfidence": "",
      "predictionTrigger": ""
    }
  ]
}
```
