# CLL Initiative Dashboard — Development-Readiness Decision Register

**Prepared:** 2026-10-08
**Status:** proposed implementation baseline — **not** an approved governance
decision. For the Data Owner, Executive Sponsor, Strategic Operations and
OIT/security partners to accept, amend, or defer before development.

> Everything labelled **Recommended default** below is a proposal. It exists so
> the foundational choices are decided deliberately rather than assumed in code.

---

## 1. Framing

The enterprise record already establishes several useful constraints:

- The immediate tracker is limited to **29 major initiatives**, uses stable
  **MI-001–MI-029** identifiers, supports many-to-many strategic relationships,
  and is **separate** from the fuller portfolio/project/KPI architecture. The
  long-term platform may **reuse** those IDs and relationships, but should not
  redefine them silently.
- The database specification establishes **Initiative** as the central object
  with **historical rather than overwritten** updates, one current primary
  reporting owner per active D-1 initiative, role separation, and lifecycle
  values of **Proposed, Active, On Hold, Completed, Retired**.

**Development recommendation.** Resolve seven foundational decisions before
coding business workflows. Design the remaining governance controls now, but do
not let future contributor features, advanced automation, or final retention
duration delay the MVP.

---

## 2. Evidence baseline

### Confirmed in enterprise material

- The dashboard's immediate operating grain is the **major initiative**, with
  leadership-ready status, progress, milestones, support needs, ownership, and
  as-of dates — not field-level institutional data or a full project/task
  hierarchy.
- **Tracker stewardship and designated initiative owners may edit**; leadership
  consumers are read-only unless explicitly given maintenance duties. Sensitive
  student, employee, research-restricted, or similar source data should **not**
  be copied into the tracker.
- Changes to **IDs, names, teams, priorities, goals, and Dean-initiative
  relationships require logged change control**. Updates and ownership
  assignments must **preserve history rather than overwrite it**.
- The intended Azure footprint includes **Linux App Service/FastAPI, Azure SQL,
  Key Vault, Application Insights/Log Analytics, Entra authentication, managed
  identity, and app roles**; the institutional infrastructure request initially
  described **Admin, Editor, and Viewer** roles.
- The KPI governance material already distinguishes **sponsor, steering,
  delivery, technical, and operational** decision classes and requires a
  Decision ID, effective date, evidence, named accountability, and versioned
  change control.

### Not found as a confirmed enterprise standard

No approved **numeric escalation SLA, risk matrix, workflow transition table,
hard-delete rule, delegation mechanism, or exact mapping between the stated
three-tier governance model and Entra application roles** was retrieved. Those
values are therefore presented below as recommended defaults.

---

## 3. Decision register

**Timing key:** **BLOCKER** = decide before development · **DESIGN NOW** =
include in schema/security design but activate later if needed · **DEFER** = no
MVP delay.

| ID | Decision area | Ambiguity / decision needed | Recommended default | Rationale / principal risk if unresolved | Timing | Decision owner | Dependencies |
|---|---|---|---|---|---|---|---|
| **DR-01** | Product scope / system-of-record boundary | Is the application the authoritative source for initiatives, KPIs, project execution, or all three? | Dashboard is the authoritative governance register for the 29 initiative records, approved relationships, ownership, lifecycle status, health, updates, decisions, and meeting snapshots. It references — but does not replace — systems of record for tasks, finance, HR, student data, research, or certified KPI evidence. | Prevents the MVP from becoming an unbounded PM/KPI integration platform. The two-project charter explicitly separates the immediate tracker from production pipelines and full portfolio/project hierarchy. | BLOCKER | Data Owner; Executive Sponsor confirms strategic boundary | None |
| **DR-02** | Initiative definition and relationships | What constitutes an initiative, and may initiatives link to multiple goals, priorities, or other initiatives? | Preserve MI-001–MI-029 as immutable business keys. Model Initiative as a distinct governed outcome/change effort; use normalized many-to-many bridges for goals, priorities, Dean initiatives, dependencies, and parent/child links. Do not use comma-separated relationship fields. | Stable IDs and normalized bridges avoid broken history, ambiguous mappings, and later redesign. The existing specification already requires many-to-many relationships and cycle/self-link controls. | BLOCKER | Data Owner | DR-01 |
| **DR-03** | Initiative ownership / accountability | Does "owner" mean executive sponsor, accountable owner, reporting owner, steward, or editor? | Store these separately. Require exactly one current Accountable Owner per active initiative; permit one Reporting Owner, one Steward, optional Sponsor, and multiple Contributors. Ownership changes are effective-dated and never overwrite history. | One overloaded Owner field would make approval, escalation, access, and reporting unreliable. The enterprise specification already distinguishes ownership roles and requires one current primary reporting owner. | BLOCKER | Data Owner, with relevant leader confirmation | DR-02 |
| **DR-04** | Three-tier decision-rights model | Where do operational, governance, and executive authorities begin and end? | Encode three decision tiers: Strategic Operations = operate and administer; Data Owner = govern data, definitions, access, approvals, and exceptions; Executive Sponsor = strategic scope, taxonomy, material override, and unresolved executive escalation. The Executive Sponsor receives no platform-administration entitlement by virtue of sponsorship. | Without explicit boundaries, platform administration and executive authority can be conflated, creating both access risk and approval bottlenecks. Existing governance sources distinguish delivery, operational, sponsor, and steering authority. | BLOCKER | Data Owner and Executive Sponsor | DR-01–03 |
| **DR-05** | Role and permission model | What may Administrators, operators, contributors, approvers, and viewers do? | Use four stable application-entitlement roles: Administrator, Operator, Contributor, Viewer. Keep approval authority as effective-dated application data, not an Entra-only role. Administrator manages configuration; Operator performs Strategic Operations data work; Contributor edits assigned initiatives only; Viewer reads published content. | Entra app roles are designed for stable authorization categories, while finer resource permissions belong in the application. | BLOCKER | Data Owner; OIT/Identity validates provisioning | DR-03–04 |
| **DR-06** | Entra/app-role mapping | Should access be assigned by individual, group, app role, or custom database role? | Single-tenant workforce application; Entra authenticates users. Assign Entra groups/users to app roles and consume the roles claim. Use application tables for initiative-level assignments and delegated approval. Require assignment for application access. | App roles can be assigned to users or groups and are emitted in the token; App Service exposes authenticated claims to FastAPI through protected request headers. | BLOCKER | OIT/Identity with Data Owner approval | DR-05 |
| **DR-07** | Status, health, and workflow semantics | Are lifecycle status, delivery health, approval state, and risk the same field? | Keep four independent concepts: Lifecycle: Proposed, Active, On Hold, Completed, Retired. Health: Green, Amber, Red, Not Assessed. Workflow: Draft, Submitted, Under Review, Approved, Published, Returned, Superseded. Risk: scored separately. | A single "status" field cannot reliably represent lifecycle, approval, execution health, and risk. Existing controlled lifecycle values should be retained rather than replaced. | BLOCKER | Data Owner; Executive Sponsor confirms lifecycle definitions | DR-01–04 |
| **DR-08** | Minimum audit, versioning, and deletion behavior | Can records be overwritten or deleted, and what history is required? | No hard delete through the application UI. "Delete" means Retired or Superseded. Use effective dates, immutable update records, actor ID, timestamp, old/new values, reason, decision ID, and correlation ID. Use Azure SQL temporal tables for governed core records plus an application event log. | Auditability is difficult to retrofit. Azure SQL temporal tables automatically preserve prior row versions and support point-in-time reconstruction. Existing enterprise material requires append-only updates and audit of ownership, mappings, validation, and modifications. | BLOCKER | Data Owner; OIT/Records confirms eventual schedule | DR-02–07 |
| **DR-09** | Azure architecture baseline | Which identity, database, telemetry, and environment choices are fixed? | Separate development and production App Services, databases, managed identities, and Entra registrations. Use App Service Entra authentication, FastAPI authorization checks, Azure SQL, managed identity/passwordless SQL access, Key Vault, and Application Insights/OpenTelemetry. | Microsoft recommends separate app registrations between environments; managed identity avoids database credentials; OpenTelemetry supports Python telemetry collection. | BLOCKER | Strategic Operations technical lead with OIT | DR-05–08 |
| **DR-10** | Strategic Operations authority | Which actions may Strategic Operations complete without approval? | Permit routine data administration: create drafts, validate required fields, publish already-approved records, append meeting updates, correct non-substantive errors, administer users/group requests, manage support queues, and place the application temporarily read-only. No unilateral taxonomy, owner, approval-threshold, or strategic-scope change. | Provides operating velocity without transferring governance ownership. | DESIGN NOW | Data Owner confirms | DR-04–07 |
| **DR-11** | Data Owner authority | Which changes require Data Owner approval? | Data Owner approves initiative creation/retirement, accountable-owner changes, workflow exceptions, contributor access, mapping changes, status Completion, delegate appointments, data definitions, and restoration of retired records. | Centralizes data governance while keeping routine operations delegated. | DESIGN NOW | Data Owner | DR-04, DR-10 |
| **DR-12** | Executive Sponsor authority / override | What requires sponsor approval and what may be overridden? | Sponsor approves strategic scope, initiative taxonomy, portfolio-level priorities, material exceptions, and unresolved cross-leader disputes. Override requires written rationale, effective date, affected records, and Data Owner acknowledgment. Sponsor cannot override security, privacy, records, or technical controls and does not directly edit production data. | Preserves strategic authority without creating privileged technical access. | DESIGN NOW | Executive Sponsor | DR-04, DR-11 |
| **DR-13** | Approval thresholds | Which changes are operational, governance-level, or executive-level? | Tier 1 — Operational: update narrative, as-of date, next milestone, support needed, and risk details within approved definitions. Tier 2 — Data Owner: initiative/owner/mapping/lifecycle/access changes. Tier 3 — Executive: taxonomy, scope, strategic priority, enterprise-level exception, or unresolved Tier 2 dispute. | Thresholds determine workflow routes, notifications, audit evidence, and authorization checks. | DESIGN NOW | Data Owner and Executive Sponsor | DR-04, DR-07, DR-10–12 |
| **DR-14** | Future contributor permissions | What will leaders be allowed to edit when contribution is enabled? | Contributors may edit assigned initiatives, submit updates, propose health/risk changes, and attach evidence links. They cannot publish, change IDs/taxonomy/owners/mappings, approve their own submissions, complete/retire initiatives, or view administration screens. Leave Contributor unassigned until the feature passes UAT. | Prevents "future contributor" from becoming uncontrolled Editor access. Current enterprise guidance already limits editing to stewards/designated owners and gives other leaders read access by default. | DESIGN NOW; ACTIVATE LATER | Data Owner | DR-03, DR-05, DR-13 |
| **DR-15** | Approval delegation | Can the Data Owner or Sponsor delegate approvals? | Permit named, time-bounded, scope-limited delegation with start/end dates, delegator, delegate, action classes, reason, and revocation. No onward delegation. A delegate may not approve their own submitted change. | Avoids stalled workflows while preserving accountability and separation of duties. | DESIGN NOW | Data Owner; Sponsor for executive delegation | DR-11–13 |
| **DR-16** | Emergency escalation | What happens during security, privacy, integrity, or availability events? | Strategic Operations may disable writes or affected accounts and preserve evidence. Security/privacy events route immediately to OIT/Privacy and the Data Owner; business-continuity or college-wide strategic impact also routes to the Executive Sponsor. Recovery requires documented authorization and post-incident review. | A predefined safe state avoids improvisation during an incident. The enterprise playbook already directs sensitive-data proposals to stop entry and route to the data/privacy owner. | DESIGN NOW | Data Owner with OIT/Privacy | DR-08–09 |
| **DR-17** | Risk scoring | How are risks scored and converted to health/escalation? | Likelihood 1–5 × Impact 1–5. Low 1–4; Moderate 5–9; High 10–16; Critical 17–25. Critical risk, privacy/security exposure, or an overdue major gate forces Red health; High risk normally forces at least Amber unless an approved exception exists. Store score inputs and narrative, not score only. | Creates consistent sorting and escalation while preserving the reasoning behind the score. | DESIGN NOW | Data Owner | DR-07, DR-13 |
| **DR-18** | Escalation SLAs | What response times apply at each tier? | Emergency: acknowledge within one support hour; immediate containment as needed. Meeting-blocking/governance: Strategic Operations acknowledgment in 1 business day; Data Owner disposition in 2 business days; Executive Sponsor escalation at 3 business days or before the next leadership meeting, whichever comes first. Routine: disposition within 5 business days or next weekly review. MVP support is business-hours, not 24×7. | Numeric SLAs are needed for timers, overdue indicators, and notification jobs. The existing plan already measures business-day SLAs and escalates institutional requests after 10 business days without acknowledgment, but does not define application-governance SLAs. | DESIGN NOW | Data Owner; OIT confirms support coverage | DR-13, DR-16–17 |
| **DR-19** | Notification channels | Which events use in-app, email, Teams, or Azure alerts? | Business workflow: in-app inbox plus email for assignments, approvals, returns, delegations, and SLA breaches; Teams weekly digest for leadership, not one message per edit. Technical operations: Azure Monitor Action Group email; Teams posting through Logic Apps for high-severity technical alerts. | Separating business workflow from technical monitoring prevents alert fatigue. Azure Action Groups support email and Logic Apps workflows that can post to Teams. | DESIGN NOW | Strategic Operations; Data Owner approves recipients | DR-13, DR-16–18 |
| **DR-20** | Audit retention and SQL/platform audit | How long should business history and technical/security logs be retained? | Keep business history and decision events without automated purge until the institutional records schedule is confirmed. Make retention configurable by event class. Enable Azure SQL auditing to Log Analytics for database/security activity, but do not treat SQL auditing as a substitute for the application's business-decision audit. | Azure SQL auditing can record queries, procedures, and successful/failed authentication to Storage, Log Analytics, or Event Hubs; it does not explain business approval intent. | DESIGN NOW; exact duration may defer | Data Owner with OIT/Records | DR-08–09 |
| **DR-21** | Weekly leadership-meeting integration | Is the meeting view live, frozen, or separately published? | Create a versioned meeting snapshot one business day before each weekly meeting containing initiative status, health, latest owner update, top risks, decisions/support needed, stale-data indicator, and as-of timestamp. Post-meeting actions and approved decisions are appended afterward; the snapshot remains immutable. | Supports repeatable weekly governance without losing what leadership actually saw. Existing materials call for summary/drill views and weekly status, RAID, escalation, and approved-change outputs. | DESIGN NOW | Strategic Operations | DR-03, DR-07–08, DR-17–19 |
| **DR-22** | Operational support and continuity owner | Who owns support if the developer or current administrator leaves? | Strategic Operations owns business operations and first-line support; designate at least two production administrators. OIT is technical contact/escalation, not business owner. Require runbook, access roster, backup/restore test, deployment record, and handoff checklist before production acceptance. | The current Azure discussion explicitly identified support continuity, maintenance, and security review as unresolved; the implementation plan also requires a named operational owner, runbook, access roster, and support route. | DESIGN NOW; owner name before production | Data Owner and Strategic Operations leadership | DR-09, DR-16, DR-20 |
| **DR-23** | Executive Sponsor application authorization | Does Dean status grant general initiative-update permission? | **No.** Executive Sponsor receives portfolio-wide read access plus explicitly authorized executive actions; Dean status alone never grants routine initiative-update permission. The application role is named `ExecutiveSponsor` (a security relationship), not `Dean` (an organizational position), so the model survives a personnel change. Executive actions — approve, return, defer, request information/recommendation, escalate, record direction, set executive priority, controlled override — are separately authorized, auditable workflow actions; the routine data change they imply is performed through the governed workflow by Strategic Operations. | Collapses two different authorities: strategic decision vs. routine data maintenance. If unchanged, the Dean effectively becomes a super-user/editor, bypassing Data Owner and Strategic Operations governance and weakening auditability. | BLOCKER (before changing `guards.py` and before executive-action development) | Elizabeth Smith as Data Owner, with Dean confirmation of the operating model | DR-04, DR-05, DR-11, DR-12, DR-13 |

**DR-23 acceptance statement.** The Executive Sponsor (Dean) shall have
portfolio-wide read access and explicitly defined executive-action permissions
but shall **not** receive general initiative-update authority. Dean status shall
not satisfy `may_update` or equivalent routine data-maintenance authorization.
Executive actions — including approval, return, deferment, escalation,
executive direction, priority designation, and controlled override — shall be
implemented as separately authorized, auditable workflow actions. Routine
initiative changes resulting from executive decisions shall be implemented
through the governed workflow by Strategic Operations or another appropriately
authorized role.

---

## 4. Dependency order

The sequence reflects the enterprise requirement that controlled IDs, version
history, restricted edit access, and evidence fields exist **before** downstream
build work begins. It also prevents authorization and workflow code from being
built before ownership and decision rights are settled.

```
DR-01 Scope
   → DR-02 Initiative model
      → DR-03 Ownership
         → DR-04 Decision rights
            → DR-05/06 RBAC and Entra
               → DR-07 Workflow semantics
                  → DR-08 Audit/deletion
                     → DR-09 Architecture
                        → downstream approvals, SLAs, notifications,
                          meeting snapshots, contributor features
```

### Critical path

**DR-01 Scope → DR-02 Initiative model → DR-03 Ownership → DR-04 Decision
rights → DR-05/06 RBAC and Entra → DR-07 Workflow semantics → DR-08
Audit/deletion → DR-09 Architecture** → downstream approvals, SLAs,
notifications, meeting snapshots, and contributor features.

### Decide before coding

1. Accept the system-of-record boundary in **DR-01**.
2. Freeze the initiative grain, stable IDs, and relationship model in **DR-02**.
3. Define accountable owner vs. reporting owner, steward, sponsor, and
   contributor in **DR-03**.
4. Approve the Strategic Operations / Data Owner / Executive Sponsor authority
   split in **DR-04**.
5. Approve application roles and Entra mapping in **DR-05–06**.
6. Approve separate lifecycle, health, workflow, and risk concepts in **DR-07**.
7. Approve no-hard-delete and minimum audit/versioning requirements in **DR-08**.
8. Confirm the Azure identity/database/environment baseline in **DR-09**.

These are genuine blockers because they affect database keys, authorization
middleware, API contracts, workflow state machines, migration logic, and test
acceptance.

### Safe to defer without delaying the MVP

- Activating the **Contributor** role and distributed leader editing, provided
  the role and assignment schema are designed now.
- Teams-based business-workflow automation beyond the weekly digest; begin with
  in-app plus email.
- **Final retention duration**, provided no hard-delete/purge occurs before
  Records/OIT approval.
- Advanced weighted rollups, automated KPI calculation, parent-progress
  derivation, portfolio/program/project/task hierarchy, and institutional-source
  integration.
- Custom domain and branded URL; the raw App Service URL can support an internal
  MVP.
- SMS/voice escalation, mobile push, sophisticated delegation chains, and
  automated substitute approvers.
- Full 24×7 operational support; document business-hours support for the MVP
  instead.

---

## 5. Recommended disposition

Approve **DR-01 through DR-09** as the development baseline; record **DR-10
through DR-22** as "default accepted unless changed," with explicit owners and
decision dates.

---

# Role-Based Home-Screen Requirements

## 6.1 Purpose

The application shall provide role-aware home screens that present each user
with the information, decisions, actions, and alerts appropriate to their
responsibilities.

The home screen shall **not** simply expose more data as authority increases. It
shall distinguish between:

- Viewing information
- Maintaining operational data
- Governing portfolio data
- Making executive decisions

**Governing principle:** Strategic Operations operates the platform and portfolio
data; the Data Owner governs the data; the Executive Sponsor governs strategic
direction; leadership users consume information initially and contribute
assigned updates in a future phase.

## 6.2 Role model

| Role | Primary purpose | Primary home-screen orientation |
|---|---|---|
| **Platform Administrator** | Technical/application administration | Platform health, access, configuration, failures |
| **Strategic Operations / Operator** | Portfolio and data operations | Data quality, updates, workflow, meeting readiness |
| **Data Owner** (Elizabeth Smith) | Portfolio data governance | Approvals, exceptions, quality, accountability |
| **Executive Sponsor** (Dean) | Strategic governance and executive decision-making | Decisions, escalations, priorities, leadership meeting |
| **Leadership Viewer** | Consume portfolio information | Assigned/relevant initiatives, portfolio status, meeting information |
| **Leadership Contributor** (future) | Maintain assigned initiative information | Assigned initiatives, updates due, risks, submissions |

A user may hold more than one role. Where this occurs, the application should
provide the **union** of authorized functions without duplicating dashboard
components.

## 6.3 Executive Sponsor home screen — Dean

### Purpose

The Dean's home screen shall function as an **executive decision and
attention-management workspace**, rather than an administrative dashboard. The
Dean shall be able to: see what requires attention, understand why it matters,
make or request a decision, and monitor whether that decision was carried out.
The Dean shall **not** require direct editing privileges over routine initiative
data.

### Executive summary

The top of the home screen shall provide a concise portfolio summary. Required
indicators:

- Total active initiatives
- Green / Amber / Red initiatives
- Critical risks
- Overdue major milestones
- Initiatives requiring executive attention
- Decisions awaiting Dean action
- Open executive directions
- Items scheduled for the next leadership meeting
- Stale initiative updates

Each indicator shall support drill-down to the underlying records.

## 6.4 Needs Your Attention

This shall be the Dean's **highest-priority actionable section**. It shall
display only items requiring executive attention. Examples: approval required,
executive escalation, cross-unit conflict, strategic priority decision, material
exception, critical risk, initiative pause/cancellation request, requested
executive direction, overdue executive decision.

| Field | Requirement |
|---|---|
| Initiative | Initiative ID and title |
| Decision/Escalation | Short description |
| Reason | Why Dean involvement is required |
| Submitted By | Originator |
| Recommendation | Data Owner/Strategic Operations recommendation |
| Submitted Date | Date routed |
| Due Date | SLA target |
| SLA Status | On time / approaching / overdue |
| Meeting Relevance | Next meeting / future / urgent |

## 6.5 Executive decision queue

The Dean shall have a dedicated decision queue. Available actions shall include:

- **Approve** — accept the recommendation.
- **Return for Revision** — return the matter for additional work. A comment
  shall be required.
- **Defer** — postpone the decision. The Dean shall specify rationale and
  follow-up date.
- **Request Information** — request additional facts without rejecting the
  proposal.
- **Request Recommendation** — direct the Data Owner and/or Strategic Operations
  to return with options, recommendation, implications, and requested decision.
- **Escalate** — direct further executive or institutional review.
- **Override** — supersede a governance recommendation within the Dean's
  authorized strategic authority. Override shall require rationale, effective
  date, affected initiative(s), and decision record. The Dean shall **not** be
  permitted to override security, privacy, records-management, or technical
  controls.

## 6.6 Executive watchlist

The Dean shall be able to place initiatives on a personal **Executive
Watchlist**. Watchlist designation shall not change the formal priority of an
initiative. The watchlist shall display: Initiative, Health, Latest update,
Major milestone, Top risk, Support needed, Last updated, Next leadership
discussion. Available action: Add to Watchlist / Remove from Watchlist. This
action shall not require Data Owner approval because it represents executive
attention rather than portfolio classification.

## 6.7 Executive priority

The application shall distinguish **Executive Watchlist** from **Formal
Executive Priority**. A formal Executive Priority designation shall constitute a
**governed portfolio decision**. The Dean may: designate an Executive Priority,
remove an Executive Priority designation, or change executive priority order.
Each change shall create a decision/audit record.

## 6.8 Leadership meeting workspace

The Dean's home screen shall include a **Next Leadership Meeting** section.
Items shall be grouped as:

- **Decision Required** — items requiring an executive decision.
- **Discussion Required** — items requiring leadership discussion but not
  necessarily a decision.
- **Information** — items presented for awareness.
- **Escalations** — critical or unresolved matters.
- **Follow-Up** — actions or decisions from previous meetings requiring review.

The Dean may: flag an initiative for discussion; request an initiative update;
designate Decision Required; designate Discussion Required; defer an item;
request additional information; request a recommendation. Strategic Operations
shall remain responsible for preparing and publishing the official meeting
snapshot.

## 6.9 Record executive direction

The Dean shall be able to issue direction **without directly modifying
initiative data**. Example: *"Return at the next leadership meeting with options
and a recommendation for consolidating these initiatives."*

An Executive Direction record shall contain: Direction ID, Date, Issued By,
Related initiative(s), Direction, Assigned To, Due Date, Status, Response,
Completion Date. Statuses: **Open → In Progress → Response Submitted → Closed**.

## 6.10 Executive decision follow-through

The Dean shall be able to monitor whether executive decisions were implemented.

**Recent Decisions:** Decision, Initiative, Responsible Party, Follow-Up,
Implementation Status. Implementation statuses should include: **Pending, In
Progress, Implemented, Blocked, Superseded**.

This separates *Decision made* from *Decision implemented*.

## 6.11 Dean vs. regular Viewer

The fundamental distinction: **a Viewer consumes portfolio information; the
Executive Sponsor can cause governance action to occur.**

| Capability | Viewer | Dean |
|---|---|---|
| View portfolio | Yes | Yes |
| Search/filter | Yes | Yes |
| View initiative details | Yes | Yes |
| View published history | Yes | Yes |
| View weekly snapshot | Yes | Yes |
| Executive portfolio view | No | Yes |
| Executive watchlist | No | Yes |
| Flag for leadership discussion | No | Yes |
| Request information | No | Yes |
| Request recommendation | No | Yes |
| Issue executive direction | No | Yes |
| Request executive review | No | Yes |
| Approve strategic decision | No | Yes |
| Return for revision | No | Yes |
| Defer decision | No | Yes |
| Resolve executive escalation | No | Yes |
| Set executive priority | No | Yes |
| Controlled override | No | Yes |
| Monitor decision implementation | No | Yes |
| Directly edit initiative data | No | No |
| Manage users | No | No |
| Configure application | No | No |
| Azure/Entra administration | No | No |

## 6.12 Data Owner home screen — Elizabeth Smith

**Purpose.** The Data Owner home screen shall function as the **portfolio
governance workspace**. Its primary question: *Is the portfolio information
governed, complete, accountable, and ready for leadership use?*

**Portfolio Governance Summary.** Display: Active initiatives, Initiatives
missing accountable owners, Stale updates, Data-quality exceptions, Pending
approvals, Ownership-change requests, Lifecycle-change requests,
Mapping/classification changes, Contributor-access requests, Open governance
escalations, Items awaiting Dean decision.

**Approval Queue.** Elizabeth shall be able to review: New initiative requests,
Initiative retirement requests, Accountable-owner changes, Reporting-owner
changes, Strategic mapping changes, Completion requests, Contributor-access
requests, Governance exceptions, Restoration requests, Delegation requests.
Actions: **Approve, Reject, Return for Revision, Request Information, Escalate
to Dean**.

**Data Quality.** A dedicated quality panel showing: Missing required fields,
Missing owners, Stale updates, Invalid relationships, Missing as-of dates,
Missing milestone dates, Unresolved validation warnings, Duplicate or
conflicting records.

**Governance Exceptions.** Display: Exception, Initiative, Requested by, Reason,
Recommendation, Age, SLA, Decision required.

**Executive Escalations.** Elizabeth shall see matters being prepared for the
Dean **before** executive routing. This supports *Strategic Operations → Data
Owner → Dean* rather than allowing routine matters to bypass governance review.

## 6.13 Strategic Operations / Operator home screen

**Purpose.** This shall be the **primary day-to-day operating workspace**. Its
primary question: *What needs to be updated, validated, prepared, routed, or
followed up today?*

**Operational Summary.** Display: Updates due, Stale initiatives, Missing data,
Validation failures, Pending workflow items, Open escalations, SLA warnings,
Leadership-meeting readiness, Decisions awaiting implementation, Executive
directions awaiting action.

**Work Queue.** A consolidated queue containing: Data corrections, Update
requests, Approval preparation, Returned submissions, Escalations, Executive
directions, Decision implementation, Meeting preparation, Access requests. Each
item shall have: owner, priority, due date, SLA, status, related initiative.

## 6.14 Leadership meeting readiness

Strategic Operations shall have a dedicated readiness panel. Example:

**Next Leadership Meeting**

- **Ready** — 24 initiatives
- **Needs Update** — 3 initiatives
- **Missing Owner Response** — 1 initiative
- **Executive Decision Required** — 2 items
- **Critical Risk** — 1 item

Strategic Operations shall be able to generate and publish the versioned meeting
snapshot from this workspace.

## 6.15 Decision implementation queue

When Elizabeth or the Dean makes a decision, Strategic Operations shall receive
an implementation item:

```
Dean approves priority change
  → Strategic Operations receives implementation task
    → Authorized data change performed
      → Change linked to decision
        → Implementation marked complete
```

This preserves separation between decision authority and data maintenance.

## 6.16 Platform Administrator home screen

Platform administration should be **separated conceptually from portfolio
operations** even where the same Strategic Operations staff initially hold both
roles. Its primary question: *Is the application secure, available, correctly
configured, and supportable?*

**Platform Summary.** Display: Application availability, Production environment
status, Development environment status, Database connectivity, Authentication
status, Recent application errors, Failed background jobs, Notification failures,
Security/access events, Deployment version, Last deployment, Backup/restore
status where available.

**Access Administration.** Display: Pending access requests, Current role
assignments, Recent role changes, Disabled users, Delegations, Expiring
delegations. Administrators may administer access **only within approved
governance rules**.

**Technical Alerts.** Display: Critical application errors, Authentication
failures, Database failures, Notification failures, Integration failures,
Unusual operational conditions. **Technical alerts shall remain separate from
business escalations.**

## 6.17 Leadership Viewer home screen

**Purpose.** The Viewer home screen shall be intentionally simple. Its primary
question: *What is happening across the portfolio and what do I need to know for
leadership discussion?*

**Portfolio Summary.** Display: Active initiatives, Green / Amber / Red, Major
milestones, Critical risks, Recent changes, Upcoming leadership meeting.

**My Relevant Initiatives.** Where initiative-to-leader relationships exist,
display initiatives associated with that leader. For each: Initiative, Health,
Latest update, Next milestone, Risks, Support needed, Last updated.

**Leadership Meeting.** Display the published meeting snapshot: Decision items,
Discussion items, Information items, Critical risks, Recent decisions. Viewers
shall **not** be able to alter the official meeting snapshot.

**Viewer Actions.** Phase 1 actions should be limited to: View, Search, Filter,
Drill down, View history, View published snapshots. If desired, a
non-governance *Ask a Question* function may later be added without granting
editing rights.

## 6.18 Leadership Contributor home screen — future phase

The Contributor home screen should be **designed now** even though the role is
not initially activated. Its primary question will be: *What information am I
responsible for keeping current?*

**My Initiatives.** Display assigned initiatives with: Current health, Last
update, Update due date, Next milestone, Open risks, Requested information,
Returned submissions.

**Updates Due.** Contributors shall be able to submit: Progress update, Proposed
health change, Milestone update, Risk, Support needed, Evidence/reference link,
Commentary. They shall **submit** changes rather than directly publish governed
data.

**Contributor Restrictions.** Contributors shall not be able to: Change
initiative IDs, Change taxonomy, Change accountable ownership, Change strategic
mappings, Approve their own submissions, Publish records, Complete or retire
initiatives, Manage users, Change application configuration.

## 6.19 Shared home-screen components

All roles should receive common components where authorized.

**Global Search** — search: Initiative ID, Initiative title, owner, priority,
goal, status, risk.

**Notifications** — role-appropriate notifications.

**Recent Activity** — only activity the user is authorized to see.

**Help / Definitions** — definitions for: lifecycle status, health, risk,
ownership roles, workflow states, escalation levels.

**Data Currency** — every portfolio view shall clearly display *Data as of:
[timestamp]* and, where appropriate, *Last published leadership snapshot:
[timestamp]*.

## 6.20 Recommended landing-page hierarchy

The application should provide **different home-screen priorities** rather than
one dashboard with different buttons hidden by role.

| Role | Landing priority |
|---|---|
| **Dean** | Attention → Decisions → Escalations → Meeting → Watchlist → Portfolio |
| **Elizabeth** | Approvals → Governance Exceptions → Data Quality → Escalations → Portfolio |
| **Strategic Operations** | Work Queue → Meeting Readiness → Data Quality → Decision Implementation → Portfolio |
| **Platform Administrator** | Platform Health → Alerts → Access → Jobs → Deployments |
| **Leadership Viewer** | Portfolio → My Relevant Initiatives → Meeting → Recent Decisions |
| **Future Contributor** | Updates Due → My Initiatives → Requests → Submitted Updates → Portfolio |

## 6.21 Development requirement

The application should **not** implement these as six completely independent
dashboards. Build reusable components such as: `PortfolioSummary`,
`AttentionQueue`, `DecisionQueue`, `ApprovalQueue`, `EscalationQueue`,
`InitiativeList`, `MeetingWorkspace`, `Watchlist`, `DataQualityPanel`,
`ActivityFeed`, `PlatformHealth`, `NotificationPanel`. The application then
**composes** the appropriate home screen based on authorization. This avoids
role-specific code duplication while preserving genuinely different user
experiences.

## 6.22 Recommended design principle

The role hierarchy should **not** be interpreted as *Viewer < Contributor <
Data Owner < Dean < Administrator* — that would incorrectly imply each role
simply receives progressively greater access. Instead, the roles represent
different authorities:

```
Platform Administrator
        └── Technical authority

Strategic Operations
        └── Operational authority

Data Owner
        └── Data-governance authority

Executive Sponsor
        └── Strategic decision authority

Leadership Contributor
        └── Assigned-data contribution authority

Leadership Viewer
        └── Information-consumption authority
```

This distinction should drive both the home-screen design and the authorization
model.

**Most importantly, the Dean is not a "super-user."** The Dean's additional
power comes from decision, direction, prioritization, escalation, and
follow-through functions, while Strategic Operations retains operational control
and Elizabeth retains data-governance authority.

---

# Part III — Executive Sponsor Authorization (DR-23) — Detail

## 7.1 The decision

The Dean shall **not** receive general initiative-update permission by virtue of
being Dean or Executive Sponsor. The Dean's application role is a
**read-plus-executive-actions** role — not an elevated Editor, Contributor,
Operator, or Administrator role.

The current behaviour in `guards.may_update`, whereby `is_dean == True`
effectively permits the Dean to update any initiative, is **inconsistent** with
the approved role model and home-screen requirements and shall be removed when
this decision is accepted.

## 7.2 Required authorization model

**READ**

```
├── View all initiatives
├── View portfolio rollups
├── View initiative history
├── View risks and escalations
├── View executive decision history
├── View leadership-meeting snapshots
└── View executive-only governance information
```

**EXECUTIVE ACTIONS**

```
├── Approve
├── Return for Revision
├── Defer
├── Request Information
├── Request Recommendation
├── Escalate
├── Resolve Executive Escalation
├── Record Executive Direction
├── Flag for Leadership Discussion
├── Add/Remove Executive Watchlist
├── Set Executive Priority
├── Exercise Controlled Override
└── Monitor Decision Follow-Through
```

**The Dean shall not have:**

```
ROUTINE DATA MAINTENANCE
├── Edit initiative narrative
├── Edit milestones
├── Edit routine status/health
├── Edit risks
├── Edit support-needed fields
├── Change owners directly
├── Change strategic mappings directly
├── Publish routine updates
└── Delete/retire records directly

ADMINISTRATION
├── Manage users
├── Assign application roles
├── Configure workflows
├── Change application settings
├── Administer Entra
├── Administer Azure
└── Administer SQL
```

## 7.3 Guard requirement

The authorization model shall **not** contain logic equivalent to:

```python
if is_dean(user):
    return True
```

inside a general-purpose update guard. These are separate authorization
questions:

```python
may_view(user, initiative)
may_update(user, initiative)
may_administer(user)
may_govern_data(user)
may_execute_action(user, action, initiative)
```

For the Dean:

```
may_view(...)            = True
may_update(...)          = False
may_administer(...)      = False
may_govern_data(...)     = False

may_execute_action(
  APPROVE, RETURN, DEFER, REQUEST_INFORMATION, REQUEST_RECOMMENDATION,
  ESCALATE, RECORD_DIRECTION, SET_EXECUTIVE_PRIORITY, OVERRIDE
)                        = conditional True
```

The last category shall be controlled by the **specific action, workflow state,
and approval threshold**, not simply by `is_dean`.

## 7.4 Important implementation distinction

An executive action may ultimately cause initiative data to change, but the Dean
should **authorize** the change rather than **perform** the underlying CRUD
operation.

```
Dean
  ↓
Approve Priority Change
  ↓
ExecutiveDecision created
  ↓
Strategic Operations implementation queue
  ↓
Authorized initiative change
  ↓
Decision ↔ change linked in audit history
```

Not:

```
Dean
  ↓
Edit Initiative
  ↓
priority = "Executive Priority"
```

That distinction is central to the governance model.

## 7.5 Role mapping

The application role is recorded as **`ExecutiveSponsor`**, not `Dean`. `Dean`
is an organizational position; `ExecutiveSponsor` describes the application's
authorization relationship. Bill Gaudelli currently occupies that role, but the
security model should survive a personnel change.

```
wgaudelli3  →  ExecutiveSponsor
```

The application can still display *"Dean / Executive Sponsor"* in the UI.

## 7.6 Guards direction

The refactor should move away from identity-specific authorization
(`is_dean(user)`, `is_elizabeth(user)`) toward capability-oriented authorization:

```python
has_role(user, "ExecutiveSponsor")
has_role(user, "DataOwner")
has_role(user, "Operator")
has_role(user, "Contributor")
```

and, more importantly:

```python
can(user, Action.VIEW_INITIATIVE, initiative)
can(user, Action.UPDATE_INITIATIVE, initiative)
can(user, Action.APPROVE_EXECUTIVE_DECISION, decision)
can(user, Action.SET_EXECUTIVE_PRIORITY, initiative)
can(user, Action.RECORD_EXECUTIVE_DIRECTION, initiative)
can(user, Action.ADMINISTER_PLATFORM)
```

This prevents the same problem from recurring as the role model expands.

## 7.7 Register entry

| Field | Value |
|---|---|
| Decision ID | DR-23 |
| Decision area | Executive Sponsor application authorization |
| Decision needed | Whether Dean status grants general initiative-update permission |
| Recommended default | No. Executive Sponsor receives portfolio-wide read access plus explicitly authorized executive actions; Dean status alone never grants routine initiative-update permission. |
| Current-state conflict | `guards.may_update` currently treats `is_dean` as authority to update initiatives. |
| Required change | Remove Dean/Executive Sponsor from general update authorization and implement executive actions as separately authorized commands/workflows. |
| Rationale | Preserves separation between strategic decision authority and operational/data-maintenance authority. |
| Principal risk if unchanged | The Dean effectively becomes a super-user/editor, bypassing Data Owner and Strategic Operations governance and weakening auditability. |
| Timing | Must decide before changing `guards.py` and before executive-action development. |
| Decision owner | Elizabeth Smith as Data Owner, with Dean confirmation of the Executive Sponsor operating model. |
| Dependencies | DR-04 Decision Rights; DR-05 Role Model; DR-11 Data Owner Authority; DR-12 Executive Sponsor Authority; DR-13 Approval Thresholds. |
| Implementation impact | Authorization guards, API endpoints, UI controls, audit events, executive-action workflow, tests. |
| Proposed status | Pending acceptance. |
