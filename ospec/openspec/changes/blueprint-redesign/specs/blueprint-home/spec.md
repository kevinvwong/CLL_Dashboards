# Spec Delta

## Purpose

Define the home screen as an executive blueprint: a hero stage that shows the Dean's outcomes as colour-keyed priority cards feeding down to initiative signals, so a reader sees the shape of the portfolio at a glance.

## ADDED Requirements

### Requirement: The home is a blueprint stage

The home screen SHALL present a hero stage: a Dean node on the left fanning into the six priority cards, so the relationship between the Dean's outcomes and the priorities is visible on first load.

#### Scenario: Stage renders the node and the priorities
- **WHEN** the home screen loads
- **THEN** it shows a Dean node and six priority cards, connected, with the node labelled as the Dean's outcomes

#### Scenario: The stage leads the page
- **WHEN** the home screen renders
- **THEN** the stage is the first and visually heaviest block, above any panel or list

### Requirement: Priority cards are colour-keyed and selectable

Each priority card SHALL carry its priority colour, its code, its name, and a count of its initiatives, and SHALL be selectable.

#### Scenario: Card contents
- **WHEN** a priority card renders
- **THEN** it shows the priority code, the priority name, the initiative count, and a marker in the priority's key colour

#### Scenario: Selecting a card
- **WHEN** the user selects a priority card
- **THEN** the selected-priority panel below the stage shows that priority's definition

### Requirement: A selected-priority panel

The stage SHALL be followed by a panel showing the selected priority's definition, its initiatives, and its relationships, so selecting a card reveals detail without leaving the page.

#### Scenario: Panel follows selection
- **WHEN** a priority is selected
- **THEN** the panel shows that priority's name, its description, and its linked initiatives

### Requirement: An initiative-signals strip

Below the panels the home SHALL show a strip of existing initiative signals with their progress, so the reader sees what work is already under way.

#### Scenario: Signals show progress
- **WHEN** the initiative-signals strip renders
- **THEN** each signal shows its name and its progress, and no aggregate or averaged figure is shown

### Requirement: The stage is honest about no-update state

An initiative with no update SHALL be marked as having no update, distinct from an initiative reported at zero.

#### Scenario: No update is distinct from zero
- **WHEN** an initiative has no progress update
- **THEN** it is shown as "no update yet" rather than as zero percent
