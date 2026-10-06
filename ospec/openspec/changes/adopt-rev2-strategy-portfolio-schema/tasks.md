# Tasks

## 0. Reversible defaults and provenance

This is a rapid prototype and destructive iteration is acceptable, so nothing
here blocks the groups below. The five package contradictions are resolved by
picking a default, not by waiting for the governance group: every table is
empty of operational rows, so changing a vocabulary costs a CHECK constraint
edit rather than a migration. Each default chosen in `design.md` D7 is marked
with what it would take to reverse, so a later governance answer is a small
change rather than a redesign.

- [x] 0.1 Adopt `Accountable Owner` as the stored accountability role name, with `Accountable Executive` as a display alias, and defer `Operational Lead` until someone asks for it. *Verify: `design.md` D7 records the choice, the alias, the deferral, and the one-constraint cost of reversing it.*
- [x] 0.2 Adopt the five relationship types the baseline CHECK actually permits (`Supports`, `Enables`, `Depends On`, `Contributes To`, `Replaces`) and defer the five the migration narrates but never applies. *Verify: `design.md` D7 records the choice, and the schema's permitted set equals this list with nothing wider.*
- [x] 0.3 Adopt `Owner Estimate` and `Metric Derived` as the progress methods, dropping `Weighted Metric` because ADR-013 defers weighted rollups and dropping `Manual` as redundant with `Owner Estimate`. *Verify: `design.md` D7 records the choice, and the accepted set matches the controlled-vocabulary spec so the two agree.*
- [x] 0.4 Remove `Data Product` from the stewardship entity vocabulary, since no `data_product` table exists to steward. *Verify: `design.md` D7 records the removal, and a structural check confirms every permitted stewardship entity type resolves to a real table.*
- [x] 0.5 Adopt `Dean` and `D-1` as the only initiative levels, matching the project config and the implementation checklist. *Verify: `design.md` D7 records the choice, and adding a `Team`-level row is refused.*
- [x] 0.6 Record where mapping and ownership change history lives, given Rev2 has no `AuditLog`. *Verify: `design.md` D7 states the decision, and the audit requirement in the traceability spec is satisfied by effective-dated rows, a log, or an explicitly recorded decision to drop it with a reason.*
- [x] 0.7 Retain the prototype's nine capability specs unchanged as a record of prototype behaviour, and let Rev2 behaviour live in this change's specs. *Verify: `design.md` D7 records the decision, and `openspec validate add-initiative-dashboard-prototype --strict` still exits 0.*
- [x] 0.8 Confirm the prototype stays live through adoption. *Verify: `design.md` D6 is marked confirmed and open question 7 is closed.*
- [x] 0.9 Add the enterprise package zip to `.gitignore`. *Verify: `git check-ignore -v` names the zip and `git status --short` does not list it. This one is not deferred: the zip is institutional data, not a prototype artefact, and destructive iteration does not apply to the only copy of a document this project did not author.*
- [x] 0.10 Record that no extract of the package's business workbooks has been written into the repository. *Verify: a repository-wide search for initiative and person names from `03_Strategy_Portfolio_Data_Package.xlsx` and `10_Business_Data_Validation_Register.xlsx` returns nothing outside the prototype's own sample database.*

## 1. Package baseline and provenance

- [x] 1.1 Record the package's provenance in the repository: archive SHA256 `EB71B8BCA667420F78E3289C4D2AB4DD341482CDAA464E7E1050E30A1251E08E`, baseline date 2026-10-05, and the verified `SHA256SUMS.txt` result of 12 of 12 files matching. *Verify: a provenance note states these values and a re-verification step recomputes the archive hash and matches it.*
- [x] 1.2 Transcribe the 27-table Rev2 model into `ospec/db/rev2/` as baseline and migration files, keeping the package's PostgreSQL forms intact and unrewritten. *Verify: the transcribed set contains 15 baseline and 12 migration tables, and the counts are asserted by a check that fails if either number differs.*
- [x] 1.3 Record the five package contradictions as named open items in the transcribed baseline's header comments, each citing the two conflicting sources. *Verify: each contradiction is traceable to the file and line in the package that states it.*
- [x] 1.4 Document that no approved initiative inventory exists, citing the package's readiness table and the empty operational sheets. *Verify: the document states the zero-row counts for `Initiatives`, `People`, `Ownership`, `Updates` and `Metrics` as read from the workbook.*

## 3. Schema construction

Each group lands its own tests. Vocabularies come from group 0's defaults, and
each group records its own platform deviations as it meets them rather than
declaring them all up front.

ADR-021 still obliges engineering to document every semantic deviation from the
PostgreSQL reference. In a prototype the register grows alongside the schema,
but a deviation is never left implicit: it is written down when the constraint
is implemented, with the residual risk stated rather than assumed away.

- [x] 3.1 Create the canonical strategy tables — goal, strategic objective, target, source record, portfolio and portfolio-to-goal — and verify canonical goal and objective records resist hard deletion. *Verify: a test attempts a hard delete of a canonical goal and of a canonical objective, and both are refused with the records still retrievable.*
- [x] 3.2 Create the initiative and priority tables including priority definition, planning cycle and priority cycle, and verify no goal-to-priority relationship exists in the created schema. *Verify: a structural check enumerates every foreign key in the created schema and asserts that none connects a goal-bearing table to a priority-bearing table.*
- [x] 3.3 Create the relationship tables — initiative-to-goal, initiative-to-priority-cycle, initiative-to-initiative, initiative-to-owner — and verify duplicate junction rows are refused. *Verify: a test inserts an identical junction row twice and asserts the second is refused.*
- [x] 3.4 Create the metric tables including effective-dated metric version, and verify a metric cannot have two current versions and that a version's effective end cannot precede its start. *Verify: both refusal tests pass.*
- [x] 3.5 Create stewardship assignment and verify overlapping periods for the same person, entity and role are refused. This is the one mechanism with no native target-platform equivalent, so implement it with an explicit substitute and record the deviation here rather than in a separate register. *Verify: the overlap test passes serially; a concurrent-write test either refuses the overlap or admits it, and whichever the outcome, the deviation entry states that behaviour and names the serialising mechanism used.*
- [x] 3.6 Verify the controlled vocabularies are enforced by the database rather than only by the application, and that the values the database accepts match the values the vocabulary documents. *Verify: for each governed field, a test inserts a permitted value and an unpermitted value, and asserts the permitted one is accepted and the other refused; the permitted set is read from the vocabulary spec rather than duplicated in the test, so a later change to the vocabulary cannot silently disagree with the schema.*

The group 0 decisions recorded a choice; these three prove the choice is what the
schema enforces. Each closes the enforcement half of a group 0 verify that could
not be checked until tables existed.

- [x] 3.7 Assert the relationship vocabulary is exactly the five D7 permits, with nothing wider. *Verify: the accepted set equals `Supports, Enables, Depends On, Contributes To, Replaces`, and inserting `Delivers` is refused - which is the constraint the package narrates but never applies.*
- [x] 3.8 Assert the initiative level vocabulary is exactly `Dean` and `D-1`. *Verify: inserting a `Team`-level or `Enterprise`-level initiative is refused.*
- [x] 3.9 Assert every permitted stewardship entity type resolves to a real table. *Verify: a structural check maps each accepted `entity_type` value to a table that exists, and fails naming any value with no table - which is the defect that made `Data Product` unsatisfiable.*

## 4. Constraint enforcement

- [x] 4.1 Enforce that a hierarchical relationship runs from a D-1 initiative to a Dean initiative, and verify the reverse direction is refused. *Verify: a D-1-to-Dean insert succeeds and a Dean-to-D-1 insert is refused with a message naming the attempted direction.*
- [x] 4.2 Enforce that an initiative cannot relate to itself. *Verify: a self-referencing insert is refused.*
- [x] 4.3 Enforce cycle prevention across the full existing chain, and verify a cycle longer than three initiatives is caught. *Verify: both the three-initiative and a longer chain are refused, and the refusal names the cycle.*
- [x] 4.4 Enforce that an active initiative has at least one current goal mapping and an active D-1 initiative supports at least one Dean initiative, and verify each requirement independently of the other. *Verify: a test shows an initiative satisfying the goal rule but failing the Dean rule is still refused on the Dean rule, and the reverse.*
- [x] 4.5 Enforce that an active D-1 initiative has exactly one current primary Reporting Owner, allowing several non-primary assignments. *Verify: a second current primary is refused, and multiple Contributor assignments are accepted.*
- [x] 4.6 Enforce that initiative updates are append-only, and verify a correction is recorded as a new update with the original retained. *Verify: an in-place modification of an existing update is refused and both updates remain retrievable afterwards.*

## 5. Read models

The prototype's views resolve through `Initiatives.OwnerID` and
`InitiativeLinks`, both replaced. These are the read models the four cards
depend on.

- [x] 5.1 Define the read models resolving a goal to its initiatives with owners, priorities, status and latest updates, and verify goal and priority lists return the same underlying records. *Verify: a test retrieves one initiative through its goal and through its priority and asserts the returned record is identical.*
- [x] 5.2 Define the read model resolving current progress and status from the latest update, per decision D2, and verify it cannot disagree with the update history. *Verify: after posting an update, the derived value equals the update's recorded value; and a test proves the model reads the update rather than the initiative row's cached column.*
- [x] 5.3 Define the read model for an initiative's upstream and downstream relationships, and verify a D-1 initiative supporting two Dean initiatives returns both. *Verify: the two-parent case returns both links and treats neither as the sole parent.*
- [x] 5.4 Define the read model for a person's owned initiatives, and verify a person with neither owned initiatives nor reports still renders a meaningful result rather than a blank. *Verify: the stewardship-only person case returns a non-empty, non-error result.*
- [x] 5.5 Verify no read model presents an aggregate or averaged progress figure for a parent initiative. *Verify: a search across the read-model definitions finds no computed parent progress, and a test asserts a parent initiative's recorded progress is unchanged when a child's progress changes.*

## 6. Traceability, provenance and validation

- [x] 6.1 Implement traceability traversal in both directions across portfolio, goal, objective, target, initiative, metric version and ownership, and verify each link in the chain is reachable. *Verify: a test walks the full chain from a goal and from an initiative and asserts both terminate at the far end.*
- [x] 6.2 Implement orphan detection for the baseline's defined conditions — initiative without goal, objective or primary owner; target without objective or measurement plan; metric without current version, stewardship or authoritative source — and verify each names its record. *Verify: a test introduces one instance of each defect and asserts each appears in the report with its identifier.*
- [x] 6.3 Implement the integrity report and verify it returns zero rows against a clean dataset and is not satisfied by silently repairing data. *Verify: the clean case returns zero rows, and a test shows that a defective record is still present and still defective after the report runs.*
- [x] 6.4 Implement source provenance retention and verify an unresolvable source reference is reported rather than loaded as confirmed. *Verify: a record with a dangling source reference is reported and does not reach a confirmed state.*
- [x] 6.5 Implement validation status handling and verify an unrelated edit does not change it, and that confirmation is explicit and attributable. *Verify: both behaviours are asserted, and a confirmation records who confirmed and when.*
- [x] 6.6 Verify that records whose relationships were inferred remain in a needs-review state and are never presented as leadership-confirmed. *Verify: an inferred mapping's status is asserted after import, and a presentation test shows it as unconfirmed.*

## 7. Integration evidence

These are cross-cutting checks over work already landed in groups 3 to 6, not
a separate test phase. Each group already tested its own behaviour; this group
confirms the parts behave correctly together and records what remains unproven.

- [x] 7.1 Execute all ten acceptance criteria from the specification and record the result of each, including failures. *Verify: a results artefact lists all ten with a pass or fail and evidence; no criterion is left blank, and none is recorded as passing on the strength of a component test alone.*
- [x] 7.2 Confirm the constraint coverage is complete by enumerating the enforcement mechanisms the schema defines and checking each has at least one test that proves it can refuse a violation. *Verify: the enumeration and the test references are recorded together, and a mechanism with no test is reported as a gap rather than omitted.*
- [x] 7.3 Verify canonical strategy wording round-trips unchanged from source through load and read. *Verify: a test compares loaded goal and objective text against the package source and asserts equality, including non-ASCII characters.*
- [x] 7.4 Record the readiness position honestly, including that business data validation has not started and that production migration remains blocked. *Verify: the recorded readiness matches the package's own gate items and does not assert approval that has not occurred.*

## 8. Prototype disposition

The prototype is destructive-replaceable, so this group is about not leaving
two contradictory schemas both looking authoritative.

- [x] 8.1 Mark `ospec/db/schema.sql` and `ospec/db/schema.mssql.sql` as superseded, recording which Rev2 tables replace each prototype table. *Verify: both files carry the supersession note, and the mapping table in `design.md` covers every prototype table.*
- [x] 8.2 Relabel the prototype's seeded initiatives as synthetic and non-governed, in the UI and in the seed data, so they are never presented as portfolio data. *Verify: a test asserts the synthetic label is present wherever an initiative is displayed, and that the live deployment shows it.*
- [x] 8.3 Record where audit history lives under Rev2, per the group 0 decision. *Verify: the prototype's audit behaviour is either reproduced under Rev2 or explicitly recorded as intentionally dropped with a reason.*
- [x] 8.4 Validate both changes together. *Verify: `openspec validate --all --strict` exits 0, covering this change and `add-initiative-dashboard-prototype`.*