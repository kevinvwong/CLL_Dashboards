# Identity colour is a code token, not a database column

**Status:** accepted (2026-10-07)

Goal, Team and Priority identity (colour, icon, order) lives in **code token
maps** keyed by ID — e.g. `P01 → var(--priority-1)` — and not in database
columns. `Priorities.Colour` already exists and holds a prototype hex
(`#53d7e8`), and nothing reads it: the home card resolves a CSS token by code,
while the initiative chips pass the stored hex into a filter that expects a
code (`P01`) and silently fall back to navy.

The deciding constraint is **dark mode**: a hex stored in a column cannot re-map
for the Night palette, whereas a CSS custom property can. A DB column would also
make colour an operator-editable setting, which it is not.

## Consequences
- One code→token map serves the card, the chip and the cascade; the chip
  fallback is fixed by using it.
- `Priorities.Colour` becomes vestigial; remove it in the model pass rather than
  leaving a second, unused source of colour.
- Seeded identity hexes must not be reintroduced as a "source of truth".
