# Spec Delta

## Purpose

Defines what it means for the initiative dashboard to be launched — the go-live criteria, the data-swap procedure that replaces illustrative figures with confirmed ones, the rollback, and the acceptance test that a real leadership meeting ran from it.

## ADDED Requirements

### Requirement: Launch is a judged state, not a deployed one
The service SHALL be considered launched only when every go-live criterion holds at once. A successful deployment SHALL NOT by itself constitute launch, because the service has been deployed and serving illustrative data since before this change.

#### Scenario: Deployment alone does not launch
- **WHEN** the service deploys successfully and serves pages
- **THEN** it is not yet launched
- **AND** the go-live criteria are still unverified

#### Scenario: Every criterion must hold together
- **WHEN** the go-live criteria are checked
- **THEN** each is verified independently
- **AND** a single failing criterion means the service is not launched, regardless of the others

### Requirement: Go-live criteria are observable
The go-live criteria SHALL each be checkable against the running service or its data, without reading the source. Every criterion SHALL be expressible as an observable fact.

#### Scenario: Goal data matches the canonical strategy
- **WHEN** the goal set is read from the running service
- **THEN** each goal's number and canonical wording match the Strategy 2035 source
- **AND** no goal carries a transposed number or a truncated title

#### Scenario: Every displayed figure is confirmed or marked
- **WHEN** any surface displays a status, percent or milestone
- **THEN** the figure is either confirmed by the person accountable for it
- **AND** or it is visibly marked as illustrative
- **AND** no figure is displayed as settled while being invented

#### Scenario: The weekly meeting ran from the service
- **WHEN** the leadership meeting is held
- **THEN** the agenda is read from the service
- **AND** every owner due to report appears with an update

#### Scenario: The live data is the live data
- **WHEN** the service is serving
- **THEN** its database is the one the service writes to
- **AND** no local database has been copied over it

### Requirement: Launch is reversible
The launch SHALL be reversible to the previous serving state, because the service is already in use and a bad launch would remove a working dashboard. The rollback SHALL be recorded and SHALL NOT depend on reconstructing anything from memory.

#### Scenario: Rollback returns the previous state
- **WHEN** a launch is judged failed
- **THEN** the previous serving revision can be restored
- **AND** the rollback procedure is written down before launch, not invented during an incident

#### Scenario: The data swap is reversible
- **WHEN** confirmed data is loaded and found to be wrong
- **THEN** the prior dataset can be restored
- **AND** the service returns to its previous figures

### Requirement: Launch status is visible on the service itself
The service SHALL state, on itself, whether it is serving confirmed or illustrative data, so that a reader cannot mistake one for the other. The marker SHALL be set by the data and SHALL NOT be a value a person remembers to change.

#### Scenario: Illustrative data announces itself
- **WHEN** the service is serving illustrative figures
- **THEN** the pages say so
- **AND** the statement survives a redeploy

#### Scenario: Confirmed data does not claim more than it is
- **WHEN** some figures are confirmed and others are not
- **THEN** the service distinguishes them
- **AND** it does not mark the whole as confirmed
