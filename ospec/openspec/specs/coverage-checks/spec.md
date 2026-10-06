# coverage-checks Specification

## Purpose
Define the admin page that combines data-quality checks with the prototype's coverage idea, so an administrator sees both what is broken and how complete the strategy's targets are, and can act on each.

## Requirements

### Requirement: Two sections on one admin page

The admin page SHALL present data-quality checks and target coverage as two distinct sections, so "is the data valid" and "is the target agreed" are not conflated.

#### Scenario: Both sections render
- **WHEN** an administrator opens the page
- **THEN** a checks section and a coverage section both render, each with its own heading and note

#### Scenario: The two questions stay distinct
- **WHEN** the coverage section reports an agreed target
- **THEN** it does not report on whether any performance is being met, and the checks section does not report target completeness

### Requirement: Checks list every rule with pass or fail

The checks section SHALL list every rule with its name, a one-line description, and a pass or fail marker, and SHALL NOT collapse the result into a single summary sentence.

#### Scenario: All passing
- **WHEN** every rule passes
- **THEN** each rule is listed with a pass marker

#### Scenario: A failing rule lists its records
- **WHEN** a rule fails
- **THEN** the rule shows how many records fail it and lists them, each linking to the place that resolves the failure

### Requirement: Coverage shows target completeness by group

The coverage section SHALL show how many targets are agreed per group, as a count and a proportion, so an administrator can see where decisions are still needed.

#### Scenario: Coverage shows a proportion
- **WHEN** a group has some agreed targets and some needing review
- **THEN** the section shows both counts and their proportion for that group

#### Scenario: Nothing is averaged into a performance figure
- **WHEN** the coverage section renders
- **THEN** it presents counts and completeness only, and no combined or averaged performance score

### Requirement: The entry is admin-only, the page is not

The entry to this page SHALL appear in the primary navigation only for an administrator. The page itself SHALL remain reachable by any signed-in person, because the existing `data-intake` requirement says the checks page SHALL show every failing row with no role restriction and the weekly meeting links to it.

#### Scenario: Non-administrator sees no entry
- **WHEN** a user without admin access is active
- **THEN** the entry to the page is not shown in the navigation

#### Scenario: The page still opens for a signed-in person
- **WHEN** a signed-in person who is not an administrator opens the page directly
- **THEN** the page renders, because the checks requirement places no role restriction on it
