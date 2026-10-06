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

#### Scenario: Stale initiative
- **WHEN** an initiative's latest update is 20 days old
- **THEN** its row shows a "Needs update" flag
