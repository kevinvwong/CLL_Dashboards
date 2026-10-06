# Spec Delta

## Purpose

Defines the governed traceability chain from Portfolio through Goal, Strategic Objective, Target, Initiative and Metric Version to ownership and stewardship, together with gap analysis for the orphan conditions the Revision 2 baseline specifies.

## ADDED Requirements

### Requirement: The governed traceability chain is answerable in both directions
The system SHALL support the chain `Portfolio -> Goal -> Strategic Objective -> Target -> Initiative -> Metric Version -> Ownership/Stewardship`. The system SHALL answer both which execution supports a given strategy element and which strategy elements a given initiative supports. Each link in the chain SHALL be optional in the sense the baseline defines, and a missing required link SHALL be reported as a traceability gap rather than silently accepted.

#### Scenario: From strategy to execution
- **WHEN** a goal is queried
- **THEN** its objectives, targets, initiatives and their metrics and owners are reachable
- **AND** the path between them is traversable in the stored relationships

#### Scenario: From execution back to strategy
- **WHEN** an initiative is queried
- **THEN** the goals, objectives, targets and metric versions it supports are reachable

#### Scenario: An objective with no execution is visible
- **WHEN** an objective has no linked initiative
- **THEN** it is reported as lacking execution coverage
- **AND** the report names the objective

#### Scenario: A metric may evidence several targets and initiatives
- **WHEN** one metric version is linked to two targets and one initiative
- **THEN** all three links are retained
- **AND** the metric version is reported as evidencing each of them

### Requirement: Objectives and targets are first-class, separate from metrics
A Target SHALL be stored separately from a Strategic Objective and separately from a Metric. A Target expresses a desired outcome; a Metric defines how performance is measured. Target wording, value, unit, timeframe and source provenance SHALL be retained. A Metric SHALL contain at least one effective-dated version, and at most one version SHALL be current at any time.

#### Scenario: A target's wording is retained verbatim
- **WHEN** a target is stored
- **THEN** its value, measure context, unit and timeframe are retained as given
- **AND** none is derived from a metric

#### Scenario: A metric has exactly one current version
- **WHEN** a second metric version is opened without closing the existing one
- **THEN** the write is refused

#### Scenario: Historical reporting references the applicable version
- **WHEN** a report is produced for a past period
- **THEN** it references the metric version effective during that period
- **AND** it does not substitute the current definition

#### Scenario: Metric version dates are coherent
- **WHEN** a metric version is given an effective end before its effective start
- **THEN** the write is refused

#### Scenario: A target needs a measurement plan or an exception
- **WHEN** a target has no linked metric version and no approved exception
- **THEN** it is reported as an orphan target

### Requirement: Metric, target and portfolio records require stewardship and source
A production metric version SHALL identify one authoritative source and a source owner. A target SHALL retain canonical provenance and connect to a governed measurement plan or an approved exception. A metric version without approved source authority SHALL NOT be promoted to production.

#### Scenario: A metric without an authoritative source is not production-eligible
- **WHEN** a metric version has no authoritative source recorded
- **THEN** it is not eligible for production promotion

#### Scenario: An ambiguous metric is reported
- **WHEN** a target exists with no definition, owner, source or calculation method for its measurement
- **THEN** it is reported as an ambiguous metric

### Requirement: Orphan conditions are defined and detectable
The system SHALL detect and report the baseline's defined orphan conditions: an active initiative missing a goal, objective or current primary Reporting Owner; a target missing an objective relationship or a metric or approved measurement exception; and a metric missing a governed use, current version, assigned stewardship or authoritative source. A detection SHALL name the record and the condition.

#### Scenario: An orphan initiative is named
- **WHEN** an active initiative has no goal mapping
- **THEN** it is reported as an orphan initiative with its identifier

#### Scenario: An orphan metric is named
- **WHEN** a metric has no current version or no assigned steward
- **THEN** it is reported as an orphan metric with its identifier

#### Scenario: Approved exceptions satisfy a gap where permitted
- **WHEN** a required traceability link is absent but a documented approved exception exists for it
- **THEN** the record is not reported as a gap
- **AND** the exception remains discoverable

### Requirement: Progress remains independent across levels
An initiative's reported progress SHALL NOT be derived from, or aggregated into, another initiative's progress. Parent completion SHALL NOT be mathematically computed until a formally approved rollup method and weights exist. Automated weighted rollups are deferred and SHALL NOT be implemented as a side effect of adopting this model.

#### Scenario: A Dean initiative's progress is owner-entered
- **WHEN** D-1 initiatives supporting a Dean initiative report progress
- **THEN** the Dean initiative's recorded progress does not change

#### Scenario: No implied total is displayed
- **WHEN** an initiative's supporting D-1 initiatives are shown
- **THEN** no combined or averaged progress figure is presented as the parent figure

#### Scenario: An approved rollup rule is a prerequisite, not a default
- **WHEN** no approved rollup rule exists
- **THEN** no rollup is computed
- **AND** progress for each initiative remains separately recorded