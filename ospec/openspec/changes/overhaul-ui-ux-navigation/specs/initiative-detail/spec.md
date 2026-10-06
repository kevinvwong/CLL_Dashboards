# Spec Delta

## Purpose

Define the initiative detail view, its partial-response contract, the update form, and the scope of Edit details, so opening and updating an initiative keeps the list context and never reloads the page.

## ADDED Requirements

### Requirement: Detail Drawer
When the user opens an initiative from a list, the system SHALL show its detail in a right-side drawer over that list and SHALL update the URL to `/initiatives/{id}`. Closing the drawer SHALL restore the list URL and the scroll position.

#### Scenario: Open from list
- **WHEN** the user clicks D-B on the Academic goal page
- **THEN** a drawer opens with D-B's detail, the URL becomes `/initiatives/D-B`, and the list stays visible behind the drawer

#### Scenario: Close drawer
- **WHEN** the user presses Esc or clicks the drawer's close control
- **THEN** the drawer closes, the URL returns to `/goals/1`, and the scroll position is unchanged

### Requirement: Full-Page Detail
When `/initiatives/{id}` is loaded directly, the system SHALL render it as a full page with breadcrumbs. The page SHALL NOT show a drawer or modal close control.

#### Scenario: Direct load
- **WHEN** a user opens `/initiatives/MAR-1` from a bookmark
- **THEN** the page shows breadcrumbs and the initiative detail, with no "×" control

### Requirement: Partial Responses
Endpoints that serve both a drawer or modal and a full page SHALL return only the content fragment for partial requests and the full layout for direct requests.

#### Scenario: Edit details in drawer
- **WHEN** the user clicks Edit details inside the drawer
- **THEN** only the edit form appears in the drawer, with no site banner or navigation inside it

### Requirement: Detail Layout
The initiative detail SHALL show:

- **Header:** ID, name, status pill, progress bar, and owner
- **Actions:** Update, and Edit details where the user is permitted
- **Facts:** goals and priorities as chips with the primary flag, and the tier
- A "Latest update" callout
- Linked initiatives (Feeds or Fed by), each with its status and progress
- A diary timeline, newest first, that marks status changes

#### Scenario: Fed-by list shows health
- **WHEN** D-B is fed by TIM-4, which is off track at 15%
- **THEN** the Fed by list shows TIM-4 with a red "Off track" pill and 15%

### Requirement: Update Form
The Update form SHALL provide:

- labels above fields
- status as a segmented control with one colored option per status
- progress as a slider paired with a number input (0–100)
- the previous progress and status values
- a note field in the body font, with a live character counter (max 500)
- a primary Save button and a secondary Cancel button

#### Scenario: Previous value shown
- **WHEN** the user opens Update on D-B, whose last update was 45% On track
- **THEN** the form shows "Previous: 45% · On track", with the controls set to those values

#### Scenario: Character limit
- **WHEN** the note reaches 500 characters
- **THEN** the counter reads "500/500" and no more input is accepted

### Requirement: Inline Save
Saving an update SHALL persist it, update the affected row and the detail view in place, and show a confirmation toast. It SHALL NOT reload the full page.

#### Scenario: Successful save
- **WHEN** the user saves an update of 50% On track
- **THEN** the toast reads "Update saved", the list row shows 50% On track, and the diary gains a new entry at the top

#### Scenario: Save failure
- **WHEN** the server rejects the update
- **THEN** the form stays open with the entered values kept, and an inline error explains the problem

### Requirement: Edit Details Scope
Edit details SHALL allow editing:

- name
- description
- owner
- goals and priorities (each with a primary flag)
- tier
- parent D-1 link

Fields the current user may not edit SHALL be disabled, with an explanation.

#### Scenario: Restricted field
- **WHEN** a user who is not permitted to change ownership opens Edit details
- **THEN** the owner field is disabled and shows "Only the Dean or an admin can change the owner"
