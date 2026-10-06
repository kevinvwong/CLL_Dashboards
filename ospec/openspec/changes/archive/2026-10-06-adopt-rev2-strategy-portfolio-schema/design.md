# Design

## Context

The prototype's schema (`ospec/db/schema.sql`) has nine tables and predates the
CLL Strategy Portfolio Enterprise Package v1.0 (Architecture Revision 2,
baseline 2026-10-05). That package is a governance review baseline for this
platform. Adopting it as the target schema is a decision about where the
production build lands, and it is separable from the questions about how the
dashboard should look.

### Verified facts about the package

Read from the zip in place, without extracting. `SHA256SUMS.txt` verified 12 of
12 files with zero mismatches; the archive SHA256 is
`EB71B8BCA667420F78E3289C4D2AB4DD341482CDAA464E7E1050E30A1251E08E`.

- **27 tables**: 15 in the baseline (`04_Schema_with_Constraints.sql`) plus 12
  added by the Rev2 migration (`09_Revision2_Migration.sql`). The ERD and the
  DDL agree once the migration is included; the only apparent mismatch is
  `PRIORITY` in the ERD, which the DDL calls `priority_definition`.
- **PostgreSQL, as a reference implementation.** Measured: 80 PostgreSQL
  markers (`language plpgsql`, `$$` bodies, `EXCLUDE USING gist`, partial
  index `WHERE`, deferred constraint triggers, `RAISE EXCEPTION`) against 0
  T-SQL markers. File 08 self-declares "PostgreSQL"; file 04 says "adapt data
  types and filtered indexes for target platform".
- **No goal-to-priority relationship exists.** Checked every file. No table,
  no foreign key, no constraint. ADR-001 explicitly rejects
  `Goal -> Priority -> Initiative` as a mandatory hierarchy and calls the
  portfolio "a network, not a cascading goal tree".
- **Canonical strategy is loaded; operational data is not.** The data package
  contains 5 goals, 25 strategic objectives, 11 targets, 6 priorities and 5
  portfolios. The `Initiatives`, `People`, `Teams`, `InitiativeGoals`,
  `InitiativeRelations`, `Ownership`, `Updates`, `Metrics`, `InitiativeMetrics`
  and `GoalMetrics` sheets are headers with zero data rows. The validation
  register has 0 business validations, 10 open issues (ISS-001 to ISS-010) and
  no signatures. Its Summary sheet is live formulas whose cached values are all
  zero.
- **No approved initiative inventory exists anywhere in the package.** Its own
  readiness table lists Dean and D-1 initiative inventories, ownership and
  stewardship assignments, and metric definitions as *Pending business
  validation*. The prototype's 22 seeded initiatives are an invention of this
  project, not a migration source.

### Five contradictions inside the package

These are recorded rather than resolved. Each needs an owner's decision, and
each has a different effect on what gets built.

| # | Conflict | Evidence | Blocks |
|---|---|---|---|
| 1 | `Accountable Executive` vs `Accountable Owner`; `Operational Lead` absent | ADR-006 names 8 roles; `initiative_owner.ownership_role` CHECK allows 4 | Ownership vocabulary |
| 2 | Ten relationship types vs five | Migration comment names Delivers, Funds, Consumes, Influences, Measures; no `ALTER` widens the CHECK | Relationship vocabulary |
| 3 | `progress_method` six values vs three | Migration replacement CHECK allows `Manual, Owner Estimate, Milestone, Metric, Weighted Metric, Portfolio`; vocabulary allows `Owner Estimate, Metric Derived, Milestone Derived` | Progress vocabulary |
| 4 | `'Data Product'` stewardship with no table | `stewardship_assignment.entity_type` permits it; no `data_product` table exists | Stewardship vocabulary |
| 5 | Initiative levels drift per file | Four values in spec/baseline/data; two in migration/checklist; three in the brief | Level vocabulary |

Note that #3 also contains a substantive conflict: `Weighted Metric` is added
while ADR-013 defers weighted rollups. And #2 is precisely the
documented-but-unimplemented failure mode — the package narrates the expansion
but never applies it.

## Decisions

### D1: The package DDL is a reference implementation; Azure SQL stands
The recorded decision 15 in `add-initiative-dashboard-prototype/design.md`
targets Azure SQL (T-SQL) and is **not reversed**. ADR-021 makes this
explicit: the PostgreSQL DDL and tests are reference implementations, and the
selected target must receive *equivalent* constraints, with engineering
obliged to *document any semantic deviation*.

**Rationale:** I initially leaned toward PostgreSQL because Rev2's
enforcement is its governance value and porting seemed risky. Reading ADR-021
corrects that: the ADR author anticipated exactly this and made platform
choice a documented-deviation exercise rather than a mandate. Reversing a
recorded decision on a false premise would be worse than the port.

**Consequence:** ADR-021's verification duty is inherited. Every mechanism
below needs either a native equivalent or a declared, tested substitute.

### D2: Progress and status are derived from the latest update
The baseline stores progress and status in two places: `initiative.progress_value`
and `initiative.status`, and `initiative_update.progress_value` and
`status_at_update`. No trigger reconciles them. The handoff brief says "the
latest entry powers the current card"; the specification says posting an update
must "create immutable update history and refresh latest-update projection" —
which implies both are maintained.

**Decision:** the read model derives current state from the latest update, as
the prototype's `vw_LatestProgress` already does. `initiative.progress_value`
and `initiative.status` are treated as a cache to be maintained on write, never
as an independent source of truth.

**Rationale:** a derived value cannot go stale. Two writable copies with no
reconciliation guarantee can, and would produce a card that disagrees with its
own history — a silent divergence rather than a visible failure.

**Consequence:** any code reading the initiative row's status directly must be
identified, because it will disagree with the card whenever the cache lags.

### D3: Constraint substitutes on the target platform
Three baseline mechanisms have no direct T-SQL equivalent.

| Baseline mechanism | Substitute | Residual risk |
|---|---|---|
| `EXCLUDE USING gist` period non-overlap for stewardship | Trigger plus a serialising lock (for example `sp_getapplock`) | Concurrent transactions may both pass the check before either writes. Must be stated, not hidden. |
| Deferred cross-row constraint trigger for "active D-1 needs Dean link" and "active initiative needs goal" | Transaction-scoped validation invoked on the write paths, plus the integrity report as the backstop | A direct write bypassing the application path could leave a violation. The report is what catches it. |
| Partial unique index `WHERE ... IS NULL` | Filtered unique index | Native. Low risk. |

**Rationale:** the serialising-lock approach for non-overlap is a genuine
weakening under concurrency, and ADR-021 requires that to be documented rather
than papered over. Stating it is the honest outcome; a claim of equivalence
would be false.

**Consequence:** the constraint test catalog must include a concurrent-write
case for stewardship overlap, and the integrity report is load-bearing rather
than advisory.

### D4: No automated rollup
ADR-013 defers weighted rollups; AC-08 requires parent progress to stay
independent absent a formally approved rule. The prototype already follows
this. Confirmed and carried forward, so that adopting Rev2 does not quietly
introduce the capability that ADR-013 excludes.

### D5: Prototype data is relabelled, not migrated
The prototype's 22 initiatives are not a migration source; no approved
inventory exists to migrate from. They stay for prototype demonstration, are
labelled synthetic, and SHALL NOT be presented as portfolio data. Relabelling
is required precisely because the prototype is live and viewable.

### D6: The prototype stays live during adoption
Not a technical decision. Changing the live environment while the target
schema is being adopted would leave a period with no working dashboard and no
target schema. Confirmed 2026-10-06 under rapid prototyping: the prototype is
destructive-replaceable, so retiring it early buys nothing and costs the only
working demonstration.

### D7: Package contradictions resolved by reversible default, not by escalation
The package contradicts itself in five places. Waiting for the governance
group would block all schema work, and the cost of being wrong is far lower
than the cost of waiting: every table is empty of operational rows, so
changing a vocabulary is a CHECK constraint edit, not a migration.

Each default below is therefore a decision with a stated reversal cost. When a
governance answer arrives, the change is confined to the mechanism named in the
last column.

| # | Conflict | Default adopted | Reversal cost |
|---|---|---|---|
| 1 | `Accountable Executive` vs `Accountable Owner`; `Operational Lead` absent | `Accountable Owner` as the stored name, `Accountable Executive` as a display alias, `Operational Lead` deferred | One CHECK on `initiative_owner.ownership_role` |
| 2 | Ten relationship types narrated, five permitted | The five the baseline CHECK actually permits: `Supports`, `Enables`, `Depends On`, `Contributes To`, `Replaces` | Widen one CHECK; no data change |
| 3 | Six progress methods vs three | `Owner Estimate` and `Metric Derived`. `Weighted Metric` dropped while ADR-013 defers rollups; `Manual` dropped as redundant with `Owner Estimate` | One CHECK on `initiative.progress_method` |
| 4 | `Data Product` stewardship with no table | Remove the value; nothing exists to steward | Remove one value from a CHECK |
| 5 | Levels drift: four values in the baseline, two in the checklist | `Dean` and `D-1` only, matching the project config and the checklist | One CHECK on `initiative.initiative_level` |

Two further decisions follow from the same reasoning:

- **Prototype specs are retained unchanged** as a record of what the prototype
  does. Rev2 behaviour lives in this change's specs. Rewriting the prototype's
  specs to describe behaviour the prototype does not have would make them
  fiction.
- **Audit history lives in the effective-dated rows themselves.**
  `initiative_goal`, `initiative_priority_cycle`, `initiative_relationship` and
  `initiative_owner` all carry `effective_start` and `effective_end`, so a
  mapping or ownership change is recorded by closing the old row and opening a
  new one rather than by mutating it. `initiative_update` is append-only per
  ADR-010. The prototype's separate `AuditLog` table has no Rev2 counterpart
  and is **intentionally dropped**, not silently lost: the prototype wrote one
  audit row per write, which cannot answer "who owned this in March" anyway,
  because it stored only the fact of a write and not the prior value. The
  effective-dated rows answer that question directly.

  *Consequence to record:* anything the prototype's `AuditLog` captured that is
  not expressible as an effective-dated row or an update — notably validation
  status changes and validation confirmations — needs its own trail. Group 0.6
  verification checks this rather than assuming the effective-dated rows cover
  it.

**Rationale:** the reversibility is real and measurable, so escalating first is
process without benefit. What is *not* deferred is anything whose error is
silent or irreversible — canonical wording drift, a lost source reference, a
constraint that was documented but never implemented. Those keep their tests.

### D8: The source package is not prototype material
Destructive iteration applies to work this project authored: the prototype
schema, its seed data, its templates. It does not apply to the enterprise
package zip, which is institutional data and the only copy of a document
authored elsewhere. That stays untracked and gitignored, and no extract of its
business workbooks is written into the repository.

### D9: One table is added to Rev2, because the spec requires what Rev2 lacks
The `source-provenance-and-validation` capability states that a confirmation
SHALL record who confirmed it and when. Revision 2 cannot satisfy that. Checked
across both the baseline and the migration: all 27 tables contain no audit,
history, log, validation or event table; `validation_status` is a bare
`varchar(40) not null default 'Needs Review'` carrying no actor and no
timestamp; and the only `updated_by_person_id` in the schema belongs to
`initiative_update`.

A mutable `validation_status` column also cannot express the register's status
workflow, which distinguishes *Not Started*, *In Review*, *Validated*,
*Requires Correction* and *Executive Approval Complete*.

**Decision:** add one table, `validation_event`, append-only, recording the
record type and identifier, the prior and new status, who acted, when, and an
optional note. `validation_status` on each record remains the current-state
projection, derived from the latest event.

**Rationale:** this is an addition to a frozen baseline, which ADR-012 governs.
It is declared rather than slipped in, and it is small and reversible. The
alternatives are both worse: dropping the who-and-when requirement weakens a
governance capability, and relying on the record's mutable column loses the
history that makes a confirmation auditable.

**Consequence:** Rev2 is 27 tables plus one, and the package's own table count
no longer matches this implementation. Task 1.2's count assertion covers the
transcribed package model; this addition lives separately and the difference is
stated rather than reconciled away.

## Risks

- **Governance change-control applies to the production build, not to this
  prototype.** ADR-012 freezes Rev2 and requires governance approval, an ADR
  amendment, migration and rollback impact analysis, updated test artifacts and
  a package version increment for any governed change. That regime governs the
  production build. Rapid prototyping deliberately works ahead of it, taking
  reversible defaults (D7) and recording each one with its reversal cost, so
  that a governance answer lands as a small edit rather than a redesign. The
  obligation that is *not* deferred is ADR-021's deviation record, because an
  undocumented deviation is indistinguishable from a constraint that was
  documented and never implemented — which is the package's own defect #2.
- **Business data does not exist yet.** The schema can be built and tested
  against synthetic data, but production migration is blocked on validation
  that has not started. Recording the block is more useful than working around
  it.
- **Zero of ten acceptance criteria are tested.** Every AC in the data package
  reads "Not Tested" with no evidence. Conformance claims must not be made
  until they are executed.
- **The package contains institutional data and is not yet gitignored.** It
  sits untracked and unignored in the repository root while the data-policy
  question about personal Azure subscriptions is open. This is the one item
  destructive prototyping does not excuse (D8).

## Findings, found while applying

### F4: The target database, provisioned and measured
Per the decision to test against the real target rather than a stand-in:

| | |
|---|---|
| Resource group | `rg-cll-rev2-dev`, `westus` |
| Server | `cllrev2sqlg7pmp.database.windows.net` |
| Database | `cllrev2`, sku `GP_S_Gen5` (serverless General Purpose), 2 vCore max, 0.5 min, auto-pause 60 min |
| Client | SQLAlchemy 2.0.51 with `mssql+pymssql`; pymssql 2.4.3, no system ODBC driver needed |
| Credentials | `%TEMP%\rev2sql.txt`, never in the repository |

Two provisioning notes worth keeping, because both cost time and will recur:

- `az sql server create` uses `--admin-user` / `--admin-password`, **not**
  `--administrator-login` / `--administrator-password`. And the password is
  re-parsed by `cmd.exe` even through the `-IBm` shim, so `%`, `!`, `#` and `^`
  must be avoided in it; Azure SQL still demands 3 of 4 character classes, so
  `_` and `*` are the safe way to satisfy complexity.
- Serverless creation needs `--compute-model Serverless`. Without it the CLI
  resolves `--capacity 0.5` against provisioned SKUs and dies with
  `invalid literal for int() with base 10: '0.5'`.

**The admin password was exposed once and rotated.** An early failed `az sql
server create` echoed the password into its error output, and that same value
was reused by the create that succeeded. The password was rotated with
`az sql server update` and the new one verified by connecting; the exposed value
is no longer valid.

`northcentralus` refuses new SQL servers (`RegionDoesNotAllowProvisioning`), so
the server is in `westus`, where the subscription's existing SQL server also
lives. Serverless auto-pause is chosen because the prototype is idle most of the
week.

The existing `cll-pmo-dev-sql` server was **not** used: its Key Vault denies this
principal, it has no firewall rules, and it sits in a shared resource group with
App Insights and a Key Vault that this project did not create. Resetting its
admin password would have been a destructive act on another owner's
infrastructure.

### F5: D3's deviations are measured on the real target, not assumed
Probed against the live database:

| Mechanism | Result on Azure SQL |
|---|---|
| Filtered unique index (`WHERE ... IS NOT NULL`) | **Present.** Refuses a duplicate inside the filter, and permits multiple `NULL`s — matching the PostgreSQL partial-index semantics the primary-owner rule depends on. |
| `CHECK` constraint | Present. |
| `EXCLUDE USING gist` | **Absent.** `Incorrect syntax near 'gist'`. |
| `tstzrange` range type | **Absent.** `Cannot find data type tstzrange`. |

The stewardship period non-overlap rule therefore has no native target
mechanism, as D3 predicted, and needs the substitute. The filtered-index result
is the good news: the exactly-one-current-primary-Reporting-Owner rule needs no
substitute at all.

### F1: The prototype's goal numbering contradicts canonical Strategy 2035
Verified by comparing `ospec/cll_initiatives.db` against the package's Goals
sheet.

| GoalNumber | Prototype | Canonical | |
|---|---|---|---|
| 1 | Academic | Academic | ok |
| 2 | Extension | Extension | ok |
| 3 | **Research** | **Learner** | mismatch |
| 4 | **Learner impact** | **Research** | mismatch |
| 5 | Operational | Operational | ok |

Goal number is the canonical identifier — the package constrains
`goal_number between 1 and 5` and treats it as unique — and the live
application routes on it, so `/goals/3` currently presents Research where
canonically 3 is Learner. Rev2 loads canonical goals from source, so the new
schema is unaffected; the defect is in the prototype's seed data and its live
presentation.

**Consequence:** it is not cosmetic. Any goal-scoped URL or bookmark is wrong,
and 3 and 4 are transposed in a live dashboard. Task 8.1 supersedes the
prototype schema and task 8.2 relabels its data; both must not silently carry
the wrong numbering forward, and the fix is to seed from canonical source
rather than correct the existing rows.

### F2: Rev2 cannot satisfy the validation-confirmation requirement
Recorded as D9. All 27 package tables lack any actor/timestamp for a
validation decision; `validation_status` is a bare varchar with no attribution.
### F3: The prototype carries a truncated paraphrase of canonical goal 1
Goal 1's `FullName` is *"Catalyze a learning society and build a home for
transformative learning"*, against the canonical *"Catalyze a learning society
and build the world's home for transformative learning-systems leaders."* Goals
2 to 5 carry no title at all. The package forbids overwriting canonical wording,
though it permits an alias. A truncated paraphrase is neither, so the prototype
is relabelled as synthetic (task 8.2) rather than treated as an alias.

### F6: `initiative.status` and an update's status are two different vocabularies
Found by writing a fixture that set `initiative.status = 'On track'` and having
the schema refuse it. The distinction is real and easy to conflate:

| Column | Vocabulary | Meaning |
|---|---|---|
| `initiative.status` | Proposed, Active, On Hold, Completed, Retired | lifecycle of the initiative |
| `initiative_update.status_at_update` | On track, At risk, Off track, Complete, ... | a progress report for that moment |

`'On track'` is not a valid initiative lifecycle state and `'Active'` is not a
valid progress report. A read model that copies the update's status into the
initiative's cached column would be writing across the two, and the CHECK stops
it. Worth keeping precisely because the two columns sit next to each other and
share several words (`Complete`/`Completed`).

### F7: The suite's own cleanup must respect the guards it is testing
Several test failures along the way were the guards working correctly and the
cleanup being wrong, not defects:

- `DELETE FROM initiative_update` is refused by the append-only guard (correct),
  so test cleanup disables it explicitly and only there.
- Removing the last goal mapping from an **active** initiative is refused (5011),
  so cleanup retires initiatives before unlinking them - the same order a real
  retirement uses.
- One leftover committed row with `goal_number = 1` failed **35 tests** at once,
  because `goal_number` is `UNIQUE` over 1..5. The fixture now purges at setup as
  well as teardown, since setup can raise and when it does teardown never runs.
- pymssql's `Cursor` refuses attribute assignment, so the fixture returns a small
  session holder rather than hanging metadata off the cursor.

### F8: `EXCLUDE USING gist` and `tstzrange` do not exist in T-SQL
Measured on the live target, not assumed: `Incorrect syntax near 'gist'`, and
`Cannot find data type tstzrange`. Deviation #5 in `../mssql/DEVIATIONS.md`. The
filtered unique index, by contrast, is fully native - including the
NULL-is-distinct behaviour the primary-owner rule depends on.

### From prototype to Rev2 (schema level)

| Prototype | Rev2 | Note |
|---|---|---|
| `Goals` | `goal` | Adds canonical title, source, display order |
| — | `strategic_objective` | New tier; 25 canonical records |
| — | `portfolio`, `portfolio_goal` | New lens |
| `Priorities(PlanYear)` | `priority_definition` + `planning_cycle` + `priority_cycle` | Splits reusable definition from cycle instance |
| `Initiatives` | `initiative` | Adds type, status, dates, validation status |
| — | `target`, `objective_target`, `objective_initiative` | New traceability tier |
| — | `metric`, `metric_version`, `initiative_metric`, `goal_metric`, `target_metric` | Metric layer, deferred from MVP use but present in schema |
| `InitiativeGoals` | `initiative_goal` | Adds relationship type, rationale, effective dates |
| `InitiativePriorities` | `initiative_priority_cycle` | Binds to cycle, not definition |
| `InitiativeLinks` | `initiative_relationship` | One meaning becomes 5 or 10 typed relations |
| `Initiatives.OwnerID` | `initiative_owner` | One slot becomes 4 or 8 effective-dated roles |
| — | `stewardship_assignment` | Separate concern |
| `ProgressUpdates` | `initiative_update` | Append-only, with attribution |
| `People` | `person` + `team` | Gains business email, team; loses admin flag |
| `AuditLog` | — | No Rev2 equivalent; see below |
| `vw_*` read models | new views | Must be redefined; existing ones resolve through replaced tables |

`AuditLog` has no counterpart in Rev2. ADR-010 makes updates append-only and
attributed, which covers the update history, but the prototype also audited
mapping and ownership changes. Where that history lives under Rev2 needs a
decision — possibly effective-dated rows are the audit trail, possibly a
separate log is required. Recorded as an open item.

### Order of work

1. Adopt the D7 defaults and gitignore the package (tasks group 0). Nothing
   blocks on these.
2. Build the schema and read models, recording each platform deviation as its
   constraint is implemented (D3).
3. Land each group's own tests as its work lands.
4. Run the cross-cutting acceptance and coverage checks. Report results
   honestly, including failures.
5. Only then consider loading any data — which is blocked on business
   validation regardless.

## Open questions

Questions 1 to 5 are the package's internal contradictions. Under D7 each is
resolved by a reversible default, so none blocks work. They remain open in the
sense that the governance group has not answered, and each answer maps to a
single named mechanism.

| # | Question | Default (D7) | Owner |
|---|---|---|---|
| 1 | `Accountable Executive` or `Accountable Owner`; is `Operational Lead` assignable? | `Accountable Owner`, alias for display, `Operational Lead` deferred | Governance group |
| 2 | Are the five additional relationship types in scope? | No; the five already permitted | Governance group |
| 3 | Authoritative `progress_method`; is `Weighted Metric` in scope while rollups are deferred? | `Owner Estimate`, `Metric Derived` | Governance group |
| 4 | Does `data_product` exist, or is that value removed? | Removed | Governance group |
| 5 | Are `Team` and `Enterprise` levels in scope? | No; `Dean` and `D-1` | Governance group |

Questions 6 to 8 are settled here or in tasks group 0.

| # | Question | Resolution |
|---|---|---|
| 6 | Revise the prototype's specs to describe Rev2 behaviour, or retain them? | Retained unchanged as a record of prototype behaviour (D7) |
| 7 | Retire the prototype at cutover, or keep it live? | Keep live through adoption (D6) |
| 8 | Where does mapping and ownership change history live? | Recorded in tasks group 0; default is effective-dated rows, with the prototype `AuditLog` explicitly dropped rather than silently lost (D7) |