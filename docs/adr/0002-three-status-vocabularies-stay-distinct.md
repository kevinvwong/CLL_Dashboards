# Three status vocabularies stay distinct

**Status:** accepted (2026-10-07)

The app carries three status sets — Initiative (`Not started` / `On track` /
`At risk` / `Off track` / `Complete` / `Paused`), Milestone (`Met` /
`In progress` / `Not started` / `Missed`) and Outcome (`On track` / `At risk` /
`Behind` / `Not started`). They are **not** unified into one set, even though
"on track / at risk" appears in two of them.

The trade-off: a single vocabulary looks tidier and would let one legend serve
everywhere, but the three describe different kinds of thing — a body of work, a
checkable event, and a reported outcome — and their valid values genuinely
differ (a milestone is `Met` or `Missed`; an initiative never is). Collapsing
them would either force every entity to carry states it cannot be in, or
silently reinterpret one vocabulary as another in existing rows.

## Consequences
- Each status set has its own allowed values and its own glyphs; a shared
  colour axis (ADR-0003) is fine, a shared vocabulary is not.
- The word "**health**" is rejected as a synonym for "status"; see `CONTEXT.md`.
