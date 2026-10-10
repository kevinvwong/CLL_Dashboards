# Spec Delta

## MODIFIED Requirements

### Requirement: reads produce identical results across providers

Each ported read in `app/queries.py` SHALL return the same keys and values on
mssql as on sqlite for the same logical data, by aliasing on select where the two
schemas name a field differently.

#### Scenario: card parity

- **GIVEN** an initiative present in both stores
- **WHEN** `initiative_card` is called under each provider
- **THEN** the returned details, tags, connections, latest progress and diary are
  equal (same keys and values).

#### Scenario: read models are the source for matching cards

- **GIVEN** the goal, priority or person card
- **WHEN** read under `DB_PROVIDER=mssql`
- **THEN** its rows come from the corresponding Rev2 read model
  (`vw_goal_initiatives` / `vw_priority_initiatives` / `vw_person_portfolio`),
  so the documented Rev2 contract and the app agree by construction.

#### Scenario: current progress is derived

- **WHEN** any read needs an initiative's current progress or status
- **THEN** it is taken from the latest update (`vw_latest_update` /
  `vw_initiative_current`), never from a stored cache column.

#### Scenario: the full-page card renders its header once

- **GIVEN** the full-page team-initiative route requested directly (not as an
  HTMX fragment)
- **WHEN** the page renders
- **THEN** the initiative's code, level, name and description each appear
  **exactly once**, the page's `h1` precedes the content it titles, and the Dean
  initiatives it contributes to are listed once — sourced from the shared card
  fragment, which carries the linkable codes, rather than a second names-only
  copy appended below.

#### Scenario: the drawer fragment keeps its own header

- **GIVEN** the same route requested with `HX-Request` so the bare fragment is
  returned for the drawer
- **WHEN** the fragment renders
- **THEN** it still carries its own code, title and close control, because the
  drawer has no page heading to inherit.
