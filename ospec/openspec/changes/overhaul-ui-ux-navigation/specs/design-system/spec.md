# Spec Delta

## Purpose

Define one visual language for the whole app: design tokens, shared components, responsive layouts, dark mode, and an accessibility baseline, all taken from the Outcomes page so the two existing visual languages become one.

## ADDED Requirements

### Requirement: Design Tokens
The system SHALL define color, spacing (on a 4px scale), radius, shadow, and type-scale values as CSS custom properties, taken from the Outcomes page. All page styles SHALL use these tokens instead of literal values.

#### Scenario: Consistent styling across pages
- **WHEN** any two pages each render a card
- **THEN** both cards use the same radius, padding, border, and shadow tokens

### Requirement: Status Scale
The system SHALL render initiative and outcome status using the status vocabulary the database itself defines, and SHALL NOT introduce a second set of status values. The vocabulary is enforced by the `Status` CHECK in `db/schema.sql`; this capability takes the values from there rather than restating them.

The committed vocabulary is `Not started`, `On track`, `At risk`, `Off track`, `Complete`, `Paused`, coloured as:

| Status (schema value) | Colour |
|---|---|
| On track | green |
| At risk | amber |
| Off track | red |
| Not started | grey |
| Complete | dark green |
| Paused | grey |

Each status SHALL always show a text label alongside its colour.

> **Reconciliation note.** The original draft of this requirement listed `Done | blue` and omitted `Complete` and `Paused`. The schema cannot store `Done`, and `Complete` and `Paused` are real stored values, so the table above uses the schema's vocabulary. This is the same rule the `status-presentation` capability (in `deepen-dashboard-modules`) already enforces — one vocabulary, read from the schema. Adding "Done" as a status is a separate data-model change and is out of scope here.

#### Scenario: Status pill
- **WHEN** an initiative with status "At risk" is displayed anywhere
- **THEN** it appears as an amber pill containing the text "At risk"

### Requirement: Shared Components
The system SHALL provide reusable components and use them on every page instead of browser-default controls:

- status pill
- progress bar
- initiative row
- stat tile
- card
- chip
- buttons (primary, secondary, ghost)
- form field
- drawer
- modal
- toast
- empty state
- breadcrumb

#### Scenario: Buttons are styled
- **WHEN** any form or dialog shows an action button
- **THEN** the button uses one of the defined button variants, and the primary action uses the primary variant

#### Scenario: Progress bar has its number
- **WHEN** a progress bar is shown
- **THEN** the percentage appears as text next to it, and the bar exposes `role="progressbar"` with `aria-valuenow`

### Requirement: Sample Data Banner
While the app runs on sample data, the system SHALL show one thin banner of at most 32px. The banner SHALL be dismissible for the session.

#### Scenario: Dismiss banner
- **WHEN** the user dismisses the sample-data banner
- **THEN** it stays hidden on later pages for that session, and a "Sample data" marker remains in the footer

### Requirement: Responsive Layout
The system SHALL support three layouts:

- **Up to 640px:** stacked cards and a collapsed nav
- **641–1024px:** two-column grids
- **Above 1024px:** full tables and multi-column grids

No layout SHALL scroll horizontally at the page level.

#### Scenario: Side-panel width
- **WHEN** the viewport is 726px wide
- **THEN** goal cards show in two columns, initiative rows fit on one line or wrap cleanly, and the page does not scroll horizontally

### Requirement: Dark Mode
The system SHALL follow the operating system's color-scheme preference and SHALL provide a dark set of every color token.

#### Scenario: OS in dark mode
- **WHEN** the user's OS prefers a dark color scheme
- **THEN** all pages render with the dark tokens, and status colors keep WCAG AA contrast

### Requirement: Accessibility Baseline
The system SHALL meet WCAG 2.1 AA for text contrast. It SHALL show visible focus indicators on all interactive elements. Every link and button SHALL have an accessible name. Every modal and drawer SHALL trap focus, close on Esc, and return focus to the element that opened it.

#### Scenario: Card links have names
- **WHEN** a screen reader reaches a goal card on the Overview
- **THEN** it announces the goal's name and initiative count

#### Scenario: Drawer focus
- **WHEN** a drawer opens
- **THEN** focus moves into the drawer, Tab cycles within it, and Esc closes it and returns focus to the row that opened it
