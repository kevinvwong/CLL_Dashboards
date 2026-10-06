# Spec Delta

## Purpose
Store goals, priorities, people, initiatives, and the links among them, and enforce the rules that keep the initiative taxonomy consistent across both entry points.

## ADDED Requirements

### Requirement: Two independent entry-point taxonomies
The system SHALL store 5 Strategy 2035 goals and the annual priorities for a plan year as separate lists, with no parent-child relationship between goals and priorities.

#### Scenario: Priority is not tied to a goal
- **WHEN** a priority is created
- **THEN** it is stored with a name and plan year and no goal reference

### Requirement: Initiative levels
The system SHALL classify every initiative as either Dean or D-1 and SHALL assign exactly one owner who is a person in the system.

#### Scenario: Invalid level rejected
- **WHEN** an initiative is saved with a level other than Dean or D-1
- **THEN** the save fails with a constraint error

#### Scenario: Unknown owner rejected
- **WHEN** an initiative is saved with an owner ID that does not exist
- **THEN** the save fails with a foreign key error

### Requirement: Many-to-many goal and priority tags
The system SHALL allow an initiative to be tagged to any number of goals and any number of priorities, with at most one primary goal and at most one primary priority.

#### Scenario: Second primary goal rejected
- **WHEN** an initiative already has a primary goal and another goal tag is saved as primary
- **THEN** the save fails with a uniqueness error

### Requirement: D-1 initiatives feed Dean initiatives
The system SHALL link D-1 initiatives to the Dean initiatives they feed and SHALL reject any link that does not run from a D-1 initiative to a Dean initiative.

#### Scenario: Valid link
- **WHEN** a D-1 initiative is linked to a Dean initiative
- **THEN** the link is saved

#### Scenario: Dean-to-Dean link rejected
- **WHEN** a link is saved between two Dean initiatives
- **THEN** the save fails with the message "Links must connect a D-1 initiative to a Dean initiative"

### Requirement: Retire instead of delete
The system SHALL retire initiatives and people with an active flag and SHALL exclude retired initiatives from all list and card views.

#### Scenario: Retired initiative hidden
- **WHEN** an initiative is marked inactive
- **THEN** it no longer appears on goal, priority, or person screens and its progress history remains in the database

### Requirement: Admin flag on people
The system SHALL mark people as admins with a flag, separate from initiative ownership, so dashboard team members can edit without owning initiatives.

#### Scenario: Admin without initiatives
- **WHEN** Kevin is stored as an admin with no initiatives
- **THEN** he appears in the person picker and no data check flags him
