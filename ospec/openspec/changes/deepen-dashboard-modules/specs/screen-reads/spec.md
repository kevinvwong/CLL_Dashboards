# Spec Delta

## Purpose

Define the read interface each screen uses to obtain its data, so a screen names the one read that serves it and the rules for what a screen shows are stated once rather than re-derived at each call site.

## ADDED Requirements

### Requirement: A screen reads through a read shaped to it

The system SHALL provide each screen one named read that returns everything that screen renders, rather than a set of single-table readers the screen must combine.

#### Scenario: The card reads in one call
- **WHEN** a screen needs an initiative's details, tags, connections, latest progress, and diary
- **THEN** it obtains them from one named read rather than several separate table reads

#### Scenario: An edit screen reads its options in one call
- **WHEN** an edit screen needs the options a caller may choose from and the values currently chosen
- **THEN** it obtains them from one named read shaped to that screen

### Requirement: The same data is not read two ways

The system SHALL NOT return the same stored data through both a screen-shaped read and a separate single-table reader, so there is one place to change how that data is read.

#### Scenario: Tag reads are not duplicated
- **WHEN** an initiative's tags are needed
- **THEN** they come from the same read used by the card, not from a second reader over the same tables

#### Scenario: A pass-through reader is removed, not left beside its replacement
- **WHEN** a single-table reader's only callers move behind a screen-shaped read
- **THEN** the pass-through reader is deleted, so no two paths read the same data

### Requirement: "No update" is distinguished from a zero value

The system SHALL report, for each initiative it returns, whether a progress update exists at all, distinct from what that update says, so a screen does not render an absent update as zero percent complete.

#### Scenario: An initiative with no update is marked as such
- **WHEN** an initiative has no progress update
- **THEN** the read reports that no update exists, and the screen shows "no update" rather than "0%"

#### Scenario: An initiative at zero percent with an update is not marked as missing
- **WHEN** an initiative has an update whose percent is zero
- **THEN** the read reports that an update exists, and the screen shows the recorded percent
