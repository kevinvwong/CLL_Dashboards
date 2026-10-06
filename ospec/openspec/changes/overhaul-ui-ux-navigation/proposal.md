# Change: Overhaul UI/UX, navigation, and design system

> **Reconciliation note (added on import, 2026-10-06).** This change was authored
> against the running app and its proposal originally read *"all new; no specs
> exist yet."* That is no longer true: 24 capability deltas already exist across
> four open changes. This change **sits alongside** them rather than superseding
> them — see the Capabilities section — so the overlapping capabilities are
> declared as dependencies to reconcile, not as greenfield. If the intent is
> instead to supersede those changes, that decision must be made explicitly and
> the Capabilities section rewritten.

## Why

The Initiative Dashboard has two visual languages. The Outcomes page (`/oct16`)
uses cards, status pills, progress bars, and milestone rows. Every other page uses
plain lists, browser-default buttons, and unstyled forms. Several defects fall out
of that split, and the two highest-traffic workflows — posting an update and
running the weekly meeting — have the least design attention. Navigation also has
gaps: no initiative or people index, no search, no breadcrumbs, one nav item tied
to a date, and an admin tool in the main nav.

## What Changes

- **Bug fixes (verified against the code, 2026-10-06):**
  - The Edit details modal loads the full site layout (`edit_details.html extends
    base.html`). It must return only the form fragment for partial requests.
  - The standalone initiative page shows both "← Back" (`card_full.html`) and the
    modal's "×" (`_card_body.html`). The full page must drop the close control.
  - The list template renders its Dean list and the "D-1" divider
    unconditionally (`list.html`), so an empty side leaves orphaned chrome. The
    recorded symptom was "headers render in the wrong order", which does **not**
    reproduce — the order is already header-then-group — so this task is
    retargeted to suppressing empty-side chrome.
  - Rollup labels read "On track 10" instead of "10 initiatives · 10 on track".
  - "1 days" renders instead of "1 day".
  - `/initiatives` returns a 405 JSON body and `/people` a 404 JSON body; both
    need real pages, and unknown routes need a styled error page.
- **Navigation:** primary nav (Overview, Initiatives, People, Meeting, Outcomes);
  `/initiatives` and `/people` index pages; `/outcomes` with a 301 from `/oct16`;
  ⌘K/Ctrl+K search; breadcrumbs; a user menu holding Switch user; Data checks
  moved to an admin entry showing the failing-check count.
- **Design system:** design tokens and shared components extracted from the
  Outcomes page; responsive breakpoints, dark mode, and an accessibility baseline;
  a slimmer sample-data banner.
- **Portfolio views:** a portfolio health strip and status breakdowns on the
  Overview; a grouping toggle and single-click rows on goal and priority pages;
  stale flags on people pages.
- **Initiative detail:** a right-side drawer over the list, a new Update form
  (segmented status, slider plus number input, previous value, character counter),
  inline save with a toast, and an Edit details form covering owner, tags, tier,
  and the parent link.
- **Meeting review:** a three-part agenda, before/after deltas, quick ranges,
  presenter mode, and a print view.
- **Admin checks:** a rule-by-rule pass/fail list whose failures link to a fix.

No breaking changes to data. `/oct16` stays reachable through a redirect.

## Capabilities

All six are **new capability paths** — `openspec/specs/` holds no archived specs,
so there is no existing requirement text to modify. Every delta is therefore
`ADDED`. Measured 2026-10-06: a `MODIFIED` block against a capability with no
main spec makes `openspec validate` report the change **valid** (exit 0) while
warning *"Archive would refuse this delta: target spec does not exist; only ADDED
requirements are allowed for new specs."* A green validator now and a refusal at
archive is the failure to avoid, so nothing here is marked `MODIFIED`.

The overlap with the four open changes is **conceptual, not path-level** — the
capability paths differ even where the subject matter coincides. That overlap
still matters: it governs what each delta may say, and the archive order. Where a
capability overlaps an existing delta, its requirements **add to** the existing
behaviour and reference it, rather than restating it.

### New Capabilities

- `app-navigation`: the primary nav, the stable `/outcomes` route, the user menu,
  the admin checks entry, global search, breadcrumbs, and styled error pages.
- `admin-checks`: the rule-by-rule checks page with actionable failures.
- `design-system`: design tokens, shared components, responsive rules, dark mode,
  and the accessibility baseline. **Reconciles with `status-presentation`** (in
  `deepen-dashboard-modules`), which defines the status vocabulary as the single
  source, read from the schema's `CHECK`. This capability adds tokens and
  components and **references that vocabulary rather than restating it**. The
  original draft's scale table said "Done | blue", which the schema cannot store
  (`Not started`, `On track`, `At risk`, `Off track`, `Complete`, `Paused`), and
  omitted `Complete` and `Paused`; the corrected table is in
  `specs/design-system/spec.md` and `design.md`.
- `portfolio-views`: the portfolio health strip, status-breakdown cards, the
  `/initiatives` index, the `/people` index and person page, and grouped lists.
  **Reconciles with `strategy-navigation`** (goal and priority lists, rollups) and
  `person-card` (stale flags) in `add-initiative-dashboard-prototype`.
- `initiative-detail`: the detail drawer, the partial-response rule, the new
  Update form, inline save, and the expanded Edit details scope. **Reconciles
  with `initiative-card`** (card contents, direct URL) and `progress-updates`
  (the update form) in `add-initiative-dashboard-prototype`.
- `meeting-review`: the three-part agenda, before/after deltas, quick ranges,
  presenter mode, and the print view. **Reconciles with `meeting-view`** (changes
  since a date, attention list, print) in `add-initiative-dashboard-prototype`.

## Out of Scope

- **No change to the data model or the permissions model.** In particular the
  status vocabulary is the schema's; if the design's "Done" is wanted, renaming
  or extending the `Status` values is a separate data-model change.
- **No changes to authentication.** Switch user stays a prototype affordance.
- **No new computation or rollup of KPI values.** Counts by status only; the
  existing "no computed rollup" decision stands.
- **No search index or service.** Search reads the database per request; revisit
  above roughly 1,000 initiatives.
- **No work on the live deployment.** This change touches templates, routes, and
  styles, not the Azure deploy, the database, or the intake template.
- **Not a supersession of the four open changes.** Their capabilities are amended
  here, not replaced, unless that is decided explicitly.

## Impact

- **Specs:** 6 new capabilities (`app-navigation`, `admin-checks`,
  `design-system`, `portfolio-views`, `initiative-detail`, `meeting-review`),
  each reconciling with the corresponding delta in the four open changes.
- **Code:** the base layout and all page templates; the shared stylesheet; the
  initiative card partial endpoints; the update and edit handlers; the meeting
  query (adds "no update since"); new routes `/initiatives`, `/people`,
  `/outcomes`, `/search`.
- **Deployment:** none. The archive and runbook are unchanged.
