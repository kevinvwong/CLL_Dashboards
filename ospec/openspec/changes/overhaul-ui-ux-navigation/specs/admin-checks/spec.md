# Spec Delta

## Purpose

Define the data checks page: every rule listed with a pass or fail and each failure linked to the fix, so a data problem is actionable rather than summarised.

## ADDED Requirements

### Requirement: Data Check Rule List
The Data checks page SHALL list every check rule with its name, a one-line description, and a pass/fail status. It SHALL NOT collapse the results into a single summary sentence.

#### Scenario: All passing
- **WHEN** every rule passes
- **THEN** each rule is listed with a green "Pass" marker, including "Every active D-1 initiative has a Dean link" and "Every initiative is tagged"

### Requirement: Actionable Failures
Each failing rule SHALL list the records that fail it. Each record SHALL link to the initiative or to the edit form that resolves the failure.

#### Scenario: Untagged initiative
- **WHEN** MAR-4 has no priority tag
- **THEN** the "Every initiative is tagged" rule shows "Fail · 1", and lists MAR-4 with a link that opens its Edit details

### Requirement: Admin-Only Access
The Data checks page SHALL be reachable from the admin entry and SHALL NOT appear in the primary navigation.

#### Scenario: Non-admin user
- **WHEN** a user without admin access is active
- **THEN** the admin entry is not shown
