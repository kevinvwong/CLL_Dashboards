# Feasibility brief — CLL Dashboard on Power Pages

**Date:** 2026-10-07
**Question:** can this dashboard be delivered on Microsoft Power Pages instead of
Azure App Service?
**Verdict:** not *deployed* — **rebuilt**. Power Pages has no Python runtime, so
this is a genuine platform fork, not a hosting change.

Sources: the repository (counts below), and Microsoft Learn
([What is Power Pages?](https://learn.microsoft.com/en-us/power-pages/introduction),
[Power Pages capabilities](https://learn.microsoft.com/en-us/power-pages/capabilities),
[Power Platform licensing FAQ](https://learn.microsoft.com/en-us/power-platform/admin/powerapps-flow-licensing-faq)).

---

## 1. What the app actually is (the thing being moved)

| | Count |
|---|---|
| Server framework | FastAPI/Python; **46 routes**, **12 write functions**, **38 query functions** |
| Templates | **35** Jinja2 (server-rendered) + HTMX |
| Data | **13 SQLite tables**; `cll_initiatives.db` |
| Tests | **54 test files, 563 passing** |
| Styling | 1,661 CSS lines (Hive tokens) |

## 2. What Power Pages is (verified, Microsoft Learn)

A low-code SaaS site builder: **Liquid** templates, **Dataverse** data,
**Power Automate** logic, **PCF** code components, Bootstrap rendering. There is
**no Python runtime** — `app/main.py` cannot run. It natively provides Entra
authentication, authorization rules, Dataverse audit, an admin/security
workspace, TLS/WAF/DDoS, and ISO/SOC/PCI compliance, and it is itself **hosted as
Azure App Service**.

## 3. Port vs rebuild

| Ports cleanly | Must be rebuilt |
|---|---|
| The **domain model** — goals, priorities, teams, Team Initiatives, Dean Initiatives, the links, ownership | **46 routes → pages/forms** |
| **The data** → Dataverse tables | **38 queries → Dataverse views + Liquid** |
| The **Hive CSS/brand** (largely reusable) | **12 write paths → Power Automate flows** |
| The **glossary / `CONTEXT.md`** vocabulary | **35 templates → Liquid**; HTMX swaps → components |
| | **563 tests** — there is no pytest on Power Pages |

Auth, audit and admin are the parts Power Pages supplies *natively*: the shared
passcode becomes Entra sign-in, the thin `AuditLog` becomes Dataverse audit, and
the hand-built admin routes become the built-in admin experience.

## 4. Cost

List prices from the licensing FAQ. **Special (education / non-profit) pricing is
offered but is not verified here** — confirm the real figure against the GT
education agreement before deciding.

At **~40 authenticated users**:

| Option | Monthly (list) | Notes |
|---|---|---|
| Power Pages authenticated pack | **~$200** | one pack = 100 users; minimum 25 assigned per environment |
| Power Apps per app | ~$200 | $5/user/app × 40; one app **or access to one Power Pages website** |
| Power Apps Premium | ~$800 | $20/user; unlimited sites |
| Current Azure (per `AZURE_PROVISIONING_REQUEST.md`) | **~$80–140** | S1 + Azure SQL; the platform roadmap work is *not* included either way |

Power Pages is therefore **comparable-to-higher on licence, plus a rebuild**.
Dataverse storage is included with the licences.

## 5. Which open roadmap tasks each path closes

| Open task group | Stay on Azure App Service | Power Pages rebuild |
|---|---|---|
| Entra auth + roles + group mapping | build it | **native** |
| Authorization tests | build it | new form (authorization rules) |
| Admin area | build it | **native** |
| Audit enrichment / retention | build it | **mostly native** (Dataverse audit) |
| Credential leak (`docker-compose.yml`, `.env` history) | fix it | **dissolves** (no passcode, no compose file) |
| TLS / WAF / compliance | platform | **native** |
| Azure SQL migration + migrations tooling | build it | Dataverse migration instead |
| Monitoring, backup, support runbook | build it | largely platform |
| Keep the 563-test suite | yes | **no** |

## 6. Timing and recommendation

- **October 16 (imminent):** a Power Pages rebuild **cannot** make the Board
  date. Freeze the demonstration on Azure.
- **Post-October:** this is a real fork, and the fog is genuine — licensing
  channel, rebuild scope, data migration, and ALM. That is exactly what
  **`/wayfinder`** is for: chart the decision tickets, not a build.

**Recommendation:** finish the already-scoped platform work on FastAPI *unless*
the deciding factor is "minimum custom code to maintain long-term." If it is,
Power Pages wins on auth / admin / audit / compliance and loses on the test suite
and licence cost.

**The one question that settles it:** is the goal to *reduce the code we own and
maintain* (favour Power Pages) or to *keep the tested asset we already have and
finish it* (favour Azure App Service)?

## Scope of this brief

This is a decision aid, **not** an approved change. It makes no code, schema,
deployment, or Planner change. A Power Pages move, if chosen, is a new build to be
planned through its own flow.
