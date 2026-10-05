# Spec Delta

## Purpose
Let initiative owners record self-reported progress as a running diary, so the Dean reports numbers that owners supplied.

## ADDED Requirements

### Requirement: Add a progress update
An owner SHALL be able to add an update with a percent from 0 to 100 (slider), a status from the fixed list, and a note of up to 500 characters. The update SHALL be appended, never overwrite earlier entries.

#### Scenario: Owner adds an update
- **WHEN** the signed-in person owns the initiative and submits 40%, "On track", and a note
- **THEN** a new diary entry is saved with today's date and the card shows 40% as latest

#### Scenario: Invalid percent
- **WHEN** a percent above 100 is submitted
- **THEN** the update is rejected and the form shows an error

### Requirement: Update button visibility
The card SHALL show the Update button only when the signed-in person owns the initiative, is the Dean, or is an admin, and the server SHALL reject update posts from anyone else.

#### Scenario: Non-owner viewing
- **WHEN** Tim views Elizabeth's initiative
- **THEN** no Update button is shown

#### Scenario: Non-owner post rejected
- **WHEN** Tim posts an update to Elizabeth's initiative directly
- **THEN** the server responds 403 and no update is saved

### Requirement: Independent Dean progress
Dean initiative progress SHALL be entered directly and SHALL NOT be calculated from linked D-1 progress.

#### Scenario: D-1 update does not change Dean percent
- **WHEN** a D-1 initiative linked to Dean initiative D-A is updated to 80%
- **THEN** D-A's latest percent is unchanged
