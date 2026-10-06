# Spec Delta

## Purpose

Define how an initiative's status is presented, so a status reads the same and carries its meaning visually wherever it appears, from one vocabulary rather than six templates each transforming it.

## ADDED Requirements

### Requirement: One status vocabulary

The system SHALL use the single set of status values the schema allows, and SHALL NOT introduce a second set of status values for any screen.

#### Scenario: A status shown anywhere is an allowed status
- **WHEN** any screen shows an initiative's status
- **THEN** it is one of the values the schema's own constraint allows

#### Scenario: A new screen reuses the vocabulary
- **WHEN** a new screen shows a status
- **THEN** it draws the value from the same source, not from a list written into the screen

### Requirement: The status presentation is derived from one source

The system SHALL derive how a status is rendered — the class name and its colour — from one source, so two screens cannot render the same status differently.

#### Scenario: The same status looks the same everywhere
- **WHEN** the same status appears on two different screens
- **THEN** both render it with the same class and the same colour

#### Scenario: A status with a space is handled the same way
- **WHEN** a status contains a space, such as "At risk"
- **THEN** the same transformation produces its class name on every screen, not a per-screen re-implementation

### Requirement: A status carries its meaning visually where it appears

The system SHALL render an initiative's status with a visual marker of its meaning (its colour) wherever the status is displayed, including outside a progress bar.

#### Scenario: A status badge is coloured
- **WHEN** a status is shown as a badge or label rather than inside a progress bar
- **THEN** it carries its status colour, not the default appearance

#### Scenario: Every status shown has a defined appearance
- **WHEN** a screen emits a status (or milestone status) class
- **THEN** that class has a defined appearance, so no class is emitted with no styling
