# Spec Delta

## Purpose
Give the Dean two ways into the same initiatives, by Strategy 2035 goal or by annual priority, each leading to a list of tagged initiatives with progress.

## ADDED Requirements

### Requirement: Home screen with two entry points
The home screen SHALL show one tile per goal (number, short name) and one tile per current-year priority, each tile showing the count of active initiatives tagged to it.

#### Scenario: Home loads
- **WHEN** a user opens `/`
- **THEN** 5 goal tiles and 6 priority tiles are shown, each with an initiative count

#### Scenario: Tile opens its list
- **WHEN** a user clicks the "Research" goal tile
- **THEN** the Research goal list screen opens

### Requirement: Goal and priority list screens
A list screen SHALL show the goal or priority name and description, then its tagged Dean initiatives, a divider, and its tagged D-1 initiatives grouped by owner. Each row SHALL show owner, initiative name, a progress bar, percent, and status.

#### Scenario: Dean initiatives above the divider
- **WHEN** a user opens a goal that has both Dean and D-1 initiatives
- **THEN** all Dean initiatives appear above the divider and D-1 initiatives appear below it, grouped by owner

#### Scenario: Primary tag shown
- **WHEN** an initiative's tag to this goal is primary
- **THEN** its row shows a "primary" badge

#### Scenario: Initiative without progress
- **WHEN** an initiative has no progress updates
- **THEN** its row shows an empty bar labeled "No update yet"

### Requirement: No computed rollup
List screens SHALL NOT display a computed percent for a goal or priority.

#### Scenario: Goal header
- **WHEN** a goal list screen renders
- **THEN** the header shows initiative counts by status and no aggregate percent

### Requirement: Navigation from rows
Clicking an initiative row SHALL open its initiative card, and clicking an owner name SHALL open that person's card.

#### Scenario: Open card from list
- **WHEN** a user clicks an initiative row on a list screen
- **THEN** the initiative card opens as a modal over the list, and closing it returns to the same list position
