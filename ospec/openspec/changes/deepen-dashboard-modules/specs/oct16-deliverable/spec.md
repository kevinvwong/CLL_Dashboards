# Spec Delta

## Purpose

Define what the October 16 page shows and where every shown value comes from, so the page reads as confirmed or illustrative by its own data and never states a figure the page itself invents.

## ADDED Requirements

### Requirement: The page shows the Dean's outcomes by milestones

The system SHALL present the six Blueprint outcomes, each showing milestones reached of milestones planned, and SHALL NOT show any composite or rolled-up score.

#### Scenario: Each outcome shows its milestone count
- **WHEN** the October 16 page is shown
- **THEN** each of the six outcomes displays how many of its milestones are reached and how many are planned

#### Scenario: No aggregate score is shown
- **WHEN** the page renders progress for any outcome
- **THEN** no invented composite figure appears anywhere on the page

### Requirement: Every shown value comes from the content module

The system SHALL render each value the page displays from the content module that owns it, and SHALL NOT compute a shown value inside the page template.

#### Scenario: The progress bar width is stated, not computed in the page
- **WHEN** the page renders an outcome's progress bar
- **THEN** the width comes from a value the module provides, not from a formula written in the template

#### Scenario: The owner label is stated, not re-spelled in the page
- **WHEN** an outcome has no confirmed owner
- **THEN** the page shows the exact placeholder label the module defines, rather than a second spelling of it

### Requirement: The confirmed marker is derived from the data

The system SHALL state at the top of the page whether the figures are illustrative or confirmed, and SHALL derive that statement from how the content was built, never from a setting that could disagree with the figures.

#### Scenario: Illustrative figures are labelled illustrative
- **WHEN** the content was built without confirmed owners
- **THEN** the page states the figures are illustrative and no owner is named

#### Scenario: Confirmed figures clear the marker by themselves
- **WHEN** the content is rebuilt with confirmed owners
- **THEN** the page no longer states the figures are illustrative, with no separate setting changed

#### Scenario: A partly confirmed dataset is not rounded to confirmed
- **WHEN** some owners are confirmed and others are not
- **THEN** the page states the partial position rather than claiming the whole is confirmed

### Requirement: An owner has one of three states

The system SHALL distinguish a named owner, a withheld owner whose name is not placed on the service, and an outcome with no owner named, and SHALL NOT treat a withheld name as a confirmed owner.

#### Scenario: A withheld name is marked as a placeholder
- **WHEN** an outcome's owner is withheld
- **THEN** the page shows it as a marked placeholder and it does not count toward confirmed owners

#### Scenario: A missing owner is stated as missing
- **WHEN** an outcome has no owner
- **THEN** the page states that no owner is named rather than leaving the row blank
