# Spec Delta

## Purpose

Define how every change to initiative data is applied: atomically, with a single mapping from a refused write to a message a person can act on, and with progress kept append-only so no update ever rewrites another.

## ADDED Requirements

### Requirement: Every write is atomic

The system SHALL apply each write to initiative data as a single all-or-nothing change, so a failure part-way leaves no partial record behind.

#### Scenario: A refused write leaves nothing behind
- **WHEN** a write fails a rule after it has begun
- **THEN** no row it would have written is present afterwards and the stored data is exactly as it was before the attempt

#### Scenario: A successful write is complete
- **WHEN** a write passes every rule
- **THEN** all of its rows are present together, or none of them are

### Requirement: Refused writes carry an actionable message

The system SHALL refuse a write that breaks a rule with a message naming what to change, and SHALL NOT surface a database driver error to the caller for any rule the system already knows.

#### Scenario: Percent out of range
- **WHEN** a progress update carries a percent outside 0 to 100
- **THEN** the write is refused with a message naming the percent range, not a driver error

#### Scenario: Unknown status
- **WHEN** a progress update carries a status outside the allowed set
- **THEN** the write is refused with a message listing the allowed statuses, not a driver error

#### Scenario: Duplicate initiative code
- **WHEN** an initiative is created with a code that already exists
- **THEN** the write is refused with a message naming the code that already exists

### Requirement: Progress is append-only

The system SHALL append every progress update as a new record and SHALL NOT modify any earlier update or any initiative's stored progress when an update is added.

#### Scenario: An update never rewrites history
- **WHEN** an owner adds a progress update
- **THEN** the earlier updates remain unchanged and the new update is added alongside them

#### Scenario: A D-1 update leaves the Dean initiative untouched
- **WHEN** a D-1 owner records an update on a D-1 initiative
- **THEN** the Dean initiative it feeds keeps its own latest percent and status unchanged

### Requirement: The write path is one interface

The system SHALL expose writing through a single named entry point so that the atomicity, refusal-message, and append-only rules above are stated once rather than restated by every kind of write.

#### Scenario: A new kind of write inherits the rules
- **WHEN** a new kind of write is added
- **THEN** it obtains atomicity, refusal-message mapping, and connection handling from the shared entry point without restating them
