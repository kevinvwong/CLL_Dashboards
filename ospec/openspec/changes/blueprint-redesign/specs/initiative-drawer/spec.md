# Spec Delta

## Purpose

Define initiative detail as a drawer over the list and a full page on direct load, with the partial-response rule and the in-drawer update and edit forms, so opening an initiative never loses the reader's place.

## ADDED Requirements

### Requirement: Detail opens as a drawer over the list

When an initiative is opened from a list, the system SHALL show its detail in a right-side drawer over that list and SHALL update the URL, so the list context is kept and the view can still be shared.

#### Scenario: Opening from a list
- **WHEN** the user opens an initiative from a list
- **THEN** a drawer opens over the list with the initiative's detail and the URL becomes its detail URL

#### Scenario: Closing returns to the list
- **WHEN** the user closes the drawer
- **THEN** the URL returns to the list and the scroll position is unchanged

### Requirement: Direct load renders a full page

When the detail URL is loaded directly, the system SHALL render it as a full page and SHALL NOT show a drawer or modal close control.

#### Scenario: Bookmark
- **WHEN** a user opens an initiative detail URL directly
- **THEN** the page renders with the site chrome and no close control

### Requirement: Partial responses

Every endpoint that serves both a drawer and a full page SHALL return only the content fragment for a partial request and the full layout for a direct request.

#### Scenario: Fragment carries no chrome
- **WHEN** a partial request reaches a detail or edit endpoint
- **THEN** the response contains no document element and no site navigation

#### Scenario: Direct request carries the chrome
- **WHEN** the same endpoint is requested directly
- **THEN** the response is a full page with navigation

### Requirement: The drawer traps and restores focus

The drawer SHALL move focus into itself when it opens, keep Tab within it, and return focus to the element that opened it when it closes.

#### Scenario: Focus moves in and comes back
- **WHEN** a drawer opens and then closes
- **THEN** focus moves into the drawer on open and returns to the opening element on close

#### Scenario: Escape closes
- **WHEN** the drawer is open and the user presses Escape
- **THEN** the drawer closes and focus returns to the opening element

### Requirement: The update form is in the drawer

The update form SHALL provide a progress control with a numeric input, a status control limited to the schema's values, the previous value shown, and a note with a character count.

#### Scenario: Previous value shown
- **WHEN** the update form opens for an initiative with a previous update
- **THEN** the previous progress and status are shown and the controls are set to them

#### Scenario: Status is limited to stored values
- **WHEN** the status control is rendered
- **THEN** its options are exactly the values the database can store

### Requirement: Saving is inline

Saving an update SHALL persist it, update the detail and the affected row, and confirm with a toast, without reloading the page.

#### Scenario: Successful save
- **WHEN** the user saves an update
- **THEN** the diary gains the new entry, the row reflects the new value, and a toast confirms

#### Scenario: Refused save keeps the input
- **WHEN** the server refuses an update
- **THEN** the form stays open with the entered values and an inline message explains why
