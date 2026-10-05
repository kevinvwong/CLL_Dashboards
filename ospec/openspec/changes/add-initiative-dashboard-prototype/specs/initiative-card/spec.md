# Spec Delta

## Purpose
Show everything about one initiative in a single card: what it is, who owns it, what it ties to above and below, and how it is progressing.

## ADDED Requirements

### Requirement: Card contents
The initiative card SHALL show code, name, level, owner, description, goal tags, priority tags (primary marked), latest percent and status with its date, and the running diary newest first.

#### Scenario: Card for a D-1 initiative
- **WHEN** a user opens a D-1 initiative card
- **THEN** all listed fields are shown and a "Feeds" section lists the Dean initiatives it links to

#### Scenario: Card for a Dean initiative
- **WHEN** a user opens a Dean initiative card
- **THEN** a "Fed by" section lists every linked D-1 initiative with owner and latest progress

### Requirement: Connected items are clickable
Every goal, priority, initiative, and person shown on a card SHALL link to its own screen or card.

#### Scenario: Follow a link upward
- **WHEN** a user clicks a Dean initiative in the "Feeds" section
- **THEN** that Dean initiative's card replaces the current card

### Requirement: Direct URL
Each initiative card SHALL be reachable at `/initiatives/{code}` as a full page.

#### Scenario: Shared link
- **WHEN** a user opens `/initiatives/ELIZ-1` in a new tab
- **THEN** the card renders as a full page with a link back to home
