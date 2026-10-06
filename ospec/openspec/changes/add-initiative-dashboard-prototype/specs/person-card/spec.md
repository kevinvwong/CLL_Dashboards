# Spec Delta

## Purpose
Let the Dean see everything one leader owns and how each item is progressing, for use during one-on-ones and the leadership meeting.

## ADDED Requirements

### Requirement: Person card contents
The person card SHALL show the person's name, title, and who they report to, then each active initiative they own with level, progress bar, status, and last-updated date.

#### Scenario: Leader with initiatives
- **WHEN** a user opens Elizabeth's person card
- **THEN** each of her active initiatives is listed with its latest progress

### Requirement: Stale update flag
The person card SHALL flag any initiative whose latest update is older than 14 days or missing.

*Amended 2026-10-06.* This requirement said 14 days while its own scenario below gave 20 days as the example, and the code followed the scenario. 14 is the threshold: it satisfies the requirement, and it also satisfies the scenario, because an update 20 days old is still older than 14. The two readings are not in conflict once the requirement is treated as the rule and the scenario as one example of it. `queries.py` previously carried a comment claiming "the spec says 20 days", which was true of the scenario and false of the requirement.

#### Scenario: Stale initiative
- **WHEN** an initiative's latest update is 20 days old
- **THEN** its row shows a "Needs update" flag

#### Scenario: Initiative just inside the window is not flagged
- **WHEN** an initiative's latest update is 13 days old
- **THEN** its row carries no "Needs update" flag

#### Scenario: Initiative with no update is flagged
- **WHEN** an initiative has never had an update
- **THEN** its row shows a "Needs update" flag
