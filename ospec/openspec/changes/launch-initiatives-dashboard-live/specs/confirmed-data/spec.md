# Spec Delta

## Purpose

Defines how the service distinguishes figures that a person has confirmed from figures it invented for demonstration, so that no reader has to guess which numbers are real and no redeploy can quietly lose the distinction.

## ADDED Requirements

### Requirement: Every displayed figure is confirmed or marked
Every figure the service displays — a status, a percent, a milestone, an owner — SHALL be either confirmed by the person accountable for it or visibly marked as illustrative. The service SHALL NOT display an invented figure as though it were settled.

#### Scenario: Unconfirmed figures are marked
- **WHEN** a figure has not been confirmed by anyone accountable for it
- **THEN** the surface displaying it says so
- **AND** a reader encountering only that surface can tell

#### Scenario: An unconfirmed figure is not shown as zero
- **WHEN** a figure is unknown because nobody has reported it
- **THEN** it is shown as unknown
- **AND** it is not shown as zero or as an empty bar that reads as zero

#### Scenario: A confirmed figure is not marked as illustrative
- **WHEN** a figure has been confirmed by the person accountable for it
- **THEN** it is not marked illustrative
- **AND** the marking distinguishes it from one that has not

### Requirement: The distinction is derived, not remembered
The service SHALL determine whether it is serving confirmed data from the data itself, and SHALL NOT rely on a value someone sets by hand. A redeploy, a restore, or a data swap SHALL NOT be able to leave the marking wrong.

#### Scenario: A redeploy preserves the correct marking
- **WHEN** the service is redeployed with the same data
- **THEN** the marking is unchanged
- **AND** no manual step is required to keep it correct

#### Scenario: Swapping in confirmed data clears the marking
- **WHEN** confirmed data replaces illustrative data
- **THEN** the service stops marking it illustrative on its own
- **AND** this does not require a second manual change

#### Scenario: A partial swap is visible
- **WHEN** some figures are confirmed and others are not
- **THEN** the service shows which is which
- **AND** it does not mark the whole dataset one way

### Requirement: An owner is a person, a placeholder, or the absence is stated
Where a surface attributes work to an owner, it SHALL show a named person, an
explicitly-marked placeholder standing in for a person, or state that no owner is
named. It SHALL NOT present a team, a role, or an unmarked string as though it
were the accountable person.

*Amended 2026-10-07.* Real people's names are withheld from this service until the
data-policy question is answered, so the owner position carries a **placeholder**
rather than a name. The placeholder must be distinguishable from a real name — a
reader must never mistake one for the other.

#### Scenario: An unnamed owner is not a placeholder person
- **WHEN** no owner is named for an item
- **THEN** the surface says so
- **AND** it does not show a role or a team in the owner position as if it were a person

#### Scenario: A withheld name is a marked placeholder, not a name
- **WHEN** an owner exists but their name is withheld pending the data-policy decision
- **THEN** the surface shows a placeholder that reads as one
- **AND** the placeholder is distinguishable at a glance from a real person's name

#### Scenario: A placeholder is never mistaken for a confirmation
- **WHEN** an owner position holds a placeholder
- **THEN** the item is not treated as having a confirmed owner
- **AND** the service does not report its owner as settled

#### Scenario: A named owner is attributable
- **WHEN** a real owner is shown
- **THEN** it is a person who can be identified
- **AND** the same person appears wherever that item's owner is shown
