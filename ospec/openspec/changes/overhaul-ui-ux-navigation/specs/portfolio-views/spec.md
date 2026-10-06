# Spec Delta

## Purpose

Define the portfolio-level screens: the Overview health strip, status breakdowns on goal and priority cards, the initiatives and people indexes, and grouped list behaviour, so the Dean can see health and drill in from one place.

## ADDED Requirements

### Requirement: Overview Health Strip
The Overview SHALL show a row of stat tiles above the goals:

- total initiatives
- a count for each status
- the number of stale initiatives (no update in 14 or more days)
- the date of the last meeting

#### Scenario: Health strip values
- **WHEN** the portfolio has 26 initiatives, 1 of them off track and 3 at risk
- **THEN** the strip shows Total 26, Off track 1, and At risk 3, and each tile links to the Initiatives index with that filter applied

### Requirement: Goal and Priority Cards with Status Breakdown
Each Strategy 2035 goal card and each 2027 priority card SHALL show:

- its name
- a one-line description
- its total initiative count
- a stacked bar of initiatives by status

#### Scenario: Card breakdown
- **WHEN** a goal has 10 initiatives, 9 on track and 1 at risk
- **THEN** the card shows "10 initiatives" and a stacked bar with segments for 9 on track and 1 at risk

### Requirement: Accurate Rollup Labels
Goal and priority detail pages SHALL label the rollup as a total count followed by a per-status breakdown. They SHALL NOT use a single status word next to the total.

#### Scenario: Rollup label
- **WHEN** the Academic goal page loads with 10 initiatives, all on track
- **THEN** the header reads "10 initiatives · 10 on track", not "On track 10"

### Requirement: Grouped Initiative Lists
Goal and priority detail pages SHALL let the user group initiatives by owner, tier, or status. Each group header SHALL render before its group. No tier label SHALL appear without a group under it.

#### Scenario: Group by owner
- **WHEN** the user picks "Group by owner"
- **THEN** each owner's name appears as a header directly above that owner's initiatives, Bill's group included

### Requirement: Single-Target Initiative Rows
Each initiative row SHALL be one clickable element that opens the initiative detail. The row SHALL show:

- ID
- name
- owner chip
- primary marker (where applicable)
- progress bar
- status pill
- last-update age

#### Scenario: Row click
- **WHEN** the user clicks anywhere on an initiative row
- **THEN** the initiative detail drawer opens

### Requirement: Initiatives Index
The system SHALL provide `/initiatives`: a sortable table of all initiatives that can be filtered by owner, tier, goal, priority, status, and staleness. The filter state SHALL be kept in the query string.

#### Scenario: Shareable filter
- **WHEN** a user opens `/initiatives?status=at-risk&owner=tim`
- **THEN** only Tim's at-risk initiatives are listed, and the filter controls reflect those values

#### Scenario: Empty result
- **WHEN** no initiatives match the filters
- **THEN** an empty state explains that nothing matches and offers to clear the filters

### Requirement: People Index and Person Page
The system SHALL provide `/people`, which lists every person with their role, initiative count, and status breakdown. Each person page SHALL list that person's initiatives sorted by attention: off track, then at risk, then stale, then the rest. Stale initiatives SHALL be flagged.

#### Scenario: Stale flag
- **WHEN** one of Mario's initiatives was last updated 15 days ago
- **THEN** his person page shows that row with an amber "15 days since update" flag

#### Scenario: Singular day count
- **WHEN** an initiative was last updated 1 day ago
- **THEN** the row reads "1 day since update"
