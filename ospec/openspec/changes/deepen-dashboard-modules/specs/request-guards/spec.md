# Spec Delta

## Purpose

Define how a request that names an initiative resolves what it is about and whether the caller may act, so the same ordering and permission rules hold on every route instead of being restated per handler.

## ADDED Requirements

### Requirement: Existence is decided before permission

The system SHALL answer a request about an unknown or retired initiative as not-found before it considers the caller's permission, so a code that does not exist is never reported as forbidden.

#### Scenario: Unknown code is not confused with a forbidden one
- **WHEN** a caller requests or posts to an initiative code that does not exist
- **THEN** the response is not-found, regardless of whether that caller would have been allowed to act on it

#### Scenario: Known but forbidden is forbidden
- **WHEN** a caller requests or posts to an initiative that exists but the caller may not act on
- **THEN** the response is forbidden

### Requirement: Permission is enforced on the server

The system SHALL decide on the server whether a caller may act, and SHALL refuse the action when they may not, independent of whether the interface offered the control.

#### Scenario: Posting without permission is refused
- **WHEN** a caller who is neither the owner, the Dean, nor an admin posts an action they may not perform
- **THEN** the server refuses the request rather than acting on it

#### Scenario: Hiding a control is not the control
- **WHEN** a control is absent from a page because the caller may not use it
- **THEN** posting the equivalent request directly is still refused

### Requirement: The caller's identity is resolved once per request

The system SHALL resolve the signed-in person, the target initiative, and the caller's permission once per request and SHALL treat the resolved person as present for any route that has passed the access gate.

#### Scenario: A gated route has a caller
- **WHEN** a request reaches a route that has passed the access gate
- **THEN** the caller's person record is available without the route re-reading or re-checking it

### Requirement: An admin-only route is gated in one place

The system SHALL refuse every admin-only route to a non-admin caller with the same rule, so the set of admin-only routes is declared rather than repeated.

#### Scenario: Non-admin refused on every admin-only route
- **WHEN** a non-admin caller reaches any admin-only route
- **THEN** the response is forbidden, and no route reaches its body
