# Spec Delta

## Purpose

Define how the application obtains its database connection and which database it names, so there is a single configured source of truth for "where the data lives" and never a second, accidental default.

## ADDED Requirements

### Requirement: One configured database path

The system SHALL resolve the database file from a single configured location, and SHALL use that one path for every read and every write.

#### Scenario: Reads and writes agree on the file
- **WHEN** any part of the application opens the database
- **THEN** it opens the file named by the one configured path, so a read and a write in the same request see the same data

#### Scenario: No second default path exists
- **WHEN** the configured path is set in the environment
- **THEN** no other default path in the code can be used instead, so an empty or stray database cannot be opened by accident

### Requirement: One interface for obtaining a connection

The system SHALL obtain every connection through one named interface, and SHALL apply the connection's required pragmas (foreign keys, write-ahead logging, busy timeout, dict-like rows) inside that interface.

#### Scenario: A caller cannot forget the pragmas
- **WHEN** any part of the application needs a connection
- **THEN** foreign-key enforcement, write-ahead logging, the busy timeout, and dict-like row access are already set, without the caller repeating them

#### Scenario: Writes take the write lock explicitly
- **WHEN** the application begins a write
- **THEN** the connection used for writing takes the write lock before the first statement, through the same interface, not through a second helper

### Requirement: Unused connection surface is removed

The system SHALL NOT expose connection helpers that no caller uses, so "how to get a connection" has exactly one answer.

#### Scenario: A dead helper is gone
- **WHEN** a connection helper has no caller
- **THEN** it is removed rather than left as a second, misleading way to reach the database
