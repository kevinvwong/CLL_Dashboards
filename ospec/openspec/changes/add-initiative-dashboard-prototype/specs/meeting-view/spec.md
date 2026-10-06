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
The meeting page SHALL show, above the change list, every active initiative that is Off track or At risk, or whose latest update is older than 14 days or missing. Entries SHALL be ordered by severity - Off track first, then At risk, then stale - and within one severity by the oldest update first, so the most stalled item is at the top. Each entry SHALL state the reason it is listed, in words, so the Dean does not have to open the card to find out why it is on the agenda. An initiative matching more than one reason SHALL appear once, showing the most severe.

*Amended 2026-10-06.* This requirement previously read "initiatives whose latest status is At risk or Off track, and initiatives with no update in 14 days" - it named Off track and the staleness window, and the implementation delivered neither. `test_off_track_is_not_in_the_attention_list` pinned the wrong behaviour and the code's own docstring asserted the spec "names At risk and only At risk", which the requirement text does not say. Corrected here, and the ordering and reason clauses are added because a bare list of codes is not an agenda.

#### Scenario: Off-track item leads the list
- **WHEN** an initiative's latest status is Off track
- **THEN** it appears in the attention list above every At risk and stale entry
- **AND** its reason reads "Off track"

#### Scenario: At-risk item surfaces
- **WHEN** an initiative's latest status is At risk
- **THEN** it appears in the attention list with a link to its card
- **AND** it sits below any Off track entry

#### Scenario: Stale initiative is listed with its age
- **WHEN** an initiative's latest update is more than 14 days old
- **THEN** it appears in the attention list below the status entries
- **AND** its reason states how many days old the update is

#### Scenario: Initiative with no update at all is listed
- **WHEN** an initiative has never had a progress update
- **THEN** it appears in the attention list
- **AND** its reason says there is no update yet, rather than reporting a number of days

#### Scenario: One initiative with two reasons appears once
- **WHEN** an initiative is both At risk and more than 14 days stale
- **THEN** it appears exactly once
- **AND** the reason shown is the more severe one

#### Scenario: Ordering is stable within a severity
- **WHEN** two initiatives share a severity
- **THEN** the one whose update is oldest is listed first
- **AND** a tie on age falls back to initiative code, so the order does not vary between renders

#### Scenario: Nothing to show
- **WHEN** no active initiative is Off track, At risk, or stale
- **THEN** the section says so in words rather than rendering an empty list

### Requirement: Print-friendly
The meeting page SHALL print cleanly on letter paper with navigation hidden.

#### Scenario: Print
- **WHEN** the Dean prints `/meeting` from the browser
- **THEN** the output shows only the attention list and change list
