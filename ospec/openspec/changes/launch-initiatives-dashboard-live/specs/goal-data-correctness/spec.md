# Spec Delta

## Purpose

Defines the correctness of the goal data the service displays: that the five goals match canonical Strategy 2035 in both number and wording, that a goal's number is treated as its identity, and that a goal's number and canonical text can never disagree.

## ADDED Requirements

### Requirement: The goal set matches canonical Strategy 2035
The service SHALL display exactly five goals, numbered 1 to 5, whose canonical wording matches the Strategy 2035 source. No goal SHALL carry a number other than the one that source assigns it, and no goal's canonical text SHALL be a paraphrase, truncation or rewrite.

#### Scenario: Numbers and wording agree with the source
- **WHEN** the goals are read from the running service
- **THEN** each number carries the canonical wording the source assigns to that number
- **AND** no two goals are transposed

#### Scenario: A paraphrased goal is not accepted
- **WHEN** a goal's stored title differs from the canonical wording
- **THEN** the difference is treated as a defect, not as an alias
- **AND** it is corrected from the source rather than edited in place

#### Scenario: A goal with no canonical text is not silently blank
- **WHEN** a goal has no title
- **THEN** this is reported rather than rendered as an empty heading
- **AND** it is distinguishable from a goal whose title is legitimately short

### Requirement: A goal's number is its identity
Every goal-scoped reference SHALL resolve by goal number, and the number SHALL refer to the same goal everywhere: in links, in list membership, and in any external reference. Two surfaces SHALL NOT disagree about which goal a given number names.

#### Scenario: A goal-scoped URL names the right goal
- **WHEN** a goal is opened by number
- **THEN** the goal shown is the one the canonical source assigns that number

#### Scenario: Tagged initiatives follow the goal, not the number
- **WHEN** a goal's number is corrected
- **THEN** the initiatives tagged to that goal remain tagged to it
- **AND** they do not move to a different goal

#### Scenario: A bookmark keeps meaning
- **WHEN** a previously issued goal URL is followed after the correction
- **THEN** it resolves to a real goal
- **AND** it does not resolve to a goal whose meaning has changed

### Requirement: The five goals and the objectives beneath them are not conflated
The service SHALL treat the five goals as distinct from the objectives that sit beneath them. An objective's text SHALL NOT be presented as a goal, and no surface SHALL imply that an objective is one of the five goals.

#### Scenario: An objective headline is not shown as a goal
- **WHEN** a screen presents a goal
- **THEN** its text is the goal's canonical wording
- **AND** it is not an objective drawn from the material beneath that goal

#### Scenario: A goal count is not inflated by objectives
- **WHEN** the number of goals is reported anywhere
- **THEN** it counts goals
- **AND** it does not count the objectives beneath them
