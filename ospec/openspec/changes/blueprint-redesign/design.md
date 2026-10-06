## Context

The app is server-rendered FastAPI + Jinja2 + htmx on SQLite at
`127.0.0.1:8000`. The design source is the Dean's prototype
(`cll-blueprint-2027.wag32002.chatgpt.site`), read in full: `index.html`,
`styles.css` (273 lines), `data.js` (6 priorities with `measure`/`target`/
`cadence`/`owner`/`colour`, 29 team KPIs, 4 teams).

Full rationale and the eight decisions taken with the user are in
`docs/superpowers/specs/2026-10-06-blueprint-redesign-design.md`.

The binding constraint is **Seq-1**: the design lands now, against Rev2's read
models as a stable interface, with the app still reading SQLite. The migration
(β) is a separate change.

## Goals / Non-Goals

- Goals: one visual language with hierarchy; every screen rebuilt on tokens; the
  meeting and outcomes keep working and stay printable; status stays the
  schema's, priority colour comes from the prototype.
- Non-Goals: the β migration; the KPI vocabulary; a new data model; extending
  `overhaul-ui-ux-navigation` rather than superseding it.

## Decisions

### D1 — D3 visual system: dark chrome, light content

Chrome (header, nav, footer) is GT navy `#003057` with a gold `#B3A369`
hairline. Content surfaces are light (`#F7F8FA` page, `#FFFFFF` card). The
accent is GT gold, not the prototype's cyan — the prototype's palette is
off-brand for a Georgia Tech audience.

*Why not the prototype's dark-blueprint theme:* it prints badly (the app has a
print-first meeting view) and reads heavy on a projector. *Why not plain light:*
that is the flatness being fixed.

### D2 — Serif headings, sans body

Headings use a Georgia stack; body stays system sans. This split is what gives
the prototype its gravitas and is the cheapest single de-flattening change.

### D3 — Layout borrowed, palette not

The stage, panels, cards, chips, stat tiles, and detail dialog are adopted from
the prototype's **structure**. Its dark palette, its KPI vocabulary, and its
"Coverage" meaning are not.

### D4 — The stage is the home

`/` becomes a hero stage: a Dean node → six priority cards (colour-keyed) → a
selected-priority panel → an initiative-signals strip. A tile grid cannot show
the relationship the stage shows.

### D5 — Detail is a drawer, and the rule is uniform

Anything reached from a list opens in a right-side drawer; anything bookmarkable
has a full page at the same URL. Endpoints serving both check `HX-Request` and
return a fragment or the full layout. This generalises the group-1 partial-
response fix from `overhaul-ui-ux-navigation`, which is carried over.

### D6 — The status vocabulary stays the schema's

`app/status.py` already reads the vocabulary from `db/schema.sql`'s `CHECK`.
This change **extends** that module with the priority colour scale; it does not
create a second status source. The prototype's scale said "Done", which the
schema cannot store.

### D7 — Coverage merges into checks

The prototype's Coverage view (target completeness) is a different question from
our data checks (data integrity). They join one admin page with two sections,
rather than becoming a top-level nav item.

### D8 — Supersede, carrying the work

`overhaul-ui-ux-navigation` is closed. Its 8 completed group-1 bug fixes and its
six spec deltas are carried in. Nothing is deleted.

## Risks / Trade-offs

- [Two palettes can drift] → both are token blocks in one file; the token test
  asserts no literal colour outside them.
- [Superseding an open change loses context] → its completed work is carried
  explicitly and the change is closed, not deleted.
- [Designing against read models the app does not yet read] → the models are
  live and tested (71 tests, 10/10 acceptance); β swaps the source under an
  existing design.
- [Dark chrome on a projector] → chrome is header/nav/footer only; content stays
  light.
- [Restyling 27 templates at once] → tokens and components first, then one page
  at a time, each group ending green.

## Migration Plan

1. Tokens and components (group 1), with the token test.
2. The stage and home (group 2).
3. The cascade drill-downs and indexes (group 3).
4. The drawer and its forms (group 4).
5. Navigation, coverage-checks, meeting and outcomes restyle (group 5).
6. Verification: visual at three widths, keyboard, print, suite green.

## Open Questions

- None blocking. Deferred to β: whether the cascade gains a team layer from the
  prototype's 29 team KPIs.
