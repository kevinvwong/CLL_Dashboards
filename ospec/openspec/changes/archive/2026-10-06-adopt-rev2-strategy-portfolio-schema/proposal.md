# Proposal

## Why

The prototype grew a nine-table schema that is a simplification of, and now a
divergent fork from, the CLL Strategy Portfolio Enterprise Package v1.0
(Architecture Revision 2, baseline 2026-10-05). That package is a governance
review baseline written for this exact platform, and it changes the shape of
the model in ways the prototype cannot currently express: a traceability tier
between Goals and Initiatives (Strategic Objective, Target, Metric Version),
effective-dated multi-role ownership in place of a single `OwnerID`, ten typed
initiative relationships in place of one, and reusable Priority definitions
bound to Planning Cycles.

Adopting Rev2 as the target schema keeps the production build aligned with the
governance baseline instead of requiring a second, larger migration once
business data is validated. It must happen now because the prototype's
invented data is actively diverging: the prototype contains 22 initiatives
that exist in no approved list, because the package ships canonical strategy
(5 goals, 25 objectives, 11 targets, 6 priorities) with **zero** operational
initiative, person, ownership, update or metric rows.

### What the package settles, with evidence

- **Priorities are not children of goals.** Confirmed across all twelve
  package files: no table, foreign key or constraint joins a goal to a
  priority. ADR-001 explicitly *rejects* `Goal -> Priority -> Initiative` as a
  mandatory hierarchy, calling the portfolio "a network, not a cascading goal
  tree." The project config already records this rule; Rev2 makes it
  structural.
- **Strategy 2035 objectives are not initiatives.** The 25 PowerPoint
  objective bullets are `strategic_objective` records, canonical and
  protected from hard deletion. Conflating them with Dean initiatives is a
  named risk in the package.
- **Parent progress never rolls up.** AC-08 and the handoff brief both
  require independent progress per level until an approved rollup method
  exists. ADR-013 defers weighted rollups outright.
- **The PostgreSQL DDL is a reference implementation, not the mandate.**
  ADR-021 states the selected platform must receive *equivalent* constraints
  and that engineering must *document any semantic deviation*. This means the
  recorded Azure SQL (T-SQL) target is compatible with the baseline provided
  deviations are declared, rather than requiring a reversal of that decision.

### What the package does not settle

The package contradicts itself in five places. Under rapid prototyping each is
resolved by a reversible default recorded in `design.md` D7, with its reversal
cost stated, rather than escalated as a blocker. Every table is empty of
operational rows, so a wrong vocabulary costs a CHECK constraint edit and not a
migration. The five conflicts:

1. **Ownership role naming.** ADR-006 names eight roles including
   `Accountable Executive` and `Operational Lead`. The
   `initiative_owner.ownership_role` CHECK permits four: `Accountable Owner`,
   `Reporting Owner`, `Sponsor`, `Contributor`. `Operational Lead` is absent
   from the schema entirely; the two names for the same accountability role
   differ between the ADR and the DDL.
2. **Relationship types.** The migration file narrates an expansion to ten
   types (adding `Delivers`, `Funds`, `Consumes`, `Influences`, `Measures`)
   but issues no `ALTER` widening the CHECK, which still permits five.
3. **`progress_method` v2.** The migration replacement CHECK permits six
   values (`Manual`, `Owner Estimate`, `Milestone`, `Metric`,
   `Weighted Metric`, `Portfolio`) while the controlled vocabulary and
   specification permit three (`Owner Estimate`, `Metric Derived`,
   `Milestone Derived`). Only `Owner Estimate` survives both. `Metric
   Derived` becomes `Metric`; `Weighted Metric` is added despite ADR-013
   deferring weighted rollups.
4. **Stewardship entity type.** `stewardship_assignment.entity_type` permits
   `'Data Product'`, but no `data_product` table exists in either the baseline
   or the migration.
5. **Initiative levels.** `Dean, D-1, Team, Enterprise` in the specification,
   data package and baseline DDL; only `Dean, D-1` in the migration and the
   implementation checklist; `Dean, D-1, Enterprise` in the handoff brief.

## What Changes

- **BREAKING** Adopt the Revision 2 logical model as the target schema:
  27 tables across a baseline (15) and a Rev2 migration (12), replacing the
  prototype's 9.
- **BREAKING** Introduce the traceability chain
  `Portfolio -> Goal -> Strategic Objective -> Target -> Initiative -> Metric
  Version -> Ownership/Stewardship` (ADR-009). Goals, objectives and targets
  become protected canonical records.
- **BREAKING** Replace `Initiatives.OwnerID` with effective-dated
  `initiative_owner` (4 or 8 roles depending on open question 1) plus
  `stewardship_assignment` (Business/Data/Technical Steward). Every active D-1
  initiative requires exactly one current primary Reporting Owner.
- **BREAKING** Replace `InitiativeLinks` with `initiative_relationship`,
  supporting 5 or 10 typed relations depending on open question 2, with
  effective dates, weight, level-direction enforcement on `Supports` and
  `Contributes To`, and cycle prevention.
- Replace `Priorities(PlanYear)` with `priority_definition` +
  `planning_cycle` + `priority_cycle`, so a named priority can recur across
  cycles with cycle-specific wording and display order.
- Add `source_record` provenance and a `validation_status` vocabulary
  (`Imported`, `Needs Review`, `Leadership Confirmed`, `Canonical`, `Retired`)
  to imported records and every inferred mapping.
- Add `portfolio` and `portfolio_goal` as a navigational lens that does not
  replace canonical Goal wording (ADR-002).
- Declare and document every semantic deviation required to express the
  baseline's PostgreSQL enforcement mechanisms on the target platform, per
  ADR-021.
- Relabel the prototype's 22 seeded initiatives as synthetic and non-governed.
  They are not in any approved inventory and must never be presented as
  portfolio data.

## Capabilities

### New Capabilities
- `rev2-schema-baseline`: the 27-table Revision 2 relational model, its
  controlled vocabularies, canonical-strategy protection, and the mapping from
  the prototype's 9 tables to it.
- `governance-constraints`: the enforcement mechanisms the baseline defines —
  cardinality minimums and maximums, effective-dating integrity, non-overlap
  of assignment periods, relationship-level semantics, cycle prevention,
  append-only updates, deletion protection — expressed on the target platform,
  with every deviation from the PostgreSQL reference recorded.
- `ownership-and-stewardship`: effective-dated multi-role initiative
  ownership and the distinct stewardship assignments, including the
  exactly-one-current-primary-Reporting-Owner rule for active D-1 initiatives.
- `traceability`: the governed chain from Portfolio through Goal, Objective,
  Target, Initiative and Metric Version to ownership and stewardship,
  including gap analysis and the orphan definitions the package specifies.
- `source-provenance-and-validation`: retention of source reference,
  authority level and validation status on every imported record and inferred
  relationship, with the rule that unconfirmed mappings remain `Needs Review`.

### Modified Capabilities
None. `openspec list --specs` reports no committed specs; the prototype's nine
capabilities live only in the in-flight `add-initiative-dashboard-prototype`
change, which this change does not modify. Whether the prototype's own specs
are revised to describe Rev2 behaviour, or left as a record of what the
prototype actually does, is an open question below.

## Out of scope

Explicitly **not** in this change:

- **Production migration.** No data is loaded into a production system. The
  package's own readiness table lists Dean and D-1 initiative inventories,
  ownership and stewardship assignments, and metric definitions as *Pending
  business validation*, with executive signoff *Pending*.
- **Business validation.** The 10 open issues in the Business Data Validation
  Register, and the 0-of-10 acceptance criteria currently untested, are not
  addressed here.
- **Governance automation.** Exception register, readiness scoring, approval
  workflows and signoff capture are governance process, not schema. Working
  ahead of ADR-012 change control is a deliberate choice for this prototype
  only; the production build is subject to it in full.
- **The deferred backlog**, per ADR-013: graph infrastructure, a generalised
  Work Item superclass, automated weighted rollups, predictive analytics, AI
  portfolio scoring, digital-twin planning. Project, task and WBS modelling is
  also deferred.
- **UI redesign.** The four-card presentation work discussed separately,
  including the Georgia Tech visual identity, is not part of adopting the
  schema.
- **Resolving the five package contradictions by escalation.** Each is resolved
  by a recorded default with a stated reversal cost rather than by waiting for
  the governance group. What is deliberately *not* deferred is any constraint
  whose failure would be silent or irreversible: canonical wording drift, a
  lost source reference, or a platform substitution left undocumented.
- **Hosting the package's business data.** The zip remains untracked and
  must be gitignored; the open question of whether personal Azure subscriptions
  may hold institutional planning data is unresolved.

## Impact

- **Schema:** `ospec/db/schema.sql` (9 tables) and its T-SQL mirror
  `ospec/db/schema.mssql.sql` are superseded by the Rev2 baseline plus
  migration. Views that are currently the read-model contract
  (`vw_LatestProgress`, `vw_GoalInitiatives`, `vw_PriorityInitiatives`,
  `vw_InitiativeConnections`, `vw_PersonInitiatives`, `vw_DataChecks`,
  `vw_RecentUpdates`) need equivalents defined against the new tables, since
  the prototype's read models resolve through `Initiatives.OwnerID` and
  `InitiativeLinks`, both of which are being replaced.
- **Application:** `app/queries.py`, `app/repo.py` and `app/auth.py` in
  `add-initiative-dashboard-prototype` resolve authorisation through a single
  owner per initiative. Multi-role ownership changes what "may this person
  edit this" means, and is a behaviour change, not only a query change.
- **Platform:** ADR-021's verification obligation lands on the recorded Azure
  SQL target. The mechanisms with no direct T-SQL equivalent are
  `EXCLUDE USING gist` period non-overlap, deferred cross-row constraint
  triggers, and partial unique indexes. Each needs a declared substitute and
  a test proving the substitute behaves equivalently.
- **Process:** ADR-012 freezes Revision 2 as the baseline. Any change to scope,
  schema, cardinality, vocabulary or traceability rules requires governance
  approval, an ADR amendment, migration and rollback impact analysis, updated
  test artifacts, and a package version increment. This change is therefore
  subject to a change-control regime the prototype has not operated under.
- **Data:** the prototype's `cll_initiatives.db` sample data is not a
  migration source. It is synthetic and was authored without reference to any
  approved inventory.

## Open questions requiring a named owner

Questions 1 to 5 have reversible defaults recorded in `design.md` D7, so they
do not block the work. They remain open because the governance group has not
answered, and each answer maps to a single named constraint.

| # | Question | Default | Owner |
|---|---|---|---|
| 1 | `Accountable Executive` or `Accountable Owner`; is `Operational Lead` assignable? | `Accountable Owner`, display alias, `Operational Lead` deferred | Governance group |
| 2 | Are the five additional relationship types in scope? | No; the five already permitted | Governance group |
| 3 | Authoritative `progress_method`; is `Weighted Metric` in scope while rollups are deferred? | `Owner Estimate`, `Metric Derived` | Governance group |
| 4 | Does `data_product` exist, or is that value removed? | Removed | Governance group |
| 5 | Are `Team` and `Enterprise` levels in scope? | No; `Dean` and `D-1` | Governance group |

Questions 6 to 8 are settled: the prototype's specs are retained unchanged as
a record of prototype behaviour, the prototype stays live through adoption, and
audit history location is recorded in `tasks.md` group 0.