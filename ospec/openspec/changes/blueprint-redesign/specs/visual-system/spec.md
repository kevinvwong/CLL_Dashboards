# Spec Delta

## Purpose

Define the single visual language the whole app is built from: a dark Georgia Tech chrome over light readable content, a serif/sans type split, a token set no page may bypass, and the status and priority colour scales.

## ADDED Requirements

### Requirement: Dark chrome over light content

The system SHALL render its header, navigation, and footer as dark GT-navy chrome, and every content surface as light, so identity sits where the app is seen and readability where it is read, projected, and printed.

#### Scenario: Chrome and content are distinct
- **WHEN** any page renders
- **THEN** the header, navigation, and footer use the navy chrome tokens and the content area uses the light surface tokens

#### Scenario: Content stays readable when printed
- **WHEN** a page is printed
- **THEN** the dark chrome is not printed and the content renders on a light background

### Requirement: Every visual value is a token

The system SHALL express every colour, spacing, radius, shadow, and type value as a CSS custom property, and SHALL NOT use a literal colour outside a token block.

#### Scenario: No literal colour outside a token block
- **WHEN** the stylesheet is scanned
- **THEN** no hex or functional colour literal appears outside the token declarations

#### Scenario: Dark content mode is complete
- **WHEN** the operating system prefers a dark colour scheme
- **THEN** every colour token has an override, so no surface is left light by omission

### Requirement: A serif heading and sans body split

The system SHALL render headings in a serif face and body text in a sans face, so sections carry visual weight without a heavier weight everywhere.

#### Scenario: Headings and body differ in face
- **WHEN** a section heading and its body text render
- **THEN** the heading uses the serif token family and the body the sans family

### Requirement: The status scale is the schema's

The system SHALL render initiative status using the vocabulary the database's own constraint defines, and SHALL NOT introduce a status value the database cannot store.

#### Scenario: Status vocabulary matches the schema
- **WHEN** the status module's vocabulary is compared with the schema's Status constraint
- **THEN** they are identical

#### Scenario: Every status has an appearance
- **WHEN** a status is displayed
- **THEN** it carries its colour and its text label together, never colour alone

### Requirement: A per-priority colour scale

The system SHALL give each annual priority a distinct key colour from a fixed six-value scale, drawn from the Dean's prototype, and SHALL use those colours only to key priorities, never as a status colour.

#### Scenario: Each priority has its own colour
- **WHEN** the six priorities render together
- **THEN** each carries a different key colour from the scale

#### Scenario: Priority colour is not status colour
- **WHEN** a priority colour and a status colour appear on the same card
- **THEN** the two scales are visually distinct and the status keeps its own colour
