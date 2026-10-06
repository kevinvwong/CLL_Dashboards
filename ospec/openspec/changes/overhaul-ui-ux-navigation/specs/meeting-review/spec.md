# Spec Delta

## Purpose

Define the weekly meeting view: the three-part agenda, change deltas, date ranges, presenter mode, and print output, so the meeting can be run from the page.

## ADDED Requirements

### Requirement: Meeting Date Range
The Meeting page SHALL default its "since" date to the last meeting date. If no meeting date is recorded, it SHALL default to 7 days ago. The page SHALL offer quick ranges (Last meeting, 7 days, 14 days) as well as a custom date.

#### Scenario: Default range
- **WHEN** the last meeting was on 2026-09-29 and the user opens Meeting
- **THEN** the page shows changes since 2026-09-29, with "Last meeting" selected

### Requirement: Meeting Agenda Sections
The Meeting page SHALL present three sections, in this order:

1. **Needs attention:** initiatives that are off track or at risk, shown as cards with their latest note.
2. **Changes since:** updates grouped by owner, with each owner's group collapsible.
3. **No update since:** initiatives with no update in the selected range, grouped by owner.

#### Scenario: Missing updates surfaced
- **WHEN** TIM-2 has had no update since the selected date
- **THEN** TIM-2 appears under "No update since", in Tim's group

#### Scenario: Attention card shows note
- **WHEN** ELIZ-5 is at risk with the note "Scope depends on reorg."
- **THEN** its card in Needs attention shows that note without opening the detail

### Requirement: Change Deltas
Under Changes since, each update SHALL show the progress and status before and after the change.

#### Scenario: Progress and status delta
- **WHEN** D-A moved from 20% At risk to 30% On track in the range
- **THEN** its entry shows "20% → 30%" and "At risk → On track"

### Requirement: Presenter Mode
The Meeting page SHALL offer a presenter mode with large type that shows one owner group at a time. Arrow keys SHALL move between groups, and Esc SHALL exit.

#### Scenario: Navigate groups
- **WHEN** presenter mode is active and the user presses the right arrow key
- **THEN** the next owner's group is shown, and a position indicator updates (e.g. "2 of 5")

### Requirement: Print View
The Meeting page SHALL print cleanly, with no navigation or interactive controls, every section expanded, and the date range in the header.

#### Scenario: Print
- **WHEN** the user prints the Meeting page
- **THEN** the output contains the date range header and all three sections fully expanded, with no nav, buttons, or banner
