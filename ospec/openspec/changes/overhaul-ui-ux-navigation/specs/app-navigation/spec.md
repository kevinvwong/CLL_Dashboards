# Spec Delta

## Purpose

Define the app-wide navigation, the stable route to the Dean's outcomes, the user menu, global search, breadcrumbs, the admin entry for data checks, and styled error pages, so every entity is reachable and no route is tied to a date.

## ADDED Requirements

### Requirement: Primary Navigation
The system SHALL show a primary navigation with Overview, Initiatives, People, Meeting, and Outcomes on every page. The item for the current section SHALL be marked active.

#### Scenario: Active section is indicated
- **WHEN** the user is on any page under `/initiatives`
- **THEN** the Initiatives item is visually marked active and has `aria-current="page"`

#### Scenario: Narrow viewport
- **WHEN** the viewport is 640px wide or less
- **THEN** the primary navigation collapses into a menu button that opens the full list

### Requirement: Stable Outcomes Route
The system SHALL serve the Dean's outcomes view at `/outcomes`. The system SHALL permanently redirect `/oct16` to `/outcomes`.

#### Scenario: Legacy link
- **WHEN** a user requests `/oct16`
- **THEN** the system responds with a 301 redirect to `/outcomes`

### Requirement: User Menu
The system SHALL show the current user in a menu at the top right. The menu SHALL contain Switch user. Switch user SHALL NOT appear in the primary navigation.

#### Scenario: Switching user
- **WHEN** the user opens the user menu and chooses Switch user
- **THEN** the user picker shows every person with their role, and the current user is marked

### Requirement: Admin Entry for Data Checks
The system SHALL move Data checks out of the primary navigation into an admin entry. When any check is failing, the entry SHALL show a badge with the count of failing checks.

#### Scenario: Failing checks
- **WHEN** two data checks are failing
- **THEN** the admin entry shows a badge reading "2"

#### Scenario: All checks pass
- **WHEN** no data checks are failing
- **THEN** the admin entry shows no badge

### Requirement: Global Search
The system SHALL provide a search box that opens with ⌘K or Ctrl+K. It SHALL return matches across initiatives (by ID or name), people, goals, and priorities.

#### Scenario: Search by initiative ID
- **WHEN** the user presses ⌘K and types "MAR-3"
- **THEN** the initiative MAR-3 appears as the first result, and pressing Enter opens its detail

#### Scenario: Keyboard dismissal
- **WHEN** the search box is open and the user presses Esc
- **THEN** the search box closes and focus returns to the element that had it before

### Requirement: Breadcrumbs
The system SHALL show breadcrumbs on every page below the top level. The breadcrumbs SHALL reflect how the page is reached in the site hierarchy.

#### Scenario: Initiative reached from a goal
- **WHEN** the user views initiative D-B at its full-page URL
- **THEN** breadcrumbs read "Overview › Initiatives › D-B", and each ancestor is a link

### Requirement: Styled Error Pages
The system SHALL render unknown routes and disallowed methods as a styled page that keeps the site layout. It SHALL NOT render raw JSON error bodies to browser requests.

#### Scenario: Unknown route
- **WHEN** a browser requests a route that does not exist
- **THEN** the system returns a 404 status with a styled page and a link back to Overview
