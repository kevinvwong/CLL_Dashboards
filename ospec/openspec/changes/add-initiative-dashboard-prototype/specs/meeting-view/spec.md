# Spec Delta

## Purpose
Give the Dean a one-page agenda for the Wednesday leadership meeting showing what changed since the last meeting and what is at risk or stale.

## ADDED Requirements

### Requirement: Changes since a date
The meeting page SHALL list every progress update entered since a chosen date (default: 7 days ago), newest first, with initiative, owner, percent, status, and note.

#### Scenario: Default window
- **WHEN** the Dean opens `/meeting`
- **THEN** updates from the last 7 days are listed, grouped by owner

#### Scenario: Custom window
- **WHEN** the Dean sets the date to the previous meeting date
- **THEN** only updates entered on or after that date are listed

### Requirement: Attention list
The meeting page SHALL show initiatives whose latest status is At risk or Off track, and initiatives with no update in 14 days, above the change list.

#### Scenario: At-risk item surfaces
- **WHEN** an initiative's latest status is At risk
- **THEN** it appears in the attention list with a link to its card

### Requirement: Print-friendly
The meeting page SHALL print cleanly on letter paper with navigation hidden.

#### Scenario: Print
- **WHEN** the Dean prints `/meeting` from the browser
- **THEN** the output shows only the attention list and change list
