# Mock data vs confirmed data

The dashboard is honest about where its data comes from.

Every dataset carries a **provenance** marker:

- **mock** — illustrative working data, for building and reviewing the layout. It
  is seeded, and it is labelled on the page ("Illustrative — not CLL results").
- **confirmed** — imported from the owner-confirmed intake workbook, and labelled
  "Confirmed by each owner".

The label is driven by **how the data got there**, not by what it says. Mock data
that happens to name owners is still labelled mock, because naming an owner in a
placeholder is not the same as that owner confirming anything.

## How data becomes confirmed

1. An admin generates the intake workbook (it pre-fills the current values).
2. The team leads **confirm** their milestone lists and statuses in it.
3. The workbook is imported. That import replaces the working data and flips the
   marker from **mock** to **confirmed**.

## Why this matters

An executive audience is the worst place to show a fabricated number. So the
dashboard will show a **gap** — "owner not named yet" — rather than a guess, and it
will never label placeholder data as real.

Next: [Glossary](/guide/glossary).
