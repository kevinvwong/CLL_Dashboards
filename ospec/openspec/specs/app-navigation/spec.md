# app-navigation Specification

## Purpose
Define the app-wide navigation for the blueprint experience: a hybrid nav that keeps the meeting and outcomes first-class while making the blueprint the home, plus breadcrumbs, a user menu, search, and styled error pages.

## Requirements

### Requirement: The primary navigation

The system SHALL show a primary navigation whose destinations are the blueprint home, initiatives, people, meeting, and outcomes, and SHALL mark the item for the current section.

#### Scenario: Active destination
- **WHEN** the user is on any page under a section
- **THEN** that section's item is marked active and carries `aria-current="page"`

#### Scenario: Narrow viewport collapses the nav
- **WHEN** the viewport is narrow
- **THEN** the navigation collapses behind a control that reveals the full list

### Requirement: The meeting and outcomes stay first-class

The navigation SHALL include the meeting and the outcomes pages as primary destinations, so the weekly review and the Dean's outcomes are reachable in one step.

#### Scenario: Meeting is one step away
- **WHEN** any page renders
- **THEN** the meeting and the outcomes are both reachable from the primary navigation

### Requirement: A stable outcomes route

The system SHALL serve the Dean's outcomes at a route that is not tied to a date, and SHALL permanently redirect the old dated route to it.

#### Scenario: Legacy link
- **WHEN** a user requests the old outcomes route
- **THEN** the system permanently redirects to the stable route

### Requirement: Breadcrumbs below the top level

The system SHALL show breadcrumbs on every page below the top level, reflecting how the page is reached.

#### Scenario: Initiative detail
- **WHEN** the user views an initiative at its full-page URL
- **THEN** breadcrumbs show the path from the home to the initiative, each ancestor a link

### Requirement: A user menu

The system SHALL show the current user in a menu, and the menu SHALL hold the switch-user control rather than the primary navigation.

#### Scenario: Switching user
- **WHEN** the user opens the menu and chooses to switch user
- **THEN** the person picker shows every person and marks the current one

### Requirement: Styled error pages

The system SHALL render unknown routes and disallowed methods as a styled page that keeps the site chrome, and SHALL NOT return a raw machine-readable error body to a browser request.

#### Scenario: Unknown route
- **WHEN** a browser requests a route that does not exist
- **THEN** the response is a styled page with a way back to the home

#### Scenario: A machine client still gets a machine answer
- **WHEN** a client that does not accept HTML requests an unknown route
- **THEN** the response remains machine-readable
