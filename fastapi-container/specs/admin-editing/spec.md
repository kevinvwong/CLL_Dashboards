# Spec Delta

## Purpose
Let the dashboard team fix descriptions, tags, and links directly in the app, and let owners maintain their own initiative descriptions, so errors no longer wait for a full re-import.

## ADDED Requirements

### Requirement: Admin role
People marked as admin SHALL be able to create, edit, and retire any initiative and edit goal and priority descriptions. Non-admins SHALL NOT see admin controls.

#### Scenario: Admin sees edit controls
- **WHEN** the signed-in person is an admin and opens an initiative card
- **THEN** Edit details, Edit tags, Edit links, and Retire controls are shown

#### Scenario: Non-admin blocked
- **WHEN** a non-admin sends a POST to an admin edit route
- **THEN** the server responds 403 and nothing changes

### Requirement: Owner edits own description
An initiative owner SHALL be able to edit the name and description of initiatives they own.

#### Scenario: Owner edits description
- **WHEN** Elizabeth edits the description of ELIZ-1
- **THEN** the new description is saved and shown on the card

### Requirement: Edit tags and links in place
Admins SHALL be able to add or remove goal tags, priority tags, primary flags, and D-1 to Dean links from the initiative card, with the same rules enforced as on import.

#### Scenario: Fix a wrong priority tag
- **WHEN** an admin removes the "Culture" tag and adds "Identity" as primary on an initiative
- **THEN** the card and both priority list screens reflect the change immediately

#### Scenario: Rule violation shown inline
- **WHEN** an admin tries to mark a second primary goal
- **THEN** the change is rejected and the form shows "Only one primary goal is allowed"

### Requirement: Create and retire initiatives
Admins SHALL be able to create a new initiative with code, name, level, and owner, and retire an initiative without deleting its history.

#### Scenario: New initiative appears in checks
- **WHEN** an admin creates a D-1 initiative with no tags or links
- **THEN** it appears on `/checks` with its missing tags and missing Dean link listed

### Requirement: Audit trail
Every admin or owner edit SHALL write an AuditLog row with who, when, action, entity, and before and after values.

#### Scenario: Edit recorded
- **WHEN** an admin changes an initiative's owner
- **THEN** an AuditLog row records the old and new owner and the admin's name
