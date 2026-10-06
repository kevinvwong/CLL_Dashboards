# Spec Delta

## Purpose

Defines the Revision 2 relational model as the governed target schema for the CLL Strategy Portfolio platform: the entities, controlled vocabularies, canonical-strategy protections, and the structural separation of Goals from annual priorities.

## ADDED Requirements

### Requirement: Revision 2 is the governed target schema
The system SHALL store strategy portfolio data in the Revision 2 relational model: a baseline of 15 tables plus a Revision 2 migration of 12 tables, replacing the nine-table model used by the prototype. Every governed relationship SHALL be represented by an explicit junction or relationship table with declared cardinality. Comma-delimited relationship fields SHALL NOT be used in storage.

#### Scenario: Initiative supports multiple goals and multiple priorities
- **WHEN** one initiative is linked to two goals and two annual priorities
- **THEN** four junction rows exist across the goal and priority mappings
- **AND** no goal row references a priority and no priority row references a goal

#### Scenario: Goal and priority remain independent lenses
- **WHEN** a goal list is retrieved
- **THEN** only initiatives linked to that goal are returned
- **AND** the result is identical whether or not those initiatives carry any priority mapping
- **AND** no priority grouping or hierarchy is imposed on the result

### Requirement: Goals and annual priorities are parallel entry points
The system SHALL expose five canonical Strategy 2035 goals and annual priorities as two independent navigation lenses over a shared initiative portfolio. The system SHALL NOT treat a priority as a child of a goal, and SHALL NOT require an initiative to be reached through a goal in order to be reached through a priority.

#### Scenario: A priority is reachable without any goal
- **WHEN** an initiative is tagged to a priority and to no goal
- **THEN** the initiative appears in that priority's list
- **AND** it does not appear in any goal's list

#### Scenario: A goal's initiatives are not partitioned by priority
- **WHEN** a goal's initiatives are listed
- **THEN** every linked initiative appears regardless of which priorities it carries
- **AND** the total is not presented as a partition of any larger set

#### Scenario: One initiative in many priority cycles
- **WHEN** a reusable priority appears in two planning cycles
- **THEN** both cycle records exist for that priority definition
- **AND** an initiative may be linked to either or both cycle records
- **AND** each cycle record may hold its own description and display order

### Requirement: Strategy 2035 objectives are canonical and distinct from initiatives
The system SHALL store the 25 Strategy 2035 objective statements as Strategic Objective records, each belonging to exactly one goal and ordered within that goal. Objectives SHALL NOT be treated as initiatives, and an initiative SHALL NOT be created from an objective statement. Canonical objective wording SHALL be aliased for display at most, and SHALL NOT be overwritten.

#### Scenario: Objectives are protected from deletion
- **WHEN** a deletion is attempted against a canonical strategic objective
- **THEN** the deletion is refused
- **AND** the objective remains present

#### Scenario: An objective is not an initiative
- **WHEN** an objective statement exists for a goal
- **THEN** no initiative record exists for that statement
- **AND** the goal's coverage is expressed only through initiative links

#### Scenario: Display alias does not replace canonical text
- **WHEN** a goal or objective is presented using a short alias
- **THEN** the canonical wording remains retrievable and unaltered
- **AND** the alias does not become the stored canonical text

### Requirement: Portfolios are a navigational lens, not a strategy replacement
The system SHALL support portfolios as a first-class organisational grouping connected to goals, without replacing or redefining canonical goal wording. Portfolio names and goal mappings SHALL carry validation status, because the canonical authority for strategy wording is the Strategy 2035 source and not the portfolio layer.

#### Scenario: A portfolio groups goals without rewriting them
- **WHEN** a portfolio is mapped to a goal
- **THEN** the goal's canonical title and description are unchanged
- **AND** the mapping itself is subject to business validation

#### Scenario: Unvalidated portfolio mapping is visible as such
- **WHEN** a portfolio-to-goal mapping has not been confirmed
- **THEN** its validation status indicates it still requires review
- **AND** it is distinguishable from a confirmed mapping

### Requirement: Controlled vocabularies govern enumerated fields
The system SHALL restrict enumerated fields to approved vocabularies and SHALL refuse any value outside them. Governed fields SHALL include initiative level, initiative type, initiative status, progress method, goal relationship type, priority relationship type, initiative relationship type, ownership role, stewardship role, validation status, and initiative type promotion.

#### Scenario: An unlisted initiative level is refused
- **WHEN** an initiative is created with a level outside the approved list
- **THEN** the write is refused
- **AND** no partial record is created

#### Scenario: A duplicate junction row is refused
- **WHEN** an identical initiative-to-goal mapping is inserted a second time
- **THEN** the insert is refused as a duplicate

#### Scenario: Vocabularies are the single source of allowed values
- **WHEN** a client displays the permitted values for a governed field
- **THEN** the values it offers match the values the database will accept

### Requirement: Source provenance and validation status are retained
The system SHALL retain a source reference, an authority level, and a validation status for every imported record and every inferred relationship. An inferred or synthesised mapping SHALL remain in a needs-review state until an authorised business owner confirms it. Records SHALL distinguish imported, needs-review, leadership-confirmed, canonical and retired states.

#### Scenario: Inferred mappings do not present as confirmed
- **WHEN** a mapping is inferred during import rather than supplied by an authoritative source
- **THEN** its validation status is needs-review
- **AND** it is not presented as leadership-confirmed

#### Scenario: Validation status is retained through later edits
- **WHEN** a needs-review record is edited for a non-validation reason
- **THEN** its validation status is unchanged
- **AND** confirmation is an explicit separate act

#### Scenario: Every imported record resolves to a source
- **WHEN** an initiative is imported
- **THEN** the record references a source whose authority level is recorded
- **AND** a record with no resolvable source is identified as an issue