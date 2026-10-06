# Spec Delta

## Purpose

Define the goal and priority drill-down screens as a cascade, so a reader can move from an outcome to the initiatives serving it, grouped and with their relationships shown.

## ADDED Requirements

### Requirement: A goal and priority drill-down

Selecting a goal or a priority SHALL open a detail view showing the initiatives tagged to it, so the cascade from outcome to work is one step.

#### Scenario: Outcome shows its initiatives
- **WHEN** the user opens a goal or priority
- **THEN** the view lists every active initiative tagged to it with its status and progress

#### Scenario: Both entry points agree
- **WHEN** the same initiative is reached through a goal and through a priority
- **THEN** it appears identical in both, field for field

### Requirement: Grouping with headers before groups

The drill-down SHALL let the user group initiatives, and every group header SHALL render before its group. No group label SHALL appear without rows under it.

#### Scenario: Group by owner
- **WHEN** the user groups by owner
- **THEN** each owner's name appears as a header directly above that owner's initiatives

#### Scenario: No orphan header
- **WHEN** a group has no initiatives
- **THEN** its header is not rendered

### Requirement: Relationships are visible

An initiative in the drill-down SHALL show what it feeds and what feeds it, so the Dean-to-D-1 relationship is visible from the cascade.

#### Scenario: Feeds and fed-by
- **WHEN** an initiative has relationships
- **THEN** the view shows both directions, each with the related initiative's code, name, status, and progress

### Requirement: A single-target row

Each initiative row SHALL be one clickable element that opens the initiative detail, carrying its code, name, owner, primary marker, progress, status, and last-update age.

#### Scenario: Clicking a row
- **WHEN** the user clicks anywhere on an initiative row
- **THEN** the initiative detail opens

#### Scenario: Progress is legible without colour
- **WHEN** a row renders its progress
- **THEN** the percentage appears as text beside the bar and the bar exposes its value to assistive technology

### Requirement: Rollup labels are a total plus a breakdown

The drill-down header SHALL label its rollup as a total count followed by a per-status breakdown, and SHALL NOT place a single status word next to the total.

#### Scenario: Header rollup
- **WHEN** a goal has ten initiatives, all on track
- **THEN** the header reads a total of ten followed by a breakdown of ten on track, not a status word before the number
