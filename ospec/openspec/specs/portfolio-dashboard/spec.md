# portfolio-dashboard Specification

## Purpose

Define the home screen as a portfolio overview: the five Strategy 2035 goals, the six priorities shown with every governed field, and the four organizational teams each with its Major Initiative count — so a reader sees the whole shape of the College's work at a glance without the home replicating the source prototype's layout. The 29 Major Initiatives themselves are shown in full on their own index.

## Requirements

### Requirement: The home is a portfolio overview

The home screen SHALL present the portfolio as a dashboard of counts and cards, and SHALL NOT present a hero stage or a single fanning node.

#### Scenario: The overview leads the page
- **WHEN** the home screen loads
- **THEN** it shows a summary band of counts followed by the goal, priority and team sections, and no hero stage or Dean node

#### Scenario: Counts, not a performance score
- **WHEN** the summary band renders
- **THEN** it shows counts only, and no combined or averaged performance figure

### Requirement: Each priority shows every governed field

Each of the six priorities SHALL be shown with its code, its full title, its description, its measure, its target, its cadence and its owning label, so no field the source register carries is dropped.

#### Scenario: Priority card contents
- **WHEN** a priority card renders
- **THEN** it shows the priority code, full title, description, measure, target, cadence and owner label

#### Scenario: The governed values are the register's
- **WHEN** a priority's measure or target is displayed
- **THEN** it is the value stored for that priority, not a value invented by the screen

### Requirement: The four teams are shown

The home SHALL show the four organizational teams, each with its description and the number of Major Initiatives it carries, and each SHALL link to its own page.

#### Scenario: Teams render
- **WHEN** the home screen loads
- **THEN** it lists the four teams with their descriptions and their Major Initiative counts

### Requirement: The Major Initiatives are shown in full

The Major Initiatives index SHALL list every Major Initiative with its id, title, team, source area, strategy alignment, initiatives, target, target status, and the priorities it feeds. A Major Initiative is a body of work, not a measurement: its `target` is the target *text carried from the source register*, and it is shown as such.

#### Scenario: A Major Initiative shows its fields
- **WHEN** a Major Initiative renders
- **THEN** its team, source area, target and target status are all shown

#### Scenario: A Major Initiative shows what it feeds
- **WHEN** a Major Initiative feeds one or more priorities
- **THEN** each of those priorities is shown as a link

#### Scenario: A target needing review is marked
- **WHEN** a Major Initiative's target status is to be reviewed
- **THEN** the row is marked as needing review, distinct from a target carried from source
