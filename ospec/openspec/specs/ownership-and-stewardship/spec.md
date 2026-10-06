# ownership-and-stewardship Specification

## Purpose
Defines effective-dated, multi-role ownership of initiatives as distinct from data stewardship, including the exactly-one-current-primary-Reporting-Owner rule for active D-1 initiatives.

## Requirements

### Requirement: Ownership is multi-role and time-bounded
An initiative MAY have several people holding different ownership roles, and each assignment SHALL carry an effective start and, when it ends, an effective end. Ownership SHALL NOT be modelled as a single owner field on the initiative. Additional roles beyond the primary owner SHALL be assignable, and role changes SHALL NOT alter the initiative's identifier.

#### Scenario: Several roles coexist on one initiative
- **WHEN** an initiative has a Reporting Owner and an Accountable Executive
- **THEN** both assignments are retained as separate rows
- **AND** neither displaces the other

#### Scenario: Reassigning ownership preserves history
- **WHEN** an initiative's Reporting Owner changes
- **THEN** the prior assignment is retained with its effective dates
- **AND** the initiative identifier is unchanged
- **AND** no prior assignment record is overwritten

#### Scenario: A role is vacated by end-dating, not deletion
- **WHEN** a person ceases to hold a role on an initiative
- **THEN** the assignment receives an effective end date
- **AND** the assignment row remains present

### Requirement: Exactly one current primary Reporting Owner for active D-1 initiatives
Every active D-1 initiative SHALL have exactly one current primary Reporting Owner. At most one may hold the role at a time. This requirement applies to active D-1 initiatives only, and is independent of whether the initiative has a Dean link.

#### Scenario: A second current primary Reporting Owner is refused
- **WHEN** a second person is assigned current primary Reporting Owner to an initiative that already has one
- **THEN** the assignment is refused

#### Scenario: Several non-primary assignments are permitted
- **WHEN** several people are assigned Contributor or Sponsor roles on one initiative
- **THEN** all assignments are retained
- **AND** none is treated as the primary Reporting Owner

#### Scenario: An active D-1 initiative with no primary owner is reported
- **WHEN** an active D-1 initiative has no current primary Reporting Owner
- **THEN** it appears in the integrity report as requiring remediation

#### Scenario: Ownership roles are governed vocabulary
- **WHEN** an assignment is created with a role outside the approved ownership vocabulary
- **THEN** the write is refused

### Requirement: Stewardship is distinct from ownership
Accountability for an initiative's outcome SHALL be recorded separately from accountability for the meaning, quality and technical operation of data relating to it. Stewardship SHALL be assignable for initiatives, metrics and targets, and each stewardship assignment SHALL be time-bounded and SHALL NOT overlap another assignment of the same person, entity and role.

#### Scenario: A steward is not an owner
- **WHEN** a person is assigned as Data Steward for an initiative
- **THEN** no ownership role is created for that person on that initiative
- **AND** the steward assignment is reported separately from ownership

#### Scenario: Overlapping stewardship periods are refused
- **WHEN** a person is assigned the same stewardship role for the same entity with a start date before an existing open-ended assignment ends
- **THEN** the write is refused

#### Scenario: Stewardship only applies to supported entity types
- **WHEN** a stewardship assignment names an entity type the system does not support
- **THEN** the assignment is refused
- **AND** the refusal names the unsupported entity type

### Requirement: Person records hold business identity only
A person record SHALL hold the business identity fields needed for portfolio accountability and SHALL NOT hold private human-resources attributes. Where a person belongs to an organisational team, that SHALL be recorded as metadata rather than as a key to strategy identity.

#### Scenario: Personal attributes are absent
- **WHEN** a person record is retrieved
- **THEN** it contains business identity fields
- **AND** it contains no private human-resources attributes

#### Scenario: Team membership does not confer strategy identity
- **WHEN** a person's team changes
- **THEN** their initiatives, ownership assignments and stewardship assignments are unchanged
- **AND** the team field is not used to determine goal or priority membership

#### Scenario: An inactive person keeps their history
- **WHEN** a person is marked inactive
- **THEN** their historical ownership and stewardship assignments remain retrievable
- **AND** they are not offered as a current assignee
