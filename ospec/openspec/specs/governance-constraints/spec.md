# governance-constraints Specification

## Purpose
Defines the enforcement mechanisms the Revision 2 baseline relies upon — cardinality limits, effective-dating integrity, assignment period non-overlap, relationship semantics by level, cycle prevention, append-only history and canonical deletion protection — together with the obligation to document and verify any semantic deviation introduced by the target platform.

## Requirements

### Requirement: Equivalent enforcement on the target platform
The system SHALL enforce every relationship rule the Revision 2 baseline defines, expressed through whatever mechanism the target platform provides. Where the target platform lacks an equivalent construct, the substitute SHALL be documented as a declared deviation, and SHALL be accompanied by a test demonstrating the substitute refuses the same invalid input the reference constraint refuses. A constraint documented but not implemented SHALL NOT be reported as satisfied.

#### Scenario: A declared deviation is traceable to its rule
- **WHEN** a constraint requires a construct the target platform does not provide
- **THEN** the deviation record names the baseline rule, the reference mechanism, the substitute, and the test evidence
- **AND** the deviation is discoverable without reading the implementation

#### Scenario: A documented constraint is proven to fail
- **WHEN** a constraint's test is executed against data violating that constraint
- **THEN** the write is refused
- **AND** the test result is evidence the constraint is active, not merely declared

#### Scenario: A test catalog cannot pass vacuously
- **WHEN** the constraint test suite runs
- **THEN** it contains both passing and failing cases
- **AND** at least one case proves each enforcement mechanism can refuse an invalid write

### Requirement: Active initiatives require a goal mapping
Every active initiative SHALL have at least one current goal mapping. The requirement SHALL be enforced across tables, because the rule spans an initiative and its mappings rather than living within either.

#### Scenario: Activating an initiative without a goal is refused
- **WHEN** an initiative with no current goal mapping is set active
- **THEN** the activation is refused
- **AND** no partial activation is committed

#### Scenario: The requirement is not deferred to commit in a way that lets it slip
- **WHEN** a transaction removes an initiative's only goal mapping while the initiative is active
- **THEN** the transaction does not complete successfully
- **AND** the initiative does not end up active with no goal

### Requirement: Active D-1 initiatives require a Dean link and one primary owner
Every active D-1 initiative SHALL support at least one Dean initiative through a hierarchical relationship type, and SHALL have exactly one current primary Reporting Owner. The two requirements are independent: satisfying one SHALL NOT be treated as satisfying the other.

#### Scenario: A D-1 initiative with no Dean link cannot go active
- **WHEN** a D-1 initiative with no link to a Dean initiative is set active
- **THEN** the activation is refused

#### Scenario: A second current primary Reporting Owner is refused
- **WHEN** a second person is assigned as current primary Reporting Owner for the same initiative
- **THEN** the assignment is refused
- **AND** the initiative retains exactly one current primary Reporting Owner

#### Scenario: Missing primary owner is detected, not merely absent
- **WHEN** an active D-1 initiative has no current primary Reporting Owner
- **THEN** it is reported by the integrity check as requiring remediation
- **AND** the report names the initiative

#### Scenario: One initiative supports several Dean initiatives
- **WHEN** one D-1 initiative is linked to two Dean initiatives
- **THEN** both links are retained
- **AND** neither is treated as the sole valid parent

### Requirement: Relationship direction follows initiative level
Hierarchical relationship types SHALL be expressed from a D-1 initiative to a Dean initiative. The reverse direction SHALL be refused for those types. Non-hierarchical relationship types SHALL NOT be constrained by level in the same way.

#### Scenario: Dean supports D-1 is refused
- **WHEN** a hierarchical relationship is created from a Dean initiative to a D-1 initiative
- **THEN** the write is refused
- **AND** the refusal identifies the direction that was attempted

#### Scenario: D-1 supports Dean is accepted
- **WHEN** a hierarchical relationship is created from a D-1 initiative to a Dean initiative
- **THEN** the write succeeds

#### Scenario: An initiative cannot relate to itself
- **WHEN** a relationship is created between an initiative and itself
- **THEN** the write is refused

### Requirement: Hierarchical relationship cycles are prevented
The system SHALL prevent a cycle formed by hierarchical relationship types, so that no chain of supports, contributes-to or enables relations returns to its starting initiative. The check SHALL consider the full existing chain, not only the immediately adjacent rows.

#### Scenario: A three-initiative cycle is refused
- **WHEN** relationships would form A to B, B to C and C to A
- **THEN** the final write is refused
- **AND** the refusal identifies the cycle

#### Scenario: A longer cycle is detected
- **WHEN** relationships would form a cycle longer than three initiatives
- **THEN** the final write is refused

### Requirement: Effective-dated assignments are temporally coherent
Every effective-dated relationship SHALL have an end date not earlier than its start date. For a given entity, person and role, assignment periods SHALL NOT overlap. A current assignment SHALL be represented by an absent end date.

#### Scenario: An end date before the start date is refused
- **WHEN** an assignment is given an effective end earlier than its effective start
- **THEN** the write is refused

#### Scenario: Overlapping assignment periods are refused
- **WHEN** a second assignment for the same entity, person and role begins before the first ends
- **THEN** the write is refused
- **AND** the first assignment is unchanged

#### Scenario: A closed assignment permits a new one
- **WHEN** a prior assignment for the same entity, person and role has an end date
- **AND** a new assignment begins on or after that end date
- **THEN** the new assignment is accepted
- **AND** the history of both assignments is retained

### Requirement: Initiative updates are append-only
Initiative updates SHALL be immutable history records. A prior update SHALL NOT be edited or deleted in place; a correction SHALL be recorded as a new superseding update or through an auditable administrative process. Attribution SHALL be retained on every update.

#### Scenario: An update cannot be overwritten
- **WHEN** an attempt is made to modify an existing update's narrative
- **THEN** the modification is refused
- **AND** the original update is unchanged

#### Scenario: A correction is additive
- **WHEN** a reported status was wrong
- **THEN** a new update records the correction
- **AND** the earlier update remains retrievable

#### Scenario: The latest update is identifiable
- **WHEN** an initiative has several updates
- **THEN** exactly one is identified as current
- **AND** the identification is derived from the recorded history rather than asserted separately

### Requirement: Canonical strategy records resist hard deletion
Canonical goals and canonical strategic objectives SHALL be protected from hard deletion. Where a record must leave active use, it SHALL be deactivated or retired so that its history and its references remain intact.

#### Scenario: A canonical goal cannot be hard deleted
- **WHEN** a hard deletion is attempted against a canonical goal
- **THEN** the deletion is refused
- **AND** the goal remains retrievable

#### Scenario: Retirement preserves traceability
- **WHEN** a goal is retired
- **THEN** its initiatives, objectives and targets remain linked to it
- **AND** the goal is marked retired rather than removed

### Requirement: Integrity problems are reported, not merely prevented
The system SHALL provide a report identifying records that violate a governance rule, including initiatives without a goal, D-1 initiatives without a Dean link, D-1 initiatives without a current primary Reporting Owner, duplicate mappings, and targets lacking a governed measurement plan. The report SHALL be expected to return zero rows against a clean dataset, and a non-empty report SHALL be treated as a defect rather than normal output.

#### Scenario: A clean dataset reports no defects
- **WHEN** the integrity report runs against fully conformant data
- **THEN** it returns zero rows

#### Scenario: Each defect class is named
- **WHEN** the integrity report runs against data with known defects
- **THEN** each defect is reported with its record identifier and the rule it violates

#### Scenario: A defect is never silently repaired
- **WHEN** a record violates a governance rule
- **THEN** the system reports it
- **AND** does not alter the record to make the report pass
