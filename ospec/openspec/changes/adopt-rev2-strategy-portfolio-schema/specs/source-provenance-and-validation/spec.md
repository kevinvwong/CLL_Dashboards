# Spec Delta

## Purpose

Defines retention of source provenance and validation status on imported records and inferred relationships, so that unconfirmed data is never presented as confirmed and every record remains traceable to the authority it came from.

## ADDED Requirements

### Requirement: Every record retains source provenance
Every imported record SHALL reference a source record identifying the source type, source name, source locator and authority level. Canonical strategy wording SHALL resolve to the canonical source. A record whose source cannot be resolved SHALL be reported as an issue rather than loaded as though confirmed.

#### Scenario: Canonical wording resolves to the canonical source
- **WHEN** a goal is loaded from the Strategy 2035 source
- **THEN** the goal references that source and its authority level is recorded as canonical

#### Scenario: An unresolved source is an issue
- **WHEN** a record is supplied with a source reference that does not resolve
- **THEN** the record is reported as an issue
- **AND** it is not treated as confirmed

#### Scenario: Supporting material does not override canonical wording
- **WHEN** a supporting resource disagrees with a canonical goal's wording
- **THEN** the canonical wording is retained unchanged
- **AND** the disagreement is recorded rather than applied

### Requirement: Validation status governs what may be presented as settled
Every record and every relationship SHALL carry a validation status drawn from the governed vocabulary. Records that were imported or whose relationships were inferred SHALL remain in a needs-review state until an authorised business owner confirms them. Validation status SHALL be changed only by an explicit confirmation act, never as a side effect of an unrelated edit.

#### Scenario: Inferred relationships remain unconfirmed
- **WHEN** a relationship is inferred during import rather than supplied
- **THEN** its validation status is needs-review

#### Scenario: An unrelated edit does not confirm a record
- **WHEN** a needs-review initiative is edited to correct its description
- **THEN** its validation status is unchanged

#### Scenario: Confirmation is explicit and attributable
- **WHEN** a business owner confirms a record
- **THEN** the confirmation is recorded with who confirmed it and when
- **AND** the record moves out of needs-review

#### Scenario: Unconfirmed data is distinguishable in every view
- **WHEN** any record is presented
- **THEN** its validation status is visible
- **AND** a needs-review record is not presented as leadership-confirmed

### Requirement: Migration loads canonical strategy first and infers nothing silently
The load order SHALL place canonical goals and strategic objectives first, then annual priorities for the planning period, then initiatives normalised into staging, then ownership matched on business identity, then explicit mappings. Inferred mappings SHALL be flagged needs-review. Duplicate, orphan and vocabulary checks SHALL run before any record is promoted to production.

#### Scenario: Load order is observable
- **WHEN** a migration runs
- **THEN** canonical goals and objectives are loaded before initiatives
- **AND** the sequence is evidenced in the migration record

#### Scenario: Ownership is matched on business identity
- **WHEN** an owner is matched to a person
- **THEN** the match is by business email
- **AND** an unmatched owner is reported rather than creating a person

#### Scenario: Defect checks precede promotion
- **WHEN** data is prepared for production
- **THEN** duplicate, orphan and vocabulary checks have run
- **AND** promotion does not proceed while a blocking defect remains

### Requirement: Validation completeness is distinct from technical presence
A record SHALL NOT be treated as complete merely because it is present in the database. Completeness requires required fields, relationships, ownership, stewardship, authoritative source, validation status and approvals. Unapproved exceptions SHALL be documented with a justification, an owner, a review or expiry date and a remediation plan where applicable, and SHALL NOT satisfy a governance requirement once expired.

#### Scenario: Presence alone does not mean complete
- **WHEN** a record exists with all required fields but no approved validation
- **THEN** it is not reported as complete

#### Scenario: An undocumented exception does not satisfy a rule
- **WHEN** a required traceability link is absent and no approved exception exists
- **THEN** the gap is reported

#### Scenario: An expired exception stops satisfying the rule
- **WHEN** an approved exception has passed its review date
- **THEN** the underlying gap is reported again

### Requirement: Migrated data retains crosswalk identity
Migrated records SHALL retain their source identifiers alongside the identifiers assigned in the system, so that any record can be traced back to its origin and reconciliation counts can be verified against the source.

#### Scenario: Crosswalk identifiers are retained
- **WHEN** a record is migrated from a source
- **THEN** both the source identifier and the system identifier are retained

#### Scenario: Reconciliation counts can be checked
- **WHEN** a migration completes
- **THEN** record counts per entity are comparable between source and target