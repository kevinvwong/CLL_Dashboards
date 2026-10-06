# Change: Blueprint redesign

## Why

The dashboard is flat: every screen carries the same visual weight, there is no
structural hierarchy, and the only colour identity is a navy accent on white.
The Dean's own prototype is a far richer reference — a hero "blueprint stage", a
Dean node fanning into six colour-coded priority cards, panels, chips, a detail
dialog, and a per-priority colour scale.

This change adopts the prototype's **structure** while staying on Georgia Tech
brand and keeping the app's actual job — the Wednesday leadership meeting —
intact. It supersedes `overhaul-ui-ux-navigation`.

Full design: `docs/superpowers/specs/2026-10-06-blueprint-redesign-design.md`.

## What Changes

- **Visual system (D3).** Dark GT-navy chrome (header, nav, footer) over light
  content surfaces. GT gold accent. Serif headings, sans body. Token-driven
  throughout; `print.css` strips chrome and keeps content.
- **Blueprint home.** `/` becomes a hero stage: a Dean node fanning into six
  colour-coded priority cards, a selected-priority panel, and an
  initiative-signals strip.
- **Cascade drill-down.** `/goals/{n}` and `/priorities/{x}` rebuilt as a
  cascade: priority → initiatives, grouped, with relationships visible.
- **Detail as a drawer.** `/initiatives/{code}` opens in a right-side drawer
  from a list and as a full page on direct load; the update and edit forms open
  inside it.
- **Coverage merged into checks.** The prototype's "target completeness" idea
  joins the admin data-quality page.
- **Kept first-class:** `/meeting` (print-first) and `/oct16` → `/outcomes`
  (301 redirect).
- **Priority colour scale adopted** from the prototype as a six-value token set,
  used only as per-priority keys — never as status.

**No data-model change.** The status vocabulary stays the schema's; the app
still reads SQLite.

---

> **SCOPE CORRECTION, 2026-10-06 (after groups 1–5 were built).** The user
> corrected two things, and they dominate the design above:
>
> 1. **Do not replicate the Dean's prototype.** Its *look* is not the goal;
>    excellent design of our own is. The **blueprint home's hero stage — which
>    is the prototype's structure — is replaced**, not restyled.
> 2. **Include every field the prototype holds.** All of them, not the subset
>    we currently show.
>
> (2) is a **DATA-MODEL CHANGE**, and it is in scope. The prototype carries a
> layer our schema does not:
>
> | Layer | Fields | We hold |
> |---|---|---|
> | Priority (6) | code, title, short, description, **measure, target, cadence, owner**, colour | code, title, description, colour — **4 fields missing** |
> | Team KPI / goal (29) | id, area, sourceArea, number, title, strategy, initiatives, sourceTarget, proposedTarget, targetStatus, slide, priorities, status, note | **nothing** |
> | Team (4) | name, description | **nothing** |
> | Source area (5) | name | **nothing** |
> | Initiative (11) | name, progress | held |
>
> This **contradicts `config.yaml`'s "Nothing below D-1 (no tasks, no metrics)"**
> — recorded here deliberately, because the user has directed otherwise and the
> contradiction should not be silent.
>
> **Sequencing:** the data layer is built FIRST (it is the redesign's
> dependency), then the UI/UX is redesigned against it. The hero stage is
> removed as part of that.

## Capabilities

Every capability here is a new path: `openspec/specs/` holds no archived specs,
so all deltas are `ADDED`. The overlap with open changes is conceptual — where a
capability overlaps an existing delta, its requirements add to that behaviour.

### New Capabilities

- `visual-system`: the D3 token set — dark chrome, light content, GT gold accent,
  serif/sans type split, the status scale read from the schema, and the
  per-priority colour scale.
- `portfolio-dashboard`: the hero stage, Dean node, priority cards, selected-priority
  panel, and initiative-signals strip.
- `cascade-views`: the goal and priority drill-down, grouping, and relationship
  display.
- `initiative-drawer`: detail as a drawer from a list and a full page on direct
  load, with the partial-response rule and the in-drawer update/edit forms.
- `app-navigation`: the hybrid navigation, active state, breadcrumbs, search,
  the user menu, and styled error pages.
- `coverage-checks`: the merged coverage and data-quality page.

## Out of Scope

- **The β migration.** Porting the five SQL modules off SQLite, re-pointing the
  17 SQLite-coupled test files, seating Rev2 — its own change.
- **The prototype's KPI vocabulary.** `config.yaml` says "say initiative, never
  KPI"; this change keeps our words.
- **New data model.** Teams and team KPIs stay out; the 29 team KPIs are a β
  question.
- **`overhaul-ui-ux-navigation`.** Superseded, not extended. Its 8 completed
  group-1 fixes are carried over; the change itself is closed.
- Authentication, permissions, and the Rev2 schema.
- The meeting's and outcomes' *roles* — restyled only.

## Impact

- **Code:** `app/static/style.css` (token rewrite), `app/templates/*` (all 27),
  `app/main.py` (routes for the new surfaces), `app/queries.py` (reads shaped to
  the new screens), `app/status.py` (extended with the priority scale).
- **Tests:** new tests for the token set, the stage, the drawer, and print;
  existing suite kept green (352 at design time).
- **Supersede:** `overhaul-ui-ux-navigation` is closed; its completed work and
  six spec deltas are carried into this change.
- **Deployment:** none. The archive and runbook are unchanged.
